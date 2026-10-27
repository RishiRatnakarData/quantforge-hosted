const test=require('node:test');
const assert=require('node:assert/strict');
const A=require('../site/private_allocation_v74.js');
const NOW='2026-10-27T12:00:00Z';
function quote(price){return {price,timestamp:'2026-10-27T11:00:00Z',venue:'IEX'};}
function sample(){return {holdings:{AAPL:5,MSFT:3},cash:3000,quotes:{AAPL:quote(200),MSFT:quote(300),AMZN:quote(100)},symbol:'AMZN',budget:1000,nowISO:NOW};}
test('virtual purchase conserves total equity and never mutates the input',()=>{
 const input=sample(),initial=JSON.stringify(input);const p=A.scenario(input);
 assert.equal(JSON.stringify(input),initial);
 assert.equal(p.totalBefore,4900);assert.equal(p.totalAfter,4900);assert.equal(p.cashAfter,2000);
 assert.equal(p.unitsBought,10);assert.equal(p.after.positions.find(x=>x.symbol==='AMZN').value,1000);
 assert.ok(Math.abs(p.after.positions.reduce((s,x)=>s+x.weight,0)+p.after.cashWeight-1)<1e-12);
});
test('proposed purchase cannot exceed cash or use bad quotes',()=>{
 const d=sample();d.budget=3001;assert.throws(()=>A.scenario(d),/exceeds/);
 d.budget=1000;d.quotes.MSFT=null;assert.throws(()=>A.scenario(d),/MSFT/);
 d.quotes.MSFT=quote(300);d.quotes.AMZN.timestamp='2026-10-01T11:00:00Z';assert.throws(()=>A.scenario(d),/AMZN/);
});
test('invalid zero, infinity, unsupported candidate and future observations rejected',()=>{
 for(const val of [0,Infinity,NaN,-5]){let d=sample();d.budget=val;assert.throws(()=>A.scenario(d));}
 const d=sample();d.symbol='"<script>';assert.throws(()=>A.scenario(d));
 const z=sample();z.quotes.MSFT.timestamp='2026-10-28T11:00:00Z';assert.throws(()=>A.scenario(z));
});
test('concentration HHI and allocation are well defined with all-cash virtual account',()=>{
 const p=A.scenario({holdings:{},cash:10000,quotes:{AAPL:quote(100)},symbol:'AAPL',budget:2000,nowISO:NOW});
 assert.equal(p.before.hhi,1);assert.ok(Math.abs(p.after.hhi-.68)<1e-10);
 assert.equal(p.after.cashWeight,.8);assert.equal(p.after.positions[0].weight,.2);
});
function rows(symbols,alter=false){
 let dates=Array.from({length:180},(_,i)=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10));
 return symbols.map((s,j)=>({symbol:s,dates:dates.map((d,i)=>alter&&j===1&&i===5?'2025-01-01':d),prices:dates.map((_,i)=>100*(1+.0006*i+.04*Math.sin(i/(8+j))))}));
}
test('aligned history supports actual before and after historical volatility comparisons',()=>{
 const p=A.scenario(sample());const risk=A.matchedRisk(p,rows(['AAPL','MSFT','AMZN']));
 assert.equal(risk.available,true);assert.equal(risk.sessions,179);
 assert.ok(Number.isFinite(risk.annualizedVolBefore));assert.ok(Number.isFinite(risk.annualizedVolAfter));
});
test('nonaligned or incomplete histories refuse risk estimates',()=>{
 const p=A.scenario(sample());
 assert.equal(A.matchedRisk(p,rows(['AAPL','MSFT'])).available,false);
 assert.equal(A.matchedRisk(p,rows(['AAPL','MSFT','AMZN'],true)).available,false);
});
test('research export excludes balances, position inventory, budget and licensed price vectors',()=>{
 const p=A.scenario(sample());const risk=A.matchedRisk(p,rows(['AAPL','MSFT','AMZN']));
 const report=A.exportResearch(p,risk,{source:'Alpaca IEX',period:'730'});
 assert.equal(report.type,'virtual-what-if');
 const text=JSON.stringify(report);
 for(const key of ['"holdings"','"cashBefore"','"cashAfter"','"proposedBudget"','"unitsBought"','"prices"'])assert.ok(!text.includes(key),key);
 assert.equal(report.risk.available,undefined);
 assert.ok(report.risk.historicalSessions===179);
});
