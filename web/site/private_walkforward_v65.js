/* Rolling past-only fitted historical allocations, next-window evaluation. Pure client-side research. */
(function(root,factory){
 'use strict';const value=factory(root.QFPrivateOptimizer|| (typeof require==='function'?require('./private_optimizer.js'):null));
 if(typeof module==='object'&&module.exports)module.exports=value;
 else root.QFPrivateWalkforward=value;
})(typeof window!=='undefined'?window:this,function(optimizer){
 'use strict';
 const sum=a=>a.reduce((s,x)=>s+x,0);
 const finite=x=>typeof x==='number'&&Number.isFinite(x);
 function metrics(wealth,annual){
  const returns=wealth.slice(1).map((x,i)=>x/wealth[i]-1);
  const avg=sum(returns)/returns.length;
  const varSample=sum(returns.map(x=>(x-avg)**2))/Math.max(1,returns.length-1);
  let high=wealth[0],drawdown=0;
  for(const v of wealth){high=Math.max(high,v);drawdown=Math.min(drawdown,v/high-1);}
  const sorted=[...returns].sort((a,b)=>a-b),count=Math.max(1,Math.ceil(sorted.length*.05));
  return {change:wealth.at(-1)/wealth[0]-1,annualVol:Math.sqrt(varSample*annual),
   maxDrawdown:drawdown,annualMean:avg*annual,
   var95:Math.max(0,-sorted[count-1]),expectedShortfall:Math.max(0,-sum(sorted.slice(0,count))/count)};
 }
 function run(history,options={}){
  if(!optimizer)throw Error('Portfolio optimizer unavailable.');
  const prep=optimizer.prepare(history); // strict schema and chronological price checks
  const train=Number(options.train??126),step=Number(options.step??21),
   feeBps=Number(options.feeBps??5),capital=Number(options.capital??10000),
   objective=options.objective||'minimum',cap=Number(options.cap??0.6);
  if(!Number.isInteger(train)||train<63||train>504||!Number.isInteger(step)||step<10||step>90||
     !finite(feeBps)||feeBps<0||feeBps>100||!finite(capital)||capital<100||capital>1e6||
     !finite(cap)||cap<=0||cap>1||cap*prep.symbols.length<1-1e-10||
     !['minimum','inverse','tilt'].includes(objective))throw Error('Invalid walk-forward window, fee, capital, or allocation limits.');
  const N=prep.symbols.length,T=history.dates.length,start=train-1;
  if(T-start-1<2*step)throw Error('Not enough observations: select a longer market-history period or shorter windows. At least two full test windows are required.');
  const prices=prep.prices;let shares=[Array(N).fill(0),Array(N).fill(0)];
  let cash=[capital,capital],fees=[0,0],turnovers=[0,0],wealth=[[capital],[capital]],
   testDates=[history.dates[start]],windows=[];
  for(let at=start;at+step<T;at+=step){
   const training={symbols:[...history.symbols],dates:history.dates.slice(at-train+1,at+1),
    closes:Object.fromEntries(history.symbols.map((s,i)=>[s,prices[i].slice(at-train+1,at+1)])),
    sessions_per_year:history.sessions_per_year,source:history.source};
   // Training ends on 'at'. No price at 'at+1' or later enters optimizer.
   const fitted=optimizer.run(training,{objective,maxWeight:cap});
   const strategies=[fitted.chosen,Array(N).fill(1/N)];
   const next=Math.min(at+step,T-1);
   const feesBefore=[...fees],turnoversBefore=[...turnovers];
   for(let k=0;k<2;k++){
    const current=shares[k].map((n,i)=>n*prices[i][at]);
    const total=cash[k]+sum(current),target=strategies[k].map(w=>total*w);
    const traded=sum(current.map((v,i)=>Math.abs(v-target[i])));
    const cost=traded*feeBps/10000;
    if(!finite(cost)||cost>=total)throw Error('Rebalance cost exceeds available portfolio value.');
    const after=total-cost;
    shares[k]=strategies[k].map((w,i)=>w*after/prices[i][at]);
    cash[k]=0;fees[k]+=cost;turnovers[k]+=traded;
   }
   windows.push({trainingStart:history.dates[at-train+1],trainingEnd:history.dates[at],
    testStart:history.dates[at+1],testEnd:history.dates[next],
    weights:[...fitted.chosen],benchmarkWeights:[...strategies[1]],
    rebalanceFees:[fees[0]-feesBefore[0],fees[1]-feesBefore[1]],
    rebalanceTurnover:[turnovers[0]-turnoversBefore[0],turnovers[1]-turnoversBefore[1]]});
   for(let t=at+1;t<=next;t++){
    const values=shares.map(x=>sum(x.map((n,i)=>n*prices[i][t])));
    if(values.some(x=>!finite(x)||x<=0))throw Error('Invalid out-of-sample wealth.');
    testDates.push(history.dates[t]);
    for(let k=0;k<2;k++)wealth[k].push(values[k]);
   }
  }
  return {symbols:[...history.symbols],train,step,feeBps,capital,objective,cap,
   annual:prep.annual,start:testDates[0],end:testDates.at(-1),dates:testDates,
   windows,optimized:{wealth:wealth[0],fees:fees[0],turnover:turnovers[0],metrics:metrics(wealth[0],prep.annual)},
   benchmark:{wealth:wealth[1],fees:fees[1],turnover:turnovers[1],metrics:metrics(wealth[1],prep.annual)},
   source:history.source||'Historical price observations',description:'Historical rolling-origin test, not live/predictive performance'};
 }
 return {run,metrics};
});
