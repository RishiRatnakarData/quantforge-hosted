# QuantForge V5.6 — free hosted website, first integration

## Status

**Implemented in source, not deployed to any account.** You must complete the steps below. This is a staging/beta architecture; authentication and provider calls were tested with mocks, not live hosted credentials. Do not enter valuable real-money brokerage credentials. Only the Alpaca **market-data** key is used; QuantForge cannot place real brokerage trades.

| Feature | Public demo | Private account |
| --- | --- | --- |
| Website reachable with PC off | Yes: Cloudflare Pages | Yes, via the same Cloudflare URL and Render API |
| Login | None | Single preapproved Supabase Auth user |
| Data | Fictional prices, returns, holdings and fundamentals | Alpaca IEX/venue observations; Supabase private virtual portfolio |
| Portfolio | Browser-session example | Server-validated buys/sells, persistent virtual holdings/cash |
| Private research notes | Not saved | Encrypted transport; saved to user's RLS-protected Supabase row |
| Quant/DCF/company peers | Simplified JavaScript synthetic calculations | **Currently synthetic demo only** when these tabs are used; full V5.4 Python models remain available in local app, not yet connected here |
| Data persistence | None | Supabase PostgreSQL; never Render local disk |

## Architecture

```
                         One Pages site (same UI)
                        https://YOUR.pages.dev
                  /             |              \
        Public demo JS     My workspace    /api/* (Pages Function)
       fictional inputs        login                |
                                         secret-bearing HTTPS proxy
                                                    |
                                            Render FastAPI
                                          (owner auth required)
                                             /         \
                                     Supabase Auth  Supabase PostgREST (RLS)
                                            |                |
                                    verified JWT        private JSON state
                                             \
                                            Alpaca read-only quotes
```

The demo never calls Render on page load. When the user selects **My workspace**, only then does it check the private session. Only the single `OWNER_USER_ID` can use the private account. Render rejects API calls lacking the matching Cloudflare proxy secret. Cookies use `Secure`, `HttpOnly` and `SameSite=Strict`; mutations also require the configured public Origin and a custom CSRF-resistant header. Supabase tables have row-level security; the server uses only a publishable key and the owner's access JWT, **not** a service-role key. The Pages function passes `Set-Cookie` headers and explicitly disables response caching.

## Before deploying

1. Rotate any previously exposed Alpaca API key. Use read-only **market-data** credentials only.
2. Review `python tools/prepublish_check.py` output and `git status`. This catches common leaks but **does not** examine all Git history or guarantee security.
3. Use a **new** repository for this source unless you already checked the complete history. Never commit `.private/`, `.sqlite3`, `.dev.vars`, `.env`, key files, licensed Alpaca history, or personal screenshots.
4. You will need free accounts at Supabase, Render and Cloudflare. **Do not send any passwords, keys, JWTs or refresh tokens to anyone.**

## A. Supabase (authentication and persistence)

1. Create a free Supabase project. Under **SQL Editor**, run `cloud/supabase.sql`.
2. Under **Authentication → Providers → Email**, disable public sign-up, if shown. Create/confirm your own user under **Authentication → Users**. Use a strong unique password. **The V5.6 login does not implement an MFA challenge. Do not treat it as fully hardened production authentication until that is added and verified.**
3. Copy the Auth user UUID (**not the email**) as `OWNER_USER_ID`.
4. Under **Project Settings → API Keys**, copy the public **publishable** key (not the secret/service role key), and your Supabase project URL.
5. Do not put Alpaca keys in Supabase tables. The `quantforge_private_state` row contains your virtual portfolio and notes, never provider credentials.
6. On a free project, manage backups yourself and be aware it can pause after inactivity.

## B. GitHub / Render Python API

