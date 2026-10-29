'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),C=require('../site/private_candidate_v85.js');
function fixture(n=260){
 const dates=Array.from({length:n},(_,i)=>new Date(Date.UTC(2025,0,i+1)).toISOString().slice(0,10));
 const A=dates.map((_,i)=>100*Math.exp(.0006*i+.018*Math.sin(i*.16)));
 const B=dates.map((_,i)=>85*Math.exp(.00035*i+.014*Math.sin(i*.16+.3)));
 const D=dates.map((_,i)=>130*Math.exp(.0003*i+.016*Math.sin(i*.16-.2)));
 return {symbol:'AAA',history:{symbols:['AAA','BBB','DDD'],dates,closes:{AAA:A,BBB:B,DDD:D},calendar:'equity_sessions'},
 selection:['AAA','BBB','DDD'],company:{symbol:'AAA',as_of:'2026-10-28',annual:[
  {fiscal_end:'2025-12-31',metrics:{revenue_usd:125,operating_income_usd:25,free_cash_flow_usd:15}},
  {fiscal_end:'2024-12-31',metrics:{revenue_usd:100,operating_income_usd:18,free_cash_flow_usd:-5}}]},
 value:{symbol:'AAA',priceTime:'2026-10-28T18:00:00Z',sharesTime:'2026-09-30',marketCap:1000,pSales:8,pFcf:66.666,fcfYield:.015,warnings:[]},
 portfolio:{cash:800,holdings:{AAA:2,BBB:1}},quotes:{AAA:{price:100,timestamp:'2026-10-28T18:00:00Z'},BBB:{price:100,timestamp:'2026-10-28T18:00:00Z'}},now:'2026-10-29T12:00:00Z'};
}
test('candidate dossier is computed from the aligned selected history',()=>{
 const f=fixture(),r=C.evaluate(f);
 assert.equal(r.ready,true);assert.equal(r.history.observations,259);assert.equal(r.history.peerCount,2);
 assert.ok(r.metrics.annualVolatility>0);assert.ok(r.metrics.dailyVaR95>=0);
 assert.ok(r.metrics.dailyES95>=r.metrics.dailyVaR95-1e-10);
 assert.ok(r.metrics.maxDrawdown<=0);
 assert.ok(Number.isFinite(r.metrics.peerBeta));assert.equal(r.metrics.annualization,252);
 assert.equal(r.graph.dates.length,121);assert.equal(r.graph.candidate.length,121);
 assert.ok(Math.abs(r.graph.candidate[0]-100)<1e-10);
 assert.ok(Math.abs(r.graph.peers[0]-100)<1e-10);
});
test('SEC growth and profitability use comparable years, not arbitrary quarters',()=>{
 const r=C.evaluate(fixture());
 assert.ok(Math.abs(r.fundamentals.revenueGrowth-.25)<1e-10);
 assert.ok(Math.abs(r.fundamentals.operatingMargin-.20)<1e-10);
 assert.ok(Math.abs(r.fundamentals.freeCashFlowMargin-.12)<1e-10);
 assert.equal(r.valuation.pSales,8);assert.equal(r.valuation.fcfYield,.015);
});
test('missed, stale or mismatched SEC and quote context produces unavailable ratios',()=>{
 const f=fixture();f.company.symbol='ZZZ';f.value.symbol='ZZZ';
 const r=C.evaluate(f);
 assert.equal(r.fundamentals.revenueGrowth,null);assert.equal(r.valuation.pFcf,null);
});
test('negative free cash flow remains negative, meaningless P/FCF omitted',()=>{
 const f=fixture();f.company.annual[0].metrics.free_cash_flow_usd=-8;
 f.value.pFcf=null;f.value.fcfYield=-.008;
 const r=C.evaluate(f);assert.equal(r.fundamentals.freeCashFlowMargin,-8/125);
 assert.equal(r.valuation.pFcf,null);assert.equal(r.valuation.fcfYield,-.008);
});
test('stale or missing investment selection blocks comparison even if history remains loaded',()=>{
 const f=fixture();f.selection=['AAA','BBB','ZZZ'];assert.equal(C.evaluate(f).ready,false);
 f.selection=['AAA','BBB','DDD'];f.history.dates[5]=f.history.dates[4];assert.equal(C.evaluate(f).ready,false);
});
test('portfolio downside represents isolated candidate shock; cash funding is conserved',()=>{
 const r=C.evaluate(fixture()),p=r.portfolioImpact;
 assert.ok(p);assert.ok(Math.abs(p.currentWeight-2/11)<1e-10);
 assert.ok(Math.abs(p.existingCandidateShock20+.2*2/11)<1e-10);
 assert.ok(Math.abs(p.additional5+.2*(2/11+.05))<1e-10);
 assert.ok(Math.abs(p.additional10+.2*(2/11+.10))<1e-10);
});
test('cannot invent purchase-impact scenarios with missing/stale quotes or insufficient cash',()=>{
 const f=fixture();f.quotes.BBB.timestamp='2026-10-05T00:00:00Z';
 assert.equal(C.evaluate(f).portfolioImpact,null);
 f.quotes.BBB.timestamp='2026-10-28T18:00:00Z';f.portfolio.cash=0;
 const p=C.evaluate(f).portfolioImpact;assert.equal(p.additional5,null);assert.equal(p.additional10,null);
});
test('all cash has zero current candidate exposure but a well-defined cash-funded scenario',()=>{
 const f=fixture();f.portfolio={cash:1000,holdings:{}};
 const p=C.evaluate(f).portfolioImpact;assert.equal(p.currentWeight,0);
 assert.equal(p.existingCandidateShock20,0);assert.ok(Math.abs(p.additional5+.01)<1e-12);
});
test('peer basket excludes candidate; constant peer returns suppress beta',()=>{
 const f=fixture();f.history.closes.BBB.fill(100);f.history.closes.DDD.fill(70);
 const r=C.evaluate(f);assert.equal(r.metrics.peerBeta,null);
 assert.ok(r.cautions.some(x=>x.includes('unavailable')));
});
test('crypto-only annualization supports 365 observations but peer beta is still not market beta',()=>{
 const f=fixture();f.history.calendar='crypto_24_7';f.history.sessions_per_year=365;
 const r=C.evaluate(f);assert.equal(r.metrics.annualization,365);
 assert.ok(r.limitations.some(x=>x.includes('NOT market beta')));
});
test('report never exports raw account amounts, holdings, quotes, cash or prices',()=>{
 const f=fixture(),original=JSON.stringify(f),r=C.evaluate(f);
 assert.equal(JSON.stringify(f),original);
 const report=JSON.stringify(r);
 for(const x of ['"portfolio"','"holdings"','"cash"','"quotes"','"closes"','"prices"','"token"','"account"'])
  assert.ok(!report.includes(x),x);
 assert.equal(C.export,undefined);
});
test('analysis contains no fetch, storage, order or account-mutating code',()=>{
 const source=fs.readFileSync(require.resolve('../site/private_candidate_v85.js'),'utf8');
 for(const regex of [/\bfetch\s*\(/,/\bXMLHttpRequest\b/,/\blocalStorage\b/,/\bsessionStorage\b/,/\bWebSocket\b/,/\beval\s*\(/,/private\/trade/,/\baddEventListener\b/])
  assert.ok(!regex.test(source),String(regex));
});
test('calendar date impossibilities and non-finite prices are not silently accepted',()=>{
 const f=fixture();f.history.dates[0]='2025-02-31';assert.equal(C.evaluate(f).ready,false);
 const g=fixture();g.history.closes.AAA[25]=Infinity;assert.equal(C.evaluate(g).ready,false);
});
