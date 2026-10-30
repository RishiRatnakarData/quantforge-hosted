'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
require('../site/private_pit_validation_v97.js');
const pit=require('../site/private_archived_sec_v99.js');
const panel=require('../site/private_historical_panel_v110.js');
const dates=Array.from({length:390},(_,i)=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10));
const accession='0000000001-25-000001';
function issuer(symbol,cik,margin=.20){
 return {symbol,cik,annual:[2024,2023,2022].map(year=>{
  const base={start:`${year}-01-01`,filed:`${year+1}-03-01`,accession,tag_priority:0};
  const income=year===2024?1400:year===2023?1200:1100;
  const item=(value,tag)=>({...base,value,tag});
  return {fiscal_end:`${year}-12-31`,revisions:{
   revenue_usd:[item(income,'RevenueFromContractWithCustomerExcludingAssessedTax')],
   operating_cash_flow_usd:[item(income*(margin+.05),'NetCashProvidedByUsedInOperatingActivities')],
   capex_usd:[item(income*.05,'PaymentsToAcquirePropertyPlantAndEquipment')]
  }};
 })};
}
const snapshot={as_of:'2026-10-29',companies:[{symbol:'AAA',cik:1},{symbol:'BBB',cik:2}]};
const archive=()=>({schema:'quantforge.sec.filing-revisions.v9.8',as_of:'2026-10-29',companies:[issuer('AAA',1,.24),issuer('BBB',2,.13)]});
const history=()=>({dates,symbols:['AAA','BBB'],closes:{
 AAA:dates.map((_,i)=>110+i*.04+Math.sin(i/18)),
 BBB:dates.map((_,i)=>85+i*.03+Math.cos(i/22))}});
const args=()=>({archive:archive(),snapshot,history:history(),selection:['AAA','BBB']});
test('cross-company historical study needs complete original filing eligibility and same prices',()=>{
 const r=panel.study(args());
 assert.equal(r.ready,true);
 assert.equal(r.coverage.complete,r.coverage.scheduled);
 assert.equal(r.performance.ready,true);
 assert.ok(r.performance.rows.every(x=>x.selected==='AAA'));
 assert.ok(Number.isFinite(r.performance.modelReturn));
 assert.equal(r.policy.label.includes('FCF'),true);
});
test('future outcome prices never change a prior selected company',()=>{
 const a=args();const before=panel.study(a);
 a.history.closes.BBB[250]*=3;
 const after=panel.study(a);
 assert.equal(before.performance.rows[0].decisionDate,after.performance.rows[0].decisionDate);
 assert.equal(before.performance.rows[0].selected,after.performance.rows[0].selected);
});
test('later filing revisions cannot influence decisions before filing',()=>{
 const a=args(),before=panel.study(a);
 const original=a.archive.companies[0].annual[0].revisions.revenue_usd[0];
 a.archive.companies[0].annual[0].revisions.revenue_usd.push({...original,filed:'2026-05-01',accession:'0000000001-26-000089',value:1});
 const after=panel.study(a);
 assert.deepEqual(before.performance.rows[0],after.performance.rows[0]);
 assert.equal(pit.validateArchive(a.archive,a.snapshot).ready,true);
});
test('one unavailable issuer in any scheduled window withholds all cumulative returns',()=>{
 const a=args();a.archive.companies[1].annual.splice(2);a.archive.companies[1].annual[0].revisions.revenue_usd[0].filed='2025-08-01';
 const r=panel.study(a);
 assert.equal(r.ready,true);
 assert.ok(r.coverage.withheld>0);
 assert.equal(r.performance.ready,false);
});
test('no positive candidate means explicit cash allocation, no fictitious stock result',()=>{
 const a=args();for(const issuer of a.archive.companies)for(const period of issuer.annual){
  period.revisions.operating_cash_flow_usd[0].value=0;
 }
 const r=panel.study(a);
 assert.equal(r.performance.ready,true);
 assert.equal(r.performance.investedWindows,0);
 assert.equal(r.performance.cashWindows,r.coverage.scheduled);
 assert.ok(r.performance.rows.every(x=>x.selected===null&&x.rulePeriodReturn===0));
});
test('historical trading costs never improve returns when strategy has entry turnover',()=>{
 const free=panel.study({...args(),feeBps:0});const charged=panel.study({...args(),feeBps:100});
 assert.ok(charged.performance.modelReturn<free.performance.modelReturn);
 assert.ok(charged.performance.equalWeightReturn<free.performance.equalWeightReturn);
});
test('bad archive, stale price format, selection mismatch, invalid fee all fail closed',()=>{
 const cases=[{...args(),selection:['AAA','ZZZ']},{...args(),selection:['AAA','AAA']},
  {...args(),feeBps:NaN},{...args(),archive:{...archive(),schema:'fake'}},
  {...args(),history:{...history(),dates:[...dates].reverse()}}];
 for(const input of cases)assert.equal(panel.study(input).ready,false);
});
test('safe export omits raw market prices, financial values, brokerage info, source accessions',()=>{
 const result=JSON.stringify(panel.exportSafe(panel.study(args()))).toLowerCase();
 for(const bad of ['"closes"','"revenue_usd"','"operating_cash_flow_usd"','"value"',
  '"raw"','"holdings"','"balance"','"accession"','"tokens"','"prices"'])
  assert.equal(result.includes(bad),false,bad);
});
test('module remains pure with no network, storage, authentication or trade capability',()=>{
 const code=fs.readFileSync(path.join(__dirname,'../site/private_historical_panel_v110.js'),'utf8');
 for(const bad of ['fetch(', 'localStorage', 'sessionStorage', 'XMLHttpRequest',
  'private/notes','private/trade','indexedDB','WebSocket('])assert.ok(!code.includes(bad),bad);
});
