const test=require('node:test');
const assert=require('node:assert/strict');
const E=require('../site/public_evidence_v76.js');
const fixture={as_of:'2026-10-25', companies:[
 {symbol:'AAA',name:'Example & Co',annual:[{fiscal_end:'2026-06-30',metrics:{revenue_usd:120,operating_income_usd:30}},{fiscal_end:'2025-06-30',metrics:{revenue_usd:100}}]},
 {symbol:'BBB',name:'Example Two',annual:[{fiscal_end:'2026-06-30',metrics:{revenue_usd:80,operating_income_usd:-8}},{fiscal_end:'2025-06-30',metrics:{revenue_usd:100}}]}
]};
test('SEC-backed exhibit computes actual revenue changes and margins without mocked fallback',()=>{
 const data=E.rows(fixture);assert.equal(data.length,2);
 assert.ok(Math.abs(data[0].growth-20)<1e-9);assert.equal(data[0].margin,25);
 assert.ok(Math.abs(data[1].growth+20)<1e-9);assert.equal(data[1].margin,-10);
 assert.match(E.view(fixture),/2026-10-25/);
 assert.match(E.view(fixture),/20.00%/);
});
test('invalid and incomplete filings are unavailable rather than zero-filled',()=>{
 assert.deepEqual(E.rows({companies:[{symbol:'ZZZ',annual:[{metrics:{revenue_usd:0}}]}]}),[]);
 assert.match(E.view({companies:[]}),/No illustrative values were substituted/);
});
test('escape issuer display strings and preserve negative financial metrics',()=>{
 const input=structuredClone(fixture);input.companies[0].name='<script>alert(1)</script>';
 const html=E.view(input);
 assert.doesNotMatch(html,/<script>/);assert.match(html,/&lt;script&gt;/);
 assert.match(html,/-20.00%/);
 assert.match(html,/-10.00%/);
});
test('view contains accessible data table as well as SVG and uses no network access',()=>{
 const html=E.view(fixture);assert.match(html,/role="img"/);assert.match(html,/<table>/);
 const src=require('node:fs').readFileSync(require.resolve('../site/public_evidence_v76.js'),'utf8');
 assert.doesNotMatch(src,/\bfetch\s*\(|XMLHttpRequest|localStorage|sessionStorage/);
});
