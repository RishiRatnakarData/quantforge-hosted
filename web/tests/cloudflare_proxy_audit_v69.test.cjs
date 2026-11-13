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
 globalThis.setTimeout=(fn,delay)=>timer(fn,delay===8000?1:delay);
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


test('configured Vercel HTTPS origin retains the same guarded single-hop proxy',async()=>{
 const {onRequest}=await modulePromise;
 const previous=globalThis.fetch;let seen;
 globalThis.fetch=async(url,init)=>{seen={url,init};return new Response('{}',{headers:{'content-type':'application/json'}});};
 try{
  const r=await onRequest({request:new Request('https://quantforge-648.pages.dev/api/private/state'),env:{...env,PRIVATE_API_ORIGIN:'https://quantforge-private-api-fixture.vercel.app'}});
  assert.equal(r.status,200);assert.equal(seen.url,'https://quantforge-private-api-fixture.vercel.app/api/private/state');
  assert.equal(seen.init.headers.get('x-qf-proxy-secret'),env.QF_PROXY_SECRET);
  assert.equal(r.headers.get('x-qf-proxy-secret'),null);
 }finally{globalThis.fetch=previous;}
});
test('alternative origins do not admit credentials ports HTTP or lookalike domains',async()=>{
 const {onRequest}=await modulePromise;
 for(const origin of ['http://quantforge.vercel.app','https://user:password@quantforge.vercel.app','https://quantforge.vercel.app:443','https://quantforge.vercel.app.example.org','https://vercel.app']){
  const r=await onRequest({request:new Request('https://quantforge-648.pages.dev/api/health'),env:{...env,PRIVATE_API_ORIGIN:origin}});
  assert.equal(r.status,503,origin);
 }
});
