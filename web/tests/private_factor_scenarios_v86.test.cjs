'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const F=require('../site/private_factor_scenarios_v86.js');
function fixture(n=260){
 const dates=Array.from({length:n},(_,i)=>new Date(Date.UTC(2025,0,i+1)).toISOString().slice(0,10));
 // Noncollinear, observed-price-style deterministic paths; NOT actual market observations.
 const market=Array.from({length:n},(_,i)=>i?(.0004+.008*Math.sin(i*.17)+.005*Math.cos(i*.37)):0);
 const small=Array.from({length:n},(_,i)=>i?(.0001+.006*Math.sin(i*.11+.7)-.003*Math.cos(i*.29)):0);
 const value=Array.from({length:n},(_,i)=>i?(-.0001+.007*Math.sin(i*.22-.4)+.004*Math.cos(i*.13)):0);
 const price=ret=>ret.reduce((a,x,i)=>{if(i)a.push(a.at(-1)*(1+x));return a;},[100]);
 const a=market.map((x,i)=>i?(1.20*x+.32*(small[i]-x)-.17*(value[i]-x)+.004*Math.sin(i*.43)):0);
 const closes={AAA:price(a),SPY:price(market),IWM:price(small),IVE:price(value)};
 return {symbol:'AAA',selection:['AAA','SPY','IWM','IVE'],history:{symbols:['AAA','SPY','IWM','IVE'],dates,closes,calendar:'equity_sessions',sessions_per_year:252},
  benchmark:'SPY',proxies:['IWM','IVE'],years:1,
  value:{symbol:'AAA',valid:true,price:100,priceTime:'2025-09-17T16:00:00Z',pSales:5}};
}
test('benchmark beta uses loaded independent ETF and correct shared return window',()=>{
 const r=F.assess(fixture());assert.equal(r.ready,true);assert.equal(r.market.ready,true);assert.equal(r.market.benchmark,'SPY');
 assert.equal(r.market.observations,259);assert.ok(Number.isFinite(r.market.singleBeta));assert.ok(r.market.singleR2>=0&&r.market.singleR2<=1);
});
test('multifactor proxy regression uses ETF-minus-market spreads, not mislabeled FF factors',()=>{
 const r=F.assess(fixture());assert.equal(r.market.multi.ready,true);
 assert.deepEqual(r.market.multi.predictorLabels,['Market ETF (SPY)','IWM minus SPY','IVE minus SPY']);
 assert.equal(r.market.multi.coefficients.length,3);assert.ok(r.market.multi.adjustedR2>0);
 assert.ok(r.limitations.some(x=>x.includes('not Fama')));
});
test('no market ETF loaded means unavailable, never peer basket silently called market',()=>{
 const x=fixture();x.benchmark='';const r=F.assess(x);
 assert.equal(r.ready,true);assert.equal(r.market.ready,false);assert.equal(r.risk.ready,true);assert.equal(r.valuation.ready,true);
});
test('non-broad ETF, candidate-as-benchmark and not-loaded benchmarks rejected',()=>{
 for(const benchmark of ['IWM','AAA','QQQ','VTI']){
  const r=F.assess({...fixture(),benchmark});assert.equal(r.market.ready,false,benchmark);
 }
});
test('duplicate, missing and non-proxy ETF choices reject whole factor result',()=>{
 for(const proxies of [['IWM','IWM'],['SPY'],['NONSENSE'],['IWM','IVE','QQQ']]){
  const r=F.assess({...fixture(),proxies});assert.equal(r.market.ready,false,proxies.join(','));
 }
});
test('collinear proxies do not produce massive or fabricated factor betas',()=>{
 const d=fixture();d.history.closes.IWM=[...d.history.closes.SPY];
 const r=F.assess(d);assert.equal(r.market.ready,true);assert.equal(r.market.multi.ready,false);
});
test('short history withholds factor beta but retains available downsides',()=>{
 const d=fixture(85);const r=F.assess(d);assert.equal(r.ready,true);
 assert.equal(r.market.ready,false);assert.equal(r.risk.ready,true);
});
test('drawdown durations and worst 20-session stress are sample-correct',()=>{
 const d=fixture();const prices=d.history.closes.AAA;
 prices[10]=70; // forces a historical decline in candidate alone
 const r=F.assess(d);assert.equal(r.risk.ready,true);assert.ok(r.risk.maxDrawdown<-.2);
 assert.ok(r.risk.longestUnderwaterSessions>=1);assert.ok(r.risk.worst20.change<0);
 assert.equal(r.risk.rollingPoints.length<=24,true);
});
test('valuation scenario is conditional on real observed price and P/S',()=>{
 const r=F.assess(fixture());assert.equal(r.valuation.ready,true);assert.equal(r.valuation.scenarios.length,9);
 const flat=r.valuation.scenarios.find(x=>x.growth===.05&&x.multipleRatio===1);
 assert.ok(Math.abs(flat.impliedPrice-105)<1e-8);assert.ok(Math.abs(flat.priceChange-.05)<1e-8);
});
test('three-year sensitivity compounds revenue growth rather than multiplying three times',()=>{
 const r=F.assess({...fixture(),years:3});const s=r.valuation.scenarios.find(x=>x.growth===.15&&x.multipleRatio===1.30);
 assert.ok(Math.abs(s.impliedPrice-100*1.15**3*1.3)<1e-8);
});
test('invalid, missing or stale-by-existing-bridge inputs withhold implied prices',()=>{
 for(const value of [null,{symbol:'AAA',valid:false,price:100,pSales:5},
  {symbol:'ZZZ',valid:true,price:100,pSales:5},
  {symbol:'AAA',valid:true,price:100,pSales:-2},
  {symbol:'AAA',valid:true,price:100,pSales:5,priceTime:'bad'}])
  assert.equal(F.assess({...fixture(),value}).valuation.ready,false);
});
test('calendar and data quality guard mixed crypto and non-finite closes',()=>{
 const d=fixture();d.history.calendar='mixed_crypto_equity';
 assert.equal(F.assess(d).market.ready,false);assert.equal(F.assess(d).risk.ready,false);
 d.history.closes.AAA[2]=NaN;assert.equal(F.assess(d).ready,false);
});
test('selection mismatch, unsorted dates, repeated symbols are rejected',()=>{
 const d=fixture();d.selection=['AAA','SPY','IWM','XYZ'];assert.equal(F.assess(d).ready,false);
 d.selection=['AAA','SPY','IWM','IVE'];d.history.dates[5]=d.history.dates[4];assert.equal(F.assess(d).ready,false);
 d.history.dates[5]='2025-01-06';d.history.symbols=['AAA','SPY','SPY','IVE'];assert.equal(F.assess(d).ready,false);
});
test('pure analysis does not mutate input or leak raw quotes, holdings, series',()=>{
 const d=fixture();const before=JSON.stringify(d);const r=F.assess(d);
 assert.equal(JSON.stringify(d),before);
 const json=JSON.stringify(r);
 for(const s of ['"holdings"','"cash"','"quotes"','"closes"','"prices"','"account"','"token"'])assert.ok(!json.includes(s),s);
});
test('no fetch, storage, order, authentication mutation, or hardcoded market prices',()=>{
 const source=fs.readFileSync(require.resolve('../site/private_factor_scenarios_v86.js'),'utf8');
 for(const x of [/\bfetch\s*\(/,/\blocalStorage\b/,/\bsessionStorage\b/,/\bXMLHttpRequest\b/,/private\/trade/,/\bWebSocket\b/,/\beval\s*\(/,/addEventListener/])assert.ok(!x.test(source),String(x));
});
