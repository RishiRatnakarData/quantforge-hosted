const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const p=require('node:path');
const api=require('../site/private_release_acceptance_v150.js');
test('six separate manual checks begin unverified, never silently passed',()=>{
 const a=api.assess();assert.equal(a.counts.notTested,6);assert.equal(a.status,'not-fully-tested');
 assert.equal(a.independentlyVerified,false);
});
test('failed checks keep the release self-attestation visibly blocked',()=>{
 const states=Object.fromEntries(api.keys.map(x=>[x,'passed']));states.provider='failed';
 const a=api.assess(states);assert.equal(a.status,'attention-required');
 assert.equal(a.counts.failed,1);assert.equal(a.counts.passed,5);
});
test('all checks explicitly passed only claims self-attested completion',()=>{
 const states=Object.fromEntries(api.keys.map(x=>[x,'passed']));const a=api.assess(states);
 assert.equal(a.status,'self-attested-complete');assert.equal(a.independentlyVerified,false);
});
test('only known statuses and keys can be assigned',()=>{
 assert.throws(()=>api.update({},'secret','passed'));
 assert.throws(()=>api.update({},'mfa','not-a-real-state'));
 assert.equal(api.update({},'mfa','passed').mfa,'passed');
});
test('safe export strips unrelated account and raw data',()=>{
 const s=api.exportSafe({mfa:'passed',holdings:[{balance:123}],password:'secret',prices:[1]});
 const j=JSON.stringify(s);assert.equal(s.checks.mfa,'passed');
 for(const x of ['holdings','balance','password','secret','prices'])assert.equal(j.includes(x),false);
 assert.equal(s.independentlyVerified,false);
});
test('pure acceptance helper cannot access providers, storage or browser APIs',()=>{
 const src=fs.readFileSync(p.join(__dirname,'../site/private_release_acceptance_v150.js'),'utf8');
 for(const token of ['fetch(', 'XMLHttpRequest(', 'localStorage','sessionStorage','document.', 'placeOrder(', 'supabase', 'alpaca'])
  assert.equal(src.includes(token),false,token);
});
