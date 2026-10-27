'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const A=require('../site/private_allocation_v74.js');
const now='2026-10-27T17:00:00Z';
const q=p=>({price:p,timestamp:'2026-10-27T16:00:00Z',venue:'IEX'});
function plan(holdings,cash,symbol,budget,quotes){return A.scenario({holdings,cash,symbol,budget,quotes,nowISO:now});}
function history(symbols){
 const dates=Array.from({length:200},(_,i)=>new Date(Date.UTC(2025,0,i+1)).toISOString().slice(0,10));
 return symbols.map((symbol,j)=>({symbol,dates,prices:dates.map((_,i)=>100+2*j+Math.sin(i/(3+j))*2+i*0.1)}));
}
test('all-cash baseline has undefined invested-only HHI, not artificial zero',()=>{
 const p=plan({},10000,'AMZN',350,{AMZN:q(100)});
 assert.equal(p.before.investmentHhi,null);
 assert.equal(p.after.investmentHhi,1);
 assert.equal(p.before.hhi,1);
 assert.ok(p.after.hhi<1);
 assert.equal(p.after.cashWeight,.965);
 assert.equal(p.after.largestInvestedWeight,1);
 assert.ok(p.warnings.some(s=>s.includes('zero-price-return cash')));
});
test('invested-only HHI is portfolio concentration among securities, not cash',()=>{
 const p=plan({AAPL:10},3000,'AMZN',1000,{AAPL:q(100),AMZN:q(100)});
 assert.equal(p.before.investmentHhi,1);
 assert.equal(p.after.investmentHhi,.5);
 assert.equal(p.after.largestInvestedWeight,.5);
 assert.equal(p.before.investedWeight,.25);
 assert.equal(p.after.investedWeight,.5);
});
test('all cash historical volatility is zero and stock purchase can raise it even as cash HHI falls',()=>{
 const p=plan({},10000,'AMZN',350,{AMZN:q(100)});
 const r=A.matchedRisk(p,history(['AMZN']));
 assert.equal(r.available,true);
 assert.equal(r.annualizedVolBefore,0);
 assert.ok(r.annualizedVolAfter>0);
 assert.ok(p.after.hhi<p.before.hhi);
 const exportData=A.exportResearch(p,r,{source:'Alpaca stock market history',period:'365'});
 assert.equal(exportData.hypotheticalAllocationChange.preInvestedOnlyHhi,null);
 assert.equal(exportData.hypotheticalAllocationChange.postInvestedOnlyHhi,1);
 assert.match(exportData.historicalVolatilityInterpretation,/increased/);
 assert.match(exportData.hypotheticalAllocationChange.concentrationInterpretation,/not equity risk/);
});
test('crypto and mixed-calendar comparison is withheld instead of applying stock annualization',()=>{
 const p=plan({},10000,'BTC/USD',200,{ 'BTC/USD':q(100) });
 const r=A.matchedRisk(p,history(['BTC/USD']));
 assert.equal(r.available,false);
 assert.match(r.reason,/mixed-calendar/);
});
test('research export still omits cash dollars, share inventory, and budget',()=>{
 const p=plan({AAPL:2},3000,'AMZN',250,{AAPL:q(200),AMZN:q(100)});
 const r=A.matchedRisk(p,history(['AAPL','AMZN']));
 const e=A.exportResearch(p,r,{source:'Alpaca IEX',period:'365'});
 const json=JSON.stringify(e);
 for(const word of ['cashBefore','cashAfter','proposedBudget','unitsBought','holdings','positions','totalAfter','observedPrice']){
  assert.ok(!json.includes('"'+word+'"'),word+' must not be exported');
 }
 assert.ok(Math.abs(e.hypotheticalAllocationChange.postInvestedOnlyHhi - ((400/650)**2 + (250/650)**2)) < 1e-9);
});
