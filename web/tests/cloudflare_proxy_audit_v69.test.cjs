'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const pathToProxy = path.join(__dirname, '../../functions/api/[[path]].js');
const source = fs.readFileSync(pathToProxy, 'utf8');
const modulePromise = import('data:text/javascript;base64,' + Buffer.from(source, 'utf8').toString('base64'));
const env = {PRIVATE_API_ORIGIN: 'https://quantforge-private-api.onrender.com', QF_PROXY_SECRET: 'fixture-secret-never-expose'};

async function callWithMock(request, mock) {
  const original = globalThis.fetch;
  globalThis.fetch = mock;
  try {
    const {onRequest} = await modulePromise;
    return await onRequest({request, env});
  } finally {
    globalThis.fetch = original;
  }
}

test('proxy refuses missing upstream secret and does not contact provider', async () => {
  const {onRequest} = await modulePromise;
  const r = await onRequest({request: new Request('https://quantforge-648.pages.dev/api/private/state'),
    env: {PRIVATE_API_ORIGIN: env.PRIVATE_API_ORIGIN, QF_PROXY_SECRET: ''}});
  assert.equal(r.status, 503);
  assert.equal(r.headers.get('Cache-Control'), 'no-store');
});

test('proxy only allows configured HTTPS Render origin', async () => {
  const {onRequest} = await modulePromise;
  const r = await onRequest({request: new Request('https://quantforge-648.pages.dev/api/health'),
    env: {...env, PRIVATE_API_ORIGIN: 'https://example.com'}});
  assert.equal(r.status, 503);
});

test('proxy forwards required auth and action headers while withholding private proxy secret from response', async () => {
  let seen;
  const request = new Request('https://quantforge-648.pages.dev/api/private/notes', {
    method:'POST', headers:{'Content-Type':'application/json','Cookie':'qf_access=fixture', 'Origin':'https://quantforge-648.pages.dev',
      'X-QF-Action':'1', 'Authorization':'some-irrelevant-client-token'}, body: JSON.stringify({expected_version:1,notes:[],watchlist:[]})
  });
  const mock = async (url, init) => {
    seen = {url, init};
    return new Response(JSON.stringify({version:2}), {status:200, headers:{
      'Content-Type':'application/json', 'Access-Control-Allow-Origin':'*', 'X-Internal-Trace':'private',
      'Set-Cookie':'qf_access=newsession; Secure; HttpOnly; SameSite=Strict; Path=/api'}});
  };
  const result = await callWithMock(request, mock);
  assert.equal(seen.url, 'https://quantforge-private-api.onrender.com/api/private/notes');
  assert.equal(seen.init.headers.get('x-qf-proxy-secret'), env.QF_PROXY_SECRET);
  assert.equal(seen.init.headers.get('cookie'), 'qf_access=fixture');
  assert.equal(seen.init.headers.get('x-qf-action'), '1');
  assert.equal(seen.init.headers.get('authorization'), null);
  assert.equal(seen.init.redirect, 'manual');
  assert.equal(result.headers.get('Access-Control-Allow-Origin'), null);
  assert.equal(result.headers.get('X-Internal-Trace'), null);
  assert.equal(result.headers.get('Cache-Control'), 'no-store');
  assert.equal(result.headers.get('X-Content-Type-Options'), 'nosniff');
  assert.equal(result.headers.get('Set-Cookie').includes('HttpOnly'), true);
  assert.equal((await result.text()).includes(env.QF_PROXY_SECRET), false);
});

test('proxy returns safe unavailable response on upstream network failure', async () => {
  const r = await callWithMock(new Request('https://quantforge-648.pages.dev/api/private/state'),
    async () => {throw Error('private-error-with-credentials');});
  assert.equal(r.status, 503);
  assert.equal(r.headers.get('Cache-Control'), 'no-store');
  assert.equal((await r.text()).includes('private-error-with-credentials'), false);
});

test('hosting HTML is unavailable rather than an authentication result, without upstream cookies', async () => {
  for (const status of [200, 403, 503]) {
    const result = await callWithMock(new Request('https://quantforge-648.pages.dev/api/auth/session'),
      async () => new Response('<html>Hosting verification / internal detail</html>', {status, headers:{
        'Content-Type':'text/html', 'Set-Cookie':'hosting-challenge=unrelated; Path=/'}}));
    assert.equal(result.status, 503);
    assert.equal(result.headers.get('Content-Type'), 'application/json');
    assert.equal(result.headers.get('Cache-Control'), 'no-store');
    assert.equal(result.headers.get('Set-Cookie'), null);
    assert.deepEqual(await result.json(), {error:'Private service is currently unavailable.'});
  }
});

