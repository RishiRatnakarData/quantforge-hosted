 'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const api=require('../site/sec_peer_model.js');
const snapshot=JSON.parse(fs.readFileSync(path.join(__dirname,'../site/sec_snapshot.json')));
test('full published issuer universe is considered without synthetic records',()=>{
 const r=api.compare(snapshot,'MSFT');
 assert.equal(r.universe,94);assert.equal(r.ready,true);
 assert.ok(r.eligible>7);assert.ok(r.eligible<=94);
 assert.equal(r.compared,r.eligible);
 assert.ok(r.peers.some(c=>c.symbol!=='MSFT'));
 assert.ok(r.peers.every(c=>c.companyfacts.startsWith('https://data.sec.gov/')));
});
test('self similarity excluded, deterministic peers and fixed four documented ratios',()=>{
 const a=api.compare(snapshot,'AAPL'),b=api.compare(snapshot,'AAPL');
 assert.equal(a.ready,true);assert.deepEqual(a.peers,b.peers);
 assert.equal(a.features.length,4);assert.ok(a.peers.every(p=>p.symbol!=='AAPL'&&p.distance>=0));
});
test('missing values and missing accession are not imputed',()=>{
 const snapshot2=structuredClone(snapshot);
 const first=snapshot2.companies.find(c=>c.symbol==='MSFT');
 first.annual[0].sources.revenue_usd=null;
 assert.equal(api.compare(snapshot2,'MSFT').ready,false);
 assert.equal(api.compare(snapshot2,'AAPL').eligible,api.compare(snapshot,'AAPL').eligible-1);
});
test('data freshness and peer group checks',()=>{
 assert.equal(api.compare(snapshot,'NO_SUCH_ISSUER').ready,false);
 const s=structuredClone(snapshot);s.expanded_as_of='2023-01-01';s.as_of='2023-01-01';
 assert.equal(api.compare(s,'AAPL').ready,false);
 const r=api.compare(snapshot,'MSFT',{sectorOnly:true});
 assert.ok(r.ready===true||/Insufficient/.test(r.reason));
});
