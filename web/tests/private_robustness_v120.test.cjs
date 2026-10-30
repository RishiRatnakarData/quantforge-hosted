'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
require('../site/private_pit_validation_v97.js');
require('../site/private_archived_sec_v99.js');
const panel=require('../site/private_historical_panel_v110.js');
const robust=require('../site/private_robustness_v120.js');
const dates=Array.from({length:390},(_,i)=>new Date(Date.UTC(2025,0,i+1)).toISOString().slice(0,10));
function company(symbol,cik,positive=true){
 const annual=[2022,2023,2024].map(y=>{
  const base={start:`${y}-01-01`,filed:`${y+1}-03-01`,accession:'0000000001-25-000001',tag_priority:0};
  const item=(tag,value)=>({...base,tag,value});
  return {fiscal_end:`${y}-12-31`,revisions:{
   revenue_usd:[item('RevenueFromContractWithCustomerExcludingAssessedTax',y===2024?1400:1200)],
   operating_cash_flow_usd:[item('NetCashProvidedByUsedInOperatingActivities',positive?350:10)],
   capex_usd:[item('PaymentsToAcquirePropertyPlantAndEquipment',30)]}};
 });return {symbol,cik,annual};
}
const snapshot={as_of:'2026-10-29',companies:[{symbol:'AAA',cik:1},{symbol:'BBB',cik:2}]};
function inputs(){return {snapshot,archive:{schema:'quantforge.sec.filing-revisions.v9.8',as_of:'2026-10-29',
 companies:[company('AAA',1),company('BBB',2)]},
 history:{dates,symbols:['AAA','BBB'],closes:{AAA:dates.map((_,i)=>100+i*.2),BBB:dates.map((_,i)=>150+i*.04)}},
 selection:['AAA','BBB']};}
test('predeclared 18 scenario grid is complete and never chooses a best parameter',()=>{
 const r=robust.analyze(inputs());
 assert.equal(r.ready,true);assert.equal(r.scenarioCount,18);
 assert.equal(r.eligibleScenarios,18);assert.equal(r.fullComparisonReady,true);
 assert.deepEqual([...new Set(r.scenarios.map(x=>x.step))],[10,21]);
 assert.deepEqual([...new Set(r.scenarios.map(x=>x.feeBps))],[0,10,30]);
 assert.deepEqual([...new Set(r.scenarios.map(x=>x.maxDrawdown))],[.15,.25,.35]);
 assert.equal(r.groups.length,2);
 assert.equal(r.selectedPolicy,undefined);
});
test('higher transaction costs never improve same-model or benchmark cumulative returns',()=>{
 const r=robust.analyze(inputs());
 for(const step of [10,21])for(const maxDrawdown of [.15,.25,.35]){
  const series=r.scenarios.filter(x=>x.step===step&&x.maxDrawdown===maxDrawdown);
  assert.ok(series[0].ruleReturn>=series[1].ruleReturn);
  assert.ok(series[1].ruleReturn>=series[2].ruleReturn);
  assert.ok(series[0].benchmarkReturn>=series[1].benchmarkReturn);
  assert.ok(series[1].benchmarkReturn>=series[2].benchmarkReturn);
 }
});
test('benchmark charges entry and exit cost in every observation window',()=>{
 const r=panel.study({...inputs(),train:126,step:21,feeBps:10});
 assert.equal(r.performance.ready,true);
 assert.equal(r.performance.benchmarkTrades,2*r.coverage.scheduled);
});
test('missing SEC windows always withhold unsupported results across the entire grid',()=>{
 const v=inputs();v.archive.companies[1].annual[1].revisions.revenue_usd[0].filed='2026-09-01';
 const r=robust.analyze(v);
 assert.equal(r.ready,true);assert.equal(r.fullComparisonReady,false);
 assert.ok(r.withheldScenarios>0);
 assert.ok(r.scenarios.some(x=>!x.performanceReady&&x.ruleReturn===null));
});
test('future market returns never affect prior selected company',()=>{
 const x=inputs(),a=panel.study({...x,train:126,step:21});
 x.history.closes.BBB[300]*=2;
 const b=panel.study({...x,train:126,step:21});
 assert.equal(a.performance.rows[0].selected,b.performance.rows[0].selected);
});
test('safe robustness export includes no account state or raw SEC/price history',()=>{
 const text=JSON.stringify(robust.exportSafe(robust.analyze(inputs())));
 for(const bad of ['"closes"','"holdings"','"accession"','"cash_balance"','"revisions"','"apiKey"'])
  assert.ok(!text.includes(bad),bad);
});
test('offline helper cannot fetch, trade, mutate MFA or use browser storage',()=>{
 const code=fs.readFileSync(path.join(__dirname,'../site/private_robustness_v120.js'),'utf8');
 for(const bad of ['fetch(', 'localStorage', 'sessionStorage', 'XMLHttpRequest', 'private/trade', 'indexedDB'])
  assert.ok(!code.includes(bad),bad);
});
