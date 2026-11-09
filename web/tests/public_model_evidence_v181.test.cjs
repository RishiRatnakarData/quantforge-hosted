'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const demo=require('../site/public_model_evidence_v181.js');
const ml=require('../site/private_predictive_ml_v180.js');

test('public synthetic example evaluates actual existing classifier with measured baselines',()=>{
 const history=demo.fixture();
 assert.equal(history.closes.DEMO.length,355);
 assert.deepEqual(history.dates,[...history.dates].sort());
 const x=ml.analyze(history,'DEMO');
 const r=demo.summary(x);
 assert.equal(r.ready,true);
 assert.ok(r.windows>=10);
 assert.ok(r.start<r.end);
 assert.ok(Number(r.modelBrier)>=0&&Number(r.modelBrier)<=1);
 assert.ok(Number(r.baselineBrier)>=0&&Number(r.baselineBrier)<=1);
 // A conservative screen must reject a synthetic series when baseline
 // directional accuracy exceeds the classifier's accuracy.
 if(x.evaluatedAccuracy<x.baselineAccuracy)assert.equal(x.qualified,false);
 assert.match(r.conclusion,/generated series/);
});
test('public example is deterministic and has zero private account or provider dependencies',()=>{
 const a=demo.fixture(),b=demo.fixture();
 assert.deepEqual(a,b);
 assert.ok(a.source.includes('synthetic'));
 for(const phrase of ['fetch(', 'XMLHttpRequest','localStorage','sessionStorage','/api/private','SUPABASE','ALPACA','private/notes','placeOrder']){
  assert.ok(!fs.readFileSync(path.join(__dirname,'../site/public_model_evidence_v181.js'),'utf8').includes(phrase),phrase);
 }
 assert.equal(demo.summary({ready:false}).ready,false);
});
