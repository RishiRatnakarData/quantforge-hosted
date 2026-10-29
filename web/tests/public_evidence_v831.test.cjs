const test=require('node:test');
const assert=require('node:assert/strict');
const E=require('../site/public_evidence_v76.js');
const example=(symbol,growth,margin,name=symbol)=>({symbol,name,annual:[
 {fiscal_end:'2025-12-31',metrics:{revenue_usd:100*(1+growth/100),operating_income_usd:100*(1+growth/100)*margin/100}},
 {fiscal_end:'2024-12-31',metrics:{revenue_usd:100}}
]});
const snapshot={as_of:'2026-10-25',companies:[...Array.from({length:36},(_,i)=>example('C'+String(i).padStart(2,'0'),i-8,10+i/3)),
 example('EXTREME',270,1420,'Outlier & Co'),example('REVGROW',620,12,'Rapid Growth')]};

test('default focused plot reduces scale compression and shows every company in table',()=>{
 const focused=E.view(snapshot),full=E.view(snapshot,{mode:'all'});
 assert.match(focused,/10th–90th percentiles/);
 assert.match(focused,/outside the plotted range/);
 assert.equal((focused.match(/<tr/g)||[]).length,(full.match(/<tr/g)||[]).length);
 assert.ok((focused.match(/<circle /g)||[]).length<(full.match(/<circle /g)||[]).length);
 assert.match(full,/Full axis range/);
 assert.match(full,/EXTREME/);
});
test('no clutter of ticker labels and company selection is visible and faithful to values',()=>{
 const html=E.view(snapshot,{selected:'C04'});
 assert.match(html,/role="img"/);
 assert.match(html,/class="qf-evidence-selection"/);
 assert.match(html,/Revenue growth -4\.00%/);
 assert.equal((html.match(/<text x=/g)||[]).length,13); // 10 ticks + two axis captions + selected label
 assert.match(html,/data-evidence-symbol="C04"/);
 assert.match(html,/qf-evidence-active/);
});
test('selection outside focus explicitly discloses outlying marker but retains row',()=>{
 const html=E.view(snapshot,{selected:'EXTREME'});
 assert.match(html,/Outside the focused plot/);
 assert.match(html,/Outlier &amp; Co/);
 assert.match(html,/>270\.00%/);
 assert.match(html,/1420\.00%/);
});
test('escapes untrusted source strings, chart math remains unchanged, no private interfaces',()=>{
 const s={companies:[example('A',12,10,'<img src=x onerror=alert(1)>'),example('B',-10,-8)]};
 assert.ok(Math.abs(E.rows(s)[0].growth-12)<1e-9);assert.ok(Math.abs(E.rows(s)[1].margin+8)<1e-9);
 const html=E.view(s);
 assert.doesNotMatch(html,/<img/);
 assert.match(html,/&lt;img src=x onerror=alert\(1\)&gt;/);
 const src=require('fs').readFileSync(require.resolve('../site/public_evidence_v76.js'),'utf8');
 assert.doesNotMatch(src,/\bfetch\s*\(|XMLHttpRequest|localStorage|sessionStorage|alpaca|tradingClient/i);
});
