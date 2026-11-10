'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const C=require('../site/research_models_core_v22.js');
const ML=require('../site/private_predictive_ml_v180.js');
function prices(n=420,trend=0.0004){
 let i=0,date=new Date('2023-01-02T00:00:00Z'),close=100;const rows=[];
 while(rows.length<n){
  if(date.getUTCDay()!==0&&date.getUTCDay()!==6){
   close*=Math.exp(trend+0.007*Math.sin(i/7)+0.005*Math.sin(i*0.37));
   rows.push({date:date.toISOString().slice(0,10),close});i++;
  }
  date=new Date(date.getTime()+86400000);
 }
 return rows;
}
function cashFlow(amount){return {metrics:{free_cash_flow_usd:amount},source:{period:'2025-12-31'}};}
test('risk has correct historical loss units, visible periods, and deterministic block bootstrap',()=>{
 const p=prices(),r=C.risk(p),again=C.risk(p);
 assert.equal(r.ready,true);assert.equal(r.sessions,p.length);assert.equal(r.observations,p.length-1);
 assert.ok(r.annual_volatility>0);assert.ok(r.max_drawdown<=0);
 assert.ok(r.daily_var95_loss>=0&&r.daily_es95_loss>=r.daily_var95_loss-1e-12);
 assert.equal(r.bootstrap.replicates,300);assert.ok(r.bootstrap.block_length>=5);
 assert.deepEqual(r.bootstrap,again.bootstrap);assert.ok(r.bootstrap.low<=r.bootstrap.high);
 assert.equal(r.last,p.at(-1).date);assert.match(r.convention,/ONE session/);
});
test('risk fail closed on short or malformed market observations',()=>{
 assert.equal(C.risk(prices(50)).ready,false);
 assert.throws(()=>C.risk([{date:'2025-01-01',close:100},{date:'2025-01-01',close:101}]),/ascending/);
 assert.throws(()=>C.risk([{date:'2025-01-01',close:-1}]),/positive/);
 assert.throws(()=>C.risk([{date:'2025-01-01',close:0}]),/positive/);
 assert.equal(C.risk(prices(91)).bootstrap,null);
});
test('DCF proxy retains actual cash-flow basis and checks discount greater than terminal growth',()=>{
 const f=cashFlow(10e9),r=C.dcfProxy(f,{growth:0.05,discount:0.12,terminal:0.025});
 assert.equal(r.ready,true);assert.equal(r.cash_flows.length,5);
 assert.equal(r.base_fcf,10e9);assert.ok(r.proxy_pv>r.explicit_pv);assert.ok(r.terminal_share>0);
 assert.ok(C.dcfProxy(f,{growth:0.05,discount:0.15,terminal:0.025}).proxy_pv<r.proxy_pv);
 assert.match(r.limitation,/not FCFF/);
 assert.throws(()=>C.dcfProxy(f,{growth:0.03,discount:0.02,terminal:0.02}),/discount/);
 assert.throws(()=>C.dcfProxy(f,{growth:Infinity}),/invalid/);
 assert.equal(C.dcfProxy(cashFlow(-1e9)).ready,false);
 assert.equal(C.dcfProxy({metrics:{}}).ready,false);
 assert.equal(C.valuation(cashFlow(-1e9)).ready,false);
});
test('strategy chooses every daily position using strictly earlier history, not future closes',()=>{
 const original=prices(),baseline=C.strategy(original);assert.equal(baseline.ready,true);
 assert.equal(baseline.indexed.length,original.length-60);
 const changed=original.map(x=>({...x}));for(let i=350;i<changed.length;i++)changed[i].close*=1.65;
 const altered=C.strategy(changed);
 // The return on day 350 changes, but no decision or index value from a completed prior day changes.
 assert.deepEqual(altered.indexed.slice(0,350-60),baseline.indexed.slice(0,350-60));
 assert.deepEqual(altered.signals.slice(0,350-61),baseline.signals.slice(0,350-61));
 assert.equal(altered.evaluation.first,baseline.evaluation.first);
 assert.match(baseline.assumption,/No cash interest/);
});
test('strategy applies transaction costs and preserves passive benchmark convention',()=>{
 const p=prices(),noFee=C.strategy(p,0),withFee=C.strategy(p,0.001);
 assert.ok(withFee.indexed.at(-1)<=noFee.indexed.at(-1)+1e-10);
 assert.ok(withFee.passive.at(-1)<noFee.passive.at(-1));
 assert.equal(withFee.evaluation.sessions,withFee.dates.length-1-Math.floor((withFee.dates.length-1)*2/3));
 assert.ok(withFee.evaluation.first<withFee.evaluation.last);
 assert.equal(C.strategy(prices(100)).ready,false);
 assert.throws(()=>C.strategy(p,-0.1),/fee/);
});
test('logistic output includes truthful dated holdout calibration diagnostics and keeps conservative gate',()=>{
 const p=prices(520),sym='DEMO',input={symbols:[sym],dates:p.map(x=>x.date),closes:{[sym]:p.map(x=>x.close)},source:'Synthetic test price series'};
 const r=ML.analyze(input,sym);assert.equal(r.ready,true);
 assert.equal(r.calibration.length,3);
 assert.equal(r.calibration.reduce((sum,b)=>sum+b.count,0),r.testWindows);
 assert.ok(r.testPositiveRate>=0&&r.testPositiveRate<=1);
 assert.ok(r.validation.first<=r.validation.last);
 assert.match(r.validation.calibration_limit,/no post-hoc/);
 assert.equal(r.qualified,r.evaluatedBrier<r.baselineBrier-0.005&&r.evaluatedAccuracy>=r.baselineAccuracy&&r.testWindows>=12);
 if(!r.qualified)assert.equal(r.direction,'Not validated');
});
test('new pure research module has no provider, account, storage or order execution side effects',()=>{
 const s=fs.readFileSync(require.resolve('../site/research_models_core_v22.js'),'utf8');
 for(const blocked of ['fetch(', 'localStorage','sessionStorage','XMLHttpRequest','brokerage/order','placeOrder(','document.'])assert.ok(!s.includes(blocked),blocked);
});
