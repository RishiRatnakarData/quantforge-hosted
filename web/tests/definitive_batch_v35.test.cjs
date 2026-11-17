'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const S=require('../site/research_study_v35.js');
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const result=(symbol,covered=true,readFailures=[])=>({input:{readFailures},report:{snapshot:{symbol},coverage:[{domain:'Observed evidence',status:covered?'covered':'incomplete'}]}});
const candidates=['AAA','BBB','CCC'].map(symbol=>({symbol,name:symbol+' company'}));
test('batch studies run sequentially, expose all stages and coalesce repeat clicks',async()=>{
 let active=0,max=0;const calls=[],states=[];
 const b=S.createBatch({onChange:rows=>states.push(rows.map(r=>r.state)),run:async(s,c,signal,analyzing)=>{active++;max=Math.max(active,max);calls.push(s);analyzing();await wait(2);active--;return result(s);}});
 const a=b.start(candidates,{}),same=b.start(candidates,{});assert.equal(a,same);await a;
 assert.equal(max,1);assert.deepEqual(calls,['AAA','BBB','CCC']);assert.deepEqual(b.snapshot().map(r=>r.state),['Completed','Completed','Completed']);
 for(const state of ['Waiting','Loading evidence','Analyzing','Completed'])assert.ok(states.some(rows=>rows.includes(state)),state);assert.equal(b.busy(),false);
});
test('one provider failure preserves successful preceding and following companies',async()=>{
 const b=S.createBatch({run:async(s)=>{if(s==='BBB')throw Error('private provider details must not escape');return result(s);}});await b.start(candidates,{});
 assert.deepEqual(b.snapshot().map(r=>r.state),['Completed','Failed','Completed']);assert.equal(b.snapshot()[0].result.report.snapshot.symbol,'AAA');assert.equal(b.snapshot()[2].result.report.snapshot.symbol,'CCC');assert.doesNotMatch(b.snapshot()[1].reason,/private provider/);
});
test('incomplete coverage or incomplete source requests never become completed research',async()=>{
 const b=S.createBatch({run:async(s)=>result(s,s!=='AAA',s==='BBB'?['capital']:[])});await b.start(candidates,{});assert.deepEqual(b.snapshot().map(r=>r.state),['Incomplete','Incomplete','Completed']);
});
test('sign-out cancellation prevents a late response from restoring private results',async()=>{
 let release;const b=S.createBatch({run:()=>new Promise(r=>{release=r;})});const pending=b.start([candidates[0]],{});b.cancel();release(result('AAA'));await pending;assert.deepEqual(b.snapshot(),[]);assert.equal(b.busy(),false);
});
test('owner-version invalidation clears both current and earlier successful rows',async()=>{
 let valid=true;const b=S.createBatch({valid:()=>valid,run:async(s)=>{if(s==='BBB')valid=false;return result(s);}});await b.start(candidates,{});assert.deepEqual(b.snapshot(),[]);
});
test('a timed-out company does not prevent another company completing',async()=>{
 const b=S.createBatch({timeoutMs:8,run:async(s)=>s==='AAA'?new Promise(()=>{}):result(s)});await b.start(candidates.slice(0,2),{});assert.deepEqual(b.snapshot().map(r=>r.state),['Failed','Completed']);
});
test('an old batch cannot overwrite the newer universe after cancellation',async()=>{
 let release;const b=S.createBatch({run:async(s)=>s==='AAA'?new Promise(r=>{release=r;}):result(s)});const old=b.start([candidates[0]],{});b.cancel();await b.start([candidates[2]],{});release(result('AAA'));await old;assert.equal(b.snapshot()[0].symbol,'CCC');assert.equal(b.snapshot()[0].state,'Completed');
});
test('empty, duplicate and oversized batches are rejected before provider access',()=>{
 let calls=0;const b=S.createBatch({run:async()=>{calls++;}});for(const rows of [[],[candidates[0],candidates[0]],Array.from({length:6},(_,i)=>({symbol:'S'+i}))])assert.throws(()=>b.start(rows,{}));assert.equal(calls,0);
});
require('../site/research_core_v20.js');require('../site/research_compare_portfolio_v21.js');require('../site/research_guide_v30.js');require('../site/research_decision_v34.js');require('../site/private_predictive_ml_v180.js');
test('isolated loader keeps partial observed evidence and never substitutes synthetic paths',async()=>{
 const snapshot={companies:[{symbol:'AAA',name:'A',annual:[]}]},portfolio={version:7,cash:100,holdings:{'BTC/USD':.01}};let calls=0;
 const input=await S.load({symbol:'AAA',snapshot,portfolio,read:async(path)=>{calls++;if(path.includes('history-single'))return {licensed_private:true,symbol:'AAA',ohlcv_available:false,observations:[{date:'2026-11-16',close:10},{date:'2026-11-17',close:11}]};throw Error('provider unavailable');}});
 assert.equal(calls,5);assert.equal(input.origin,'market');assert.equal(input.assessmentPrices.length,2);assert.equal(input.capital,null);assert.ok(input.readFailures.includes('quotes'));assert.ok(!input.history.symbols.includes('BTC/USD'));assert.equal(input.portfolio,portfolio);
});
test('a false private-price contract cannot silently become market evidence',async()=>{
 const input=await S.load({symbol:'AAA',snapshot:{companies:[{symbol:'AAA',annual:[]}]},portfolio:{version:1,holdings:{}},read:async()=>({licensed_private:false,observations:[{date:'2026-11-17',close:123}]})});assert.deepEqual(input.assessmentPrices,[]);assert.ok(input.readFailures.includes('prices'));
});
test('partial source refresh is disclosed by the canonical decision, not a second batch policy',()=>{
 const D=global.QFDecision34,G=global.QFResearchGuide30;const report=D.assess({financial:{symbol:'AAA',source:{period:'2026-06-30'},metrics:{}},readFailures:['capital'],rules:{}},G);assert.equal(report.proposal.code,'evidence-incomplete');assert.ok(report.coverage.some(r=>r.domain==='Requested source refresh'&&r.status==='incomplete'));assert.equal(report.authoritative,true);
});

