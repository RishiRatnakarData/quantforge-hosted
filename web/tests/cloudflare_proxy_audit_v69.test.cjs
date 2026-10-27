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
