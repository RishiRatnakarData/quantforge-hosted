/* QuantForge V8.5 — private, session-only candidate dossier calculation.
 * Pure functions: no API calls, storage, account modification, trades or exports.
 * Peer-relative exposure is not a market-index or Fama–French beta. */
(function(root){
'use strict';
const finite=n=>typeof n==='number'&&Number.isFinite(n);
const date=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&Number.isFinite(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;
const mean=a=>a.reduce((t,v)=>t+v,0)/a.length;
const variance=a=>{const m=mean(a);return a.reduce((t,v)=>t+(v-m)**2,0)/(a.length-1);};
const quantile=(sorted,p)=>{const at=(sorted.length-1)*p;const lo=Math.floor(at),hi=Math.ceil(at);return sorted[lo]+(sorted[hi]-sorted[lo])*(at-lo);};
function maxDrawdown(prices){let high=prices[0],worst=0;for(const x of prices){high=Math.max(high,x);worst=Math.min(worst,x/high-1);}return worst;}
const cap=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
function evaluate(input){
 const d=input&&typeof input==='object'?input:{};
 const history=d.history,selection=d.selection,candidate=d.symbol;
 if(!history||!Array.isArray(history.symbols)||history.symbols.length<2||history.symbols.length>5||
  typeof candidate!=='string'||!history.symbols.includes(candidate)||new Set(history.symbols).size!==history.symbols.length||
  !Array.isArray(selection)||new Set(selection).size!==history.symbols.length||
  !history.symbols.every(s=>selection.includes(s))||!Array.isArray(history.dates)||
  history.dates.length<64||history.dates.length>2500||
  !history.dates.every((s,i)=>date(s)&&(!i||s>history.dates[i-1]))||
  !history.closes||history.symbols.some(s=>!Array.isArray(history.closes[s])||
    history.closes[s].length!==history.dates.length||history.closes[s].some(x=>!finite(x)||x<=0)))
  return {ready:false,reason:'Load at least 64 aligned observations for the current 2–5 selected investments before assessing a candidate.'};
 const peers=history.symbols.filter(s=>s!==candidate);
 const prices=history.closes[candidate];
 const returns=prices.slice(1).map((p,i)=>p/prices[i]-1);
 const peerReturns=returns.map((_,i)=>mean(peers.map(sym=>history.closes[sym][i+1]/history.closes[sym][i]-1)));
 if(!returns.every(finite)||!peerReturns.every(finite))return {ready:false,reason:'Observed prices have a non-finite daily change; the risk dossier is withheld.'};
 const sorted=[...returns].sort((a,b)=>a-b),p5=quantile(sorted,.05),tail=sorted.filter(x=>x<=p5);
 const v=variance(returns),pv=variance(peerReturns);
 const sd=Math.sqrt(v),pSd=Math.sqrt(pv);
 const cov=returns.reduce((t,x,i)=>t+(x-mean(returns))*(peerReturns[i]-mean(peerReturns)),0)/(returns.length-1);
 const beta=pv>1e-12?cov/pv:null;
 const corr=v>1e-12&&pv>1e-12?cap(cov/(sd*pSd),-1,1):null;
 const annual=history.sessions_per_year===365?365:252;
 const metrics={
  periodReturn:prices.at(-1)/prices[0]-1,
  trailing63Return:prices.at(-1)/prices.at(-64)-1,
  annualVolatility:sd*Math.sqrt(annual),
  dailyVaR95:Math.max(0,-p5),
  dailyES95:Math.max(0,-mean(tail)),
  worstDay:sorted[0],
  maxDrawdown:maxDrawdown(prices),
  peerBeta:beta,
  peerCorrelation:corr,
  peerR2:corr===null?null:corr**2,
  peerPeriodReturn:peerReturns.reduce((value,r)=>value*(1+r),1)-1,
  peerAnnualVolatility:pSd*Math.sqrt(annual),
  observations:returns.length,
  annualization:annual
 };
 const study=history.dates;
 const historyFacts={start:study[0],end:study.at(-1),observations:returns.length,peerCount:peers.length,peerNames:[...peers],calendar:history.calendar||'Aligned observations'};
 let pricesIndexed=[100],peerIndexed=[100];
 for(let i=0;i<returns.length;i++){
  pricesIndexed.push(pricesIndexed.at(-1)*(1+returns[i]));
  peerIndexed.push(peerIndexed.at(-1)*(1+peerReturns[i]));
 }
 if(!pricesIndexed.every(x=>finite(x)&&x>0)||!peerIndexed.every(x=>finite(x)&&x>0))
  return {ready:false,reason:'Extreme observations overflow the indexed comparison; results are withheld.'};
 // Return bounded recent chart values only; no private raw quote/holdings export.
 const candidateRecent=pricesIndexed.slice(-121),peerRecent=peerIndexed.slice(-121);
 const graph={dates:study.slice(-121),candidate:candidateRecent.map(x=>100*x/candidateRecent[0]),peers:peerRecent.map(x=>100*x/peerRecent[0])};
 const cautions=[];
 if(metrics.dailyES95>.035)cautions.push('The historical worst 5% of daily returns averaged a loss greater than 3.5%; this is a descriptive risk flag, not a forecast.');
 if(metrics.maxDrawdown<-.30)cautions.push('This investment experienced a historical price-only drawdown greater than 30% over the loaded window.');
 if(beta!==null&&beta>1.5)cautions.push('Daily returns showed elevated sensitivity to the other selected investments; those peers are not a broad market benchmark.');
 if(beta===null)cautions.push('Peer beta is unavailable because the comparison basket has essentially no variance.');
 if(returns.length<126)cautions.push('Fewer than 126 aligned daily returns: tail and co-movement estimates are especially unstable.');
 const sec=d.company?.symbol===candidate&&Array.isArray(d.company.annual)?d.company.annual:[];
 const annualRows=sec.filter(a=>date(a?.fiscal_end)&&a.metrics&&typeof a.metrics==='object').sort((a,b)=>b.fiscal_end.localeCompare(a.fiscal_end));
 const latest=annualRows[0];
 const revenue=latest?.metrics?.revenue_usd;
 const income=latest?.metrics?.operating_income_usd;
 const fcf=latest?.metrics?.free_cash_flow_usd;
 const prior=annualRows.find(a=>a!==latest&&finite(a.metrics?.revenue_usd)&&a.metrics.revenue_usd>0&&
  latest&&((Date.parse(latest.fiscal_end)-Date.parse(a.fiscal_end))/86400000)>=300&&
  ((Date.parse(latest.fiscal_end)-Date.parse(a.fiscal_end))/86400000)<=430);
 const fundamentals={fiscalEnd:latest?.fiscal_end||null,filingAsOf:d.company?.as_of||null,
  revenueGrowth:finite(revenue)&&revenue>0&&prior?(revenue/prior.metrics.revenue_usd-1):null,
  operatingMargin:finite(revenue)&&revenue>0&&finite(income)?income/revenue:null,
  freeCashFlowMargin:finite(revenue)&&revenue>0&&finite(fcf)?fcf/revenue:null,
  available:finite(revenue)&&revenue>0};
 const value=d.value?.symbol===candidate?d.value:null;
 const valuation={
  priceTime:value?.priceTime||null,fiscalEnd:value?.fiscalEnd||null,sharesTime:value?.sharesTime||null,
  marketCapAvailable:finite(value?.marketCap)&&value.marketCap>0,
  pSales:finite(value?.pSales)?value.pSales:null,
  pFcf:finite(value?.pFcf)?value.pFcf:null,
  fcfYield:finite(value?.fcfYield)?value.fcfYield:null,
  warnings:Array.isArray(value?.warnings)?[...value.warnings]:[],
  limitations:['Price-to-sales and FCF yield are observed-price ratios, not intrinsic values or price targets.',
  'Cash-flow and share-count reporting periods may differ from the market quote.']
 };
 const portfolio=d.portfolio,holdings=portfolio?.holdings,quotes=d.quotes;
 let portfolioImpact=null;
 if(portfolio&&finite(portfolio.cash)&&portfolio.cash>=0&&holdings&&typeof holdings==='object'&&!Array.isArray(holdings)&&quotes&&typeof quotes==='object'){
  let total=portfolio.cash,holdingValue=0,complete=true,oldestMarkAgeSeconds=0,transactionQualityMarks=true;
  for(const [sym,qty] of Object.entries(holdings)){
   const quote=quotes[sym],age=Date.parse(d.now)-Date.parse(quote?.timestamp);
   if(!finite(qty)||qty<0||(qty>0&&(!finite(quote?.price)||quote.price<=0||!Number.isFinite(age)||age<0||age>7*86400000))){complete=false;break;}
   if(qty===0)continue;
   oldestMarkAgeSeconds=Math.max(oldestMarkAgeSeconds,age/1000);
   if(age/1000>(sym.includes('/')?300:900))transactionQualityMarks=false;
   const val=qty*quotes[sym].price;
   if(!finite(val)){complete=false;break;}
   total+=val;
   if(sym===candidate)holdingValue=val;
  }
  if(complete&&total>0){
   const present=holdingValue/total,cashPct=portfolio.cash/total;
   portfolioImpact={currentWeight:present,oldestMarkAgeSeconds,transactionQualityMarks,existingCandidateShock20:present===0?0:-.20*present,
    cashWeight:cashPct,
    additional5:cashPct>=.05-1e-12?-.20*(present+.05):null,
    additional10:cashPct>=.10-1e-12?-.20*(present+.10):null};
  }
 }
 return {ready:true,symbol:candidate,history:historyFacts,metrics,graph,fundamentals,valuation,portfolioImpact,
  cautions,limitations:[
   'Peer basket is an equally weighted combination of the other selected investments; the sensitivity coefficient is NOT market beta, a Fama–French factor loading, or predictive alpha.',
   'Historical prices can exclude dividends; estimation uses the same observed dates and does not resolve survivorship or selection bias.',
   'Empirical one-day VaR and expected shortfall are in-sample historical loss estimates, not probabilities of future outcomes.',
   'The -20% single-name shock and incremental 5%/10% cash-funded allocations are hypothetical, instant, and exclude spreads, taxes, fees and correlated market moves.',
   'No score or suggested trade is generated. Review business fundamentals, market price, portfolio exposures and missing evidence before deciding.'
  ]};
}
const api=Object.freeze({evaluate});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateCandidateV85=api;
})(typeof window!=='undefined'?window:globalThis);
