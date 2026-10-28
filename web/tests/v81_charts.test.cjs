'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ctx={window:{}};
vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'..','site','sec_visuals_v81.js'),'utf8'),ctx);
const charts=ctx.window.QFPublicVisualsV81;
const company={name:'Example <script> company',annual:[
 {fiscal_end:'2025-12-31',metrics:{revenue_usd:120e9,operating_income_usd:36e9,net_income_usd:23e9,free_cash_flow_usd:-3e9}},
 {fiscal_end:'2024-12-31',metrics:{revenue_usd:100e9,operating_income_usd:20e9,net_income_usd:18e9,free_cash_flow_usd:6e9}},
 {fiscal_end:'2023-12-31',metrics:{revenue_usd:95e9,operating_income_usd:19e9,net_income_usd:null,free_cash_flow_usd:null}},
]};
test('margin uses observed SEC numerator and denominator, chronological periods',()=>{
 const p=charts.history(company,'margin');
 assert.equal(p[0].period,'2023-12-31');assert.equal(p[2].value,0.3);
 assert.match(charts.historicalHtml(company,'margin'),/30\.0%/);
});
test('negative FCF is not silently zeroed and missing values are not invented',()=>{
 const p=charts.history(company,'fcf');
 assert.equal(p[0].value,null);assert.equal(p[2].value,-3e9);
 const h=charts.historicalHtml(company,'fcf');assert.match(h,/Not reported/);
 assert.match(h,/\-\$3\.00B/);
});
test('scenarios are explicitly hypothetical, bounded, and compound from SEC baseline',()=>{
 const arr=charts.projection(company,10,3);assert.equal(arr[0].value,120e9);
 assert.ok(Math.abs(arr[3].value-159.72e9)<1);
 assert.equal(arr[1].observed,false);
 assert.equal(charts.projection(company,100,3),null);
 assert.match(charts.projectionHtml(company,5,3),/not an earnings prediction|Not an earnings prediction/i);
 assert.match(charts.projectionHtml(company,5,3),/assumed scenario/i);
});
test('projections refuse missing SEC annual revenue',()=>{
 assert.equal(charts.projection({annual:[{fiscal_end:'2025-12-31',metrics:{revenue_usd:null}}]},5,3),null);
});
test('comparison graph retains units, escape controls, and labels fiscal-year differences',()=>{
 const html=charts.rankingHtml([{symbol:'BAD<svg>',name:'Company',value:42.5},{symbol:'GOOD',name:'Company B',value:15}], 'Margin', 'percent');
 assert.match(html,/BAD&lt;svg&gt;/);assert.doesNotMatch(html,/<svg>/);
 assert.match(html,/42\.5%/);assert.match(html,/Fiscal years differ/);
 assert.match(charts.rankingHtml([{symbol:'A',value:20e9}], 'Revenue', 'usd'),/\$20\.00B/);
});
test('pure chart builder has no network, browser storage, or trading mutations',()=>{
 const source=fs.readFileSync(require('node:path').join(__dirname,'..','site','sec_visuals_v81.js'),'utf8');
 assert.doesNotMatch(source,/\bfetch\s*\(|XMLHttpRequest|localStorage|sessionStorage|navigator\.|alpaca|api\/private|sendOrder/i);
});
