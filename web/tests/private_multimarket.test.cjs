'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const analysis = require('../site/private_multimarket.js');
const opt = require('../site/private_optimizer.js');
function fixture(annual=252){
 const dates=Array.from({length:60},(_,i)=>new Date(Date.UTC(2026,0,1+i)).toISOString().slice(0,10));
 return {symbols:['MSFT','BTC/USD'],dates,
  closes:{MSFT:dates.map((_,i)=>100*Math.pow(1.001,i)), 'BTC/USD':dates.map((_,i)=>30000*Math.pow(1.003,i))},
  asset_classes:{MSFT:'us_equity','BTC/USD':'crypto'},sessions_per_year:annual,
  calendar:'shared US stock sessions',source:'Alpaca private historical bars'};
}
test('mixed market report yields finite descriptive comparisons and three explicit stress scenarios',()=>{
 const out=analysis.analyze(fixture());
 assert.equal(out.annual,252);assert.equal(out.assets.length,2);
 assert.equal(out.observationCount,59);
 assert.deepEqual(out.stress.map(x=>x.name),['Broad simultaneous shock','Crypto-specific selloff','Equity-specific selloff']);
 assert.ok(Math.abs(out.stress[0].change+0.15)<1e-10);
 assert.ok(Math.abs(out.stress[1].change+0.175)<1e-10);
 assert.ok(out.assets.every(x=>Number.isFinite(x.annualVolatility)));
});
test('crypto only uses 365 observations per year in optimizer and diagnostics',()=>{
 const f=fixture(365);f.symbols=['BTC/USD','ETH/USD'];
 f.closes['ETH/USD']=f.closes.MSFT;delete f.closes.MSFT;
 f.asset_classes={ 'BTC/USD':'crypto','ETH/USD':'crypto'};
 const result=opt.run(f,{maxWeight:.6,objective:'minimum'});
 assert.equal(result.annualSessions,365);
 const report=analysis.analyze(f);assert.equal(report.annual,365);
 const instead=opt.run({...f,sessions_per_year:252},{maxWeight:.6,objective:'minimum'});
 assert.ok(result.equal.annualVolatility>instead.equal.annualVolatility);
});
test('optimizers reject invalid price data and stress analyzer never fabricates history',()=>{
 const f=fixture();f.closes['MSFT'][6]=0;
 assert.throws(()=>analysis.analyze(f),/Invalid aligned prices/);
 assert.throws(()=>opt.run(f),/invalid price history/);
});
test('scenario math keeps crypto-specific shocks away from equities',()=>{
 const f=fixture();
 const r=analysis.analyze(f);
 assert.equal(r.stress[1].equity,0);
 assert.equal(r.stress[2].crypto,0);
 assert.ok(r.observedWorstDay > -1);
});
