'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const brief=require('../site/private_research_brief_v93.js');
function fixture(){
 const assessment={symbol:'ABC',selection:['ABC','DEF'],orchestration:{models:[
  {key:'history',title:'Price history',status:'completed',required:true,scope:'Matched observations',detail:'Loaded 270 sessions',source:'Observed closes',period:{start:'2025-01-03',end:'2026-01-02',sessions:270}},
  {key:'french',title:'Official FF3',status:'ineligible',required:false,scope:'Candidate exposures',detail:'No local import',source:'Kenneth French Library'}
 ]},portfolio:{cash:450000,holdings:{ABC:120}},quote:{price:72.25},token:'SHOULD_NOT_EXPORT'};
 const review={schema:'quantforge.decision-review.v9.2',symbol:'ABC',action:'Research further',readiness:'Conditional / caution',blocked:false,
  reason:'Observed evidence conflicts.',asOf:'2026-10-29',policy:'explicit-screens.v1',
  coverage:[{key:'history',name:'Observed history',status:'available',scope:'Price',detail:'Enough history',source:'Observed data'},
    {key:'factors',name:'Independent factors',status:'unavailable',scope:'Optional',detail:'Not imported',source:'No source'}],
  comparison:{ready:true,period:{start:'2025-01-03',end:'2026-01-02',observations:270},rows:[{symbol:'ABC',totalChange:.12555,maxDrawdown:-.28},{symbol:'DEF',totalChange:-.1,maxDrawdown:-.45}]},
  pro:['Revenue improved'],con:['Drawdown remains large'],flags:['Risk contradicts growth'],next:['Review valuation'],limitations:['Historical observations only'],
  constraints:{risk:'moderate',horizon:'long',maxWeight:.35,maxDrawdown:.30}};
 return {assessment,review};
}
test('one connected packet uses the actual assessment, comparison, model ledger and sources',()=>{
 const {assessment,review}=fixture();const x=brief.summarize(assessment,review,{ABC:'A Corp',DEF:'D Corp'},['ABC','DEF']);
 assert.equal(x.candidate,'A Corp');assert.equal(x.action,review.action);assert.deepEqual(x.universe.map(u=>u.symbol),['ABC','DEF']);
 assert.equal(x.modelCoverage.completed,1);assert.equal(x.modelCoverage.ineligible,1);
 assert.equal(x.models[0].route,'research');assert.equal(x.models[1].route,'candidate');
 assert.deepEqual(x.missing,['Independent factors']);assert.equal(x.comparison.assets[0].priceChangePercent,12.55);
 assert.equal(x.comparison.assets[1].maxDrawdownPercent,-45);
});
test('does not create new investment recommendation, expected return or probability',()=>{
 const {assessment,review}=fixture();const x=brief.summarize(assessment,review,{},['ABC','DEF']);
 assert.equal(x.action,'Research further');assert.equal(x.blocked,false);
 assert.equal(x.comparison.basis.includes('no dividends'),true);
 assert.equal(JSON.stringify(x).includes('expectedReturn'),false);
});
test('required failures are transparently included and hold remains intact',()=>{
 const {assessment,review}=fixture();assessment.orchestration.models[0].status='failed';review.blocked=true;review.action='Insufficient evidence';
 const x=brief.summarize(assessment,review,{},['ABC','DEF']);assert.equal(x.blocked,true);
 assert.deepEqual(x.mandatoryMissing,['Price history']);assert.equal(x.modelCoverage.failed,1);
 assert.equal(x.action,'Insufficient evidence');
});
test('no price comparison when data does not support one',()=>{
 const {assessment,review}=fixture();review.comparison={ready:false,reason:'Misaligned prices'};
 const x=brief.summarize(assessment,review,{},['ABC','DEF']);assert.equal(x.comparison,null);
});
test('missing or conflicting candidate evidence refuses to create report',()=>{
 const {assessment,review}=fixture();assert.throws(()=>brief.summarize(null,review,{},['ABC','DEF']));
 assessment.symbol='DIFFERENT';assert.throws(()=>brief.summarize(assessment,review));
});
test('briefing and export cannot leak original holdings, balances, quotes, raw arrays or tokens',()=>{
 const {assessment,review}=fixture();const out=JSON.stringify(brief.summarize(assessment,review,{},['ABC','DEF']));
 for(const secret of ['SHOULD_NOT_EXPORT','450000','72.25','120','token','holdings','cash','rawPrices'])assert.equal(out.includes(secret),false,secret);
});
test('pure module contains no fetch, storage, brokerage order or external AI calls',()=>{
 const source=fs.readFileSync(path.join(__dirname,'../site/private_research_brief_v93.js'),'utf8');
 for(const banned of ['fetch(', 'localStorage','sessionStorage','XMLHttpRequest',"api('private/trade'",'alpaca.markets','openai.com'])assert.equal(source.includes(banned),false,banned);
});
test('user-selected symbols and names are bounded before rendering',()=>{
 const {assessment,review}=fixture();const x=brief.summarize(assessment,review,{ABC:'Z'.repeat(2000)},['ABC','DEF']);
 assert.equal(x.candidate.length,350);
});
test('invalid model statuses cannot impersonate completed',()=>{
 const {assessment,review}=fixture();assessment.orchestration.models[0].status='success!';
 const out=brief.summarize(assessment,review,{},['ABC','DEF']);assert.equal(out.models[0].status,'ineligible');assert.equal(out.modelCoverage.completed,0);
});
