const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'../..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');

test('navigation uses readable names while preserving all stable routes',()=>{
 const html=read('web/site/site.template.html');
 for(const [slug,label] of Object.entries({lab:'Analysis dashboard',quant:'Risk &amp; allocation',valuation:'DCF scenarios',ml:'Peer comparison',systems:'Research methods',methods:'Data &amp; engineering'})){
  assert.ok(html.includes(`data-page="${slug}">${label}</button>`));
  assert.ok(html.includes(`id="page-${slug}"`));
 }
});

test('authenticated pages keep nine unique identifiers and portfolio history controls',()=>{
 const html=read('tools/build_unified_site.py');
 for(const tab of ['home','trade','ideas','research','optimization','backtest','walkforward','valuation','settings']){
  assert.equal((html.match(new RegExp(`data-private-view="${tab}"`,'g'))||[]).length,1);
  assert.ok((html.match(new RegExp(`data-private-tab="${tab}"`,'g'))||[]).length>=1);
 }
 assert.ok(html.includes('id="private-history-load"'));
 assert.ok(html.includes('id="private-mfa-submit"'));
});

test('public findings name their inputs rather than presenting fake market results',()=>{
 const html=read('web/site/site.template.html');
 const lab=read('web/site/public_lab_v77.js');
 assert.match(html,/SEC: reported annual company figures/);
 assert.match(html,/Portfolio: simulated return inputs/);
 assert.match(lab,/Simulated comparison:/);
 assert.match(lab,/Source: SEC Company Facts/);
});
