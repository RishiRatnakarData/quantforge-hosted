'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const workflow=require('../site/private_workflow_v140.js');
const dates=Array.from({length:70},(_,i)=>new Date(Date.UTC(2026,0,1+i)).toISOString().slice(0,10));
const prices=()=>({symbols:['AAA','BBB'],dates:dates.slice(),closes:{AAA:dates.map((_,i)=>90+i/3),BBB:dates.map((_,i)=>100+i/2)}});
const brief=()=>({schema:'quantforge.research-brief.v9.3',symbol:'AAA',universe:[{symbol:'AAA'},{symbol:'BBB'}],models:[{status:'completed'}],readiness:'review'});
const integrity=()=>({schema:'quantforge.integrity-console.v13.0',ready:true,candidate:'AAA',classification:'evidence-limited'});
const full=()=>({authenticated:true,selection:['AAA','BBB'],history:prices(),archive:{issuers:[{symbol:'AAA'}]},brief:brief(),integrity:integrity()});
test('private workflow recognizes signed-out state without pretending an MFA check passed',()=>{
 const r=workflow.assess();assert.equal(r.state,'sign-in-required');assert.equal(r.completed,0);
 assert.equal(r.next.route,'decision');assert.match(r.steps[0].detail,/authenticator/);
});
test('selection is required and must have 2–5 distinct valid companies',()=>{
 for(const selection of [[],['AAA'],['AAA','AAA'],['AAA','bad ticker'],['A','B','C','D','E','F']]){
  const r=workflow.assess({authenticated:true,selection});assert.equal(r.state,'select-companies');
 }
});
test('selected investments are not automatically considered loaded price data',()=>{
 const r=workflow.assess({authenticated:true,selection:['AAA','BBB']});
 assert.equal(r.state,'load-history');assert.equal(r.steps[1].ready,true);assert.equal(r.steps[2].ready,false);
});
test('matched history validates company set, chronology, strict prices and minimum observations',()=>{
 let d=full();assert.equal(workflow.assess(d).ready,true);
 d=full();d.history.symbols=['AAA','CCC'];assert.equal(workflow.assess(d).state,'load-history');
 d=full();d.history.closes.AAA[4]=0;assert.equal(workflow.assess(d).state,'load-history');
 d=full();d.history.dates[4]='2026-01-01';assert.equal(workflow.assess(d).state,'load-history');
 d=full();d.history.dates=d.history.dates.slice(0,10);assert.equal(workflow.assess(d).state,'load-history');
});
test('brief must match exact selected universe and have the current candidate',()=>{
 let d=full();d.brief.universe=[{symbol:'AAA'},{symbol:'CCC'}];assert.equal(workflow.assess(d).state,'run-research');
 d=full();d.brief.symbol='DDD';assert.equal(workflow.assess(d).state,'run-research');
 d=full();d.brief.schema='unsupported';assert.equal(workflow.assess(d).state,'run-research');
});
test('archive is optional, never counted as evidence of fully authenticated data',()=>{
 const d=full();d.archive=null;const r=workflow.assess(d);
 assert.equal(r.ready,true);assert.equal(r.evidence.ready,false);
 assert.equal(r.completed,5);assert.match(r.limitation,/not provider uptime/);
});
test('integrity classification retains blocked and limited labels without creating a forecast score',()=>{
 for(const label of ['blocked','evidence-limited','evidence-complete']){
  const d=full();d.integrity.classification=label;const r=workflow.assess(d);
  assert.equal(r.ready,true);assert.equal(r.state,label==='evidence-complete'?'research-review-ready':label==='blocked'?'assessment-blocked':'evidence-limited');
  assert.equal(r.next.route,'settings');
 }
});
test('sanitized export never contains balances, raw prices, selected tickers or SEC records',()=>{
 const d=full();d.brief.accountBalance=123456;d.history.closes.AAA[0]=444.12345;
 const out=JSON.stringify(workflow.exportSafe(workflow.assess(d)));
 for(const word of ['123456','444.12345','"AAA"','"BBB"','"issuers"','"closes"','"holdings"','"portfolio"','"token"']) assert.equal(out.includes(word),false,word);
});
test('module is pure and has no network, browser storage, MFA, or order execution',()=>{
 const s=fs.readFileSync(path.join(__dirname,'../site/private_workflow_v140.js'),'utf8');
 for(const item of ['fetch(', 'localStorage', 'sessionStorage', 'WebSocket(', 'XMLHttpRequest(', 'placeOrder(', 'executeTrade(', 'getAccessToken(', 'document.']) assert.equal(s.includes(item),false,item);
});
