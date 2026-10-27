'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const Ideas=require('../site/private_ideas_v70.js');
const prices=(n, growth=0.001,shock=0)=>Array.from({length:n},(_,i)=>100*Math.pow(1+growth,i)*(i>100?1+shock:1));
test('price-only research requires substantial valid history',()=>{
 assert.throws(()=>Ideas.researchMetrics(prices(15)),/126/);
 assert.throws(()=>Ideas.researchMetrics(prices(180).map((x,i)=>i===18?NaN:x)),/valid/);
 assert.throws(()=>Ideas.researchMetrics(prices(180).map((x,i)=>i===18?-1:x)),/valid/);
});
test('historical metrics are finite and do not silently add dividends',()=>{
 const m=Ideas.researchMetrics(prices(260,0.001));
 for(const field of ['quarterReturn','periodReturn','annualVol','maxDrawdown','var95'])assert.ok(Number.isFinite(m[field]));
 assert.equal(m.priceOnly,true);
 assert.ok(m.periodReturn>m.quarterReturn);
});
test('different research lenses transparently change priorities',()=>{
 const low=Ideas.analyze('LOW',prices(260,.00015),'defensive');
 const high=Ideas.analyze('HIGH',prices(260,.002),'growth');
 assert.ok(low.score>=0 && low.score<=100 && high.score>=0 && high.score<=100);
 const rows=[{symbol:'LOW',prices:prices(260,.00015)},{symbol:'HIGH',prices:prices(260,.002)}];
 assert.equal(Ideas.rank(rows).length,2);
 assert.notEqual(Ideas.researchScore(Ideas.researchMetrics(prices(260,.002)),'defensive'),Ideas.researchScore(Ideas.researchMetrics(prices(260,.002)),'growth'));
});
test('higher volatility and deep drawdowns reduce risk-aware scoring',()=>{
 const flat=Ideas.researchMetrics(prices(260,.0001));
 const risky=Ideas.researchMetrics(prices(260,.0001,-.55));
 assert.ok(Ideas.researchScore(flat,'defensive')>Ideas.researchScore(risky,'defensive'));
});
test('SEC missing fundamentals are unavailable rather than zero',()=>{
 assert.equal(Ideas.fundamentals({annual:[]}),null);
 const c={annual:[{fiscal_end:'2026-01-01',metrics:{revenue_usd:150,free_cash_flow_usd:null}},
 {fiscal_end:'2025-01-01',metrics:{revenue_usd:100}}]};
 const v=Ideas.fundamentals(c);
 assert.ok(Math.abs(v.revenueGrowth-.5)<1e-8);
 assert.equal(v.fcfMargin,null);
});
test('reported SEC fundamentals never become invented market price targets',()=>{
 const c={source:'SEC EDGAR',as_of:'2026-10-26',annual:[
 {fiscal_end:'2026-06-30',metrics:{revenue_usd:150,free_cash_flow_usd:-15}},
 {fiscal_end:'2025-06-30',metrics:{revenue_usd:100,free_cash_flow_usd:10}}]};
 const view=Ideas.fundamentals(c);
 assert.equal(view.fcfMargin,-.1);
 assert.equal(view.revenueGrowth,.5);
 assert.equal(Object.hasOwn(view,'priceTarget'),false);
});
