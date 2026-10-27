# QuantForge platform audit - evidence, limitations and priority decisions

**Date:** 2026-10-27. **Scope:** User-exported V7.4 allocation research and reconstructed QuantForge source through V7.4. This is a source-focused review, **not** an authenticated production penetration test or independent certification of the deployment.

## Primary finding: allocation risk communication (fix in V7.5)

The real V7.4 export for the illustrative Amazon purchase reports:

- A proposed allocation leaving 96.5004% cash and a largest equity position of 2.5000% of total account value.
- Annualized observed static-weight portfolio volatility 0.3304% before and 1.0460% after, based on 250 reported sessions; approximately 0.716 percentage points higher after the proposed purchase.
- A cash-inclusive HHI change of -0.04825. The result is *not* evidence that market risk decreased. HHI includes virtual cash as one bucket; moving money from a very large cash bucket to a stock bucket mechanically reduces this HHI.

**Correction:** Show invested-only HHI alongside cash-inclusive allocation HHI, label zero invested capital as undefined, and explicitly explain the zero-price-return cash assumption. For crypto/mixed portfolios the stock annualization convention is not applied.

## Financial and data quality review

**Observed controls in reconstructed code:** cash-funded what-if validates budget<=cash, restricts stale/invalid quotes, carries forward unchanged total marked-to-market portfolio value, requires identical history dates across holdings before computing covariance-equivalent historical volatility, and prevents NaNs/nonpositive prices. Research exports omit amounts and holdings inventory. The walk-forward system has past-only fit checks and nonoverlapping evaluation; SEC-derived model assumptions and realized figures are labeled distinctly in the previous versions' tests and exports.

**Remaining model limitations:** Quotes may be from different sessions/exchanges; hypothetical fractional units assume no slippage/spreads/fees/taxes; distributions, risk-free return on cash, expected alpha, security borrow, and real-world suitability are not modeled; correlation and annualization depend on return definition and calendar. New risk ratios still do **not** indicate whether to buy any stock.

## API authorization and data privacy (source review, not live verification)

**Observed controls in reconstructed code:** Render API requires a proxy secret except on health; state-changing methods check configured Origin and an action header; private routes call owner verification using Supabase Auth and MFA AAL2; owner state reads/writes are version-checked through Supabase RLS; session cookies have Secure/HttpOnly/SameSite; Cloudflare proxy restricts the target Render origin and strips sensitive response headers. The what-if calculator doesn't call private trade or capital write APIs.

**Required live checks:** Confirm no unauthorized access through Render's direct hostname or Cloudflare; probe signed-out/expired/AAL1 sessions; verify owner isolation, MFA reset/recovery flows, cookie rotation, proxy secret parity, CORS/CSRF, rate limits, response caching, and no leakage in browser console and deployed assets. Do not copy secrets into GitHub or reports.

## CI, dependencies and deployment

**Evidence from user-provided V6.9/V7.0 logs:** Both CI matrix jobs passed, including full JavaScript regression testing and CSP integrity auditing; V7.4 success was user-confirmed, not independently rechecked from its CI log here. Reconstructed repo versions are not guaranteed byte-identical to the deployed commit. Dependencies emitted nonblocking warnings about Starlette TestClient/httpx and NumPy timedelta; track them as maintenance items, avoid untested upgrades.

**Next operational checks:** Compare GitHub HEAD, Cloudflare Pages deployed commit, and Render service commit; verify owner-only routes, cold starts, failure modes and timeouts with rate-limited providers; test full mobile keyboard and screen-reader navigation; run a backup/recovery rehearsal for Supabase state.

## Public technical presentation

The public Research systems page and source README now explain SEC ingestion, mathematical optimization, walk-forward testing, model limitations, architectural boundary, and CI. Verify current live copy on desktop and mobile and ensure claims match source and reproducible results. Do not publish personal holdings, provider-licensed historical prices, secrets, or selected account details as demonstration content.

## Prioritized roadmap

**P0:** Prevent misleading concentration/risk labels (this V7.5 patch). **P1:** Validate live deployed authorization boundaries and deployment SHA parity. **P1:** Verify accounting and quote staleness under adversarial inputs. **P2:** Mobile accessibility walkthrough and graceful provider failures. **P2:** Public methods and GitHub documentation claims synchronized to reproducible evidence. **Future, separate:** Fair-value methodology, sector exposures, risk budgeting and tax assumptions before treating investment-idea scores as allocation advice.
