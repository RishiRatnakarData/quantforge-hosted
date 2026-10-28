'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..','..');
const html=fs.readFileSync(path.join(root,'web/site/site.template.html'),'utf8');
const app=fs.readFileSync(path.join(root,'web/site/app.js'),'utf8');
const builder=fs.readFileSync(path.join(root,'tools/build_unified_site.py'),'utf8');
const nav=html.split('<nav id="navigation" aria-label="Main navigation">')[1].split('</nav>')[0];

test('all nine public navigation routes are visible without accordions',()=>{
 assert.equal((nav.match(/class="qf-nav-section"/g)||[]).length,3);
 assert.doesNotMatch(nav,/<details|<summary| hidden\b/);
 const routes=[...nav.matchAll(/data-page="([^"]+)"/g)].map(m=>m[1]);
 assert.deepEqual(routes,['overview','sec','lab','portfolio','quant','valuation','ml','systems','methods']);
});
test('the homepage directs public reviewers to data, models and engineering',()=>{
 const home=html.split('id="page-overview"')[1].split('</section>')[0];
 for(const route of ['sec','lab','systems'])assert.match(home,new RegExp(`data-go="${route}"`));
 assert.doesNotMatch(home,/data-go="private"/);
 assert.match(home,/View GitHub source and tests/);
});
test('public routing and private MFA are preserved',()=>{
 assert.match(app,/document\.querySelectorAll\('\.nav-btn'\)/);
 assert.doesNotMatch(app,/details\.qf-nav-fold/);
 assert.match(builder,/data-page="private">Private workspace/);
 assert.match(builder,/id="private-mfa-code"/);
});
