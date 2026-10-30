"use strict";
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const integrity=require('../site/private_decision_integrity_v130.js');
const attribution=require('../site/private_historical_attribution_v130.js');
const windows=[
 {decisionDate:'2025-01-01',executionDate:'2025-01-02',testThrough:'2025-01-21',selected:'AAA',rulePeriodReturn:.08,benchmarkPeriodReturn:.04},
 {decisionDate:'2025-02-01',executionDate:'2025-02-02',testThrough:'2025-02-21',selected:'BBB',rulePeriodReturn:-.03,benchmarkPeriodReturn:-.02},
 {decisionDate:'2025-03-01',executionDate:'2025-03-02',testThrough:'2025-03-21',selected:null,rulePeriodReturn:0,benchmarkPeriodReturn:.01}
];
const historical=()=>({ready:true,coverage:{scheduled:3,complete:3},performance:{ready:true,rows:structuredClone(windows)}});
const brief=()=>({schema:'quantforge.research-brief.v9.3',symbol:'AAA',asOf:'2026-10-29',action:'Review',
 blocked:false,universe:[{symbol:'AAA'},{symbol:'BBB'}],models:[{status:'completed'},{status:'completed'}],
 modelCoverage:{total:2,completed:2},mandatoryMissing:[],conflicts:[],cautions:['Data limitations.']});
const inputs=()=>({brief:brief(),historical:historical(),robustness:{ready:true,scenarioCount:18,eligibleScenarios:18,fullComparisonReady:true},
 portfolio:{schema:'quantforge.portfolio-validation.v9.5',symbol:'AAA',portfolio:{ready:true}}});
test('descriptive attribution reconstructs observed after-fee windows and drawdowns',()=>{
 const r=attribution.study(historical());
 assert.equal(r.ready,true);assert.equal(r.windowsEvaluated,3);
 assert.equal(r.outcomes.outperform,1);assert.equal(r.outcomes.underperform,2);
 assert.equal(r.outcomes.cashWindows,1);assert.equal(r.outcomes.distinctSelectedCompanies,2);
 assert.ok(r.outcomes.modelMaxDrawdown<=0);assert.ok(r.outcomes.benchmarkMaxDrawdown<=0);
 assert.equal(r.windows.length,3);
});
test('missing SEC window never becomes a computed attribution',()=>{
 const h=historical();h.coverage.complete=2;
 assert.equal(attribution.study(h).ready,false);
 assert.equal(attribution.study({ready:true,performance:{ready:false}}).ready,false);
});
test('future or overlapping windows reject historical attribution',()=>{
 const h=historical();h.performance.rows[1].executionDate='2025-01-20';
 assert.equal(attribution.study(h).ready,false);
 const f=historical();f.performance.rows[0].rulePeriodReturn=-1.5;
 assert.equal(attribution.study(f).ready,false);
});
test('complete checklist is labeled as evidence only, not investment confidence',()=>{
 const x=inputs();x.attribution=attribution.study(x.historical);
 const r=integrity.assess(x);
 assert.equal(r.ready,true);assert.equal(r.classification,'evidence-complete');
 assert.equal(r.coveredGates,5);assert.ok(r.attribution.available);
 assert.match(r.statement,/not a confidence score/);
 assert.equal(r.action,undefined);
});
test('blocked original decision dominates apparent positive history',()=>{
 const x=inputs();x.brief.blocked=true;
 assert.equal(integrity.assess(x).classification,'blocked');
});
test('partial SEC or unavailable private portfolio explicitly degrades integrity',()=>{
 const x=inputs();x.historical.coverage.complete=2;
 const r=integrity.assess(x);
 assert.equal(r.classification,'evidence-limited');
 assert.equal(r.attribution,null);
 assert.equal(r.gates.find(g=>g.key==='historicalFilingCoverage').status,'limited');
 x.historical=historical();x.portfolio.symbol='OTHER';
 assert.equal(integrity.assess(x).gates.find(g=>g.key==='portfolioRiskEvidence').status,'limited');
});
test('empty or stale briefing fails closed',()=>{
 assert.equal(integrity.assess({}).ready,false);
 const x=inputs();x.brief.universe=[{symbol:'BBB'},{symbol:'BBB'}];
 assert.equal(integrity.assess(x).ready,false);
});
test('exports exclude holdings, prices, timestamps of individual trades and raw accessions',()=>{
 const x=inputs();x.attribution=attribution.study(x.historical);
 const text=JSON.stringify({a:attribution.exportSafe(x.attribution),b:integrity.exportSafe(integrity.assess(x))});
 for(const forbidden of ['"closes"','"holdings"','"quantity"','"balance"','"revisions"','"accession"','"executionDate"','"token"','"apiKey"'])
  assert.ok(!text.includes(forbidden),forbidden);
});
test('both modules are pure and cannot fetch, mutate MFA or submit brokerage orders',()=>{
 for(const f of ['private_decision_integrity_v130.js','private_historical_attribution_v130.js']){
  const text=fs.readFileSync(path.join(__dirname,'../site',f),'utf8');
  for(const bad of ['fetch(', 'localStorage', 'sessionStorage', 'XMLHttpRequest', 'private/trade', 'indexedDB', 'WebSocket('])
   assert.ok(!text.includes(bad),f+':'+bad);
 }
});
