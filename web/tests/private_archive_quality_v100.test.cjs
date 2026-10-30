'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'../site');
const validator=require('../site/private_archived_sec_v99.js');
const quality=require('../site/private_archive_quality_v100.js');
const acc='0000000001-25-000001';
function issuer(symbol,cik){
 return {symbol,cik,annual:[2024,2023].map(year=>{
  const base={start:`${year}-01-01`,filed:`${year+1}-03-01`,accession:acc};
  const values={revenue_usd:100+10*(year-2023),operating_cash_flow_usd:40,capex_usd:10};
  const tags={revenue_usd:'RevenueFromContractWithCustomerExcludingAssessedTax',
   operating_cash_flow_usd:'NetCashProvidedByUsedInOperatingActivities',
   capex_usd:'PaymentsToAcquirePropertyPlantAndEquipment'};
  return {fiscal_end:`${year}-12-31`,revisions:Object.fromEntries(Object.keys(values).map(field=>[field,[{...base,value:values[field],tag:tags[field],tag_priority:0}]]))};
 })};
}
function fixture(){
 const companies=[issuer('AAA',1),issuer('BBB',2)];
 return {archive:{schema:'quantforge.sec.filing-revisions.v9.8',as_of:'2026-10-29',companies},
  snapshot:{companies:companies.map(({symbol,cik})=>({symbol,cik}))}};
}
test('checkpoint sampling is dated, bounded and cannot exceed archive cutoff',()=>{
 const dates=quality.checkpoints('2026-10-29',2023);
 assert.deepEqual(dates.slice(0,3),['2023-01-01','2023-07-01','2024-01-01']);
 assert.equal(dates.at(-1),'2026-07-01');
 assert.deepEqual(quality.checkpoints('not-date'),[]);
});
test('two issuer readiness uses filing dates, not the fiscal year end',()=>{
 const {archive,snapshot}=fixture();
 const r=quality.inspect({archive,snapshot,selection:['AAA','BBB'],startYear:2023});
 assert.equal(r.ready,true);
 assert.equal(r.archivedIssuers,2);
 assert.equal(r.selectedCount,2);
 assert.equal(r.dates.firstComplete,'2025-07-01');
 assert.ok(r.dates.complete<r.dates.scheduled);
 assert.ok(r.rows.every(x=>x.eligible===r.dates.complete));
});
test('missing selected issuer withholds complete-universe coverage without omitting it',()=>{
 const {archive,snapshot}=fixture();snapshot.companies.push({symbol:'CCC',cik:3});
 const r=quality.inspect({archive,snapshot,selection:['AAA','CCC'],startYear:2024});
 assert.equal(r.ready,true);assert.equal(r.dates.complete,0);
 assert.equal(r.rows[1].eligible,0);
 assert.match(r.rows[1].primaryGap.reason,/absent/);
});
test('invalid identities and CIK mismatches never qualify',()=>{
 const {archive,snapshot}=fixture();
 archive.companies[0].cik=999;
 assert.equal(quality.inspect({archive,snapshot}).ready,false);
 archive.companies[0].cik=1;
 assert.equal(quality.inspect({archive,snapshot,selection:['AAA','AAA']}).ready,false);
});
test('safe export omits original SEC metrics and excludes all account/private contents',()=>{
 const {archive,snapshot}=fixture();
 const r=quality.inspect({archive,snapshot,selection:['AAA','BBB']});
 const encoded=JSON.stringify(quality.exportSafe(r));
 for(const forbidden of ['accession','revenue_usd','cashFlow','holdings','balance','value','quotes','weights','tokens']){
  assert.ok(!encoded.includes('"'+forbidden+'"'),forbidden);
 }
 assert.match(encoded,/coveragePct/);
});
test('readiness code cannot fetch, save, authenticate or place broker orders',()=>{
 const code=fs.readFileSync(path.join(root,'private_archive_quality_v100.js'),'utf8');
 for(const forbidden of ['fetch(', 'localStorage', 'sessionStorage','XMLHttpRequest','private/trade','private/notes','portfolio/order']){
  assert.ok(!code.includes(forbidden),forbidden);
 }
 assert.equal(typeof validator.auditAt,'function');
});
