/* Pure multi-asset historical diagnostics; no network, account access or brokerage writes. */
(function(root,factory){
 'use strict';
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.QFPrivateMultiMarket=api;
})(typeof window!=='undefined'?window:this,function(){
 'use strict';
 const finite=x=>typeof x==='number'&&Number.isFinite(x);
 const avg=a=>a.reduce((s,x)=>s+x,0)/a.length;
 function analyze(history){
  if(!history||!Array.isArray(history.symbols)||history.symbols.length<2||history.symbols.length>5||
   !Array.isArray(history.dates)||history.dates.length<16||!history.closes||!history.asset_classes)throw Error('Load valid aligned market history first.');
  const annual=history.sessions_per_year===365?365:252;
  const assets=history.symbols.map(symbol=>{
   const prices=history.closes[symbol];
   if(!Array.isArray(prices)||prices.length!==history.dates.length||prices.some(x=>!finite(x)||x<=0))throw Error('Invalid aligned prices.');
   const returns=prices.slice(1).map((x,i)=>x/prices[i]-1);
   if(returns.some(r=>!finite(r)||r<=-1||r>10))throw Error('Unsupported daily price discontinuity.');
   const mean=avg(returns);
   const variance=returns.reduce((s,x)=>s+(x-mean)*(x-mean),0)/(returns.length-1);
   let peak=1,w=1,drawdown=0;
   for(const r of returns){w*=1+r;peak=Math.max(peak,w);drawdown=Math.min(drawdown,w/peak-1);}
   return {symbol,kind:history.asset_classes[symbol],returns,
    annualVolatility:Math.sqrt(Math.max(0,variance)*annual),
    observedChange:prices.at(-1)/prices[0]-1,
    maxDrawdown:drawdown,worstDay:Math.min(...returns)};
  });
  const n=assets.length;
  const equalReturns=assets[0].returns.map((_,i)=>avg(assets.map(x=>x.returns[i])));
  const sorted=[...equalReturns].sort((a,b)=>a-b);
  const tailCount=Math.max(1,Math.ceil(0.05*sorted.length));
  const stressScenarios=[
   {name:'Broad simultaneous shock',equity:-.10,crypto:-.20},
   {name:'Crypto-specific selloff',equity:0,crypto:-.35},
   {name:'Equity-specific selloff',equity:-.20,crypto:0},
  ];
  const stress=stressScenarios.map(s=>({name:s.name,change:assets.reduce((acc,a)=>acc+(a.kind==='crypto'?s.crypto:s.equity)/n,0),equity:s.equity,crypto:s.crypto}));
  return {assets,annual,observationCount:equalReturns.length,stress,
   observedWorstDay:Math.min(...equalReturns),
   historicalVaR95:Math.max(0,-sorted[tailCount-1]),
   historicalES95:Math.max(0,-avg(sorted.slice(0,tailCount))),
   periodStart:history.dates[0],periodEnd:history.dates.at(-1),
   calendar:history.calendar||'common dates',source:history.source||'Private observations'};
 }
 return {analyze};
});
