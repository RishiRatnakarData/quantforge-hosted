'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const ml=require('../site/private_predictive_ml_v180.js');
function history(n=330){
 const dates=Array.from({length:n},(_,i)=>new Date(Date.UTC(2024,0,1+i)).toISOString().slice(0,10));
 const trend=Array.from({length:n},(_,i)=>100*Math.exp(0.0003*i+0.035*Math.sin(i/6)));
 const another=Array.from({length:n},(_,i)=>75*Math.exp(0.0002*i+0.023*Math.cos(i/9)));
 return {symbols:['AAPL','MSFT'],dates,closes:{AAPL:trend,MSFT:another},asset_classes:{AAPL:'us_equity',MSFT:'us_equity'},source:'Dated provider prices'};
}
test('real fitted model evaluates strictly later disjoint observation windows',()=>{
 const result=ml.analyze(history(),'AAPL');
 assert.equal(result.ready,true);
 assert.equal(result.forecastHorizon,5);
 assert.ok(result.testWindows>=10);
 assert.match(result.model,/logistic regression/);
 assert.ok(result.firstTestDate<result.lastTestDate);
 assert.ok(result.evaluatedBrier>=0&&result.evaluatedBrier<=1);
 assert.ok(result.baselineBrier>=0&&result.baselineBrier<=1);
 assert.ok(!Object.hasOwn(result,'priceTarget'));
 assert.match(result.limitations,/uncalibrated/);
});
test('feature construction cannot incorporate a later price change',()=>{
 const d=history(),before=ml.features(d.closes.AAPL,180);
 d.closes.AAPL[210]*=2;
 assert.deepEqual(ml.features(d.closes.AAPL,180),before);
});
test('invalid histories, crypto and short samples fail closed',()=>{
 const d=history();d.closes.AAPL[7]=0;
 assert.equal(ml.analyze(d,'AAPL').ready,false);
 const short=history(120);
 assert.equal(ml.analyze(short,'MSFT').ready,false);
 const crypto=history();crypto.asset_classes.AAPL='crypto';
 assert.equal(ml.analyze(crypto,'AAPL').ready,false);
});
test('selection is bounded, model does not invent confidential account fields',()=>{
 const r=ml.all(history(),['AAPL','MSFT']);
 assert.equal(r.ready,true);assert.equal(r.rows.length,2);
 assert.equal(ml.all(history(),['AAPL','AAPL']).ready,false);
 const text=JSON.stringify(r);
 assert.ok(!/credentials|positions|account_number|order_id|holdings/.test(text));
});
test('standalone learning model never accesses browser fetch/storage/order endpoints',()=>{
 const code=fs.readFileSync(path.join(__dirname,'../site/private_predictive_ml_v180.js'),'utf8');
 for(const x of ['fetch(', 'localStorage','sessionStorage','placeOrder(', 'postMessage(', '/api/private/trade']){
  assert.ok(!code.includes(x),x);
 }
});
