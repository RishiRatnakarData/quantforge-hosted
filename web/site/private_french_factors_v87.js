/* QuantForge V8.7 — independently sourced Fama–French three-factor research.
 * No API, provider, storage, account, or trading mutations. Research-only pure module.
 * Imported daily factor observations are user supplied, not automatically authenticated. */
(function(root){
'use strict';
const finite = x => typeof x === 'number' && Number.isFinite(x);
const average = a => a.reduce((s,x)=>s+x,0)/a.length;
const validDate = s => /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(Date.parse(s)) && new Date(s).toISOString().slice(0,10)===s;
function invertSolve(matrix, vector) {
 const n=vector.length,a=matrix.map((row,i)=>[...row,vector[i]]);
 for(let j=0;j<n;j++){
  let pivot=j;for(let i=j+1;i<n;i++)if(Math.abs(a[i][j])>Math.abs(a[pivot][j]))pivot=i;
  if(!finite(a[pivot][j])||Math.abs(a[pivot][j])<1e-10)return null;
  [a[j],a[pivot]]=[a[pivot],a[j]];
  const value=a[j][j];for(let k=j;k<=n;k++)a[j][k]/=value;
  for(let i=0;i<n;i++)if(i!==j){const factor=a[i][j];for(let k=j;k<=n;k++)a[i][k]-=factor*a[j][k];}
 }
 return a.map(row=>row[n]);
}
function parseDateCompact(str){
 if(!/^\d{8}$/.test(str))return null;
 const date=str.slice(0,4)+'-'+str.slice(4,6)+'-'+str.slice(6,8);
 return validDate(date)?date:null;
}
function parseDailyCsv(csv){
 if(typeof csv!=='string'||!csv.trim()||csv.length>3_000_000)throw new Error('Choose an extracted daily factor CSV smaller than 3 MB.');
 const lines=csv.replace(/^\uFEFF/,'').split(/\r?\n/);
 const headerIndex=lines.findIndex(s=>/\bMkt-RF\s*,\s*SMB\s*,\s*HML\s*,\s*RF\b/i.test(s));
 if(headerIndex<0)throw new Error('The file lacks the expected daily Fama–French 3-factor columns: Mkt-RF, SMB, HML, RF.');
 const rows=[],seen=new Set();let missing=0,dated=0;
 for(const line of lines.slice(headerIndex+1)){
  const cols=line.trim().replace(/^"|"$/g,'').split(',').map(x=>x.trim());
  if(!/^\d{8}$/.test(cols[0]))continue; // footnotes and monthly/annual blocks are not observations
  const day=parseDateCompact(cols[0]);if(!day)throw new Error('Invalid YYYYMMDD factor date.');
  if(seen.has(day))throw new Error('Duplicate daily factor date: '+day);
  seen.add(day);dated++;
  if(cols.length!==5)throw new Error('Expected four numeric factor fields on '+day+'.');
  const vals=cols.slice(1).map(Number);
  if(cols.slice(1).some(x=>x==='')||vals.some(x=>!finite(x)))throw new Error('Nonnumeric factor return on '+day+'.');
  if(vals.some(x=>x===-99.99||x===-999)){missing++;continue;}
  if(vals.slice(0,3).some(x=>Math.abs(x)>50)||Math.abs(vals[3])>5)
   throw new Error('Factor values are outside a plausible daily percentage range on '+day+'. Check file frequency and units.');
  rows.push({date:day,mkt:vals[0]/100,smb:vals[1]/100,hml:vals[2]/100,rf:vals[3]/100});
 }
 if(rows.length<200)throw new Error('At least 200 valid daily factor rows are required. Do not use the monthly factor file.');
 if(rows.some((v,i)=>i>0&&rows[i-1].date>=v.date))throw new Error('Factor dates must be strictly ascending.');
 return {source:'User-imported Kenneth French daily FF3-format CSV (source not authenticated)',rows,available:rows.length,missing,
  from:rows[0].date,to:rows.at(-1).date,dated};
}
function fit(rows){
 const n=rows.length,k=4;
 const xraw=rows.map(r=>[r.mkt,r.smb,r.hml]);
 const means=[0,1,2].map(j=>average(xraw.map(x=>x[j])));
 const sd=[0,1,2].map(j=>Math.sqrt(xraw.reduce((s,x)=>s+(x[j]-means[j])**2,0)/(n-1)));
 if(sd.some(x=>!finite(x)||x<1e-8))return {ready:false,reason:'A factor has insufficient variation for a stable regression.'};
 const X=xraw.map(x=>[1,...x.map((v,j)=>(v-means[j])/sd[j])]);
 const y=rows.map(r=>r.excess);
 const xtx=Array.from({length:k},(_,i)=>Array.from({length:k},(_,j)=>X.reduce((s,x)=>s+x[i]*x[j],0)));
 const xty=Array.from({length:k},(_,i)=>X.reduce((s,x,j)=>s+x[i]*y[j],0));
 const b=invertSolve(xtx,xty);
 if(!b)return {ready:false,reason:'The factor series are collinear; model withheld.'};
 const predicted=X.map(x=>x.reduce((s,v,j)=>s+v*b[j],0));
 const residual=y.map((v,i)=>v-predicted[i]);
 const total=y.reduce((s,v)=>s+(v-average(y))**2,0);
 const sse=residual.reduce((s,v)=>s+v*v,0);
 if(total<1e-15)return {ready:false,reason:'The candidate has essentially zero excess-return variation.'};
 const coeff=b.slice(1).map((v,j)=>v/sd[j]);
 const intercept=b[0]-coeff.reduce((s,v,j)=>s+v*means[j],0);
 // Newey–West/Bartlett lag 5 heteroskedasticity and autocorrelation-consistent covariance.
 const meat=Array.from({length:k},()=>Array(k).fill(0));
 function add(i,j,weight){
  const cross=residual[i]*residual[j]*weight;
  for(let a=0;a<k;a++)for(let c=0;c<k;c++)meat[a][c]+=cross*X[i][a]*X[j][c];
 }
 for(let t=0;t<n;t++)add(t,t,1);
 for(let lag=1;lag<=5;lag++){
  const w=1-lag/6;
  for(let t=lag;t<n;t++){add(t,t-lag,w);add(t-lag,t,w);}
 }
 const inverse=Array.from({length:k},(_,j)=>invertSolve(xtx,Array.from({length:k},(_,i)=>i===j?1:0)));
 if(inverse.some(x=>!x))return {ready:false,reason:'Regression covariance could not be estimated.'};
 const inv=Array.from({length:k},(_,i)=>Array.from({length:k},(_,j)=>inverse[j][i]));
 const variance=Array.from({length:k},(_,i)=>Array.from({length:k},(_,j)=>{
  let v=0;for(let a=0;a<k;a++)for(let c=0;c<k;c++)v+=inv[i][a]*meat[a][c]*inv[j][c];
  return v;
 }));
 // Transform standardized regression coefficients to alpha and raw factor coefficients.
 const transform=[ [1,...means.map((m,j)=>-m/sd[j])], [0,1/sd[0],0,0],[0,0,1/sd[1],0],[0,0,0,1/sd[2]] ];
 const se=transform.map(T=>{
  let v=0;for(let i=0;i<k;i++)for(let j=0;j<k;j++)v+=T[i]*variance[i][j]*T[j];
  return Math.sqrt(Math.max(0,v));
 });
 const r2=1-sse/total;
 const result={ready:true,alphaDaily:intercept,alphaAnnualApprox:intercept*252,
  alphaAnnualCi95:[(intercept-1.96*se[0])*252,(intercept+1.96*se[0])*252],
  factorBetas:coeff,factorHacSe:se.slice(1),alphaHacSeDaily:se[0],
  r2,adjustedR2:1-(1-r2)*(n-1)/(n-k),observations:n,
  residualAnnualVolatility:Math.sqrt(sse/(n-k))*Math.sqrt(252),hacLag:5};
 if([result.alphaDaily,...coeff,...se,...result.alphaAnnualCi95,result.r2,result.adjustedR2].some(x=>!finite(x)))
  return {ready:false,reason:'Unstable regression diagnostics withheld.'};
 return result;
}
function assess({history,selection,symbol,factors}={}){
 const h=history;
 if(!h||!Array.isArray(h.symbols)||!Array.isArray(h.dates)||!h.closes||
  !Array.isArray(selection)||selection.length!==h.symbols.length||new Set(selection).size!==selection.length||
  !h.symbols.every(s=>selection.includes(s))||typeof symbol!=='string'||!h.symbols.includes(symbol)||
  !Array.isArray(h.closes[symbol])||h.closes[symbol].length!==h.dates.length||
  h.dates.length<201||h.dates.length>2500||
  h.dates.some((d,i)=>!validDate(d)||(i>0&&h.dates[i-1]>=d))||
  h.closes[symbol].some(v=>!finite(v)||v<=0))return {ready:false,reason:'Reload valid matching historical prices and select an investment.'};
 if(h.sessions_per_year===365||/crypto|mixed/i.test(String(h.calendar||'')))
  return {ready:false,reason:'Daily U.S. equity factors cannot be fitted to crypto or mixed-calendar observations.'};
 if(!factors||!Array.isArray(factors.rows)||factors.rows.length<200)
  return {ready:false,reason:'Import an extracted Fama–French daily three-factor CSV first.'};
 const map=new Map(factors.rows.map(r=>[r.date,r]));
 if(map.size!==factors.rows.length)return {ready:false,reason:'Duplicate imported factor dates.'};
 const records=[];
 for(let i=1;i<h.dates.length;i++){
  const f=map.get(h.dates[i]);if(!f)continue; // exact-date join, never forward fill
  const ret=h.closes[symbol][i]/h.closes[symbol][i-1]-1;
  if(!finite(ret)||ret<=-1)return {ready:false,reason:'Invalid observed candidate price return.'};
  records.push({...f,excess:ret-f.rf});
 }
 if(records.length<200)return {ready:false,reason:'Only '+records.length+' matching daily factor/price dates. Load at least one year of equity history with 200 aligned returns.'};
 const split=Math.floor(records.length*.7);
 if(split<126||records.length-split<60)return {ready:false,reason:'Insufficient chronological train/holdout sample.'};
 const model=fit(records);
 const train=fit(records.slice(0,split));
 if(!model.ready||!train.ready)return {ready:false,reason:model.ready?train.reason:model.reason};
 const test=records.slice(split);
 const predictions=test.map(r=>train.alphaDaily+train.factorBetas[0]*r.mkt+train.factorBetas[1]*r.smb+train.factorBetas[2]*r.hml);
 const sse=test.reduce((s,r,i)=>s+(r.excess-predictions[i])**2,0);
 const trainMean=average(records.slice(0,split).map(r=>r.excess));
 const baselineSse=test.reduce((s,r)=>s+(r.excess-trainMean)**2,0);
 if(baselineSse<1e-14)return {ready:false,reason:'Holdout excess returns have insufficient variation for validation.'};
 const rmse=Math.sqrt(sse/test.length);
 const baselineRmse=Math.sqrt(baselineSse/test.length);
 return {ready:true,symbol,source:factors.source||'User-imported daily FF3-format CSV (unverified)',
  factorRange:[factors.from,factors.to],aligned:records.length,from:records[0].date,to:records.at(-1).date,
  excludedPrices:h.dates.length-1-records.length,model,
  holdout:{train:split,test:test.length,trainThrough:records[split-1].date,testFrom:records[split].date,
   testThrough:records.at(-1).date,rmse,baselineRmse,r2:1-sse/baselineSse,
   interpretation:'Coefficient stability with realized contemporaneous factors; NOT an executable return forecast.'},
  limitations:['Source CSV was imported by the user; its identity and release version have not been cryptographically verified.',
   'Excess candidate price returns use the dataset RF; this is not dividend-adjusted unless the loaded series includes distributions.',
   'FF3 factors represent U.S. equity research portfolios; not suitable for crypto, international or mixed trading calendars.',
   'Alpha and betas describe historical linear co-movement, not a guaranteed return or causal relationship.',
   'Newey–West lag-5 intervals are approximate. The chronological holdout uses realized factor values after the fact, so it tests stability, not investable forecasting.']};
}
const api=Object.freeze({parseDailyCsv,assess});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateFrenchFactorsV87=api;
})(typeof window!=='undefined'?window:globalThis);
