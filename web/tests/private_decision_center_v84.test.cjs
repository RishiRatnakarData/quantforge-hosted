'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const C=require('../site/private_decision_center_v84.js');
const dates=n=>Array.from({length:n},(_,i)=>new Date(Date.UTC(2026,0,i+1)).toISOString().slice(0,10));
const base=()=>{
 const series=dates(260);
 const history={symbols:['AAA','BBB'],dates:series,closes:{AAA:series.map((_,i)=>100+i),BBB:series.map((_,i)=>90+i*.3)}};
 const walkforward={symbols:['AAA','BBB'],start:series[25],end:series.at(-1),windows:[{},{},{}],optimized:{metrics:{change:.08}},benchmark:{metrics:{change:.12}}};
 const screening={lens:'balanced',comparisons:[{symbol:'AAA',score:77,cautions:['Elevated historical volatility']},{symbol:'BBB',score:71,cautions:[]}]};
 return {portfolio:{cash:120,holdings:{AAA:2}},quotes:{AAA:{price:100,timestamp:'2026-09-01T15:00:00Z'}},
  history,selection:['AAA','BBB'],optimizer:{symbols:['AAA','BBB'],equal:{annualVolatility:.21},optimized:{annualVolatility:.18}},
  walkforward,screening,company:{symbol:'AAA',annual:[{fiscal_end:'2026-06-30',metrics:{revenue_usd:1000,free_cash_flow_usd:190}}]},
  purchaseImpact:{proposedBudget:40,before:{},after:{}},robustness:{schema:'quantforge.robustness.v1',symbols:['AAA','BBB'],dates:{start:walkforward.start,end:walkforward.end},strategyCases:[{}],summary:{fullActivePp:-4,windowDependentSign:true}}};
};
test('empty signed-in session gives no fabricated investment conclusions',()=>{
 const r=C.evaluate({portfolio:{cash:0,holdings:{}}});
 assert.equal(r.coverage.available,1);
 assert.match(r.status,/Build the evidence/);
 assert.ok(r.steps.some(x=>x.route==='research'));
 assert.ok(!r.findings.some(x=>/historic.*strategy/.test(x)));
});
test('integrated results reconcile risk versus out-of-sample underperformance',()=>{
 const r=C.evaluate(base());
 assert.equal(r.coverage.available,r.coverage.total);
 assert.match(r.status,/Core evidence assembled/);
 assert.ok(r.findings.some(x=>x.includes('equal-weight benchmark')));
 assert.ok(r.conflicts.some(x=>x.includes('underperformed equal weights')));
 assert.ok(r.conflicts.some(x=>x.includes('sign reverses')));
 assert.ok(r.conflicts.some(x=>x.includes('Lower fitted')));
 assert.deepEqual(r.dataset.symbols,['AAA','BBB']);
});
test('selection changes block reuse of old optimizer, walk-forward and robustness',()=>{
 const b=base();b.selection=['AAA','CCC'];
 const r=C.evaluate(b);
 for(const id of ['history','optimization','walkforward','robustness'])assert.equal(r.details.find(x=>x.id===id).available,false,id);
 assert.equal(r.dataset,null);
 assert.ok(r.conflicts.some(x=>x.includes('differ')));
});
test('missing priced holding suppresses concentration',()=>{
 const b=base();b.portfolio.holdings.BBB=5;
 const r=C.evaluate(b);
 assert.equal(r.details.find(x=>x.id==='portfolio').available,false);
 assert.ok(!r.findings.some(x=>x.includes('Largest priced holding')));
 assert.ok(r.steps.some(x=>x.route==='trade'));
});
test('other universe cannot masquerade as completed optimized research',()=>{
 const b=base();b.optimizer.symbols=['AAA','ZZZ'];b.walkforward.symbols=['AAA','ZZZ'];
 const r=C.evaluate(b);
 assert.ok(!r.details.find(x=>x.id==='optimization').available);
 assert.ok(!r.details.find(x=>x.id==='walkforward').available);
 assert.ok(!r.details.find(x=>x.id==='robustness').available);
});
test('incomplete filing with no valid revenue does not produce financial evidence',()=>{
 const b=base();b.company.annual=[{fiscal_end:'2026-06-30',metrics:{revenue_usd:null}}];
 const r=C.evaluate(b);
 assert.equal(r.details.find(x=>x.id==='fundamentals').available,false);
 assert.ok(!r.findings.some(x=>x.includes('SEC revenue')));
});
test('evaluation never mutates its input and does not export private numbers or raw arrays',()=>{
 const b=base(),copy=JSON.stringify(b);
 const r=C.evaluate(b);
 assert.equal(JSON.stringify(b),copy);
 const report=JSON.stringify(r);
 for(const field of ['"holdings"','"cash"','"quotes"','"closes"','"prices"','"email"','"token"','"quantity"','"privateState"'])assert.ok(!report.includes(field),field);
 assert.equal(typeof C.export, 'undefined');
});
test('model has no network, storage, account mutations or trade execution APIs',()=>{
 const fs=require('node:fs');
 const s=fs.readFileSync(require.resolve('../site/private_decision_center_v84.js'),'utf8');
 for(const expression of [/\bfetch\s*\(/,/\bXMLHttpRequest\b/,/\blocalStorage\b/,/\bsessionStorage\b/,/\bWebSocket\b/,/\beval\s*\(/,/\bprivate\/trade\b/,/\baddEventListener\b/])assert.ok(!expression.test(s),String(expression));
});

test('exposes next research action rather than a buy or sell instruction',()=>{
 const r=C.evaluate(base());
 assert.ok(['trade','valuation','research','ideas','home','walkforward','optimization'].includes(r.nextAction.route));
 assert.ok(!/\b(buy now|sell now|guaranteed)\b/i.test(JSON.stringify(r)));
});
test('stale observation warns and never creates an executable quote',()=>{
 const b=base();b.now='2026-10-29T12:00:00Z';
 const r=C.evaluate(b);
 assert.ok(r.conflicts.some(x=>x.includes('seven calendar days old')));
 assert.ok(!JSON.stringify(r).includes('2026-09-01T15:00:00Z'));
});
