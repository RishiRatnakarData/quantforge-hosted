'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const center=require('../site/private_unified_decision_v160.js');
const states=['supports','supports','mixed','supports','mixed'];
function brief(){return {schema:'quantforge.research-brief.v9.3',symbol:'AAA',candidate:'Example A',asOf:'2026-10-29',action:'Research further before adding',reason:'Screening rationale',blocked:false,universe:[{symbol:'AAA'},{symbol:'BBB'}],models:[{status:'completed'},{status:'completed'},{status:'ineligible'}],modelCoverage:{total:3,completed:2},mandatoryMissing:[],next:['Read the filings'],conflicts:[],cautions:[],evidence:[{key:'history',status:'available'},...center.domains.map((d,i)=>({key:d.key,status:states[i],detail:'Verified method evidence',source:'SEC or observations'}))],comparison:{assets:[{symbol:'AAA',name:'Example A',priceChangePercent:8,maxDrawdownPercent:-12},{symbol:'BBB',name:'Example B',priceChangePercent:-2,maxDrawdownPercent:-7}]}};}
function integrity(){return {schema:'quantforge.integrity-console.v13.0',ready:true,candidate:'AAA',classification:'evidence-complete',gates:[{key:'linkedModelEvidence',status:'covered'}]};}
function workflow(){return {schema:'quantforge.workflow-readiness.v14.0',state:'research-review-ready'};}
test('full eligible and positive evidence yields a legible green screening signal',()=>{
 const r=center.summarize({brief:brief(),integrity:integrity(),workflow:workflow()});
 assert.equal(r.ready,true);assert.equal(r.signal,'green');assert.equal(r.alignment,85);
 assert.equal(r.coverage,67);assert.equal(r.domains.length,5);assert.equal(r.comparison.length,2);
 assert.match(r.methodology,/not.*forecast accuracy/i);
});
test('a missing core method withholds score even when others look strong',()=>{
 const b=brief();b.evidence=b.evidence.filter(x=>x.key!=='fundamentals');
 const r=center.summarize({brief:b,integrity:integrity(),workflow:workflow()});
 assert.equal(r.signal,'gray');assert.equal(r.alignment,null);assert.deepEqual(r.requiredMissing,['fundamentals']);
});
test('missing optional historical archive never becomes complete-green',()=>{
 const i=integrity();i.classification='evidence-limited';
 const r=center.summarize({brief:brief(),integrity:i,workflow:{...workflow(),state:'evidence-limited'}});
 assert.equal(r.ready,true);assert.equal(r.signal,'amber');assert.equal(r.classification,'evidence-limited');assert.ok(r.notes.some(x=>/historical/i.test(x)));
});
test('required model block dominates attractive support signals',()=>{
 const b=brief();b.blocked=true;b.mandatoryMissing=['Portfolio risk'];
 const r=center.summarize({brief:b,integrity:integrity()});
 assert.equal(r.alignment,null);assert.equal(r.signal,'red');
});
test('non-directional availability never inflates score',()=>{
 const b=brief();b.evidence.find(x=>x.key==='valuation').status='available';
 const r=center.summarize({brief:b,integrity:integrity()});
 assert.equal(r.alignment,80);assert.equal(r.signal,'amber');
});
test('research universe and historical outcomes cannot be fabricated',()=>{
 const b=brief();b.universe=[{symbol:'AAA'},{symbol:'AAA'}];
 assert.equal(center.summarize({brief:b,integrity:integrity()}).ready,false);
 const b2=brief();b2.comparison.assets[0].priceChangePercent=Number.NaN;
 assert.equal(center.summarize({brief:b2,integrity:integrity()}).comparison.length,1);
});
test('stale or inconsistent workflow refuses existing scores',()=>{
 assert.equal(center.summarize({brief:brief(),integrity:integrity(),workflow:{...workflow(),state:'load-history'}}).ready,false);
 assert.equal(center.summarize({brief:brief(),integrity:{...integrity(),candidate:'BBB'}}).ready,false);
});
test('safe export retains only aggregate method status, not personal or market data',()=>{
 const r=center.exportSafe(center.summarize({brief:brief(),integrity:integrity()}));
 const s=JSON.stringify(r);
 for(const secret of ['holdings','password','accession','closes','quantity','cash','token','apiKey','rawPrice','priceChangePercent']) assert.ok(!s.includes(secret),secret);
});
test('module is pure and cannot upload or submit orders',()=>{
 const src=fs.readFileSync(path.join(__dirname,'../site/private_unified_decision_v160.js'),'utf8');
 for(const forbidden of ['fetch(', 'localStorage', 'sessionStorage', 'XMLHttpRequest', 'private/trade', 'WebSocket('])assert.ok(!src.includes(forbidden),forbidden);
});

test('missing evidence is neutral and does not impersonate a measured loss',()=>{
 const b=brief();b.evidence=b.evidence.filter(x=>x.key!=='downside');
 const r=center.summarize({brief:b,integrity:integrity()});
 assert.equal(r.signal,'gray');assert.equal(r.alignment,null);
 assert.equal(r.domains.find(x=>x.key==='downside').label,'Not evaluated');
});

test('hard risk veto is displayed as red despite a green-weight evidence index',()=>{
 const b=brief();b.blocked=true;b.mandatoryMissing=[];b.reason='Drawdown exceeds limit';
 const r=center.summarize({brief:b,integrity:integrity()});
 assert.equal(r.signal,'red');assert.equal(r.riskVeto,true);
 assert.match(r.blockers[0],/Drawdown exceeds limit/);
 assert.equal(r.alignment,null);
});
test('mandatory missing evidence is neutral without a measured risk breach',()=>{
 const b=brief();b.mandatoryMissing=['Independent valuation'];
 const r=center.summarize({brief:b,integrity:integrity()});
 assert.equal(r.signal,'gray');assert.equal(r.riskVeto,false);
 assert.ok(r.blockers.includes('Independent valuation'));
});
