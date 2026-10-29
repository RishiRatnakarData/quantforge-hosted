/* QuantForge V9: deterministic and auditable research assessment. No IO, persistence or trading. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const iso=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&!Number.isNaN(Date.parse(x));
const pct=x=>(100*x).toFixed(1)+'%';
function assess(raw){
 const input=raw&&typeof raw==='object'?raw:{};
 const now=Date.parse(input.asOf),d=input.dossier,portfolio=input.portfolio;
 const risk=['conservative','balanced','growth'].includes(input.risk)?input.risk:'balanced';
 const horizon=['short','medium','long'].includes(input.horizon)?input.horizon:'medium';
 const maxWeight=finite(input.maxWeight)&&input.maxWeight>=.05&&input.maxWeight<=.5?input.maxWeight:.2;
 const maxDrawdown=finite(input.maxDrawdown)&&input.maxDrawdown>=.1&&input.maxDrawdown<=.6?input.maxDrawdown:.25;
 const symbols=Array.isArray(input.selection)?input.selection:[];
 const evidence=[],gaps=[],pro=[],con=[],steps=[];
 function record(key,title,state,detail,source){evidence.push({key,title,state,detail,source});}
 function gap(text){if(!gaps.includes(text))gaps.push(text);}
 const sym=typeof input.symbol==='string'?input.symbol:'';
 const validHistory=!!d?.ready&&d.symbol===sym&&symbols.includes(sym)&&
  Array.isArray(input.history?.symbols)&&input.history.symbols.length>=2&&
  input.history.symbols.length<=5&&input.history.symbols.length===symbols.length&&
  input.history.symbols.every(s=>symbols.includes(s))&&
  d.history?.observations>=63&&iso(d.history?.end)&&Number.isFinite(now)&&
  Date.parse(d.history.end)<=now&&now-Date.parse(d.history.end)<=7*86400000;
 if(!validHistory)gap('Load fresh, matching historical prices for this candidate and the selected investments.');
 record('history','Market evidence',validHistory?'available':'unavailable',validHistory?`${d.history.observations} aligned returns through ${d.history.end}`:'Selected investments and historical observations do not match or are older than seven days.','Candidate dossier · historical closes');
 const fiscal=d?.fundamentals?.fiscalEnd;
 const fundamentals=validHistory&&d.fundamentals?.available&&iso(fiscal)&&Date.parse(fiscal)<=now&&now-Date.parse(fiscal)<=800*86400000;
 if(!fundamentals)gap('Refresh valid SEC statements for this issuer and confirm the fiscal period.');
 let fundamentalState='unavailable';
 if(fundamentals){
  const f=d.fundamentals;
  const positive=[f.revenueGrowth,f.operatingMargin,f.freeCashFlowMargin].filter(finite).filter(x=>x>0).length;
  const negative=[f.revenueGrowth,f.operatingMargin,f.freeCashFlowMargin].filter(finite).filter(x=>x<0).length;
  fundamentalState=negative>=2?'cautions':positive>=2?'supports':'mixed';
  if(positive>=2)pro.push('At least two available annual growth/profitability/cash-generation indicators are positive.');
  if(negative>0)con.push('At least one available SEC growth or profitability indicator is negative.');
  if(!finite(f.freeCashFlowMargin))gap('Free-cash-flow comparability is missing for the latest SEC period.');
 }
 record('fundamentals','Company fundamentals',fundamentalState,fundamentals?`SEC fiscal ${fiscal}; revenue growth ${finite(d.fundamentals.revenueGrowth)?pct(d.fundamentals.revenueGrowth):'unavailable'}, operating margin ${finite(d.fundamentals.operatingMargin)?pct(d.fundamentals.operatingMargin):'unavailable'}, FCF margin ${finite(d.fundamentals.freeCashFlowMargin)?pct(d.fundamentals.freeCashFlowMargin):'unavailable'}.`:'No sufficiently recent, matched annual SEC figures.', 'Candidate dossier · reported SEC annual metrics');
 const quoteTime=Date.parse(input.quote?.timestamp);
 const validQuote=validHistory&&finite(input.quote?.price)&&input.quote.price>0&&Number.isFinite(quoteTime)&&quoteTime<=now&&now-quoteTime<=7*86400000&&input.quote.symbol===sym;
 if(!validQuote)gap('Obtain a dated current market observation before considering a purchase or sale.');
 const v=d?.valuation||{};
 const validValuation=validQuote&&v.marketCapAvailable&&finite(v.pSales)&&v.pSales>=0&&finite(v.fcfYield);
 let valState='unavailable';
 if(validValuation){
  valState=v.pSales>20||v.fcfYield<0?'cautions':v.fcfYield>0&&v.pSales<=10?'supports':'mixed';
  if(valState==='supports')pro.push('Observed cash-flow yield is positive and price-to-sales is within the selected descriptive screening band.');
  if(valState==='cautions')con.push('Price-to-sales exceeds 20 or observed free-cash-flow yield is negative; investigate business-specific valuation before adding exposure.');
 }else gap('Match current quotes, shares and annual reporting periods to compute observed-price valuation ratios.');
 record('valuation','Observed-price valuation',valState,validValuation?`P/S ${v.pSales.toFixed(2)}×; FCF yield ${pct(v.fcfYield)}. Descriptive thresholds, not intrinsic value.`:'Market-cap-based ratios missing or quote/filing context is incomplete.','V8.5 · observed-price valuation; no fair-value target');
 const m=d?.metrics||{};
 const validRisk=validHistory&&finite(m.maxDrawdown)&&m.maxDrawdown<=0&&finite(m.dailyES95)&&m.dailyES95>=0;
 const breach=validRisk&&-m.maxDrawdown>maxDrawdown;
 const esLimit=risk==='conservative'?.025:risk==='growth'?.06:.04;
 const highTail=validRisk&&m.dailyES95>esLimit;
 let riskState=validRisk?(breach||highTail?'cautions':'mixed'):'unavailable';
 if(validRisk){
  if(breach)con.push(`Observed maximum drawdown exceeded your selected ${pct(maxDrawdown)} tolerance.`);
  if(highTail)con.push('Observed one-day expected shortfall exceeds the selected risk-screening limit.');
  if(!breach&&!highTail)pro.push('Observed downside statistics were within the configured historical risk screens.');
 }else gap('A complete aligned return sample is required for downside-risk evaluation.');
 record('downside','Historical downside risk',riskState,validRisk?`Max drawdown ${pct(m.maxDrawdown)}, daily ES95 ${pct(m.dailyES95)}; tolerance ${pct(maxDrawdown)}.`:'Risk estimates unavailable.','V8.5 · historical drawdown and empirical tail loss');
 const holdings=portfolio?.holdings;
 const validPortfolio=validHistory&&portfolio&&finite(portfolio.cash)&&portfolio.cash>=0&&holdings&&typeof holdings==='object'&&!Array.isArray(holdings)&&d?.portfolioImpact&&finite(d.portfolioImpact.currentWeight);
 const current=validPortfolio?d.portfolioImpact.currentWeight:null;
 const concentrationBreach=validPortfolio&&current>maxWeight;
 const addingBreach=validPortfolio&&current+.05>maxWeight;
 const impactState=!validPortfolio?'unavailable':concentrationBreach||addingBreach?'cautions':'supports';
 if(!validPortfolio)gap('Refresh virtual holdings and priced positions to assess portfolio concentration.');
 if(validPortfolio){
  if(concentrationBreach)con.push('Current candidate concentration exceeds your configured single-name limit.');
  else if(addingBreach)con.push('An additional hypothetical 5% allocation would breach the single-name limit.');
  else pro.push('A hypothetical 5% allocation does not breach the selected concentration limit.');
 }
 record('portfolio','Portfolio fit',impactState,validPortfolio?`Current weight ${pct(current)}; single-name limit ${pct(maxWeight)}. Illustration assumes cash-funded purchases.`:'Portfolio impact withheld because priced virtual positions are incomplete.','V8.5 · hypothetical portfolio impact');
 const wf=input.walkforward,history=input.history;
 const validWalk=validHistory&&wf&&Array.isArray(wf.symbols)&&wf.symbols.length===symbols.length&&wf.symbols.every(s=>symbols.includes(s))&&Array.isArray(wf.windows)&&wf.windows.length>=2&&finite(wf.optimized?.metrics?.change)&&finite(wf.benchmark?.metrics?.change)&&iso(wf.end)&&history.dates.includes(wf.end);
 if(validWalk&&wf.optimized.metrics.change<wf.benchmark.metrics.change)con.push('The multi-asset allocation trailed its historical equal-weight benchmark in tested windows. This is not candidate-specific evidence.');
 record('walkforward','Strategy robustness',validWalk?(wf.optimized.metrics.change>=wf.benchmark.metrics.change?'mixed':'cautions'):'unavailable',validWalk?`Multi-asset walk-forward: strategy ${pct(wf.optimized.metrics.change)} versus equal weight ${pct(wf.benchmark.metrics.change)}; not a single-company forecast.`:'Walk-forward results missing or not matched to the selected universe.','Research Lab · past-only walk-forward, portfolio scope');
 const ff=input.french;
 const validFF=validHistory&&ff?.ready&&ff.symbol===sym&&ff.aligned>=100;
 record('factors','Independent factors',validFF?'mixed':'unavailable',validFF?'Imported independent FF3 sample is available; estimated exposures are descriptive, not expected returns.':'No eligible, imported official daily factor sample for this candidate.','V8.7 · independent FF3 (optional; user-supplied CSV)');
 if(horizon==='short')con.push('Short investment horizon may be inconsistent with historical equity downside.');
 const critical=validHistory&&fundamentals&&validQuote&&validRisk&&validPortfolio;
 let decision='Insufficient evidence';let reason='A material required input is unavailable, stale or mismatched; the system will not infer a trade from incomplete data.';
 if(critical){
  if(concentrationBreach){decision='Review / consider reducing exposure';reason='The observed portfolio weight exceeds your stated concentration ceiling; reassess exposure before increasing it.';}
  else if(breach||highTail||addingBreach){decision=current>0?'Hold / avoid increasing':'Avoid adding for now';reason='Historical downside or portfolio concentration exceeds at least one of your explicit constraints.';}
  else if(fundamentalState==='cautions'||valState==='cautions'){decision='Research further before adding';reason='The available fundamental or valuation context raises meaningful objections even though the risk screens may pass.';}
  else if(!validValuation){decision='Research further before adding';reason='Risk and fundamentals are available, but the observed-price valuation case is incomplete.';}
  else if(current>0){decision='Hold / monitor';reason='Available evidence does not breach the specified screening limits; this is a monitoring assessment, not a return prediction.';}
  else if(fundamentalState==='supports'&&valState==='supports'&&horizon!=='short'){
   decision='Consider a small position (conditional)';reason='Positive fundamental screens, available valuation ratios and selected risk/weight limits are compatible; review assumptions before any transaction.';
  }else{decision='Research further before adding';reason='Available evidence is mixed or does not establish a sufficiently clear case under the selected screens.';}
 }
 steps.push(...gaps);
 if(validPortfolio&&addingBreach)steps.push('Compare a smaller hypothetical allocation under the configured concentration limit.');
 if(validWalk&&wf.optimized.metrics.change<wf.benchmark.metrics.change)steps.push('Investigate the multi-asset strategy underperformance in Research Lab.');
 if(!validFF)steps.push('Optional: import and validate daily FF3 factors for descriptive exposures.');
 const checked=evidence.filter(x=>x.state!=='unavailable').length;
 return {schema:'quantforge.research-os.v9.0',policy:'explicit-screens.v1',symbol:sym,asOf:input.asOf||null,decision,reason,
  summary:`${checked} of ${evidence.length} evidence categories available. ${critical?'Required data gates passed.':'Required data gates not all satisfied.'}`,
  evidence,pro,con,gaps,steps:steps.slice(0,9),constraints:{risk,horizon,maxWeight,maxDrawdown},
  readiness:critical?'required-inputs-valid':'withheld',
  limitations:['Screening cutoffs are configurable research assumptions, not learned return probabilities or calibrated predictions.',
   'Financial-statement dates, observed market prices and historical return windows are different evidence types.',
   'Portfolio walk-forward analysis is not candidate-specific proof. Correlated metrics are not counted as independent votes.',
   'No virtual or live trade is initiated or authorized by this report.']};
}
const api=Object.freeze({assess});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateResearchOSV90=api;
})(typeof window!=='undefined'?window:globalThis);
