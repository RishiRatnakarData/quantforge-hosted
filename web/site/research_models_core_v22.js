/* QuantForge 2.0 Release C: pure, deterministic, source-aware research experiments.
 * No fetching, account state, trading, storage, or proprietary data included.
 * Public inputs are explicitly synthetic; owner price histories are never serialized.
 */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const avg=a=>a.reduce((s,x)=>s+x,0)/a.length;
const variance=a=>{if(a.length<2)throw Error('Variance requires at least two observations.');const m=avg(a);return a.reduce((s,x)=>s+(x-m)**2,0)/(a.length-1);};
const percentile=(sorted,q)=>{const at=(sorted.length-1)*q,i=Math.floor(at),j=Math.ceil(at);return sorted[i]+(sorted[j]-sorted[i])*(at-i);};
const iso=d=>typeof d==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(d)&&!Number.isNaN(Date.parse(d+'T00:00:00Z'));
function series(points){
 if(!Array.isArray(points)||points.length>2500)throw Error('Invalid or oversized history.');
 let last='';return points.map(p=>{
  if(!p||!iso(p.date)||p.date<=last||!finite(p.close)||p.close<=0)throw Error('History must contain distinct ascending dates and positive finite closes.');
  last=p.date;return {date:p.date,close:p.close};
 });
}
function returns(points){const p=series(points);return p.slice(1).map((r,i)=>r.close/p[i].close-1);}
function drawdown(levels){let peak=levels[0],lowest=0;for(const p of levels){peak=Math.max(peak,p);lowest=Math.min(lowest,p/peak-1);}return lowest;}
function risk(points,sessionsPerYear=252){
 if(![252,365].includes(sessionsPerYear))throw Error('Unsupported observation calendar.');
 const p=series(points);if(p.length<91)return {ready:false,reason:'Risk needs at least 91 consecutive eligible dated closes; no replacement data are used.'};
 if(sessionsPerYear===365&&p.some((v,i)=>i>0&&Date.parse(v.date)-Date.parse(p[i-1].date)!==86400000))return {ready:false,reason:'Crypto annualization requires consecutive daily observations; calendar gaps are not filled.'};
 const r=returns(p),sorted=[...r].sort((a,b)=>a-b),cut=percentile(sorted,0.05),tail=sorted.filter(x=>x<=cut+1e-12);
 const rolling=[];for(let end=60;end<=r.length;end+=5){const window=r.slice(end-60,end);rolling.push({date:p[end].date,volatility:Math.sqrt(variance(window)*sessionsPerYear)});}
 const halves=[r.slice(0,Math.floor(r.length/2)),r.slice(Math.floor(r.length/2))];
 const historyVol=Math.sqrt(variance(r)*sessionsPerYear);
 // A deterministic circular moving-block bootstrap estimates sample-volatility sensitivity.
 // The interval is NOT a predictive VaR bound or confidence band on future returns.
 let bootstrap=null;
 if(r.length>=180){
  let seed=0x19f34a57;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  const block=Math.max(5,Math.ceil(Math.sqrt(r.length))),draws=[];
  for(let rep=0;rep<300;rep++){
   const draw=[];while(draw.length<r.length){const at=Math.floor(rand()*r.length);for(let k=0;k<block&&draw.length<r.length;k++)draw.push(r[(at+k)%r.length]);}
   draws.push(Math.sqrt(variance(draw)*sessionsPerYear));
  }
  draws.sort((a,b)=>a-b);
  bootstrap={low:percentile(draws,0.025),high:percentile(draws,0.975),replicates:300,block_length:block,scope:'Historical realized-volatility sample sensitivity; not a calibrated future volatility interval.'};
 }
 return {ready:true,first:p[0].date,last:p.at(-1).date,sessions:p.length,observations:r.length,
  annual_volatility:historyVol,max_drawdown:drawdown(p.map(x=>x.close)),
  daily_var95_loss:Math.max(0,-cut),daily_es95_loss:Math.max(0,-avg(tail)),
  worst_day:Math.min(...r),positive_share:r.filter(v=>v>0).length/r.length,
  rolling,split_volatility:halves.map(h=>Math.sqrt(variance(h)*sessionsPerYear)),bootstrap,
  sessions_per_year:sessionsPerYear,convention:'Close-to-close simple daily returns; '+sessionsPerYear+' observations/year on the stated calendar. Historical 5th percentile loss and tail-average loss over ONE session. No dividends, fees or prediction.'};
}
function dcfProxy(financial,assumptions={}){
 const a=Number(assumptions.growth??0.04),d=Number(assumptions.discount??0.10),t=Number(assumptions.terminal??0.02),h=5;
 if(![a,d,t].every(finite)||a< -0.5||a>0.5||d<0.01||d>0.5||t< -0.1||t>=d)throw Error('DCF assumptions invalid: discount must exceed terminal growth; bounded rates are required.');
 const fcf=financial?.metrics?.free_cash_flow_usd;
 if(!finite(fcf)||fcf<=0)return {ready:false,reason:finite(fcf)?'Non-positive annual cash-flow proxy: no positive terminal-value extrapolation is shown.':'SEC cash-flow proxy unavailable; no value was imputed.'};
 const cashFlows=[];let presentValue=0;
 for(let year=1;year<=h;year++){
  const projected=fcf*(1+a)**year,discounted=projected/(1+d)**year;
  cashFlows.push({year,cash_flow:projected,discounted});presentValue+=discounted;
 }
 const terminalFlow=cashFlows.at(-1).cash_flow*(1+t);
 const terminalPV=terminalFlow/(d-t)/(1+d)**h;
 return {ready:true,period:financial.source?.period||null,base_fcf:fcf,growth:a,discount:d,terminal:t,horizon:h,
  cash_flows:cashFlows,explicit_pv:presentValue,terminal_pv:terminalPV,proxy_pv:presentValue+terminalPV,
  terminal_share:terminalPV/(presentValue+terminalPV),
  limitation:'Illustrative discounted value of the reported operating-cash-flow-minus-capex proxy. This is not FCFF, enterprise value, equity value, fair share price, or a consensus target; it omits the debt/cash/share bridge.'};
}
function valuation(financial){
 const scenarios=[['Conservative',-0.02,0.13,0.015],['Base',0.04,0.10,0.02],['High-growth',0.09,0.095,0.025]].map(([name,growth,discount,terminal])=>({name,...dcfProxy(financial,{growth,discount,terminal})}));
 const sensitivity=[];for(const discount of [0.085,0.10,0.12,0.15]){
  const cells=[0.01,0.02,0.03].map(terminal=>dcfProxy(financial,{growth:0.04,discount,terminal}));
  sensitivity.push({discount,cells});
 }
 return {ready:scenarios.some(s=>s.ready),scenarios,sensitivity,period:financial?.source?.period||null,
  note:'This sensitivity uses the most recent published annual SEC-derived cash-flow proxy. All forward growth and discount assumptions are hypothetical; no point-in-time market forecast is claimed.'};
}
function strategy(points,fee=0.0005){
 const p=series(points);if(p.length<181)return {ready:false,reason:'Strategy testing needs 181+ eligible closes for lagged 20/60-session signals and a later evaluation window.'};
 if(!finite(fee)||fee<0||fee>0.02)throw Error('Trading fee must be in [0, 2%].');
 // Entry at previous close, return earned only on the following day. No future close is read in the signal.
 const indexed=[100],passive=[100],dates=[p[60].date],positions=[];let position=0,turnover=0;
 for(let i=61;i<p.length;i++){
  const past=p.slice(0,i).map(x=>x.close),ma20=avg(past.slice(-20)),ma60=avg(past.slice(-60));
  const next=ma20>ma60?1:0,cost=fee*Math.abs(next-position),day=p[i].close/p[i-1].close-1;
  indexed.push(indexed.at(-1)*(1+next*day-cost));
  passive.push(passive.at(-1)*(1+day-(i===61?fee:0)));
  dates.push(p[i].date);turnover+=Math.abs(next-position);position=next;positions.push(next);
 }
 const boundary=Math.floor((dates.length-1)*2/3),evalStart=dates[boundary];
 const evalRet=(values)=>values.at(-1)/values[boundary]-1;
 const summary=(values)=>({total_return:values.at(-1)/100-1,max_drawdown:drawdown(values),later_return:evalRet(values)});
 return {ready:true,dates,indexed,passive,signals:positions,turnover,fee,first:dates[0],last:dates.at(-1),
  evaluation:{first:evalStart,last:dates.at(-1),sessions:dates.length-1-boundary,
   strategy_return:evalRet(indexed),passive_return:evalRet(passive),kind:'Chronologically later window; parameters fixed before evaluation, not optimized on the holdout.'},
  strategy:summary(indexed),benchmark:summary(passive),
  assumption:'20-vs-60-session trailing-close filter; cash when inactive; daily simple close returns; 5-bp assumed switch cost by default, passive pays one entry. No cash interest, slippage, dividends or taxes. Closing-only approximations are not executable fills.'};
}
const api=Object.freeze({series,returns,risk,dcfProxy,valuation,strategy});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFResearchModelsCore22=api;
})(typeof window!=='undefined'?window:globalThis);
