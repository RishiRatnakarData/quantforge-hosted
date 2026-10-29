'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const I=require('../site/private_investment_intelligence_v94.js');
const date=i=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10);
function sample(){
 const selection=['ABC','DEF','FUND'];
 const prices=Array.from({length:150},(_,i)=>Math.exp(i*.0007+.018*Math.sin(i/8)));
 const history={symbols:[...selection],dates:Array.from({length:150},(_,i)=>date(i)),closes:{
  ABC:prices,DEF:prices.map((x,i)=>x*Math.exp(.01*Math.sin(i/13))),FUND:prices.map((x,i)=>x*Math.exp(.02*Math.cos(i/19)))} };
 const snapshot={as_of:'2026-10-25',companies:[
  {symbol:'ABC',name:'Alpha',source_url:'https://data.sec.gov/abc',annual:[
   {fiscal_end:'2025-12-31',metrics:{revenue_usd:110,operating_income_usd:22,free_cash_flow_usd:-11}},
   {fiscal_end:'2024-12-31',metrics:{revenue_usd:100}}]},
  {symbol:'DEF',name:'Delta',source_url:'https://data.sec.gov/def',annual:[
   {fiscal_end:'2025-09-30',metrics:{revenue_usd:200,operating_income_usd:40}},
   {fiscal_end:'2024-09-30',metrics:{revenue_usd:180}}]}]};
 const brief={schema:'quantforge.research-brief.v9.3',symbol:'ABC',action:'Research further',universe:selection.map(symbol=>({symbol}))};
 const variants=['conservative','balanced','growth'].map(r=>({symbol:'ABC',decision:r==='growth'?'Hold':'Research further',readiness:'Conditional / caution'}));
 return {selection,history,snapshot,brief,variants,asOf:'2026-10-29'};
}
test('SEC annual comparatives retain missingness and negative free cash flow',()=>{
 const x=I.build(sample());assert.equal(x.schema,'quantforge.investment-intelligence.v9.4');
 assert.equal(x.coverage.issuersWithMetrics,2);assert.equal(x.sec.rows[0].yearlyGrowthPercent,10);
 assert.equal(x.sec.rows[0].operatingMarginPercent,20);assert.equal(x.sec.rows[0].freeCashFlowMarginPercent,-10);
 assert.equal(x.sec.rows[1].freeCashFlowMarginPercent,null);
 assert.equal(x.sec.rows[2].status,'unavailable');assert.equal(x.sec.rows[2].revenueUsd,null);
 assert.equal(x.sec.mismatchedFiscalYears,false);
});
test('outdated, future or malformed SEC snapshots never silently produce metrics',()=>{
 const x=sample();x.snapshot.as_of='2026-12-31';assert.equal(I.build(x).sec.available,0);
 x.snapshot.as_of='2020-01-01';assert.equal(I.build(x).sec.available,0);
 x.snapshot.as_of='2026-10-25';x.snapshot.companies[0].annual[0].fiscal_end='2025-02-31';
 assert.equal(I.build(x).sec.rows[0].status,'unavailable');
});
test('SEC no implied industry, market cap, price target or invented yield',()=>{
 const x=I.build(sample());const row=x.sec.rows[0];assert.equal('expectedReturn' in row,false);
 assert.equal('priceTarget' in row,false);assert.equal('marketCap' in row,false);
});
test('historical correlation comes from exact matched return vectors, not holdings',()=>{
 const x=I.build(sample());assert.equal(x.comovement.ready,true);
 assert.equal(x.comovement.rows.length,3);assert.ok(x.comovement.averagePairCorrelation<=1);
 assert.ok(x.comovement.rows.every(r=>r.averagePeerCorrelation>=-1&&r.averagePeerCorrelation<=1));
 assert.equal(Object.hasOwn(x,'cash'),false);
});
test('disordered, mismatched, constant and corrupted market histories fail closed',()=>{
 for(const edit of [
  s=>s.history.dates[10]=s.history.dates[9],
  s=>s.history.symbols[1]='WRONG',
  s=>s.history.closes.DEF[5]=null,
  s=>s.history.closes.DEF=s.history.closes.DEF.map(()=>1)
 ]){const x=sample();edit(x);assert.equal(I.build(x).comovement.ready,false);}
});
test('scenario sensitivity retains baseline action, reports changed rules, not a forecast',()=>{
 const x=I.build(sample());assert.equal(x.policies.sameAction,false);
 assert.equal(x.policies.baselineAction,'Research further');assert.equal(x.policies.rows[2].action,'Hold');
 assert.equal(x.policies.rows.length,3);
});
test('incompatible variants and universe reject output rather than fabricating evidence',()=>{
 const x=sample();x.variants[0].symbol='BAD';assert.throws(()=>I.build(x));
 const y=sample();y.brief.universe[0].symbol='WRONG';assert.throws(()=>I.build(y));
});
test('no accounts, price vectors, provider tokens or order capabilities in exported intelligence',()=>{
 const x=sample();x.brief.holdings={ABC:10000};x.brief.cash=900000;x.snapshot.token='SECRETPRIVATE';
 const json=JSON.stringify(I.build(x));for(const secret of ['900000','10000','SECRETPRIVATE','"holdings":','"closes":','"account":','password','orderId'])
  assert.equal(json.includes(secret),false,secret);
 const source=fs.readFileSync(path.join(__dirname,'../site/private_investment_intelligence_v94.js'),'utf8');
 for(const forbidden of ['fetch(', 'XMLHttpRequest','localStorage','sessionStorage',"api('private/trade'",'alpaca.markets','openai.com'])
  assert.equal(source.includes(forbidden),false,forbidden);
});
