const test=require('node:test');
const assert=require('node:assert/strict');
require('../site/sec_analytics.js');
const S=globalThis.QFSecAnalytics;
function issuer(symbol,{income=20,rev=100,prior=80,fcf=10,sector='Technology'}={}){
 const annual=[
 {fiscal_end:'2025-12-31',metrics:{revenue_usd:rev,operating_income_usd:income,free_cash_flow_usd:fcf},sources:{revenue_usd:{tag:'Revenue',filed:'2026-01-20',accession:'123-456'}}},
 {fiscal_end:'2024-12-31',metrics:{revenue_usd:prior,operating_income_usd:income,free_cash_flow_usd:fcf},sources:{}},
 {fiscal_end:'2023-12-31',metrics:{revenue_usd:50,operating_income_usd:income,free_cash_flow_usd:fcf},sources:{}}
 ];
 return {symbol,name:symbol,sector,cik:42,source_url:'https://data.sec.gov/example',annual};
}
test('real annual revenue trend is chronological, not reverse filing order',()=>{
 assert.deepEqual(S.revenueSeries(issuer('ABC')).map(r=>r.fiscal_end),['2023-12-31','2024-12-31','2025-12-31']);
 assert.deepEqual(S.revenueSeries({annual:[]}),[]);
});
test('available metrics sort above unavailable fields; zero is not missing',()=>{
 const data={companies:[issuer('JNJ',{income:null,rev:99}),issuer('ALPHA',{income:10,rev:100}),issuer('ZERO',{income:0,rev:98})]};
 const rows=S.ranking(data,'margin');
 assert.deepEqual(rows.map(r=>r.symbol),['ALPHA','ZERO','JNJ']);
 assert.equal(rows[1].value,0);
 assert.equal(rows[2].value,null);
 assert.throws(()=>S.ranking(data,'arbitrary'));
});
test('year-over-year growth requires valid comparable prior annual revenue',()=>{
 assert.equal(S.metricValue(issuer('A').annual,'growth'),25);
 assert.equal(S.metricValue(issuer('B',{prior:0}).annual,'growth'),null);
 assert.equal(S.metricValue(issuer('C',{prior:null}).annual,'growth'),null);
 assert.equal(S.metricValue(issuer('D',{income:null}).annual,'margin'),null);
});
test('free cash flow can be negative and stays numeric',()=>{
 const data={as_of:'2026-10-25',companies:[issuer('A',{fcf:-500})]};
 assert.equal(S.ranking(data,'fcf')[0].value,-500);
 const csv=S.snapshotCsv(data);
 assert.match(csv,/,-500,/);
 assert.doesNotMatch(csv,/'-500/);
});
test('CSV preserves filing-level lineage and three issuer-year rows',()=>{
 const data={as_of:'2026-10-25',companies:[issuer('MSFT')]};
 const csv=S.snapshotCsv(data);
 assert.equal(csv.trim().split('\r\n').length,4);
 for(const field of ['revenue_usd_tag','revenue_usd_filed','revenue_usd_accession','source_url']){
  if(field==='source_url')continue;
  assert.ok(csv.includes(field));
 }
 assert.ok(csv.includes('2026-01-20'));
 assert.ok(csv.includes('123-456'));
});
test('CSV blocks formula injection in source strings, not authentic numeric negatives',()=>{
 const bad=issuer('B',{fcf:-5}); bad.name='=HYPERLINK("https://bad.invalid", "Click")';
 const csv=S.snapshotCsv({as_of:'2026-10-25',companies:[bad]});
 assert.ok(csv.includes("' =")===false);
 assert.ok(csv.includes("'=HYPERLINK"));
 assert.ok(csv.includes('""https://bad.invalid""'));
 assert.match(csv,/,-5,/);
});
test('missing snapshot yields no fabricated comparison and cannot export',()=>{
 assert.deepEqual(S.ranking(null,'revenue'),[]);
 assert.throws(()=>S.snapshotCsv(null));
});
