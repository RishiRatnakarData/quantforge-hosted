/* V12.0: predeclared historical sensitivity grid, not a tuned trading policy.
 * Pure derived evidence; never accesses accounts, storage, or providers. */
(function(root){
'use strict';
const finite=n=>typeof n==='number'&&Number.isFinite(n);
const safe=s=>String(s||'Unavailable').slice(0,160);
const thresholds=[.15,.25,.35],fees=[0,10,30],windows=[10,21];
function analyze(inputs={}){
 const study=root.QFPrivateHistoricalPanelV110?.study;
 if(typeof study!=='function')return {ready:false,reason:'Historical model is missing.'};
 if(!inputs||!inputs.archive||!inputs.snapshot||!inputs.history||!inputs.selection)
  return {ready:false,reason:'Import a dated SEC archive and load selected investment price history.'};
 const scenarios=[];
 for(const step of windows){
  for(const limit of thresholds){
   for(const feeBps of fees){
    const r=study({...inputs,train:126,step,maxDrawdown:limit,feeBps});
    if(!r?.ready)return {ready:false,reason:safe(r?.reason),scenarios:[]};
    const p=r.performance;
    scenarios.push({step,maxDrawdown:limit,feeBps,
     scheduled:r.coverage.scheduled,covered:r.coverage.complete,
     performanceReady:!!p.ready,
     ruleReturn:p.ready?p.modelReturn:null,benchmarkReturn:p.ready?p.equalWeightReturn:null,
     spread:p.ready?Number((p.modelReturn-p.equalWeightReturn).toFixed(6)):null,
     investedWindows:p.ready?p.investedWindows:null,
     cashWindows:p.ready?p.cashWindows:null,
     restriction:p.ready?null:safe(p.reason)});
   }
  }
 }
 const eligible=scenarios.filter(s=>s.performanceReady);
 const incomplete=scenarios.length-eligible.length;
 // Never choose or optimize a policy from the grid; report ALL assumptions.
 const stable=eligible.length===scenarios.length;
 const group=windows.map(step=>{
  const rows=scenarios.filter(s=>s.step===step);
  const ok=rows.filter(s=>s.performanceReady);
  return {step,comparable:ok.length===rows.length,completeScenarios:ok.length,scheduledScenarios:rows.length,
   positiveSpread:ok.filter(s=>s.spread>0).length,
   negativeSpread:ok.filter(s=>s.spread<0).length,
   noDifference:ok.filter(s=>s.spread===0).length,
   minSpread:ok.length?Math.min(...ok.map(s=>s.spread)):null,
   maxSpread:ok.length?Math.max(...ok.map(s=>s.spread)):null};
 });
 return {ready:true,fullComparisonReady:stable,scenarioCount:scenarios.length,
  eligibleScenarios:eligible.length,withheldScenarios:incomplete,groups:group,scenarios,
  interpretation:stable?'All predefined scenarios have full filing coverage. Outcome dispersion is descriptive, not a parameter recommendation.':
   'At least one preset scenario is missing dated filing evidence. Do not compare or select strategies from available-only subsets.',
  limitations:[
   'All 18 settings are fixed before evaluation: 2 window lengths, 3 drawdown screens and 3 fee schedules.',
   'Window lengths 10 and 21 have different horizons; do not rank their total returns against one another.',
   'Current selected issuers remain survivorship-biased; historical delistings and universe changes are absent.',
   'Not a statistical significance test, causal experiment, out-of-sample optimization or prediction.',
   'Price-only outcomes omit distributions, delisting returns, spread, slippage, taxes and market impact.',
   'Missing archival evidence withholds aggregate findings; no missing windows are silently dropped.'
  ]};
}
function exportSafe(r){
 if(!r||!r.ready)return {schema:'quantforge.research-robustness.v12.0',ready:false,reason:safe(r?.reason)};
 return {schema:'quantforge.research-robustness.v12.0',ready:true,fullComparisonReady:r.fullComparisonReady,
  scenarioCount:r.scenarioCount,eligibleScenarios:r.eligibleScenarios,withheldScenarios:r.withheldScenarios,
  groups:r.groups.map(g=>({...g})),scenarios:r.scenarios.map(s=>({...s})),
  interpretation:r.interpretation,limitations:r.limitations.slice()};
}
const api=Object.freeze({analyze,exportSafe});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateHistoricalRobustnessV120=api;
})(typeof window!=='undefined'?window:globalThis);
