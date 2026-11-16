/** Same-origin API proxy for Cloudflare Pages. No quote caching. */
export async function onRequest(context) {
  const { request, env } = context;
  const origin = String(env.PRIVATE_API_ORIGIN || '').replace(/\/$/, '');
  const secret = String(env.QF_PROXY_SECRET || '');
  if (!/^https:\/\/[a-zA-Z0-9.-]+$/.test(origin) || !secret || !origin.endsWith('.onrender.com')) {
    return new Response(JSON.stringify({ error: 'Private API not configured' }), {
      status: 503, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }
    });
  }
  const url = new URL(request.url);
  if (!url.pathname.startsWith('/api/')) return new Response('Not found', { status: 404 });
  const upstream = origin + url.pathname + url.search;
  const headers = new Headers();
  for (const h of ['content-type', 'cookie', 'x-qf-action', 'origin']) {
    if (request.headers.has(h)) headers.set(h, request.headers.get(h));
  }
  headers.set('x-qf-proxy-secret', secret);
  // Identify the actual intermediary software, without forwarding a browser identity.
  headers.set('user-agent', 'QuantForge/2.0 (Cloudflare Pages API proxy)');
  // Render expects Origin to be exactly the Pages site for state-changing calls.
  if (!headers.has('origin') && !['GET', 'HEAD'].includes(request.method)) {
    headers.set('origin', url.origin);
  }
  // Allow a normal Render Free cold start within the browser readiness deadline.
  // Other requests, especially writes, are forwarded once and never replayed.
  const probe = request.method === 'GET' && url.pathname === '/api/health';
  const controller = probe ? new AbortController() : null;
  const timer = controller ? setTimeout(() => controller.abort(), 70000) : null;
  const readinessHeaders = (reason, status) => probe ? {
    'X-QF-Readiness': reason,
    ...(status === undefined ? {} : {'X-QF-Upstream-Status': String(status)})
  } : {};
  let result;
  try {
    result = await fetch(upstream, {
      method: request.method,
      headers,
      body: ['GET', 'HEAD'].includes(request.method) ? undefined : request.body,
      redirect: 'manual',
      ...(controller ? {signal: controller.signal} : {}),
    });
  } catch (_e) {
    return new Response(JSON.stringify({ error: 'Private service is currently unavailable.' }), {
      status: 503, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store',
        ...readinessHeaders(controller?.signal.aborted ? 'upstream-timeout' : 'upstream-network') }
    });
  }
  finally { if (timer !== null) clearTimeout(timer); }
  // Hosting interstitials (including a 200/403 HTML challenge) are not API
  // authentication decisions. Do not forward their markup or cookies.
  if (!(result.headers.get('content-type') || '').toLowerCase().includes('application/json')) {
    const verification = result.headers.get('cf-mitigated') === 'challenge';
    const limited = !verification && result.status === 429;
    const retryHeader = result.headers.get('retry-after') || '';
    const retrySeconds = /^\d+$/.test(retryHeader) ? Number(retryHeader) : Math.ceil((Date.parse(retryHeader) - Date.now()) / 1000);
    // Never retry earlier than the provider requests; long waits exhaust the client deadline.
    const retryAfter = Number.isFinite(retrySeconds) && retrySeconds >= 0 ? Math.max(30, Math.min(86400, retrySeconds)) : 30;
    return new Response(JSON.stringify({ error: 'Private service is currently unavailable.',
      ...(verification ? {code: 'hosting_verification'} : limited ? {code: 'hosting_rate_limited', retry_after_seconds: retryAfter} : {}) }), {
      status: 503, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
        ...readinessHeaders(verification ? 'upstream-verification' : limited ? 'upstream-rate-limit' : 'upstream-non-json', result.status),
        ...(probe ? {'X-QF-Upstream-Challenge': result.headers.get('cf-mitigated') === 'challenge' ? 'confirmed' : 'not-reported'} : {}) }
    });
  }
  const outgoing = new Headers();
  for (const h of ['content-type', 'content-security-policy']) {
    if (result.headers.has(h)) outgoing.set(h, result.headers.get(h));
  }
  const cookies = typeof result.headers.getSetCookie === 'function' ? result.headers.getSetCookie() : [];
  for (const item of cookies) outgoing.append('Set-Cookie', item);
  if (!cookies.length && result.headers.has('set-cookie')) outgoing.append('Set-Cookie', result.headers.get('set-cookie'));
  outgoing.set('Cache-Control', 'no-store');
  outgoing.set('X-Content-Type-Options', 'nosniff');
  return new Response(result.body, { status: result.status, headers: outgoing });
}