test('real JSON authentication denial is preserved for the non-retry gate', async () => {
  for (const status of [401, 403, 429]) {
    const result = await callWithMock(new Request('https://quantforge-648.pages.dev/api/auth/login'),
      async () => new Response(JSON.stringify({detail:'Denied'}), {status,
        headers:{'Content-Type':'application/json'}}));
    assert.equal(result.status, status);
    assert.deepEqual(await result.json(), {detail:'Denied'});
  }
});


test('only readiness GETs have a bounded upstream signal; writes are forwarded once', async () => {
 for (const [route,method] of [['health','GET'],['auth/login','POST'],['private/trade','POST']]) {
  let calls=0,seen;
  const response=await callWithMock(new Request('https://quantforge-648.pages.dev/api/'+route,{method,...(method==='POST'?{body:'{}'}:{})}),async(_url,init)=>{calls++;seen=init;return new Response('{}',{headers:{'content-type':'application/json'}});});
  assert.equal(response.status,200);assert.equal(calls,1);assert.equal(Boolean(seen.signal),route==='health');
 }
});
test('a stalled readiness fetch returns safe 503 after abort without retrying upstream', async () => {
 const timer=globalThis.setTimeout;let calls=0;
 globalThis.setTimeout=(fn,delay)=>timer(fn,delay===70000?1:delay);
 try {
  const response=await callWithMock(new Request('https://quantforge-648.pages.dev/api/health'),async(_url,init)=>{calls++;return new Promise((_resolve,reject)=>init.signal.addEventListener('abort',()=>reject(Error('internal timeout')),{once:true}));});
  assert.equal(response.status,503);assert.equal(calls,1);assert.equal(response.headers.get('Cache-Control'),'no-store');
  assert.deepEqual(await response.json(),{error:'Private service is currently unavailable.'});
 } finally {globalThis.setTimeout=timer;}
});

test('non-JSON hosting 429 is classified separately without forwarding challenge cookies',async()=>{
 const r=await callWithMock(new Request('https://quantforge-648.pages.dev/api/health'),async()=>new Response('<html>Just a moment</html>',{status:429,headers:{'content-type':'text/html','cf-mitigated':'challenge','set-cookie':'unrelated=challenge'}}));
 assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null);
 assert.equal((await r.json()).code,'hosting_verification');
});


test('readiness diagnostics expose only classification and numeric status, never upstream headers or secrets', async () => {
 const headers={'Content-Type':'text/html','cf-mitigated':'challenge','Set-Cookie':'sensitive=value','X-Internal-Trace':'private-details'};
 for (const route of ['health','auth/session']) {
  const r=await callWithMock(new Request('https://quantforge-648.pages.dev/api/'+route),async()=>new Response('<html>private diagnostic body</html>',{status:429,headers}));
  assert.equal(r.status,503);
  assert.equal(r.headers.get('X-QF-Readiness'),route==='health'?'upstream-verification':null);
  assert.equal(r.headers.get('X-QF-Upstream-Status'),route==='health'?'429':null);
  for(const h of ['cf-mitigated','Set-Cookie','X-Internal-Trace','x-qf-proxy-secret'])assert.equal(r.headers.get(h),null);
  assert.deepEqual(await r.json(),{error:'Private service is currently unavailable.',code:'hosting_verification'});
 }
 const r=await callWithMock(new Request('https://quantforge-648.pages.dev/api/health'),async()=>{throw Error('sensitive upstream URL');});
 assert.equal(r.headers.get('X-QF-Readiness'),'upstream-network');
 assert.equal(r.headers.get('X-QF-Upstream-Status'),null);
 assert.doesNotMatch(await r.text(),/sensitive/);
});


test('readiness permits a slow cold start without replay and stays inside the browser budget', async () => {
 const originalTimer=globalThis.setTimeout;let calls=0,budget;
 globalThis.setTimeout=(fn,delay)=>{budget=delay;return originalTimer(fn,delay/1000);};
 try {
  const r=await callWithMock(new Request('https://quantforge-648.pages.dev/api/health'),async(_url,init)=>{
   calls++;return new Promise((resolve,reject)=>{
    init.signal.addEventListener('abort',()=>reject(Error('premature abort')),{once:true});
    originalTimer(()=>resolve(new Response('{"status":"ok"}',{headers:{'content-type':'application/json'}})),32);
   });
  });
  assert.equal(budget,70000);assert.equal(calls,1);assert.equal(r.status,200);
  assert.deepEqual(await r.json(),{status:'ok'});
  const client=fs.readFileSync(path.join(__dirname,'../site/private.js'),'utf8');
  assert.match(client,/Math\.min\(75000,deadline-Date\.now\(\)\)/);
  assert.match(client,/const deadline=Date\.now\(\)\+120000/);
 } finally {globalThis.setTimeout=originalTimer;}
});
