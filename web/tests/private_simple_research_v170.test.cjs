'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const api=require('../site/private_simple_research_v170.js');
const input=()=>({selected:['AAPL','MSFT'],asOf:'2026-10-30',rows:[
 {symbol:'AAPL',name:'Apple',decision:'Avoid adding for now',reason:'Historical downside exceeds the selected risk limit.',pro:['Profitability available'],con:['Downside screen exceeded'],steps:[],modelCompleted:8,modelTotal:10},
 {symbol:'MSFT',name:'Microsoft',decision:'Consider a small position (conditional)',reason:'Reported fundamentals and selected screens are compatible.',pro:['Cash generation positive'],con:[],steps:['Check valuation assumptions'],modelCompleted:9,modelTotal:10}
],comparison:{ready:true,period:{start:'2025-10-01',end:'2026-10-01',observations:252},rows:[
 {symbol:'AAPL',maxDrawdown:-.3,totalChange:.07},{symbol:'MSFT',maxDrawdown:-.2,totalChange:.10}]}});
test('one comparison retains risk veto despite positive statistics elsewhere',()=>{
 const data=api.prepare(input());assert.equal(data.ready,true);
 assert.equal(data.rows[0].signal,'red');assert.equal(data.rows[1].signal,'green');
 assert.equal(data.priority,'MSFT');
 const html=api.render(input());assert.match(html,/Current risk limits caution against adding/);
 assert.match(html,/worst peak-to-trough fall/);assert.match(html,/30.0%/);
});
test('unavailable data never becomes a positive verdict',()=>{
 const i=input();i.rows[1].decision='Insufficient evidence';
 const out=api.prepare(i);assert.equal(out.priority,null);assert.equal(out.rows[1].signal,'gray');
});
test('untrusted provider company and note text is HTML-escaped',()=>{
 const i=input();i.rows[0].name='<script>alert(1)</script>';
 i.rows[0].reason='<img src=x onerror=alert(1)>';
 const html=api.render(i);assert.ok(!html.includes('<script>'));assert.ok(!html.includes('<img'));
 assert.match(html,/&lt;script&gt;/);
});
test('different selected universe invalidates current dashboard',()=>{
 const i=input();i.selected=['AAPL','NVDA'];assert.equal(api.prepare(i).ready,false);
});
test('pure presentation does not access accounts, market feeds or brokerage order endpoints',()=>{
 const src=fs.readFileSync(path.join(__dirname,'../site/private_simple_research_v170.js'),'utf8');
 for(const text of ['fetch(', 'localStorage','sessionStorage','document.cookie','private/trade','XMLHttpRequest'])assert.ok(!src.includes(text));
});
