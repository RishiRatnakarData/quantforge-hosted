/* Private-only, explainable investment research shortlist. No provider calls or trade mutations. */
(function(root){
'use strict';
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const finite=x=>typeof x==='number'&&Number.isFinite(x);
function researchMetrics(prices,annualization=252){
 if(!Array.isArray(prices)||prices.length<126||prices.length>800||!
    [252,365].includes(annualization)||prices.some(x=>!finite(x)||x<=0)){
  throw Error('At least 126 valid, positive historical closes are required.');
 }
 const r=[];
 for(let i=1;i<prices.length;i++)r.push(prices[i]/prices[i-1]-1);
 const mu=r.reduce((a,b)=>a+b,0)/r.length;
 const vol=Math.sqrt(r.reduce((a,b)=>a+(b-mu)**2,0)/(r.length-1))*Math.sqrt(annualization);
 let peak=prices[0],drawdown=0;
 for(const x of prices){peak=Math.max(peak,x);drawdown=Math.min(drawdown,x/peak-1);}
 const lookback=Math.min(63,prices.length-1);
 const momentumQuarter=prices.at(-1)/prices.at(-1-lookback)-1;
 const momentumYear=prices.at(-1)/prices[0]-1;
 const losses=r.map(x=>-x).sort((a,b)=>a-b);
 const var95=losses[Math.min(losses.length-1,Math.floor(0.95*losses.length))];
 return {observations:prices.length,quarterReturn:momentumQuarter,periodReturn:momentumYear,
  annualVol:vol,maxDrawdown:drawdown,var95,priceOnly:true};
}
function researchScore(m,mode='balanced'){
 if(!['balanced','growth','defensive'].includes(mode))throw Error('Unknown research lens');
 const price=clamp(50+100*m.periodReturn,0,100);
 const recent=clamp(50+170*m.quarterReturn,0,100);
 const risk=clamp(110-170*m.annualVol,0,100);
 const draw=clamp(100+170*m.maxDrawdown,0,100);
 const weights={balanced:[.27,.23,.30,.20],growth:[.43,.32,.15,.10],defensive:[.13,.10,.45,.32]}[mode];
 const components=[price,recent,risk,draw];
 if(components.some(x=>!finite(x)))throw Error('Invalid metrics');
 return Math.round(components.reduce((s,x,i)=>s+x*weights[i],0));
}
function analyze(symbol,prices,mode='balanced',annual=252){
 const m=researchMetrics(prices,annual);
 const score=researchScore(m,mode);
 const notes=[];
 if(m.periodReturn>0)notes.push('Positive return across the observed period');
 else notes.push('Negative return across the observed period');
 if(m.quarterReturn>0.04)notes.push('Positive recent price momentum');
 else if(m.quarterReturn<0)notes.push('Recent price momentum is negative');
 if(m.annualVol>.40)notes.push('High historical annualized volatility');
 if(m.maxDrawdown<-.25)notes.push('Large historical peak-to-trough decline');
 if(m.periodReturn>0.25)notes.push('Strong past gains could reverse');
 return {symbol,score,metrics:m,notes};
}
function rank(rows,mode='balanced'){
 if(!Array.isArray(rows))throw Error('Missing candidates');
 const results=rows.map(x=>analyze(x.symbol,x.prices,mode,x.annual||252));
 return results.sort((a,b)=>b.score-a.score||a.symbol.localeCompare(b.symbol));
}
function fundamentals(company){
 if(!company||!Array.isArray(company.annual))return null;
 const periods=[...company.annual].sort((a,b)=>String(b.fiscal_end).localeCompare(String(a.fiscal_end)));
 const latest=periods[0],prior=periods[1];if(!latest)return null;
 const metric=(row,key)=>row&&row.metrics?row.metrics[key]:null;
 const revenue=metric(latest,'revenue_usd'),old=metric(prior,'revenue_usd'),fcf=metric(latest,'free_cash_flow_usd');
 const revGrowth=finite(revenue)&&finite(old)&&old>0?revenue/old-1:null;
 const fcfMargin=finite(fcf)&&finite(revenue)&&revenue>0?fcf/revenue:null;
 return {fiscalEnd:latest.fiscal_end,revenueGrowth:revGrowth,fcfMargin,asOf:company.as_of||'',source:company.source||'SEC EDGAR'};
}
root.QFPrivateIdeas=Object.freeze({researchMetrics,researchScore,analyze,rank,fundamentals});
if(typeof module!=='undefined'&&module.exports)module.exports=root.QFPrivateIdeas;
})(typeof window!=='undefined'?window:globalThis);
