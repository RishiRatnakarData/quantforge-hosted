'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const O = require('../site/private_optimizer.js');
const seed = () => {
  const dates=[],closes={ALPHA:[],BETA:[],GAMMA:[]};
  const base={ALPHA:100,BETA:80,GAMMA:45};
  for(let i=0;i<140;i++){
    dates.push(new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10));
    const shared=0.003*Math.sin(i*0.35);
    base.ALPHA*=1+0.0006+shared+0.001*Math.cos(i*0.3);
    base.BETA*=1+0.0003+shared*1.4+0.012*Math.sin(i*1.2);
    base.GAMMA*=1+0.0002-shared*0.2+0.005*Math.sin(i*2.2);
    for(const name of Object.keys(closes))closes[name].push(base[name]);
  }
  return {dates,closes,symbols:Object.keys(closes),source:'synthetic TEST FIXTURE (not deployed data)'};
};
const near=(a,b,epsilon=1e-7)=>assert.ok(Math.abs(a-b)<epsilon,`${a} not close to ${b}`);
test('aligned price preparation and shrinkage give symmetric positive diagonals',()=>{
  const d=O.prepare(seed());
  assert.equal(d.count,139);
  assert.equal(d.covariance.length,3);
  d.covariance.forEach((row,i)=>{
    assert.ok(row[i]>0);
    d.covariance.forEach((_,j)=>near(row[j],d.covariance[j][i]));
  });
});
test('constrained min variance has no higher modeled risk than equal weights',()=>{
  const d=O.prepare(seed()),p=O.run(seed(),{maxWeight:0.5,objective:'minimum'});
  near(p.chosen.reduce((a,b)=>a+b,0),1);
  assert.ok(p.chosen.every(x=>x>=-1e-9&&x<=0.50000001));
  assert.ok(p.optimized.annualVolatility<=p.equal.annualVolatility+1e-8);
  near(p.optimized.riskContributions.reduce((a,b)=>a+b,0),1);
  assert.equal(p.frontier.length,7);
  near(p.optimized.annualVolatility**2,252*(p.chosen.reduce((a,w,i)=>a+w*d.covariance[i].reduce((b,c,j)=>b+c*p.chosen[j],0),0)),1e-7);
});
test('risk-balanced inverse volatility and return tilt obey position cap',()=>{
  for(const objective of ['inverse','tilt']){
    const p=O.run(seed(),{maxWeight:0.35,objective});
    near(p.chosen.reduce((a,b)=>a+b,0),1);
    assert.ok(p.chosen.every(x=>x>=0&&x<=0.35000001));
    assert.ok(Number.isFinite(p.optimized.dailyES));
    assert.ok(p.optimized.dailyES>=p.optimized.dailyVaR-1e-10);
  }
});
test('weights are rejected when the cap makes the problem infeasible',()=>{
  assert.throws(()=>O.run(seed(),{maxWeight:0.30}),/Maximum position weight/);
});
test('synthetic or missing alignment cannot be replaced with invented observations',()=>{
  const d=seed();d.closes.BETA.pop();
  assert.throws(()=>O.run(d),/Incomplete or invalid price history/);
  const e=seed();e.dates[4]=e.dates[3];
  assert.throws(()=>O.run(e),/Load at least/);
  const f=seed();f.closes.GAMMA[4]=0;
  assert.throws(()=>O.run(f),/Incomplete or invalid/);
});
test('portfolio optimization depends on observed input prices, not public demo fixtures',()=>{
  const d=seed(),a=O.run(d,{objective:'minimum'});
  const reversed=JSON.parse(JSON.stringify(d));
  reversed.closes.ALPHA=reversed.closes.ALPHA.map((x,i)=>x*(1+0.2*Math.sin(i*2)));
  const b=O.run(reversed,{objective:'minimum'});
  assert.notDeepEqual(a.chosen,b.chosen);
});
test('correlation matrix is symmetric and bounded',()=>{
  const c=O.correlation(O.prepare(seed()));
  c.forEach((row,i)=>row.forEach((v,j)=>{
    assert.ok(v===null||(v>=-1&&v<=1));
    near(v,c[j][i]);
    if(i===j)near(v,1);
  }));
});
