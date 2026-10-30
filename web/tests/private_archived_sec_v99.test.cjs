const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
require('../site/private_pit_validation_v97.js');
const api=require('../site/private_archived_sec_v99.js');
const d=i=>new Date(Date.UTC(2023,0,1+i)).toISOString().slice(0,10);
const dates=Array.from({length:900},(_,i)=>d(i));
const history={dates,symbols:['AAA','BBB'],closes:{
 AAA:dates.map((_,i)=>90+i*.07+2*Math.sin(i/18)),
 BBB:dates.map((_,i)=>60+i*.05+2*Math.cos(i/14))
}};
const accession=(year,n=1)=>`0000000001-${String(year).slice(2)}-${String(n).padStart(6,'0')}`;
function period(year,revenue=1000){
 const end=`${year}-12-31`,start=`${year}-01-01`,filed=`${year+1}-03-15`;
 const row=(v,tag,extra={})=>({start,filed,accession:accession(year+1),tag,tag_priority:0,value:v,...extra});
 return {fiscal_end:end,revisions:{revenue_usd:[row(revenue,'RevenueFromContractWithCustomerExcludingAssessedTax')],
  operating_cash_flow_usd:[row(revenue*.23,'NetCashProvidedByUsedInOperatingActivities')],
  capex_usd:[row(revenue*.05,'PaymentsToAcquirePropertyPlantAndEquipment')]}};
}
const company=(symbol,cik)=>({symbol,cik,annual:[period(2024,1500),period(2023,1400),period(2022,1250),period(2021,1100)]});
const archive=()=>({schema:'quantforge.sec.filing-revisions.v9.8',as_of:'2026-10-29',
 companies:[company('AAA',1),company('BBB',2)]});
const snapshot={as_of:'2026-10-29',companies:[{symbol:'AAA',cik:1},{symbol:'BBB',cik:2}]};
const input=()=>({archive:archive(),snapshot,history,selection:['AAA','BBB'],candidate:'AAA'});
test('valid source has dated original versions and cross-issuer coverage, withhold if any windows missing',()=>{
 const r=api.run(input());
 assert.equal(r.ready,true);
 assert.equal(r.counts.scheduled,r.counts.completeUniverse);
 assert.equal(r.performance.ready,true);
 assert.equal(r.issuers.length,2);
 assert.ok(Number.isFinite(r.performance.ruleReturn));
});
test('future amendment never changes decision before its filing date',()=>{
 const a=archive();const before=api.auditAt(a.companies[0],'2025-04-01');
 const extra={...a.companies[0].annual[0].revisions.revenue_usd[0],
  filed:'2025-05-01',accession:'0000000001-25-000099',value:9000};
 a.companies[0].annual[0].revisions.revenue_usd.push(extra);
 const still=api.auditAt(a.companies[0],'2025-04-01');
 assert.deepEqual(still,before);
 const after=api.auditAt(a.companies[0],'2025-06-01');
 assert.equal(after.usedLaterVersion,true);
});
test('substituted restatement affects only later decisions while preserving historical original',()=>{
 const a=archive();const before=api.auditAt(a.companies[0],'2024-05-01');
 const update={...a.companies[0].annual[1].revisions.revenue_usd[0],filed:'2024-09-01',
  accession:'0000000001-24-000033',value:2000};
 a.companies[0].annual[1].revisions.revenue_usd.push(update);
 assert.deepEqual(api.auditAt(a.companies[0],'2024-05-01'),before);
 assert.notEqual(api.auditAt(a.companies[0],'2024-10-01').revenueGrowth,before.revenueGrowth);
});
test('missing issuer or filing history never gives a partial-universe cumulative result',()=>{
 const a=archive();a.companies.pop();
 const r=api.run({...input(),archive:a});
 assert.equal(r.ready,true);assert.equal(r.counts.completeUniverse,0);
 assert.equal(r.performance.ready,false);
 const b=archive();b.companies[1].annual.splice(1);
 const partial=api.run({...input(),archive:b});
 assert.equal(partial.performance.ready,false);
});
test('CIK mismatch, duplicated issuer, conflicting source facts, future filing, bad fiscal dates fail validation',()=>{
 const cases=[];
 let a=archive();a.companies[0].cik=5;cases.push(a);
 a=archive();a.companies.push(a.companies[0]);cases.push(a);
 a=archive();a.companies[0].annual[0].revisions.revenue_usd.push({...a.companies[0].annual[0].revisions.revenue_usd[0],value:999});cases.push(a);
 a=archive();a.companies[0].annual[0].revisions.revenue_usd[0].filed='2027-01-01';cases.push(a);
 a=archive();a.companies[0].annual[0].revisions.revenue_usd[0].start='2024-12-01';cases.push(a);
 a=archive();a.companies[0].annual[0].fiscal_end='not-a-date';cases.push(a);
 a=archive();a.companies[0].annual[0].revisions.revenue_usd[0].tag='MadeUpFinancialTag';cases.push(a);
 a=archive();a.companies[0].annual[0].revisions.revenue_usd[0].tag_priority=2;cases.push(a);
 for(const sample of cases)assert.equal(api.validateArchive(sample,snapshot).ready,false);
});
test('malformed observations and different selection refuse research conclusions',()=>{
 for(const value of [
  {...input(),history:{...history,dates:[...dates].reverse()}},
  {...input(),selection:['AAA','ZZZ']},
  {...input(),selection:['AAA','AAA']},
  {...input(),maxDrawdown:NaN},
 ])assert.equal(api.run(value).ready,false);
});
test('archive export excludes raw SEC figures, source accessions, holdings, account and raw price vectors',()=>{
 const report=JSON.stringify(api.exportSafe(api.run(input()))).toLowerCase();
 for(const token of ['accession','revenue_usd','operating_cash_flow_usd','closes','holdings','cash',
   'accountid','providerkey','pricevector','sources','tag_priority'])assert.equal(report.includes(token),false,token);
 assert.ok(report.includes('archived-sec-evidence'));
});
test('pure research helper cannot fetch, trade, touch storage, network, or mutate an account',()=>{
 const code=fs.readFileSync(path.resolve(__dirname,'../site/private_archived_sec_v99.js'),'utf8');
 for(const token of ['fetch(', 'localStorage', 'sessionStorage','XMLHttpRequest','WebSocket(',
    'private/notes','private/trade','indexedDB','sendBeacon('])
  assert.equal(code.includes(token),false,token);
});
