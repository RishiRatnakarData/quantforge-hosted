/* QuantForge V11.0: read-only point-in-time cross-issuer research and fair-period price study.
 * User supplied SEC archive remains memory-only. No network, storage or order access. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const fix=x=>finite(x)?Number(x.toFixed(6)):null;
const safe=x=>String(x||'Unavailable').slice(0,160);
const fail=reason=>({ready:false,reason:safe(reason),coverage:{scheduled:0,complete:0,withheld:0},performance:{ready:false,reason:'Historical study unavailable.'}});
const dd=xs=>{let high=xs[0],low=0;for(const x of xs){high=Math.max(x,high);low=Math.min(low,x/high-1);}return low;};
function study({archive,snapshot,history,selection,train=126,step=21,maxDrawdown=.25,feeBps=10}={}){
 const pit=root.QFPrivateArchivedSECValidationV99,price=root.QFPrivatePointInTimeV97;
 if(!pit||!price||typeof pit.validateArchive!=='function'||typeof pit.auditAt!=='function')return fail('Historical SEC audit dependencies are missing.');
 const checked=pit.validateArchive(archive,snapshot);
 if(!checked.ready)return fail(checked.reason);
 if(!Array.isArray(selection)||selection.length<2||selection.length>5||new Set(selection).size!==selection.length||
  !selection.every(x=>typeof x==='string'&&/^[A-Z0-9.\-]{1,15}$/.test(x))||!price.validatePrice(history,selection[0])||
  history.symbols.length!==selection.length||selection.some(s=>!history.symbols.includes(s)))
  return fail('Load the exact selected, dated 2–5-investment history before evaluating the archive.');
 if(!Number.isInteger(train)||train<63||train>504||!Number.isInteger(step)||step<5||step>63||
  !finite(maxDrawdown)||maxDrawdown<=0||maxDrawdown>=1||!finite(feeBps)||feeBps<0||feeBps>100)
  return fail('Invalid training, holdout or historical cost assumptions.');
 const dates=history.dates,sources=new Map(archive.companies.map(c=>[c.symbol,c]));
 const boundaries=[];
 for(let end=train-1;end+step<dates.length&&boundaries.length<80;end+=step)boundaries.push(end);
 if(boundaries.length<2)return fail('At least two independent evaluation windows are required.');
 const issuerCoverage=new Map(selection.map(s=>[s,{symbol:s,complete:0,withheld:0,laterVersion:0,gaps:new Map()}]));
 let cash=0,complete=0,changes=0,selectedCount=0,ruleWealth=1,benchmarkWealth=1,prior=null;
 const steps=[];
 let lastBenchmarkWeights=null,benchmarkTrades=0;
 for(const end of boundaries){
  const date=dates[end],raw=[];
  for(const s of selection){
   const issuer=sources.get(s),evidence=issuer&&date<=archive.as_of?pit.auditAt(issuer,date):
    {ready:false,reason:issuer?'Decision after archive source cutoff.':'Issuer absent from imported SEC archive.'};
   const row=issuerCoverage.get(s);
   if(evidence.ready){
    const tail=history.closes[s].slice(end-train+1,end+1),risk=dd(tail);
    row.complete++;if(evidence.usedLaterVersion)row.laterVersion++;
    raw.push({symbol:s,growth:evidence.revenueGrowth,margin:evidence.fcfMargin,drawdown:risk,
     eligible:evidence.revenueGrowth>0&&evidence.fcfMargin>0&&risk>=-maxDrawdown,
     fiscalEnd:evidence.period,latestFiled:evidence.latestFiled});
   }else{row.withheld++;const reason=safe(evidence.reason);row.gaps.set(reason,(row.gaps.get(reason)||0)+1);}
  }
  if(raw.length!==selection.length)continue;
  complete++;
  // A predefined, deterministic within-universe research screen. No future returns in this selection.
  const ranked=raw.filter(r=>r.eligible).sort((a,b)=>b.margin-a.margin||b.growth-a.growth||a.symbol.localeCompare(b.symbol));
  const chosen=ranked[0]||null;
  if(!chosen)cash++;else selectedCount++;
  const next=dates[end+1],last=dates[end+step];
  const returns=Object.fromEntries(selection.map(s=>[s,history.closes[s][end+step]/history.closes[s][end+1]-1]));
  if(selection.some(s=>!finite(returns[s])||returns[s]<=-1))return fail('Invalid observed next-close evaluation return.');
  const nextSymbol=chosen?chosen.symbol:null;
  const turnover=prior===nextSymbol?0:prior&&nextSymbol?2:1;
  const tradeCost=turnover*feeBps/10000;
  // Equal weight benchmark is REBALANCED on each documented evaluation window.
  const mean=selection.reduce((acc,s)=>acc+returns[s],0)/selection.length;
  const model=chosen?returns[chosen.symbol]:0;
  const ruleFactor=(1-tradeCost)*(1+model),benchmarkFactor=(1+mean)*(1-(complete===1?feeBps/10000:0));
  if(!finite(ruleFactor)||!finite(benchmarkFactor)||ruleFactor<=0||benchmarkFactor<=0)return fail('Historical return computation failed.');
  ruleWealth*=ruleFactor;benchmarkWealth*=benchmarkFactor;changes+=turnover;
  prior=chosen?chosen.symbol:null;
  steps.push({decisionDate:date,executionDate:next,testThrough:last,selected:chosen?.symbol||null,
   candidateCount:ranked.length,rulePeriodReturn:fix(ruleFactor-1),benchmarkPeriodReturn:fix(benchmarkFactor-1),
   winnerFiscalEnd:chosen?.fiscalEnd||null,winnerLatestFiled:chosen?.latestFiled||null});
 }
 const issuers=selection.map(s=>{
  const r=issuerCoverage.get(s),g=[...r.gaps].sort((a,b)=>b[1]-a[1])[0];
  return {symbol:s,eligible:r.complete,withheld:r.withheld,scheduled:boundaries.length,
   coveragePct:fix(100*r.complete/boundaries.length),laterVersionWindows:r.laterVersion,
   principalGap:g?{reason:g[0],count:g[1]}:null};
 });
 const full=complete===boundaries.length;
 const coverage={scheduled:boundaries.length,complete,withheld:boundaries.length-complete};
 return {ready:true,asOf:archive.as_of,coverage,issuers,policy:{train,step,maxDrawdown,feeBps,
  label:'Positive annual revenue growth and free-cash-flow margin; drawdown inside limit; highest FCF margin among eligible selected companies'},
  performance:full?{ready:true,modelReturn:fix(ruleWealth-1),equalWeightReturn:fix(benchmarkWealth-1),
   changes,benchmarkTrades:fix(benchmarkTrades),cashWindows:cash,investedWindows:selectedCount,observedStart:steps[0].executionDate,
   observedEnd:steps.at(-1).testThrough,rows:steps.slice(-12)}:
   {ready:false,reason:'At least one scheduled window lacks complete SEC evidence for every selected issuer; cumulative returns withheld.',
    complete,scheduled:boundaries.length},
  limitations:[
   'The comparison universe is selected today and excludes historical delistings; survivorship and selection bias remain.',
   'Only available SEC Company Facts revisions are checked; original superseded filings may be missing.',
   'The cross-sectional rule is predefined for illustration, not a calibrated predictor or the complete Research Hub decision policy.',
   'Next-close price-only evaluation excludes dividends, bid-ask spread, slippage, taxes and corporate actions.',
   'The benchmark is equal-weighted for each test interval, with illustrative proportional turnover fees for initial entry and weight resets; it omits boundary-session price moves.',
   'Windows evaluate next-close through the end of each holdout; boundary-session returns are omitted for both alternatives.'
  ]};
}
function exportSafe(r){
 if(!r||!r.ready)return {schema:'quantforge.historical-panel.v11.0',ready:false,reason:safe(r?.reason)};
 const p=r.performance;
 return {schema:'quantforge.historical-panel.v11.0',ready:true,asOf:r.asOf,coverage:{...r.coverage},
  issuers:r.issuers.map(x=>({symbol:x.symbol,eligible:x.eligible,withheld:x.withheld,
   scheduled:x.scheduled,coveragePct:x.coveragePct,laterVersionWindows:x.laterVersionWindows})),
  policy:{...r.policy},performance:p.ready?{ready:true,modelReturn:p.modelReturn,equalWeightReturn:p.equalWeightReturn,
   changes:p.changes,benchmarkTrades:p.benchmarkTrades,cashWindows:p.cashWindows,investedWindows:p.investedWindows,
   observedStart:p.observedStart,observedEnd:p.observedEnd}:
   {ready:false,reason:safe(p.reason),complete:p.complete,scheduled:p.scheduled},
  limitations:r.limitations.slice(0,6)};
}
const api=Object.freeze({study,exportSafe});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateHistoricalPanelV110=api;
})(typeof window!=='undefined'?window:globalThis);
