/* QuantForge V8.6 — observational benchmark, proxy-factor, valuation and drawdown study.
 * Pure session-local numeric calculations. No provider, storage, holdings or trading APIs.
 * ETF proxy regressions are NOT Fama–French factor estimates. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const sd=a=>{const m=mean(a);return Math.sqrt(a.reduce((s,x)=>s+(x-m)*(x-m),0)/(a.length-1));};
const date=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;
const MARKET=new Set(['SPY','VTI','VOO','IVV']);
const PROXY=new Set(['IWM','IWD','IVE','IWF','IWO','QQQ','VTV','VUG','VB','VBR']);
const between=(n,l,h)=>Math.max(l,Math.min(h,n));
function solve(matrix,vector){
 const n=vector.length,a=matrix.map((row,i)=>[...row,vector[i]]);
 for(let j=0;j<n;j++){
  let idx=j;
  for(let i=j+1;i<n;i++)if(Math.abs(a[i][j])>Math.abs(a[idx][j]))idx=i;
  if(!finite(a[idx][j])||Math.abs(a[idx][j])<1e-6)return null; // standardized, collinearity guard
  [a[idx],a[j]]=[a[j],a[idx]];
  const z=a[j][j];for(let k=j;k<=n;k++)a[j][k]/=z;
  for(let i=0;i<n;i++)if(i!==j){const f=a[i][j];for(let k=j;k<=n;k++)a[i][k]-=f*a[j][k];}
 }
 return a.map(row=>row[n]);
}
function regress(y,xs){
 const n=y.length,p=xs.length;
 if(n<126||n<=p+2)return {ready:false,reason:'At least 126 aligned daily return observations are needed.'};
 const means=xs.map(mean),scales=xs.map(sd);
 if(scales.some(s=>!finite(s)||s<1e-9))return {ready:false,reason:'A benchmark or proxy has insufficient return variation.'};
 const z=xs.map((xs0,i)=>xs0.map(x=>(x-means[i])/scales[i]));
 const cy=mean(y);
 const matrix=z.map(a=>z.map(b=>a.reduce((s,x,i)=>s+x*b[i],0)/(n-1)));
 const rhs=z.map(a=>a.reduce((s,x,i)=>s+x*(y[i]-cy),0)/(n-1));
 const bz=solve(matrix,rhs);
 if(!bz)return {ready:false,reason:'Benchmark and ETF proxy returns are highly collinear; regression withheld.'};
 const betas=bz.map((v,i)=>v/scales[i]);
 const intercept=cy-betas.reduce((s,b,i)=>s+b*means[i],0);
 const predicted=y.map((_,i)=>intercept+betas.reduce((s,b,j)=>s+b*xs[j][i],0));
 const sse=y.reduce((s,v,i)=>s+(v-predicted[i])**2,0);
 const sst=y.reduce((s,v)=>s+(v-cy)**2,0);
 if(sst<1e-15)return {ready:false,reason:'Candidate returns are essentially constant; model fit is undefined.'};
 const r2=between(1-sse/sst,0,1);
 const result={ready:true,coefficients:betas,rawDailyIntercept:intercept,r2,
  adjustedR2:1-(1-r2)*(n-1)/(n-p-1),residualAnnualVolatility:Math.sqrt(sse/(n-p-1))*Math.sqrt(252),observations:n};
 return Object.values(result).some(v=>typeof v==='number'&&!finite(v))?{ready:false,reason:'Unstable regression result withheld.'}:result;
}
function drawdown(prices,dates){
 let peak=prices[0],peakIndex=0,worst=0,worstIndex=0,worstPeakIndex=0,underwater=0,longest=0;
 for(let i=1;i<prices.length;i++){
  if(prices[i]>=peak){peak=prices[i];peakIndex=i;underwater=0;}
  else{underwater++;if(underwater>longest)longest=underwater;}
  const dd=prices[i]/peak-1;
  if(dd<worst){worst=dd;worstIndex=i;worstPeakIndex=peakIndex;}
 }
 const returns=prices.slice(1).map((x,i)=>x/prices[i]-1);
 const risk=[];
 for(let i=63;i<=returns.length;i++){
  const v=sd(returns.slice(i-63,i))*Math.sqrt(252);
  if(!finite(v))return {ready:false,reason:'Rolling volatility calculation failed.'};
  risk.push({date:dates[i],value:v});
 }
 const worst20=(()=>{
  if(prices.length<21)return null;
  let min=Infinity,start=0;
  for(let i=20;i<prices.length;i++){
   const r=prices[i]/prices[i-20]-1;
   if(r<min){min=r;start=i-20;}
  }
  return {change:min,from:dates[start],to:dates[start+20],start};
 })();
 return {ready:true,maxDrawdown:worst,drawdownPeak:dates[worstPeakIndex],drawdownTrough:dates[worstIndex],
  longestUnderwaterSessions:longest,underwaterNow:underwater,latestRolling63Volatility:risk.length?risk.at(-1).value:null,
  highestRolling63Volatility:risk.length?Math.max(...risk.map(x=>x.value)):null,
  rollingPoints:risk.filter((x,i)=>i%Math.max(1,Math.ceil(risk.length/24))===0).slice(-24),worst20};
}
function assess(input){
 const d=input&&typeof input==='object'?input:{};
 const h=d.history,symbol=d.symbol,selection=d.selection,benchmark=d.benchmark,proxies=d.proxies||[];
 if(!h||!Array.isArray(h.symbols)||!Array.isArray(h.dates)||!h.closes||typeof symbol!=='string'||!h.symbols.includes(symbol)||
  new Set(h.symbols).size!==h.symbols.length||!Array.isArray(selection)||selection.length!==h.symbols.length||new Set(selection).size!==selection.length||
  !h.symbols.every(x=>selection.includes(x))||h.symbols.length<2||h.symbols.length>5||
  h.dates.length<64||h.dates.length>2500||!h.dates.every((x,i)=>date(x)&&(!i||h.dates[i-1]<x))||
  h.symbols.some(s=>!Array.isArray(h.closes[s])||h.closes[s].length!==h.dates.length||h.closes[s].some(v=>!finite(v)||v<=0)))
  return {ready:false,reason:'Reload valid, matching investment history before performing V8.6 analysis.'};
 const allReturns={};for(const sym of h.symbols){const px=h.closes[sym];allReturns[sym]=px.slice(1).map((x,i)=>x/px[i]-1);}
 const stockSession=h.sessions_per_year!==365&&!String(h.calendar||'').toLowerCase().includes('mixed')&&
  !String(h.calendar||'').toLowerCase().includes('crypto');
 const candidate=allReturns[symbol],risk=stockSession?drawdown(h.closes[symbol],h.dates):{ready:false,reason:'Stock-session risk scaling is withheld for crypto or mixed trading calendars.'};
 if(risk.ready&&risk.worst20){const a=risk.worst20;delete a.start;}
 const metrics={ready:false,reason:'Select a loaded broad-market ETF (SPY, VTI, VOO, IVV) to estimate benchmark-relative exposure.'};
 let market=metrics;
 if(benchmark){
  if(!stockSession)market={ready:false,reason:'Market ETF regressions require equity-session history, not crypto or mixed trading calendars.'};
  else if(!MARKET.has(benchmark)||!h.symbols.includes(benchmark)||benchmark===symbol)
   market={ready:false,reason:'The benchmark must be an independently loaded broad-market ETF, different from the candidate.'};
  else if(!Array.isArray(proxies)||proxies.length>2||new Set(proxies).size!==proxies.length||
    proxies.some(x=>!PROXY.has(x)||x===benchmark||x===symbol||!h.symbols.includes(x)))
   market={ready:false,reason:'Choose at most two distinct, loaded ETF proxies different from the candidate and market benchmark.'};
  else{
   const m=allReturns[benchmark];const main=regress(candidate,[m]);
   if(!main.ready)market=main;
   else{
    const spreads=proxies.map(s=>allReturns[s].map((x,i)=>x-m[i]));
    const multi=spreads.length?regress(candidate,[m,...spreads]):null;
    const n=candidate.length;
    const yMean=mean(candidate),mMean=mean(m);
    market={ready:true,benchmark,proxies:[...proxies],observations:n,from:h.dates[0],to:h.dates.at(-1),
     singleBeta:main.coefficients[0],marketCorrelation:between((main.coefficients[0]*sd(m))/sd(candidate),-1,1),
     singleR2:main.r2,singleRawDailyIntercept:main.rawDailyIntercept,
     multi:multi||{ready:false,reason:'No additional ETF proxy selected.'},
     marketPeriodReturn:h.closes[benchmark].at(-1)/h.closes[benchmark][0]-1,
     candidatePeriodReturn:h.closes[symbol].at(-1)/h.closes[symbol][0]-1};
    if(multi&&multi.ready)market.multi={...multi,predictorLabels:['Market ETF ('+benchmark+')',...proxies.map(s=>s+' minus '+benchmark)]};
   }
  }
 }
 const value=d.value,yrs=d.years;
 let valuation={ready:false,reason:'Fresh observed-price P/S and current quote are required for a sensitivity grid.'};
 if(yrs!==1&&yrs!==3)valuation={ready:false,reason:'Choose a one-year or three-year scenario horizon.'};
 else if(value?.symbol!==symbol||value?.valid!==true||!finite(value.price)||value.price<=0||
  !finite(value.pSales)||value.pSales<=0||!date(String(value.priceTime||'').slice(0,10)))
  valuation={ready:false,reason:'Valid observed quote, annual revenue, and SEC share count are not jointly available. No implied prices shown.'};
 else {
  const growth=[-.05,.05,.15],multiple=[.70,1,1.30];
  valuation={ready:true,years:yrs,observedPrice:value.price,observedPS:value.pSales,quoteTime:value.priceTime,
   revenueGrowthAssumptions:growth,multipleAssumptions:multiple,
   scenarios:growth.flatMap(g=>multiple.map(k=>({growth:g,multipleRatio:k,
    impliedPrice:value.price*(1+g)**yrs*k,priceChange:(1+g)**yrs*k-1}))).filter(x=>finite(x.impliedPrice)&&x.impliedPrice>0),
   assumptions:'Constant share count; projected annual revenue growth; terminal P/S as a percentage of observed P/S. Excludes dilution, dividends, taxes, and discounting. Not an intrinsic valuation or price recommendation.'};
 }
 return {ready:true,symbol,history:{from:h.dates[0],to:h.dates.at(-1),observations:candidate.length},market,risk,valuation,
  limitations:['A broad-market ETF is a tradable tracking proxy, not the underlying index total-return series. Prices may omit distributions.',
   'Proxy spreads are observed ETF returns minus broad-market ETF returns, not Fama–French SMB/HML or a cost-of-capital model.',
   'Raw-return regression intercept is NOT risk-free-adjusted CAPM alpha. Regression estimates are in-sample and can be unstable.',
   'Historical worst-window losses and rolling volatility are not forecasts or event probabilities.',
   'Valuation sensitivity is conditional arithmetic on the quoted price, revenue growth and P/S multiple; not a fair-value estimate.']};
}
const api=Object.freeze({assess});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateFactorScenariosV86=api;
})(typeof window!=='undefined'?window:globalThis);
