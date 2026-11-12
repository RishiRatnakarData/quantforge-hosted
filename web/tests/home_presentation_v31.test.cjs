'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=path.join(__dirname,'..','site');
const html=fs.readFileSync(path.join(base,'site.template.html'),'utf8');
const js=fs.readFileSync(path.join(base,'research_private_shell_v23.js'),'utf8');
const css=fs.readFileSync(path.join(base,'research_guide_v30.css'),'utf8');
test('Home has one company-search action and all five section descriptions',()=>{
 const start=html.indexOf('id="qf-v23-landing"'),end=html.indexOf('</section>',start);
 assert.ok(start>=0&&end>start);
 const home=html.slice(start,end);
 assert.match(home,/id="qf24-home-search"/);
 assert.match(home,/id="qf24-home-find"/);
 assert.doesNotMatch(home,/id="qf-v23-open-research"/);
 assert.match(home,/research-case-study\.html/);
 for(const name of ['Explore','Compare','Models','Portfolio','Methods'])assert.match(home,new RegExp('<strong>'+name+'</strong>'));
});
test('Home revenue exhibit uses published SEC figures and has honest missing-data behavior',()=>{
 assert.match(html,/id="qf31-home-chart"/);
 assert.match(js,/window\.QFPublishedSEC\?\.companies/);
 assert.match(js,/Number\.isFinite\(r\?\.metrics\?\.revenue_usd\)/);
 assert.match(js,/SEC example is unavailable/);
 assert.match(css,/\.qf31-home-bars/);
});
test('Investment guide and thesis form are direct, visible sections rather than accordions',()=>{
 const guide=fs.readFileSync(path.join(base,'research_guide_ui_v30.js'),'utf8');
 assert.match(guide,/class="qf30-step"/);
 assert.doesNotMatch(guide,/<details/);
 assert.doesNotMatch(guide,/qf30-more-prompts/);
 assert.match(guide,/id="qf30-thesis-form"/);
});

test('Private session restoration requires an explicit preference and retains server MFA gate',()=>{
 const backend=fs.readFileSync(path.join(base,'..','..','cloud','api.py'),'utf8');
 const builder=fs.readFileSync(path.join(base,'..','..','tools','build_unified_site.py'),'utf8');
 const client=fs.readFileSync(path.join(base,'private.js'),'utf8');
 assert.match(builder,/id="qf31-remember-session"/);
 assert.match(client,/REMEMBER_PRIVATE_KEY/);
 assert.match(client,/if\(rememberPrivate\(\)/);
 assert.match(client,/setRememberPrivate\(false\)/);
 assert.match(client,/auth\/session/);
 assert.match(client,/wakePrivateService\(/);
 assert.match(client,/authEpoch/);
 assert.match(backend,/if not auth_state\(user, token\)\["signed_in"\]/);
 assert.match(backend,/httponly=True/);
 assert.match(backend,/samesite="strict"/);
});
test('Home is presented to fresh production visitors without hijacking deep links or local test navigation',()=>{
 assert.match(js,/function showFreshHome\(/);
 assert.match(js,/window\.addEventListener\('load',showFreshHome/);
 assert.match(js,/renderHomeEvidence\(\);[\s\S]+landing=true;/);
});
test('Home suppresses duplicate mobile creator footer but retains normal site footer',()=>{
 assert.match(css,/body\.qf31-home-active #qf28-mobile-credit\{display:none!important\}/);
 assert.match(html,/class="footerline"/);
});
