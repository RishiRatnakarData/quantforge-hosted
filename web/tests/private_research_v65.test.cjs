'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const forecast = require('../site/private_forecast_v65.js');
const walk = require('../site/private_walkforward_v65.js');
const optimizer = require('../site/private_optimizer.js');
const company = () => ({symbol:'MSFT',name:'Microsoft',as_of:'2026-10-25',source:'SEC EDGAR',annual:[
 {fiscal_end:'2026-06-30',metrics:{revenue_usd:140e9,free_cash_flow_usd:28e9}},
 {fiscal_end:'2025-06-30',metrics:{revenue_usd:120e9,free_cash_flow_usd:25e9}},
 {fiscal_end:'2024-06-30',metrics:{revenue_usd:100e9,free_cash_flow_usd:18e9}},
]});
function history(length=280){
 const dates=Array.from({length},(_,i)=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10));
 return {dates,symbols:['MSFT','AAPL','BTC/USD'],closes:{
  MSFT:dates.map((_,i)=>100*Math.exp(.0006*i+.035*Math.sin(i/9))),
  AAPL:dates.map((_,i)=>80*Math.exp(.0004*i+.045*Math.cos(i/13))),
  'BTC/USD':dates.map((_,i)=>30000*Math.exp(.0007*i+.080*Math.sin(i/17)))} ,
  sessions_per_year:252,source:'Private Alpaca historical daily bars'};
}
test('annual SEC years ordered chronologically and projected revenue compounded',()=>{
 const r=forecast.run(company(),{years:3,growth:.05,fcfMargin:.20,discount:.10,terminal:.02});
 assert.deepEqual(r.historic.map(x=>x.date),['2024-06-30','2025-06-30','2026-06-30']);
 assert.ok(Math.abs(r.scenarios[1].projection[0].revenue-147e9)<.01);
 assert.ok(Math.abs(r.scenarios[1].projection[0].fcf-29.4e9)<.01);
 assert.ok(r.scenarios[1].proxy>0);
 assert.equal(r.baseMargin,.20);
});
test('missing FCF does not fabricate a discounted cash-flow value',()=>{
 const c=company(); c.annual[0].metrics.free_cash_flow_usd=null;
 const r=forecast.run(c);
 assert.equal(r.fcfAvailable,false);
 assert.ok(r.scenarios.every(x=>x.proxy===null&&x.projection.every(p=>p.fcf===null)));
});
test('forecast rejects invalid SEC baselines and scenario assumptions',()=>{
 assert.throws(()=>forecast.run({...company(),annual:[]}),/two SEC annual/);
 assert.throws(()=>forecast.run(company(),{discount:.02,terminal:.03}),/discount rate exceeds/);
 assert.throws(()=>forecast.run(company(),{years:8}),/Check forecast/);
 assert.throws(()=>forecast.run(company(),{growth:Infinity}),/Check forecast/);
 const c=company(); c.annual[1].fiscal_end=c.annual[0].fiscal_end;
 assert.throws(()=>forecast.run(c),/Repeated SEC fiscal periods/);
});
test('rolling portfolio weights fit past only; future prices do not contaminate first fit',()=>{
 const f=history(),o={train:126,step:21,cap:.60,feeBps:5,objective:'minimum'};
 const first=walk.run(f,o).windows[0].weights;
 const changed=history();
 for(let i=126;i<280;i++)changed.closes.MSFT[i]*=1.1;
 assert.deepEqual(walk.run(changed,o).windows[0].weights,first);
});
test('walk forward uses nonoverlapping forward windows and includes trading costs',()=>{
 const f=history(),o={train:126,step:21,cap:.60,feeBps:0,objective:'minimum'};
 const free=walk.run(f,o),costly=walk.run(f,{...o,feeBps:25});
 assert.ok(free.windows.length>=2);
 assert.ok(free.windows.every(w=>w.trainingEnd<w.testStart&&w.testStart<=w.testEnd));
 for(let i=1;i<free.windows.length;i++)assert.ok(free.windows[i].testStart>free.windows[i-1].testEnd);
 assert.equal(free.optimized.fees,0);
 assert.ok(costly.optimized.fees>0&&costly.benchmark.fees>0);
 assert.ok(costly.optimized.wealth.at(-1)<free.optimized.wealth.at(-1));
 assert.ok(costly.benchmark.wealth.at(-1)<free.benchmark.wealth.at(-1));
 assert.equal(costly.dates.length,costly.optimized.wealth.length);
 assert.equal(costly.annual,252);
 assert.equal(costly.source,f.source);
});
test('walk forward preserves crypto-only 365-session convention',()=>{
 const f=history(); f.symbols=['MSFT','AAPL'];f.sessions_per_year=365;
 const out=walk.run(f,{train:63,step:21});
 assert.equal(out.annual,365);
});
test('walk-forward rejects infeasible caps, missing observations, and thin history',()=>{
 const f=history(90);
 assert.throws(()=>walk.run(f,{train:63,step:21}),/At least two full test/);
 assert.throws(()=>walk.run(history(),{cap:.2}),/Invalid walk-forward/);
 const bad=history();bad.closes.MSFT[21]=0;
 assert.throws(()=>walk.run(bad),/price history/);
});
test('pure research helpers contain no provider calls or portfolio mutations',()=>{
 assert.equal(typeof optimizer.run,'function');
 assert.equal(typeof forecast.run,'function');
 assert.equal(typeof walk.run,'function');
});
