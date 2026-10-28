'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..','..');
const html=fs.readFileSync(path.join(root,'web/site/site.template.html'),'utf8');
const builder=fs.readFileSync(path.join(root,'tools/build_unified_site.py'),'utf8');
const pub=fs.readFileSync(path.join(root,'web/site/app.js'),'utf8');
const priv=fs.readFileSync(path.join(root,'web/site/private.js'),'utf8');
test('critical public anchors and model pages remain',()=>{
 for(const name of ['overview','sec','lab','portfolio','quant','valuation','ml','methods','systems']){
  assert.ok(html.includes(`id="page-${name}"`));
  assert.ok(html.includes(`data-page="${name}"`));
 }
 assert.equal((html.match(/class="qf-nav-section"/g)||[]).length,3);
});
test('public pages remain visible while private groups open for activated pages',()=>{
 assert.doesNotMatch(pub,/activeButton\?\.closest\('details\.qf-nav-fold'\)/);
 assert.match(priv,/activeButton\?\.closest\('details\.private-nav-group'\)/);
});
test('private MFA, guide, and research selection remain',()=>{
 for(const name of ['private-login','private-mfa','private-guide-card-v79','private-research-dataset','private-research-loaded']){
  assert.ok(builder.includes(`id="${name}"`));
 }
});
