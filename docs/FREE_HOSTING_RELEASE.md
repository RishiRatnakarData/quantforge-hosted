# Free-host release continuation

Baseline: validated candidate 8c04ee973825f1c7fa90d719d2a0a1f03a01106e. This document records deployment preparation; it does not assert a migration or production publication occurred.

## Observed Render limitation

Rechecks found the existing Free service unsuspended, maintenance off, correct health path and unchanged source. Primary Pages health returns safe 503 JSON. Direct upstream returns 429 HTML with cf-mitigated: challenge; no later FastAPI startup is present after the clean shutdown. These observations locate the failure before application authentication. They do not establish the hosting provider's internal trigger. Replaying credentials, suppressing MFA, spoofing a browser, disabling provider protection, restarting on a timer or keepalive polling are not acceptable fixes.

Render documents [15-minute inactivity spin-down and roughly minute-long resume](https://render.com/docs/free). Its [HTTP error guide](https://render.com/docs/troubleshooting-deploys#http-error-codes) distinguishes startup unavailability from inbound rate limiting. The current path has not demonstrated reliable recovery, so temporary healthy JSON would not alone close acceptance.

## Free alternatives checked

| Option | Verified conditions and technical fit | Decision |
| --- | --- | --- |
| Existing Render Free | Existing owner identity/storage retained; service sleeps and currently presents a hosting challenge before app startup | Preserve for rollback; no paid upgrade or artificial keepalive |
| Vercel Hobby | [Free plan](https://vercel.com/docs/plans/hobby) with finite included CPU/memory/invocation quotas; exhaustion generally pauses service rather than charging overages. [Native FastAPI support](https://vercel.com/docs/functions/runtimes/python), Python 3.12, standard bundle limit 500 MB, maximum Hobby invocation 300 seconds | Best candidate for this personal application, conditional on verifying the connected account is Hobby with no paid add-ons or trials |
| Cloudflare Python Workers Free | [Standard-library restrictions](https://developers.cloudflare.com/workers/languages/python/stdlib/) include nonfunctional threading; existing API uses synchronous FastAPI handlers and requests, plus thread locks. Free [CPU limits](https://developers.cloudflare.com/workers/platform/limits/) also require measured compatibility | Not a drop-in move; do not rush an auth/accounting rewrite |
| Koyeb | [Pricing FAQ](https://www.koyeb.com/docs/faqs/pricing) requires a credit card and describes a preauthorization and selected-plan charges | Excluded by the absolute zero-cost/card constraint |
| Hugging Face compute Spaces | Current [Spaces documentation](https://huggingface.co/docs/hub/spaces-overview) says creating compute Spaces requires a paid plan, despite CPU Basic having no hourly charge; source-private/public-runtime protection also requires paid visibility | Excluded |
| PythonAnywhere | [Free-account outbound restrictions](https://help.pythonanywhere.com/pages/403ForbiddenError/) constrain external API access; existing authenticated Supabase/Alpaca/SEC requests must all work | Not selected over the directly supported FastAPI alternative |

No new hosting resource, billing plan, trial, subscription, database or API purchase has been created. Free means bounded availability within genuine free quotas, not unlimited uptime. The existing frontend remains on Pages and Supabase remains the record system; no data migration or owner-record write is required.

## Implemented adapter

`tools/build_free_backend.py` builds a fresh, explicit 17-file source allowlist into an isolated deployment folder. It excludes credentials, local databases, account records, licensed caches and unrelated development dependencies. It refuses nonempty destinations and dirty runtime sources. The generated app imports the existing FastAPI application; identity, AAL2 checks, cookies, RLS, Decimal arithmetic, concurrency and idempotency stay in the same implementation. Source hashes and the full committed revision are recorded in release.json. The API health route recognizes Render, Vercel and packaged-release revision metadata, validating the full SHA format.

The proxy accepts only configured HTTPS Render/Vercel hostnames without credentials, ports or path injection. It does not discover arbitrary upstream hosts, replay writes, forward hosting challenge cookies or expose the proxy secret. Adding a supported hostname does not itself route production anywhere new.

## Cutover gates

1. Verify an authenticated Vercel personal Hobby account and zero paid add-ons/trial/usage billing before creating a resource. New account login/terms/connection must remain owner-controlled.
2. Build from the final committed source; deploy the small backend artifact with its existing API security configuration supplied through supported secret storage. Never print or commit values. Secure transfer of existing configuration must be available; do not replace credentials with placeholders.
3. Verify the deployed SHA, contract, no-store headers and anonymous denial, then test the configured same-origin path. Keep existing Supabase records and MFA enrollment unchanged.
4. Complete full CI, public browser regression, protected API checks and deployment-size/runtime verification. No simulated test substitutes for an actual host invocation or owner MFA.
5. Switch the Pages PRIVATE_API_ORIGIN only after the backend gate passes; merge/publish the validated frontend using the normal workflow and verify its exact production deployment. Leave Render available as rollback without sending periodic pings.
6. Verify idle-to-request behavior on the new serverless host, bounded failures and owner-controlled MFA when available. Preserve the prior backend origin and source revision for rollback.

If Vercel cannot be authenticated through authorized access, or secrets cannot be transferred securely, preserve this working candidate and report that specific missing permission. Do not create a chargeable team or claim a deployed backend.
