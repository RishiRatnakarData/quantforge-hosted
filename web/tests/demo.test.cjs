const test=require('node:test');
const assert=require('node:assert/strict');
require('../site/model.js');
const m=globalThis.QFModel;
test('demonstration inputs are explicitly fictional and bounded',()=>{
 assert.equal(m.bySymbol.MSFT.price,400);
 assert.equal(m.ASSETS.every(a=>a.price>0),true);
});
test('covariance symmetric, diagonals positive',()=>{
 const c=m.covariance(['MSFT','VOO','BND']);
 c.forEach((row,i)=>{assert.ok(row[i]>0);row.forEach((x,j)=>assert.ok(Math.abs(x-c[j][i])<1e-12));});
});
test('constrained weights obey limits, sum to one and reduce model variance',()=>{
 const o=m.optimize(['MSFT','VOO','BND'],0.6,0.15);
 assert.ok(Math.abs(o.weights.reduce((a,b)=>a+b,0)-1)<1e-6);
 assert.ok(o.weights.every(w=>w>=-1e-9&&w<=.6+1e-9));
 assert.ok(o.optimalVol<=o.baselineVol+1e-8);
});
test('crypto limits bind and max-weight infeasibility rejected',()=>{
 const o=m.optimize(['MSFT','VOO','BTC/USD'],.6,.15);
 assert.ok(o.weights[2]<=.150001);
 assert.throws(()=>m.optimize(['MSFT','VOO'],.4,.15),/Max weight/);
});
test('Monte Carlo seeded result stable and ES not below VaR',()=>{
 const o=m.optimize(['MSFT','VOO','BND']), a=m.monteCarlo(o.weights,o.cov,10000,42,1000);
 const b=m.monteCarlo(o.weights,o.cov,10000,42,1000);
 assert.deepEqual(a,b);assert.ok(a.es95>=a.var95);assert.ok(a.low<=a.median&&a.median<=a.high);
});
test('DCF terminal valuation sensitivities',()=>{
 const a=m.dcf('MSFT'),b=m.dcf('MSFT',{growth:.09}),c=m.dcf('MSFT',{wacc:.12});
 assert.ok(Number.isFinite(a.value)&&a.value>0);
 assert.ok(b.value>a.value);assert.ok(c.value<a.value);
 assert.throws(()=>m.dcf('MSFT',{terminal:.12,wacc:.1}),/WACC/);
});
test('ML excludes target and sorts nearest neighbors',()=>{
 const p=m.peers('MSFT');assert.equal(p.ranking.length,Object.keys(m.COMPANY_FACTS).length-1);
 assert.ok(p.ranking.every(x=>x.symbol!=='MSFT'));assert.ok(p.ranking[0].distance<=p.ranking[1].distance);
});
test('ETF overlap includes direct holdings and ETF constituent look-through',()=>{
 const e=m.exposure({MSFT:5,VOO:8});
 assert.equal(e.total,6240);assert.ok(Math.abs(e.lookthrough.find(x=>x.symbol==='MSFT').value-2254.4)<1e-8);
});
