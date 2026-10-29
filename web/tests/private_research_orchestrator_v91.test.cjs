const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const orchestrator=require('../site/private_research_orchestrator_v91.js');
const oldPolicy=require('../site/private_research_os_v90.js');
function fixture(){
 const dates=[];for(let i=0;i<300;i++){const d=new Date(Date.UTC(2025,0,1+i));dates.push(d.toISOString().slice(0,10));}
 const history={symbols:['MSFT','SPY'],dates,source:'Observed test history',
  closes:{MSFT:dates.map((_,i)=>100+i*.2),SPY:dates.map((_,i)=>200+i*.3)}};
 return {selection:['MSFT','SPY'],symbol:'MSFT',history,train:126,step:21,cap:.6,frenchImported:false};
}
function plan(){return orchestrator.plan(fixture());}
test('eligible models require complete aligned matching dates and closes',()=>{
 const p=plan();assert.equal(p.models.find(m=>m.key==='history').eligible,true);
 assert.equal(p.models.find(m=>m.key==='walkforward').eligible,true);
 assert.equal(p.models.find(m=>m.key==='french').eligible,false);
 assert.deepEqual(p.period,{start:'2025-01-01',end:'2025-10-27',sessions:300,source:'Observed test history'});
 const bad=fixture();bad.history.closes.MSFT[3]=NaN;
 assert.match(orchestrator.checkHistory(bad.selection,bad.history),/incomplete/);
 const duplicate=fixture();duplicate.history.dates[3]=duplicate.history.dates[2];
 assert.match(orchestrator.checkHistory(duplicate.selection,duplicate.history),/unordered/);
 const mismatch=fixture();mismatch.selection=['MSFT','NVDA'];
 assert.match(orchestrator.checkHistory(mismatch.selection,mismatch.history),/match/);
});
test('walk-forward eligibility respects exact train/step windows and weight feasibility',()=>{
 let x=fixture();x.history.dates=x.history.dates.slice(0,145);
 for(const key of ['MSFT','SPY'])x.history.closes[key]=x.history.closes[key].slice(0,145);
 assert.equal(orchestrator.plan(x).models.find(m=>m.key==='walkforward').eligible,false);
 x=fixture();x.cap=.3;
 assert.equal(orchestrator.plan(x).models.find(m=>m.key==='optimization').eligible,false);
 assert.equal(orchestrator.plan(x).models.find(m=>m.key==='walkforward').eligible,false);
});
test('ledger tracks scope and failures without inventing model success',()=>{
 const p=plan();let l=orchestrator.ledger(p);
 assert.equal(l.find(m=>m.key==='candidate').status,'pending');
 assert.equal(l.find(m=>m.key==='french').status,'ineligible');
 l=orchestrator.mark(l,'history','completed','Verified 300 observations.');
 l=orchestrator.mark(l,'candidate','failed','SEC endpoint was unavailable.');
 for(const e of l.filter(e=>e.status==='pending'))l=orchestrator.mark(l,e.key,'skipped','Not performed.');
 const baseline={decision:'Consider a small position (conditional)',reason:'test',readiness:'required-inputs-valid',
  limitations:[],evidence:[{key:'history',state:'available'}]};
 const out=orchestrator.reconcile(baseline,l);
 assert.equal(out.decision,'Insufficient evidence');assert.equal(out.readiness,'withheld');
 assert.equal(out.orchestration.failed,1);
 assert(out.orchestration.models.some(m=>m.key==='candidate'&&m.status==='failed'));
 assert.equal(baseline.decision,'Consider a small position (conditional)');
 assert.throws(()=>orchestrator.mark(l,'trade','completed','Never'),/Unknown/);
 assert.throws(()=>orchestrator.reconcile(baseline,orchestrator.ledger(p)),/unfinished/);
});
test('optional model failure remains visible without silently overriding the existing policy',()=>{
 const p=plan();let l=orchestrator.ledger(p);
 for(const m of l.filter(m=>m.status==='pending'))l=orchestrator.mark(l,m.key,m.key==='optimization'?'failed':'completed',m.title);
 const result=orchestrator.reconcile({decision:'Hold / monitor',readiness:'required-inputs-valid',reason:'test',
  limitations:[],evidence:[{key:'history',state:'available'}]},l);
 assert.equal(result.decision,'Hold / monitor');assert.equal(result.orchestration.failed,1);
 assert(result.limitations.some(x=>/failed/.test(x)));
});
test('module remains pure; orchestrator does not connect to brokerage or mutate state',()=>{
 const s=fs.readFileSync(path.join(__dirname,'../site/private_research_orchestrator_v91.js'),'utf8');
 for(const token of ['fetch(', 'XMLHttpRequest', 'localStorage', 'sessionStorage', 'private/trade', 'placeOrder(', 'alpaca.markets'])
  assert(!s.includes(token),token);
 assert.deepEqual(plan(),plan());
 assert.equal(typeof oldPolicy.assess,'function');
});
