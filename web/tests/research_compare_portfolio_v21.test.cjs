'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const Q=require('../site/research_core_v20.js');
const B=require('../site/research_compare_portfolio_v21.js');
const symbols=['MSFT','AAPL','NVDA'];
const sample=()=>B.align(Object.fromEntries(symbols.map(s=>[s,Q.syntheticPrice(s)])),symbols);
const results=()=>B.compare(sample());

test('3 company historical paths use exact common dates and start indexed to 100',()=>{
 const r=results();assert.equal(r.coverage.common_closes,520);assert.equal(r.dates.length,520);
 for(const s of symbols){assert.equal(r.indexed[s][0],100);assert.equal(r.returns[s].length,519);assert(Number.isFinite(r.metrics[s].daily_es95_loss));}
 assert.equal(r.convention.includes('252'),true);
});
test('2–5 companies are unique; malformed daily dates and negative prices fail closed',()=>{
 assert.throws(()=>B.requireUniverse(['MSFT','MSFT']),/distinct/);
 assert.throws(()=>B.requireUniverse(['A']),/2–5/);
 assert.throws(()=>B.align({MSFT:[{date:'2026-03-04',close:1}],AAPL:[{date:'2026-03-04',close:-2}]},['MSFT','AAPL']),/Malformed/);
 const a=Q.syntheticPrice('AAPL');assert.throws(()=>B.align({MSFT:a.slice(0,30),AAPL:a.slice(40,70)},['MSFT','AAPL']),/common/);
 const invalid=a.map(x=>({...x}));invalid[15].date='2026-02-30';
 assert.throws(()=>B.align({MSFT:invalid,AAPL:a},['MSFT','AAPL']),/Malformed/);
});
test('Private batch rejects nonMFA contract, wrong symbols, misaligned dates, and crypto annualization',()=>{
 const aligned=sample();const batch={licensed_private:true,symbols,dates:aligned.dates,closes:aligned.closes,sessions_per_year:252};
 assert.equal(B.fromBatch(batch,symbols).dates.length,520);
 assert.throws(()=>B.fromBatch({...batch,licensed_private:false},symbols),/Authenticated/);
 assert.throws(()=>B.fromBatch({...batch,symbols:['NVDA','MSFT','AAPL']},symbols),/mismatched/);
 assert.throws(()=>B.fromBatch({...batch,sessions_per_year:365},symbols),/US-equity/);
 assert.throws(()=>B.fromBatch({...batch,closes:{...aligned.closes,MSFT:[1,2]}},symbols),/Unaligned/);
});
test('Daily return and covariance matrix are symmetric and finite',()=>{
 const r=results();for(let i=0;i<3;i++)for(let j=0;j<3;j++){
  assert(Math.abs(r.covariance_matrix[i][j]-r.covariance_matrix[j][i])<1e-14);
  assert.equal(r.correlation_matrix[i][j],r.correlation_matrix[j][i]);
 }assert.equal(r.correlation_matrix[0][0],1);
});
test('Histogram preserves every observed return and uses a single shared bin scale',()=>{
 const r=results(),h=B.histogram(r);assert.equal(h.edges.length,10);
 for(const s of symbols)assert.equal(h.counts[s].reduce((a,b)=>a+b,0),519);
});
test('Cash only is explicit and its invested HHI stays undefined',()=>{
 const w={cash:1,MSFT:0,AAPL:0,NVDA:0},c=B.concentration(symbols,w);assert.equal(c.invested_hhi,null);
 const p=B.scenario(results(),w);assert.equal(p.summary.annual_volatility,0);assert.equal(p.summary.total_return,0);
 assert.throws(()=>B.minimumVariance(results(),w),/All cash/);
});
test('Sample full investment risk is not less than its all-cash counterpart',()=>{
 const r=results();const cash=B.scenario(r,{cash:1,MSFT:0,AAPL:0,NVDA:0});const invested=B.scenario(r,{cash:0,MSFT:1/3,AAPL:1/3,NVDA:1/3});
 assert(invested.summary.annual_volatility>cash.summary.annual_volatility);
});
test('Weights validate sum and cannot silently use zero-fill or negative exposures',()=>{
 assert.throws(()=>B.validWeights(symbols,{cash:.2,MSFT:.2,AAPL:.2,NVDA:.2}),/sum/);
 assert.throws(()=>B.validWeights(symbols,{cash:.2,MSFT:.5,AAPL:.5,NVDA:-.2}),/between/);
 const x=B.suggestedWeights(symbols);assert(Math.abs(Object.values(x).reduce((a,b)=>a+b,0)-1)<1e-12);
});
test('Historical portfolio path starts at 100 and is reproducible for fixed weights',()=>{
 const r=results(),w=B.suggestedWeights(symbols);const a=B.scenario(r,w),b=B.scenario(r,w);
 assert.deepEqual(a,b);assert.equal(a.indexed[0],100);assert.equal(a.indexed.length,r.dates.length);
 assert(Math.abs(a.ending_value-10000*(1+a.summary.total_return))<1e-6);
 assert(a.assumption.includes('No cash interest'));
});
test('Lower-risk fit preserves cash, nonnegative weights, company cap and never raises fitted volatility',()=>{
 const r=results(),before=B.suggestedWeights(symbols),opt=B.minimumVariance(r,before,.45);
 assert.equal(opt.weights.cash,0.2);
 assert(Math.abs(Object.values(opt.weights).reduce((a,b)=>a+b,0)-1)<1e-7);
 assert(symbols.every(s=>opt.weights[s]>=0&&opt.weights[s]<=0.4500001));
 assert.equal(opt.improved_in_sample,true);
 assert(opt.optimized.summary.annual_volatility<=opt.base.summary.annual_volatility+1e-7);
 assert(opt.limitation.includes('No untouched future holdout'));
});
test('Infeasible caps are rejected; projection keeps bounded sums',()=>{
 assert.throws(()=>B.projectCapped([1,2],1,.2),/Infeasible/);
 const p=B.projectCapped([0.8,0.1,0.1],1,.45);
 assert(Math.abs(p.reduce((a,b)=>a+b,0)-1)<1e-8);
 assert(p.every(x=>x>=0&&x<=.450000001));
});
test('Later history cannot change earlier aligned return results when truncated',()=>{
 const a=sample(),a1={symbols:a.symbols,dates:a.dates.slice(0,260),closes:Object.fromEntries(symbols.map(s=>[s,a.closes[s].slice(0,260)]))};
 const r=B.compare(a1),extended=B.compare(a);
 for(const s of symbols)assert.deepEqual(r.returns[s],extended.returns[s].slice(0,259));
});
test('Only model data and pure calculations; no broker, fetch, DOM, storage or personal portfolio state',()=>{
 const src=require('node:fs').readFileSync(require.resolve('../site/research_compare_portfolio_v21.js'),'utf8');
 for(const word of ['fetch(', 'localStorage','sessionStorage','document.', 'window.fetch', '/api/private/trade','apikey'])assert(!src.includes(word),word);
});
test('Owner virtual contributions do not masquerade as investment profits',()=>{
 const p={cash:400,initial_cash:1000,holdings:{MSFT:2,AAPL:1}},now='2026-11-09T21:00:00Z';
 const quotes=[{symbol:'MSFT',price:210,timestamp:'2026-11-09T20:59:00Z',synthetic:false},
  {symbol:'AAPL',price:230,timestamp:'2026-11-09T20:58:00Z',synthetic:false}];
 const r=B.ownerSnapshot(p,quotes,now);
 assert.equal(r.total_value,1050);assert.equal(r.net_contributions,1000);assert.equal(r.cumulative_paper_pnl,50);
 assert(r.note.includes('NOT time-weighted'));
 assert.throws(()=>B.ownerSnapshot(p,[quotes[0]],now),/every authenticated quote/);
 assert.throws(()=>B.ownerSnapshot(p,[quotes[0],{...quotes[1],synthetic:true}],now),/Unverified/);
 assert.throws(()=>B.ownerSnapshot(p,[quotes[0],{...quotes[1],timestamp:'2026-10-01T10:00:00Z'}],now),/stale/);
});
