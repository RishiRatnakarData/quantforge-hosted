"use strict";
const test=require('node:test'), assert=require('node:assert/strict'), fs=require('node:fs'), path=require('node:path');
const picker=require('../site/investment_picker_v27.js');
require('../site/research_models_core_v22.js');
require('../site/methods_lab_v27.js');
const lab=globalThis.QFMethods27;
test('name-first ranking distinguishes common issuer from associated funds and preserves exact ticker intent',()=>{
 const rows=[{symbol:'MSFU',name:'Direxion Daily Microsoft Bull ETF'},{symbol:'MSFT',name:'Microsoft Corporation'},{symbol:'MSFD',name:'Microsoft Bear Fund'}];
 assert.equal(picker.rank(rows,'Microsoft')[0].symbol,'MSFT');
 assert.equal(picker.rank(rows,'MSFU')[0].symbol,'MSFU');
 assert.equal(picker.rank([{symbol:'<script>',name:'bad'}],'bad').length,0);
 const description=picker.describe(rows[0],true,false).join(' ');
 assert.match(description,/SEC snapshot not covered/);assert.match(description,/not verified until loaded/);
 assert.match(picker.describe(rows[1],false,true).join(' '),/unavailable in public/);
});
test('worked mathematics agrees with hand calculations and retains extreme-case guards',()=>{
 assert.equal(lab.calculate('returns',110).values.at(-1),110);
 assert.ok(Math.abs(lab.calculate('portfolio',50,{},0).variance-.0325)<1e-12);
 assert.equal(lab.calculate('portfolio',60,{},-1).variance>=-1e-12,true);
 assert.ok(lab.calculate('portfolio',60,{},-1).values.every(Number.isFinite));
 assert.throws(()=>lab.calculate('portfolio',50,{},1.01));
 assert.ok(Math.abs(lab.calculate('regression',4).beta-.7)<1e-12);
 assert.ok(Math.abs(lab.calculate('regression',4).covariance-1.75)<1e-12);
 assert.ok(Math.abs(lab.calculate('tails',-8).var95-.066)<1e-12);
 assert.ok(Math.abs(lab.calculate('tails',-8).es95-.08)<1e-12);
 assert.ok(Math.abs(lab.calculate('brier',.2).brier-.17/3)<1e-12);
 assert.equal(lab.calculate('logistic',0).rows[1][1],'50.00%');
 assert.ok(Math.abs(lab.calculate('nlp',1).cosine-1/(1+(1+Math.log(1.5))**2))<1e-12);
 assert.throws(()=>lab.calculate('drawdown',0));
 const dc=lab.calculate('dcf',10,{financial:{metrics:{free_cash_flow_usd:-1}}});assert.equal(dc.ready,false);
});
test('all mathematical methods cite existing implementation and test files',()=>{
 assert.equal(lab.catalog.length,12);
 for(const row of lab.catalog)for(const file of row.slice(8))assert.ok(fs.statSync(path.resolve(__dirname,'../..',file)).isFile(),file);
});