test('wrong-company responses and malformed quote contracts remain incomplete',async()=>{
 const input=await S.load({symbol:'AAA',snapshot:{companies:[{symbol:'AAA',annual:[]}]},portfolio:{version:1,holdings:{}},read:async(path)=>path.includes('history-single')?{licensed_private:true,symbol:'BBB',ohlcv_available:false,observations:[{date:'2026-11-17',close:123}]}:path.includes('quotes')?{quotes:null}:{symbol:'BBB',annual:[]}});
 assert.deepEqual(input.assessmentPrices,[]);assert.equal(input.company.symbol,'AAA');assert.equal(input.capital,null);
 for(const key of ['prices','capital','company','quotes'])assert.ok(input.readFailures.includes(key),key);
});
test('complete provider failure rejects without creating a report or replacement evidence',async()=>{
 await assert.rejects(S.load({symbol:'AAA',snapshot:{companies:[{symbol:'AAA',annual:[]}]},portfolio:{version:1,holdings:{}},read:async()=>{throw Error('unavailable');}}),/No requested evidence/);
});

test('shared assessment inputs retain crypto calendar and classifier ineligibility',()=>{
 let calendar,kind;const E={QFResearchCore20:{financialSummary:()=>({source:{period:null}}),priceStatistics:(p,n)=>{calendar=n;return {}; }},QFPrivatePredictiveMLV180:{analyze:h=>{kind=h.asset_classes['BTC/USD'];return {ready:false};}},QFResearchB21:{compare:()=>{throw Error('No mixed-calendar overlap');}}};
 const input=S.assessmentInput({symbol:'BTC/USD',assessmentPrices:[{date:'2026-11-17',close:100}],origin:'market',portfolio:{version:1,holdings:{}},asOf:'2026-11-17'}, {results:{}}, E);
 assert.equal(calendar,365);assert.equal(kind,'crypto');assert.equal(input.prediction.ready,false);assert.deepEqual(input.overlap,[]);
});
