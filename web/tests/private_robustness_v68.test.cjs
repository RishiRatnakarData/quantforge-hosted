'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const walk = require('../site/private_walkforward_v65.js');
const robust = require('../site/private_robustness_v68.js');
const integrity = require('../site/private_integrity_v67.js');
function history(n=500) {
 const dates=Array.from({length:n},(_,i)=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10));
 return {dates,symbols:['AAPL','TSLA','AMZN'],closes:{
  AAPL:dates.map((_,i)=>100*Math.exp(.00050*i+.06*Math.sin(i/22))),
  TSLA:dates.map((_,i)=>145*Math.exp(.00030*i+.085*Math.cos(i/19))),
  AMZN:dates.map((_,i)=>110*Math.exp(.00047*i+.043*Math.cos(i/14)))},
  source:'Alpaca stocks IEX-only split-adjusted daily bars',sessions_per_year:252,as_of:'2026-10-26'};
}
const settings={train:126,step:21,objective:'minimum',cap:.60,feeBps:5,capital:10000};
function approx(a,b,tol=1e-7){assert.ok(Math.abs(a-b)<=tol,`${a} != ${b}`);}
test('Longer history supports more distinct evaluation windows',()=>{
 const one=walk.run(history(251),settings),two=walk.run(history(500),settings);
 assert.ok(one.windows.length>=2);assert.ok(two.windows.length>one.windows.length);
 const r=robust.analyze(history(500),two);
 assert.equal(r.windowCount,two.windows.length);assert.equal(r.evaluationSessions,two.dates.length-1);
});
test('All allocation sensitivity scenarios use the exact same evaluation dates and trading window count',()=>{
 const h=history(330),b=walk.run(h,settings),r=robust.analyze(h,b);
 assert.ok(r.strategyCases.length>=4);
 assert.equal(r.strategyCases[0].optimizedReturn,b.optimized.metrics.change);
 for(const row of r.strategyCases){
  assert.equal(row.windows,b.windows.length);
  assert.equal(row.train,settings.train);assert.equal(row.step,settings.step);
  assert.ok(Number.isFinite(row.optimizedReturn));assert.ok(Number.isFinite(row.activeDifferencePp));
 }
 assert.ok(r.strategyCases.some(x=>x.objective==='inverse'));
 assert.ok(r.strategyCases.some(x=>x.objective==='tilt'));
 assert.ok(r.strategyCases.some(x=>x.label==='Higher transaction fee'));
});
test('Passive benchmark deploys equal weights once, deducts one entry fee and never rebalances',()=>{
 const h=history(200),b=walk.run(h,settings),p=robust.passiveBenchmark(h,b),start=h.dates.indexOf(b.start);
 approx(p.fee,5);approx(p.wealth[0],10000);
 for(let i=1;i<b.dates.length;i++){
  const expected=9995*(h.symbols.reduce((s,sym)=>s+h.closes[sym][start+i]/h.closes[sym][start],0)/3);
  approx(p.wealth[i],expected);
 }
 approx(p.change,p.wealth.at(-1)/p.wealth[0]-1);
});
test('Leave-one-window-out study excludes one evaluated window and preserves the remaining actual wealth ratios',()=>{
 const h=history(250),b=walk.run(h,settings),rows=robust.leaveOneWindowOut(b);
 assert.equal(rows.length,b.windows.length);
 for(let k=0;k<rows.length;k++){
  let o=1,eq=1;
  b.windows.forEach((w,i)=>{if(i===k)return;
   const lo=b.dates.indexOf(w.trainingEnd),hi=b.dates.indexOf(w.testEnd);
   o*=b.optimized.wealth[hi]/b.optimized.wealth[lo];
   eq*=b.benchmark.wealth[hi]/b.benchmark.wealth[lo];
  });
  approx(rows[k].differencePp,(o-eq)*100);
 }
});
test('Research manifest fingerprint is preserved, reports exclude raw price and wealth vectors',()=>{
 const h=history(250),b=walk.run(h,settings),r=robust.analyze(h,b);
 const manifest=integrity.marketManifest(h,b,'365');
 const out=robust.report(r,manifest);
 assert.equal(out.manifest.data.fingerprint,manifest.data.fingerprint);
 assert.ok(integrity.verifyMarketFingerprint(h,out.manifest));
 assert.equal(out.passive.wealth,undefined);
 assert.ok(!JSON.stringify(out).includes(JSON.stringify(h.closes.AAPL)));
 assert.throws(()=>robust.report(r,{...manifest,data:{...manifest.data,symbols:['FAKE']}}),/mismatch/);
});
test('Reject stale, tampered, missing and non-contiguous data',()=>{
 const h=history(250),b=walk.run(h,settings);
 assert.throws(()=>robust.analyze({...h,symbols:['TSLA','AAPL','AMZN']},b),/Run Walk-forward/);
 assert.throws(()=>robust.analyze({...h,dates:[...h.dates].reverse()},b),/Aligned historical/);
 assert.throws(()=>robust.analyze({...h,closes:{...h.closes,AAPL:[...h.closes.AAPL.slice(0,-1),0]}},b),/Incomplete|invalid/);
 const altered={...h,closes:{...h.closes,AAPL:[...h.closes.AAPL]}}; altered.closes.AAPL[140] *= 1.05;
 assert.throws(()=>robust.analyze(altered,b),/Loaded market data changed/);
 assert.throws(()=>robust.analyze(h,{...b,dates:[...b.dates.slice(0,2),'2026-10-26',...b.dates.slice(3)]}),/Evaluation dates/);
 assert.throws(()=>robust.analyze(h,{...b,windows:[...b.windows.slice(0,1),{...b.windows[1],testStart:'2026-12-31'},...b.windows.slice(2)]}),/Non-contiguous/);
});
test('Pure robustness implementation contains no network or virtual state mutations',()=>{
 const fs=require('node:fs');const source=fs.readFileSync(require.resolve('../site/private_robustness_v68.js'),'utf8');
 for(const forbidden of ['fetch(', 'localStorage', 'sessionStorage', '/api/private/trade', '/private/capital', 'XMLHttpRequest']){
  assert.ok(!source.includes(forbidden),`Unexpected unsafe operation: ${forbidden}`);
 }
});
