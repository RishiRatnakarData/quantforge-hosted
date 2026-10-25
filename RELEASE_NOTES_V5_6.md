# QuantForge V5.6 — unified website foundation

- Same Pages-hosted interface for public demo and private workspace entry.
- Public demo remains immediately accessible with synthetic data; no provider keys.
- Cloudflare Pages Function proxies same-origin `/api` calls with a server-held secret.
- Render FastAPI private API: single-owner Supabase Auth session, HttpOnly secure cookies, Origin/CSRF checks, PostgREST with user-scoped RLS, atomic version-checked private portfolio saves.
- Server-side Alpaca latest-trade lookups for stock/ETF IEX and supported crypto venues, with timestamp freshness checks preventing stale virtual trade fills.
- Persistent virtual buys, sells, and private notes (hosted state is separate from local SQLite).
- Tests for unauthorized access, invalid origin, stale quotes, owner mismatch, version conflicts, quote mismatch, and demo privacy.
- Honest limitation: hosted Quant/DCF/ML is simplified fictional JavaScript, **not yet integrated with the existing Python algorithms and actual private SEC/Alpaca history**.
- Staging-ready source only. No live cloud accounts connected by this release.