1. Upload this source to a carefully reviewed GitHub repository. Render requires Git repository integration for the steps below.
2. From Render → New → Web Service, connect the repository and choose the **Free** instance. Root directory is repository root.
3. **Build command:** `pip install -r cloud/requirements.txt`
4. **Start command:** `PYTHONPATH=src uvicorn cloud.api:app --host 0.0.0.0 --port $PORT`
5. Add these environment variables in **Render's secrets/environment UI**, not to repository files:
   - `SUPABASE_URL` = your HTTPS Supabase URL
   - `SUPABASE_PUBLISHABLE_KEY` = publishable key only
   - `OWNER_USER_ID` = your confirmed Supabase Auth user UUID
   - `ALPACA_API_KEY_ID` and `ALPACA_API_SECRET_KEY` = private market-data credentials
   - `QF_PROXY_SECRET` = 64 random hexadecimal characters (e.g. create privately with `py -3.12 -c "import secrets; print(secrets.token_hex(32))"`)
   - `PUBLIC_SITE_ORIGIN` = exact production Pages URL, e.g. `https://quantforge-demo.pages.dev`
6. Check that `https://YOUR-API.onrender.com/api/health` returns `{"status":"ok"...}`. Other API endpoints must return **403** if called directly without the private proxy header.
7. Render Free goes to sleep after idle periods and may take time to wake. Do **not** store state in Render local SQLite. This project uses Supabase for hosted persistence.

## C. Cloudflare Pages (one website)

**This release requires Git integration or Wrangler for Pages Functions; do not use simple ZIP drag-and-drop.**

1. In Cloudflare Pages create a new Git-integrated site from the same GitHub repo.
2. Build command: `python tools/build_unified_site.py`. Build output directory: `public`. Root directory: repo root.
3. The `functions/api/[[path]].js` file will proxy `/api/*` privately to Render. It is part of the Pages project and is *not* placed inside `public/`.
4. In Cloudflare Pages project **Settings → Variables and Secrets**, set:
   - `PRIVATE_API_ORIGIN` = `https://YOUR-API.onrender.com` (HTTPS only, no trailing slash)
   - `QF_PROXY_SECRET` = the **same** private random secret set on Render (store as an encrypted secret where supported)
5. Rebuild/redeploy after configuring variables. The pages.dev URL is your shared website: public demo plus **My workspace**.
6. If the site has a preview branch URL, private sign-in can be blocked by the exact-production-Origin check; this is intentional.

## D. Verify after deployment

- Open your Cloudflare Pages URL in a logged-out browser. The demo must load immediately and work even if Render is sleeping.
- Confirm the public Quant, DCF, and Company Peers pages clearly say **fictional**.
- Open **My workspace**. Sign in with the one confirmed Supabase user. All other users must be rejected.
- Save a private note and refresh the page. After opening **My workspace**, the note should be restored from Supabase.
- Fetch MSFT observed price. It must show **IEX** and its observation time, not claim consolidated live execution pricing.
- Make one small *virtual* buy while IEX timestamps are fresh (market hours), and verify cash and holdings persist across refresh, including from your phone.
- Sign out; make sure private positions cannot be read in a logged-out tab. Test stale quotes are refused for virtual trades.
- Verify your GitHub repository contains no `.private`, `.sqlite3`, credentials, or licensed quotes.

## Important limitations

- **No live end-to-end deployment has been verified here.** The API auth/storage/provider tests run against mocked upstream services. Deploy to staging, confirm every check, and conduct independent security review before relying on it.
- The private hosted portfolio is initially **new** (starts with $10,000 fictional cash). This upgrade **does not migrate** the existing local `.private/alpaca.sqlite3`. Local data is preserved.
- Full Python Quant/SEC DCF/ML analysis remains in the existing local V5.4 code. The current hosted UI exposes the public simplified fictional equivalents; **do not claim model parity**.
- This free setup does not guarantee 24/7 API availability, automatic backups, or zero risk. Render cold starts and Supabase inactivity pauses are expected free-tier limitations.
- This project does not provide price forecasts or investment advice. Do not call hypothetical outputs empirical risk estimates.
- Only fictional data belongs in the public demo; restricted Alpaca data must not be logged, cached publicly, or redistributed.
