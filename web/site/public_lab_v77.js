/* QuantForge V7.7: accessible public analysis dashboard. SEC facts and synthetic modeling never mix. */
(function(root){
'use strict';
const names=['US equity basket','Technology basket','Investment-grade bonds','International equity','Gold exposure'];
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const round=(x,d=1)=>finite(x)?x.toFixed(d):'—';
const percent=(x,d=1)=>finite(x)?`${(100*x).toFixed(d)}%`:'—';
const toMoney=x=>finite(x)?'$'+(x/1e9).toFixed(2)+'B':'Unavailable';
function synthetic(count=360,seed=7707){
 let x=seed>>>0;
 const uniform=()=>{x=(1664525*x+1013904223)>>>0;return (x+.5)/4294967296;};
 const normal=()=>Math.sqrt(-2*Math.log(uniform()))*Math.cos(2*Math.PI*uniform());
 const drift=[.00023,.00028,.00007,.00017,.00008];
 const vol=[.0085,.013,.003,.0095,.0075];
 const data=[];
 for(let t=0;t<count;t++){
  const broad=normal(),rates=normal(),defensive=normal();
  data.push(vol.map((v,i)=>{
   const marketWeight=[.83,1.02,-.25,.71,.12][i];
   const defensiveWeight=[.05,.04,.66,.10,.67][i];
   const noise=.40*normal();
   return drift[i]+v*(.65*marketWeight*broad+.45*defensiveWeight*defensive+.18*rates+noise);
  }));
 }
 return data;
}
function covariance(data,shrink=.12){
 if(!Array.isArray(data)||data.length<3||data.some(r=>!Array.isArray(r)||r.length!==5||r.some(x=>!finite(x))))throw Error('Invalid or insufficient training returns');
 const n=data.length,k=5,mean=Array.from({length:k},(_,j)=>data.reduce((a,r)=>a+r[j],0)/n);
 const cov=Array.from({length:k},()=>Array(k).fill(0));
 for(const row of data)for(let i=0;i<k;i++)for(let j=0;j<k;j++)cov[i][j]+=(row[i]-mean[i])*(row[j]-mean[j])/(n-1);
 for(let i=0;i<k;i++)for(let j=0;j<k;j++)if(i!==j)cov[i][j]*=(1-shrink);
 return cov;
}
function project(v,cap){
 const n=v.length;
 if(!(cap>0&&cap<=1&&n*cap>=1-1e-10))throw Error('The investment weight limit makes the portfolio infeasible');
 let lo=Math.min(...v)-1,hi=Math.max(...v)+1;
 for(let k=0;k<90;k++){
  const mid=(lo+hi)/2,sum=v.reduce((a,vi)=>a+Math.max(0,Math.min(cap,vi-mid)),0);
  if(sum>1)lo=mid;else hi=mid;
 }
 const weights=v.map(vi=>Math.max(0,Math.min(cap,vi-(lo+hi)/2)));
 // Correct rounding residue without changing feasibility.
 let diff=1-weights.reduce((a,b)=>a+b,0);
 for(let i=0;i<n&&Math.abs(diff)>1e-11;i++){
  const change=diff>0?Math.min(diff,cap-weights[i]):Math.max(diff,-weights[i]);
  weights[i]+=change;diff-=change;
 }
 return weights;
}
function variance(w,cov){return w.reduce((s,wi,i)=>s+wi*cov[i].reduce((a,c,j)=>a+c*w[j],0),0);}
function optimize(cov,cap=.55){
 if(!Array.isArray(cov)||cov.length!==5||cov.some((row,i)=>!Array.isArray(row)||row.length!==5||row.some((v,j)=>!finite(v)||Math.abs(v-cov[j]?.[i])>1e-8)))throw Error('Covariance matrix must be finite and symmetric');
 const maxRow=Math.max(...cov.map(row=>row.reduce((a,x)=>a+Math.abs(x),0)));
 const step=1/(2*Math.max(maxRow,1e-10));
 let w=Array(5).fill(.2);
 for(let i=0;i<1100;i++){
  const grad=w.map((_,j)=>2*cov[j].reduce((acc,v,k)=>acc+v*w[k],0));
  const next=project(w.map((v,j)=>v-step*grad[j]),cap);
  const change=next.reduce((a,v,j)=>a+Math.abs(v-w[j]),0);
  w=next;if(change<1e-11)break;
 }
 return w;
}
function modeledRisk(returns,cap=.55){
 const cov=covariance(returns),optimal=optimize(cov,cap),equal=Array(5).fill(.2);
 return {cov,optimal,equal,volOptimal:Math.sqrt(Math.max(0,variance(optimal,cov))*252),volEqual:Math.sqrt(Math.max(0,variance(equal,cov))*252)};
}
function drawdown(wealth){let peak=wealth[0],worst=0;for(const w of wealth){peak=Math.max(peak,w);worst=Math.min(worst,w/peak-1);}return worst;}
function walkforward(data,{train=120,feeBps=10,cap=.55,test=20}={}){
 if(!Array.isArray(data)||data.length<train+test||!Number.isInteger(train)||train<60||!Number.isInteger(test)||test<1||!finite(feeBps)||feeBps<0||feeBps>100)throw Error('Invalid evaluation settings');
 const paths={optimized:[1],equal:[1]},weights={optimized:Array(5).fill(.2),equal:Array(5).fill(.2)},fees={optimized:0,equal:0},windows=[];
 for(let start=train;start<data.length;start+=test){
  const risk=modeledRisk(data.slice(start-train,start),cap);
  const planned={optimized:risk.optimal,equal:risk.equal};
  const begin=paths.optimized.length-1;
  const rebalanceValue={};
  for(const key of ['optimized','equal']){
   const turnover=planned[key].reduce((acc,w,i)=>acc+Math.abs(w-weights[key][i]),0);
   const fee=turnover*feeBps/10000;
   const prior=paths[key][paths[key].length-1];
   rebalanceValue[key]=prior*(1-fee);
   fees[key]+=fee;
   weights[key]=planned[key].slice();
  }
  const first=start,last=Math.min(data.length,start+test);
  for(let t=first;t<last;t++){
   for(const key of ['optimized','equal']){
    const oldW=weights[key],r=oldW.reduce((acc,w,j)=>acc+w*data[t][j],0);
    const previous=t===first?rebalanceValue[key]:paths[key][paths[key].length-1];
    paths[key].push(previous*(1+r));
    weights[key]=oldW.map((w,j)=>w*(1+data[t][j])/(1+r));
   }
  }
  windows.push({trainStart:start-train+1,trainEnd:start,testStart:first+1,testEnd:last,optimized:paths.optimized.at(-1),equal:paths.equal.at(-1),start:begin});
 }
 return {paths,fees,windows,maxDrawdown:{optimized:drawdown(paths.optimized),equal:drawdown(paths.equal)},train,feeBps,cap};
}
function secSeries(snapshot,symbol){
 if(!Array.isArray(snapshot?.companies))return [];
 const issuer=snapshot.companies.find(c=>c.symbol===symbol);
 if(!issuer||!Array.isArray(issuer.annual))return [];
 return issuer.annual.filter(a=>a&&typeof a.fiscal_end==='string'&&finite(a.metrics?.revenue_usd)&&a.metrics.revenue_usd>0)
  .map(a=>({end:a.fiscal_end,revenue:a.metrics.revenue_usd,operating:finite(a.metrics.operating_income_usd)?a.metrics.operating_income_usd:null}))
  .sort((a,b)=>a.end.localeCompare(b.end));
}
function trend(series){
 return series.map((r,i)=>({...r,margin:finite(r.operating)?r.operating/r.revenue:null,growth:i&&series[i-1].revenue>0?r.revenue/series[i-1].revenue-1:null}));
}
function lineChart(series,{title='Model series',labelA='Optimized',labelB='Equal weight'}={}){
 if(!series?.length||series.every(s=>s.length<2))return '<p>Insufficient chart data.</p>';
 const values=series.flat().filter(finite);
 const lo=Math.min(...values),hi=Math.max(...values),pad=(hi-lo||Math.abs(hi)||1)*.12;
 const min=lo-pad,max=hi+pad,width=690,height=285,plotW=610,plotH=209;
 const x=(i,n)=>52+plotW*(n<=1?0:i/(n-1)),y=v=>20+plotH*(max-v)/(max-min);
 const lines=series.map((s,i)=>`<polyline fill="none" stroke="${i?'#b87935':'#16705d'}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" points="${s.map((v,j)=>`${x(j,s.length).toFixed(2)},${y(v).toFixed(2)}`).join(' ')}"/>`).join('');
 const grid=[0,.25,.5,.75,1].map(t=>`<line x1="52" x2="662" y1="${20+209*t}" y2="${20+209*t}" stroke="#dceae2"/><text x="46" y="${24+209*t}" font-size="11" fill="#536d61" text-anchor="end">${round(max-(max-min)*t,2)}</text>`).join('');
 return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(title)}: ${esc(labelA)} compared with ${esc(labelB)} across evaluation sessions"><title>${esc(title)}</title>${grid}${lines}<text x="360" y="263" font-size="12" text-anchor="middle" fill="#536d61">Out-of-sample sessions →</text></svg><div class="lab-legend"><span><i class="lab-key" style="background:#16705d"></i>${esc(labelA)}</span><span><i class="lab-key" style="background:#b87935"></i>${esc(labelB)}</span></div>`;
}
function secChart(rows){
 if(rows.length<2)return '<p>At least two annual records are required.</p>';
 const vals=rows.map(r=>r.revenue/1e9),maximum=Math.max(...vals)*1.17;
 const barW=650/rows.length*.54;
 const bars=rows.map((r,i)=>{
  const x=60+(i+.5)*625/rows.length-barW/2,h=180*vals[i]/maximum;
  return `<rect x="${round(x,2)}" y="${round(222-h,2)}" width="${round(barW,2)}" height="${round(h,2)}" rx="3" fill="#287d69"><title>${esc(r.end)} annual revenue ${esc(toMoney(r.revenue))}</title></rect><text x="${round(x+barW/2,2)}" y="241" text-anchor="middle" font-size="10" fill="#536d61">${esc(r.end.slice(0,4))}</text>`;
 }).join('');
 return `<svg viewBox="0 0 735 260" role="img" aria-label="Reported annual revenue by fiscal year in billions of US dollars"><title>Annual reported revenue (US dollars)</title><line x1="45" x2="704" y1="222" y2="222" stroke="#a3b9ad"/>${bars}<text x="8" y="25" fill="#536d61" font-size="12">Revenue ($B)</text></svg>`;
}
function marginChart(rows){
 const valid=rows.filter(r=>finite(r.margin));
 if(valid.length<2)return '<p class="tiny">A margin trend is unavailable because fewer than two operating-income observations are comparable.</p>';
 const values=valid.map(r=>r.margin*100),lo=Math.min(...values),hi=Math.max(...values),pad=(hi-lo||10)*.22;
 const min=lo-pad,max=hi+pad;
 const x=i=>48+(i/(rows.length-1))*625,y=v=>20+(180*(max-v)/(max-min));
 const segments=[];let current=[];
 for(let i=0;i<rows.length;i++){
  if(!finite(rows[i].margin)){if(current.length>1)segments.push(current);current=[];continue;}
  current.push(`${round(x(i),2)},${round(y(rows[i].margin*100),2)}`);
 }
 if(current.length>1)segments.push(current);
 const lines=segments.map(points=>`<polyline fill="none" stroke="#b87935" stroke-width="3" stroke-linejoin="round" points="${points.join(' ')}"/>`).join('');
 const dots=rows.map((r,i)=>finite(r.margin)?`<circle cx="${round(x(i),2)}" cy="${round(y(r.margin*100),2)}" r="4.5" fill="#b87935"><title>FY ${esc(r.end)} operating margin ${percent(r.margin)}</title></circle>`:'').join('');
 const labels=rows.map((r,i)=>`<text x="${round(x(i),2)}" y="225" text-anchor="middle" fill="#64786e" font-size="10">${esc(r.end.slice(0,4))}</text>`).join('');
 return `<svg viewBox="0 0 735 249" role="img" aria-label="Operating margin over reported annual fiscal years, percent"><title>SEC operating margin trend (percent)</title><line x1="45" x2="700" y1="200" y2="200" stroke="#b9cdc0"/>${lines}${dots}${labels}<text x="8" y="16" fill="#64786e" font-size="12">Operating margin (%)</text></svg>`;
}
function renderSec(snapshot,symbol){
 const company=snapshot?.companies?.find(c=>c.symbol===symbol),rows=trend(secSeries(snapshot,symbol));
 if(!company||!rows.length)return '<p class="notice">The reviewed SEC snapshot has no comparable annual figures for this issuer. No observations have been invented.</p>';
 const current=rows.at(-1),previous=rows.at(-2);
 const impact=current.growth===null?'Revenue growth is unavailable.':`Reported revenue ${current.growth>=0?'increased':'decreased'} ${percent(Math.abs(current.growth))} versus the preceding available fiscal record.`;
 const table=rows.map(r=>`<tr><td>${esc(r.end)}</td><td>${toMoney(r.revenue)}</td><td>${percent(r.growth)}</td><td>${percent(r.margin)}</td></tr>`).join('');
 const source=String(company.source_url||'');
 const href=/^https:\/\/data\.sec\.gov\/api\/xbrl\/companyfacts\/CIK\d{10}\.json$/.test(source)?` <a href="${esc(source)}" target="_blank" rel="noopener noreferrer">SEC Company Facts</a>`:'';
 return `<div class="lab-metrics"><div><small>Latest reported revenue</small><strong>${toMoney(current.revenue)}</strong></div><div><small>Change vs prior available FY</small><strong>${percent(current.growth)}</strong></div><div><small>Operating margin</small><strong>${percent(current.margin)}</strong></div></div><div class="lab-chart">${secChart(rows)}${marginChart(rows)}</div><p class="lab-insight"><strong>From the data:</strong> ${impact} ${finite(current.margin)?`Operating income was ${percent(current.margin)} of reported revenue.`:'Operating margin is unavailable.'}</p><div class="table-wrap"><table><thead><tr><th>Fiscal year-end</th><th>Revenue</th><th>Annual change</th><th>Operating margin</th></tr></thead><tbody>${table}</tbody></table></div><p class="tiny lab-foot">Source: SEC Company Facts${href}. Snapshot cutoff: ${esc(snapshot.as_of||'not specified')}. Comparison uses the preceding available annual record, which may not represent a consecutive year; issuer fiscal periods can differ. Revenue and operating income are reported; growth and margin are derived. Historical financials do not predict stock returns.</p>`;
}
function renderOptimize(data,cap){
 const out=modeledRisk(data.slice(0,120),cap);
 const drop=out.volEqual>0?(1-out.volOptimal/out.volEqual):0;
 const bars=names.map((name,i)=>`<div class="lab-weight-row"><span>${esc(name)}</span><div class="lab-bars"><div class="lab-bar" style="width:${round(out.equal[i]*100,3)}%" title="Equal weight ${percent(out.equal[i])}"></div><div class="lab-bar optimized" style="width:${round(out.optimal[i]*100,3)}%" title="Constrained minimum variance ${percent(out.optimal[i])}"></div></div><strong>${percent(out.optimal[i])}</strong></div>`).join('');
 return `<div class="lab-metrics"><div><small>Equal-weight fitted volatility</small><strong>${percent(out.volEqual)}</strong></div><div><small>Optimized fitted volatility</small><strong>${percent(out.volOptimal)}</strong></div><div><small>Fitted volatility difference</small><strong>${percent(drop)}</strong></div></div><p class="lab-insight"><strong>Model result:</strong> Under these synthetic training returns, the feasible minimum-variance solution ${drop>=0?'reduces':'does not reduce'} estimated annualized volatility by ${percent(Math.abs(drop))} compared with equal weighting. This is an in-sample estimate, not an investment return forecast.</p><div class="lab-weight-head"><span>Investment basket</span><span>Weights — baseline / optimized</span><span>Optimized</span></div>${bars}<div class="lab-legend"><span><i class="lab-key" style="background:#b87935"></i>Equal weight</span><span><i class="lab-key" style="background:#16705d"></i>Optimized</span></div><p class="tiny lab-foot">120 synthetic sessions; sample covariance with 12% off-diagonal shrinkage; long-only, fully invested; per-asset weight cap ${round(cap*100,0)}%. Objective: min wᵀΣw. The fitted result is calculated, not a drawn example.</p>`;
}
function renderWalk(data,cap,feeBps,train){
 const r=walkforward(data,{cap,feeBps,train});
 const a=r.paths.optimized.at(-1),b=r.paths.equal.at(-1);
 const difference=a/b-1;
 const rows=r.windows.map((w,i)=>`<tr><td>${i+1}</td><td>${w.trainStart}–${w.trainEnd}</td><td>${w.testStart}–${w.testEnd}</td><td>${percent(w.optimized-1)}</td><td>${percent(w.equal-1)}</td></tr>`).join('');
 return `<div class="lab-metrics"><div><small>Optimized ending wealth · start 1.00</small><strong>${round(a,3)}×</strong></div><div><small>Equal-weight ending wealth</small><strong>${round(b,3)}×</strong></div><div><small>Optimized maximum drawdown</small><strong>${percent(r.maxDrawdown.optimized)}</strong></div></div><div class="lab-chart">${lineChart([r.paths.optimized,r.paths.equal],{title:'Simulated, after-cost out-of-sample wealth',labelA:'Constrained minimum variance',labelB:'Rebalanced equal weight'})}</div><p class="lab-insight"><strong>Simulated comparison:</strong> In this controlled simulation, the optimized strategy finished ${difference>=0?'above':'below'} the equal-weight benchmark by ${percent(Math.abs(difference))} on a relative-wealth basis. Both strategies include modeled rebalancing costs; neither curve represents actual historical trading.</p><details class="lab-details"><summary>Inspect each past-only training and test window (${r.windows.length})</summary><div class="table-wrap"><table><thead><tr><th>Window</th><th>Train sessions</th><th>Unseen test sessions</th><th>Optimized cumulative</th><th>Benchmark cumulative</th></tr></thead><tbody>${rows}</tbody></table></div></details><p class="tiny lab-foot">${train} preceding sessions to fit each model; next 20 non-overlapping sessions for evaluation. ${round(feeBps,0)} basis points applied to two-sided traded weight at each window boundary. Equal-weight benchmark is periodically rebalanced. Simulated assets, dates and returns; real-data performance claims are not made.</p>`;
}
function mount(snapshot){
 const byId=id=>document.getElementById(id);
 const host=byId('lab-sec-results');
 if(!host)return;
 const companies=Array.isArray(snapshot?.companies)?snapshot.companies.filter(c=>Array.isArray(c.annual)&&c.annual.length>0):[];
 const issuer=byId('lab-issuer');
 issuer.innerHTML=companies.map(c=>`<option value="${esc(c.symbol)}">${esc(c.name)} (${esc(c.symbol)})</option>`).join('');
 if(companies.some(c=>c.symbol==='MSFT'))issuer.value='MSFT';
 function refreshSec(){host.innerHTML=renderSec(snapshot,issuer.value);const selected=companies.find(c=>c.symbol===issuer.value);const label=byId('qf-v83-active-company');if(label)label.textContent=selected?selected.name+' ('+selected.symbol+')':'No company selected';}
 function refreshModels(){
  const cap=Number(byId('lab-cap').value)/100,fee=Number(byId('lab-fee').value),train=Number(byId('lab-train').value),error=byId('lab-error');
  try{
   if(!finite(cap)||cap<.2||cap>1||!finite(fee)||fee<0||fee>100||![80,120,160].includes(train))throw Error('Choose valid model assumptions');
   const observations=synthetic();
   byId('lab-opt-results').innerHTML=renderOptimize(observations,cap);
   byId('lab-walk-results').innerHTML=renderWalk(observations,cap,fee,train);
   const note=byId('qf-v83-model-settings');if(note)note.textContent='Simulated dataset · maximum investment weight '+Math.round(cap*100)+'% · trading cost '+fee+' basis points · training window '+train+' sessions. Both model exhibits refreshed.';
   error.textContent='';
  }catch(e){error.textContent=e.message;}
 }
 issuer.addEventListener('change',refreshSec);
 for(const id of ['lab-cap','lab-fee','lab-train'])byId(id).addEventListener('change',refreshModels);
 byId('lab-recalculate').addEventListener('click',refreshModels);
 if(!companies.length)issuer.disabled=true;
 refreshSec();refreshModels();
}
const api={synthetic,covariance,project,variance,optimize,modeledRisk,walkforward,secSeries,trend,renderSec,renderOptimize,renderWalk,mount};
root.QFResearchLab=api;
if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
