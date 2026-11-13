'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const J=require('../site/research_guide_v30.js');
test('thesis serialization preserves beliefs and version ancestry without claiming observations',()=>{
 const text=J.encode({interest:'Understand cash generation',concerns:'Cyclicality',review:'2027-01-15'},{id:'case-1',revision:2,parent:'2026-11-12',period:'2026-06-30',snapshot:'2026-10-25'});
 const d=J.decode(text);assert.equal(d.revision,2);assert.equal(d.parent,'2026-11-12');assert.equal(d.concerns,'Cyclicality');assert.match(J.describe(d),/User-written beliefs/);assert.equal(J.decode('An original plain note'),null);assert.equal(J.decode('QFTHESIS1|broken'),null);
 assert.throws(()=>J.encode({interest:'x'.repeat(221)}));assert.throws(()=>J.encode({}));assert.throws(()=>J.encode({interest:'valid',review:'2026-02-31'}));
 const snap=J.decode(J.encode({interest:'Compare later'},{observed:{revenue_usd:100,operating_margin:.2,free_cash_flow_usd:-10}}));assert.equal(snap.observed.revenue_usd,100);assert.equal(snap.observed.free_cash_flow_usd,-10);
});
test('liquidity and leverage use same-filing facts, never null-as-zero or mixed accessions',()=>{
 const row={metrics:{current_assets_usd:150,current_liabilities_usd:100,assets_usd:300,liabilities_usd:120,long_term_debt_current_usd:10,long_term_debt_noncurrent_usd:40},sources:{}};
 for(const key of Object.keys(row.metrics))row.sources[key]={accession:'filing-A'};
 assert.deepEqual(J.health(row),{current_ratio:1.5,liabilities_to_assets:.4,long_term_debt_components:50});
 row.sources.current_assets_usd.accession='filing-B';assert.equal(J.health(row).current_ratio,null);
 row.metrics.long_term_debt_current_usd=null;assert.equal(J.health(row).long_term_debt_components,null);
 row.metrics.assets_usd=0;assert.equal(J.health(row).liabilities_to_assets,null);
 assert.equal(J.health(null).current_ratio,null);
});
test('concentration reconciles marked cash and positions and withholds incomplete quotes',()=>{
 const r=J.concentration({A:2,B:1},100,{A:100,B:200});assert.equal(r.total,500);assert.equal(r.cash_weight,.2);assert.ok(Math.abs(r.hhi-.36)<1e-12);assert.equal(r.positions,2);
 assert.equal(J.concentration({A:1},100,{}),null);assert.equal(J.concentration({},0,{}),null);
});


test('decision synthesis withholds simulated signals and preserves missing financials',()=>{
 const d=J.decisionSummary({financial:{metrics:{}},observed:false,prediction:{ready:true}});
 assert.equal(d.disposition,'Current evidence is incomplete');
 assert.equal(d.favorable.length,0);
 assert.match(d.model,/No validated/);
 assert.match(d.concerns.join(' '),/not zero/);
});
test('optional loss boundary frames historical evidence without a trading verdict',()=>{
 const d=J.decisionSummary({financial:{metrics:{revenue_growth:-.1,operating_margin:.2,free_cash_flow_usd:12}},observed:true,risk:{max_drawdown:-.4},held:true,preferences:{drawdown:'.3',horizon:'long'},prediction:{ready:true,evaluatedAccuracy:.5,baselineAccuracy:.6,evaluatedBrier:.27,baselineBrier:.24,testWindows:18,qualified:false}});
 assert.match(d.disposition,/exceeded/);assert.match(d.model,/Signal withheld/);
 assert.match(d.context,/Already held/);assert.match(d.concerns.join(' '),/fell 10.0%/);
 assert.doesNotMatch(d.disposition,/buy|sell|hold/i);
});
