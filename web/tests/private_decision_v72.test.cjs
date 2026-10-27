'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
require('../site/private_ideas_v70.js');
const D=require('../site/private_decision_v72.js');
const dates=n=>Array.from({length:n},(_,i)=>new Date(Date.UTC(2023,0,1+i)).toISOString().slice(0,10));
const prices=(n,k=0)=>Array.from({length:n},(_,i)=>100*Math.exp(.001*i + .03*Math.sin(i*.21+k)));
const inputs=(n=260)=>['AAA','BBB','CCC'].map((symbol,i)=>({symbol,prices:prices(n,i*.5),dates:dates(n),annual:252}));

test('returns and Pearson correlation are finite on real-style noisy histories',()=>{
 const p=prices(260),r=D.dailyReturns(p);
 assert.equal(r.length,259);
 assert.ok(Math.abs(D.correlation(r,r)-1)<1e-12);
 assert.ok(D.correlation(r,r.map(x=>-x))<-.999999);
});
test('constant returns do not silently receive a fabricated correlation',()=>{
 assert.equal(D.correlation([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],Array(30).fill(1)),null);
});
test('one misaligned date blocks an otherwise plausible correlation',()=>{
 const data=inputs();data[1].dates[5]='2023-02-20';
 assert.ok(!D.sameSessions(data[0],data[1]));
 const result=D.correlations(data);
 assert.equal(result.notAligned,2);
 assert.equal(result.pairs.length,1);
});
test('matched-session pair accounting reports all three investment pairs',()=>{
 const result=D.correlations(inputs());
 assert.equal(result.notAligned,0);
 assert.equal(result.pairs.length,3);
 assert.ok(result.pairs.every(p=>p.sessions===259&&Number.isFinite(p.value)));
});
test('decision brief reflects multiple research perspectives and includes explicit limits',()=>{
 const brief=D.build(inputs(),'growth');
 assert.equal(brief.selected.length,3);
 assert.equal(brief.top.length,3);
 assert.equal(brief.comparisons.length,3);
 assert.ok(brief.comparisons.every(p=>p.score>=0&&p.score<=100&&p.rankSpread>=0));
 assert.ok(brief.warnings.join(' ').includes('do not estimate expected returns'));
});
test('portfolio overlap only uses complete observed quotes; missing prices suppress percent',()=>{
 const b=D.build(inputs(),'balanced',{}, {AAA:2, BBB:3},{AAA:{price:100}},400);
 assert.equal(b.portfolio.complete,false);
 assert.ok(b.comparisons.find(x=>x.symbol==='AAA').held);
 assert.equal(b.comparisons.find(x=>x.symbol==='AAA').concentration,null);
 const good=D.build(inputs(),'balanced',{}, {AAA:2}, {AAA:{price:100}},200);
 assert.equal(good.portfolio.complete,true);
 assert.ok(Math.abs(good.comparisons.find(x=>x.symbol==='AAA').concentration-.5)<1e-12);
});
test('negative reported cash flow creates a model-risk caution rather than target price',()=>{
 const brief=D.build(inputs(),'balanced',{AAA:{fcfMargin:-.1,revenueGrowth:.2,fiscalEnd:'2026-06-30'}});
 const a=brief.comparisons.find(x=>x.symbol==='AAA');
 assert.ok(a.cautions.includes('Negative reported FCF proxy margin'));
 assert.ok(!Object.hasOwn(a,'targetPrice'));
});
test('reports exclude virtual positions, raw price vectors and identity details',()=>{
 const brief=D.build(inputs(),'balanced',{}, {AAA:200}, {AAA:{price:70}},100);
 const report=D.report(brief,'Alpaca stocks IEX-only','730');
 assert.equal(report.schema,'quantforge.decision-brief.v1');
 const j=JSON.stringify(report);
 for(const field of ['holdings','cash','email','token','dates','prices','priceVector','concentration']){
  assert.ok(!Object.hasOwn(report,field),field);
  assert.ok(!report.results.some(x=>Object.hasOwn(x,field)),field);
 }
 assert.ok(!j.includes('14000')); // Account-specific numerical amount must never leak.
 assert.equal(report.source,'Alpaca stocks IEX-only');
 assert.ok(report.results.length===3);
});
test('rejects duplicate candidates and malformed histories instead of inventing metrics',()=>{
 const rows=inputs();rows[1].symbol='AAA';
 assert.throws(()=>D.build(rows),/Duplicate/);
 assert.throws(()=>D.build(inputs(),'insane'),/Unknown/);
 assert.throws(()=>D.build([inputs()[0]]),/2–10/);
 assert.throws(()=>D.dailyReturns([50,-1]),/Invalid/);
});
