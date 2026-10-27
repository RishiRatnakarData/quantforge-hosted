'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const L=require('../site/public_lab_v77.js');
const almost=(a,b,tolerance=1e-8)=>Math.abs(a-b)<tolerance;
const observations=L.synthetic();
function fixture(){
 return {as_of:'2026-10-01',companies:[{symbol:'MSFT',name:'Microsoft',source_url:'https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json',annual:[
  {fiscal_end:'2025-06-30',metrics:{revenue_usd:120e9,operating_income_usd:36e9}},
  {fiscal_end:'2024-06-30',metrics:{revenue_usd:100e9,operating_income_usd:28e9}},
  {fiscal_end:'2023-06-30',metrics:{revenue_usd:90e9,operating_income_usd:24e9}}
 ]}]};
}
test('synthetic input is seeded, reproducible, finite and independent of globals',()=>{
 assert.deepEqual(observations,L.synthetic());assert.notDeepEqual(observations,L.synthetic(360,7708));
 assert.equal(observations.length,360);assert.ok(observations.every(r=>r.length===5&&r.every(Number.isFinite)));
});
test('covariance is symmetric with nonnegative diagonals',()=>{
 const c=L.covariance(observations.slice(0,120));
 for(let i=0;i<5;i++){assert.ok(c[i][i]>0);for(let j=0;j<5;j++)assert.ok(almost(c[i][j],c[j][i]));}
});
test('simplex projection obeys caps and sum',()=>{
 for(const cap of [.2,.25,.35,.55,1]){
  const w=L.project([2,-3,5,0,4],cap);
  assert.ok(almost(w.reduce((a,b)=>a+b,0),1));assert.ok(w.every(x=>x>=-1e-10&&x<=cap+1e-10));
 }
 assert.throws(()=>L.project([1,2,3,4,5],.19),/infeasible/);
});
test('optimized solution is feasible, reduces fitted variance and uses covariance',()=>{
 for(const cap of [.2,.25,.45,.55,1]){
  const {optimal,equal,cov,volOptimal,volEqual}=L.modeledRisk(observations.slice(0,120),cap);
  assert.ok(almost(optimal.reduce((a,b)=>a+b,0),1));
  assert.ok(optimal.every(x=>x>=-1e-9&&x<=cap+1e-9));
  assert.ok(volOptimal<=volEqual+1e-8);assert.ok(L.variance(optimal,cov)<=L.variance(equal,cov)+1e-12);
 }
});
test('walk-forward windows are chronologically disjoint and start in the past',()=>{
 const out=L.walkforward(observations,{train:120,test:20,cap:.55,feeBps:10});
 assert.equal(out.paths.optimized.length,241);assert.equal(out.paths.equal.length,241);
 assert.ok(almost(out.paths.optimized[0],1));assert.ok(almost(out.paths.equal[0],1));
 assert.equal(out.windows.length,12);
 for(let i=0;i<out.windows.length;i++){
  const w=out.windows[i];assert.ok(w.trainEnd<w.testStart);
  assert.equal(w.testStart,w.trainEnd+1);
  if(i>0)assert.equal(out.windows[i-1].testEnd+1,w.testStart);
 }
 assert.ok(out.paths.optimized.every(x=>Number.isFinite(x)&&x>0));
});
test('first evaluation window cannot depend on later observations',()=>{
 const changed=observations.map(row=>row.slice());
 for(let i=141;i<changed.length;i++)changed[i]=[.1,.2,-.1,.3,-.05];
 const original=L.walkforward(observations,{train:120,feeBps:10});
 const adjusted=L.walkforward(changed,{train:120,feeBps:10});
 assert.deepEqual(original.paths.optimized.slice(0,21),adjusted.paths.optimized.slice(0,21));
 assert.deepEqual(original.paths.equal.slice(0,21),adjusted.paths.equal.slice(0,21));
});
test('transaction costs lower model wealth with same return paths',()=>{
 const free=L.walkforward(observations,{feeBps:0});
 const priced=L.walkforward(observations,{feeBps:50});
 assert.ok(priced.paths.optimized.at(-1)<free.paths.optimized.at(-1));
 assert.ok(priced.paths.equal.at(-1)<free.paths.equal.at(-1));
});
test('reported SEC data gives correct historical growth and margin',()=>{
 const rows=L.trend(L.secSeries(fixture(),'MSFT'));
 assert.deepEqual(rows.map(x=>x.end),['2023-06-30','2024-06-30','2025-06-30']);
 assert.ok(almost(rows.at(-1).growth,.2));assert.ok(almost(rows.at(-1).margin,.30));
 const html=L.renderSec(fixture(),'MSFT');
 assert.match(html,/20\.0%/);assert.match(html,/30\.0%/);
 assert.match(html,/120\.00B/);assert.match(html,/SEC Company Facts/);
});
test('missing SEC values are not replaced, untrusted content is escaped',()=>{
 const snapshot=fixture();snapshot.companies[0].name='<script>alert(1)</script>';
 snapshot.companies[0].annual[0].metrics.operating_income_usd=null;
 const html=L.renderSec(snapshot,'MSFT');
 assert.ok(!html.includes('<script>'));assert.match(html,/Operating margin is unavailable/);
 assert.match(L.renderSec(null,'MSFT'),/No observations have been invented/);
});
test('model exhibits are computed and communicate simulation status',()=>{
 const portfolio=L.renderOptimize(observations,.55),evalHtml=L.renderWalk(observations,.55,10,120);
 assert.match(portfolio,/synthetic training returns/);
 assert.match(evalHtml,/neither curve represents actual historical trading/);
 assert.match(evalHtml,/train sessions/i);
});
