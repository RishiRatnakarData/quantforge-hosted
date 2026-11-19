"use strict";
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
require('../site/research_models_core_v22.js');
require('../site/research_exhibits_v24.js');
require('../site/research_evidence_v26.js');
require('../site/methods_lab_v27.js');

function publicReferences(html,minimum){
 assert.doesNotMatch(html,/Repository access is restricted/i);
 const links=[...html.matchAll(/<a\b[^>]*href="([^"]+)"[^>]*>/g)];
 assert.ok(links.length>=minimum,'Implementation/test references must be actionable links');
 for(const [tag,href] of links){
  const prefix='https://github.com/RishiRatnakarData/quantforge-hosted/blob/main/';
  assert.ok(href.startsWith(prefix),href);
  const relative=decodeURIComponent(href.slice(prefix.length));
  const target=path.resolve(__dirname,'../..',relative);
  assert.ok(target.startsWith(path.resolve(__dirname,'../..')+path.sep));
  assert.ok(fs.statSync(target).isFile(),relative);
  assert.doesNotMatch(href,/[?#]/);
  assert.match(tag,/target="_blank"/);
  assert.match(tag,/rel="noopener noreferrer"/);
  assert.match(tag,/referrerpolicy="no-referrer"/);
 }
}
test('worked mathematics renders public implementation and regression links',()=>publicReferences(globalThis.QFMethods27.statistical({}),2));
test('statistical exhibits render existing public implementation links',()=>publicReferences(globalThis.QFExhibits24.methods('statistical',{}),5));
test('engineering evidence accurately describes its publicly reviewable source',()=>publicReferences(globalThis.QFEvidence26.methods('engineering',{}),4));

require('../site/research_core_v20.js');
test('Methods ledger shows the latest dated operating income, retaining negative and missing facts',()=>{
 const original=globalThis.QFPublishedSEC;
 const amounts=[1.234e9,-.25e9,null,0];
 globalThis.QFPublishedSEC={as_of:'2026-10-25',companies:['MSFT','AMD','ADBE','AMAT'].map((symbol,i)=>({symbol,name:symbol,annual:[
  {fiscal_end:'2024-06-30',metrics:{revenue_usd:1e9,operating_income_usd:777e6},sources:{}},
  {fiscal_end:'2025-06-30',metrics:{revenue_usd:2e9,operating_income_usd:amounts[i]},sources:{}}
 ]}))};
 try{
  const html=globalThis.QFMethods27.overview({});
  for(const [symbol,expected] of [['MSFT','1.234'],['AMD','-0.25'],['ADBE','Unavailable'],['AMAT','0']]){
   const row=[...html.matchAll(new RegExp('<tr><td>'+symbol+'</td>(.*?)</tr>','g'))].at(-1)[1];
   assert.ok(row.endsWith('<td>'+expected+'</td>'),row);
  }
 }finally{globalThis.QFPublishedSEC=original;}
});
