const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
// V9.7 audit is the source of the strict per-metric filing-date validation.
require('../site/private_pit_validation_v97.js');
const api=require('../site/private_sec_coverage_v98.js');
const dateAt=i=>new Date(Date.UTC(2024,0,1+i)).toISOString().slice(0,10);
const dates=Array.from({length:850},(_,i)=>dateAt(i));
const history={dates,symbols:['AAA','BBB'],closes:{
 AAA:dates.map((_,i)=>90+i*.14),BBB:dates.map((_,i)=>80+i*.09)
}};
function annual(end,filed,v,accession){
 return {fiscal_end:end,metrics:{revenue_usd:v,operating_cash_flow_usd:v*.2,capex_usd:v*.05,free_cash_flow_usd:v*.15},
  sources:Object.fromEntries(['revenue_usd','operating_cash_flow_usd','capex_usd'].map(k=>[k,{filed,accession,tag:'USGAAP_'+k}]))};
}
const company=symbol=>({symbol,annual:[
 annual('2025-12-31','2026-03-04',1400,'0000000001-26-000001'),
 annual('2024-12-31','2025-03-04',1250,'0000000001-25-000001'),
 annual('2023-12-31','2024-03-04',1100,'0000000001-24-000001'),
]});
const snapshot={as_of:'2026-04-29',companies:[company('AAA'),company('BBB')]};
const input={snapshot,history,selection:['AAA','BBB'],candidate:'AAA'};
test('identical filing coverage for two valid issuers, no performance forecast',()=>{
 const r=api.run(input);
 assert.equal(r.ready,true);assert.equal(r.rows.length,2);
 assert.deepEqual(r.rows.map(x=>x.eligible),[r.rows[0].eligible,r.rows[0].eligible]);
 assert.equal(r.counts.eligible,r.rows[0].eligible);
 assert.equal(r.counts.withheld+r.counts.eligible,r.counts.scheduled);
 assert.ok(r.rows[0].medianFilingLagDays>0);
 assert.ok(!('expectedReturn' in r));
});
test('missing one issuer withholds complete universe, never implicitly excludes it',()=>{
 const r=api.run({...input,snapshot:{...snapshot,companies:[snapshot.companies[0]]}});
 assert.equal(r.ready,true);assert.equal(r.rows[1].eligible,0);
 assert.equal(r.counts.eligible,0);assert.equal(r.counts.withheld,r.counts.scheduled);
 assert.ok(r.rows[1].gaps[0].reason.includes('No SEC'));
});
test('future-dated filings and issuer-specific cutoff cannot be backdated',()=>{
 const c=company('BBB');c.as_of='2025-04-01';
 const r=api.run({...input,snapshot:{...snapshot,companies:[company('AAA'),c]}});
 assert.ok(r.rows[1].withheld>0);assert.ok(r.rows[1].eligible<r.rows[0].eligible);
 const revised=company('BBB');revised.annual[1].sources.revenue_usd.filed='2026-01-02';
 const b=api.run({...input,snapshot:{...snapshot,companies:[company('AAA'),revised]}});
 assert.ok(b.rows[1].eligible<r.rows[0].eligible);
});
test('bad histories, stale selection and repeated issuer entries fail closed',()=>{
 for(const change of [
  {...input,selection:['AAA','ZZZ']},
  {...input,selection:['AAA','AAA']},
  {...input,history:{...history,dates:[...history.dates].reverse()}},
  {...input,snapshot:{...snapshot,companies:[company('AAA'),company('AAA')]}},
 ])assert.equal(api.run(change).ready,false);
});
test('sanitized summary contains no prices, account information, accessions or source facts',()=>{
 const exported=JSON.stringify(api.exportSafe(api.run(input)));
 for(const forbidden of ['closes','holdings','balance','prices','token','accession','revenue_usd','sources','provider','cash','portfolio'])
  assert.equal(exported.toLowerCase().includes(forbidden),false,forbidden);
});
test('pure helper has no fetching, storage, API requests or order entry',()=>{
 const source=fs.readFileSync(path.resolve(__dirname,'../site/private_sec_coverage_v98.js'),'utf8');
 for(const token of ['fetch(', 'localStorage', 'sessionStorage','XMLHttpRequest','WebSocket(', 'private/notes', 'private/trade'])
  assert.equal(source.includes(token),false,token);
});
