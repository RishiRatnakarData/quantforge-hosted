# Current architecture

Authoritative for the consolidated QuantForge 2.0 application. Historical Render and local-only documents are development records, not current operating instructions.

```mermaid
flowchart LR
  Browser[Shared five-section browser interface] --> Pages[Cloudflare Pages and same-origin API proxy]
  SEC[Published annual SEC facts] --> Browser
  Pages --> API[Vercel Hobby FastAPI]
  API --> Auth[Supabase identity and authenticator MFA]
  API --> State[Versioned owner records in Supabase]
  API --> Alpaca[Entitled Alpaca listings, quotes, history and news]
  API --> EDGAR[Bounded SEC Company Facts reads]
```

Public research runs from published SEC statements and clearly labeled deterministic market demonstrations. Public code never needs owner credentials. Private access uses the same interface with an unmistakable mode banner, owner verification and authenticated provider observations. Losing provider access withholds dependent results; it does not replace them with synthetic prices.

The browser sends same-origin requests to Pages Functions. The proxy validates an exact configured upstream origin, removes client-supplied privileged headers, supplies its server-side authentication header and restricts origin, cookies and forwarded responses. FastAPI independently verifies the proxy and owner session. Supabase MFA assurance remains required; a remembered browser preference only requests restoration of an existing server-verified session.

`research_app_v20.js` owns the selected company, revision, market history and shared basket. Analyze awaits its pending history request and checks that company, mode, account version and run token still match. `research_deep_v25.js` adapts retained numerical specialists. Identical in-flight company studies share one promise; changed context invalidates displayed and pending evidence.

`research_guide_v30.js` explains sourced evidence. `research_decision_v34.js` adds the single current assessment, explicit optional research conditions and traceable coverage. `research_workspace_v34.js` supplies My Briefing, Research an Investment and My Portfolio without adding a sixth Public route or another account store. Its new operations are read-only. Temporary conditions and reviewed assessments clear when Private mode ends.

The eligible universe is the intersection of bundled SEC company coverage and the existing hourly cached Alpaca active/tradable US listing catalogue. One protected metadata request supports local financial filtering; it does not fetch prices for every issuer or claim whole-market coverage. Each shortlisted name still requires individual market, valuation and portfolio research.

Supabase records preserve notes, thesis revisions, holdings, basis, transactions and owner-requested valuation marks. Writes retain expected-version and request-replay protection. New briefing code never invokes account writers. Existing virtual transactions require an explicit server preview and confirmation; this application does not submit real-money orders.

The hosted API package is deliberately small. `tools/package_vercel_api.py` permits named runtime files and records clean Git revision and file hashes. Offline Python forecasting, GARCH, options and integrated research remain available in the repository and CLI; they are not all server-hosted models.

Source: [browser orchestration](../../web/site/research_app_v20.js), [deep adapter](../../web/site/research_deep_v25.js), [assessment](../../web/site/research_decision_v34.js), [API](../../cloud/api.py), [proxy](../../functions/api/[[path]].js), [package manifest builder](../../tools/package_vercel_api.py).

## Company-study isolation

`research_study_v35.js` assembles independent single-company inputs: observed single-name history, common-date history, dated quotes, SEC capital and annual facts. Protected reads check the verified owner version and mode before and after acquisition. Partial responses retain usable observed evidence and disclose failed refreshes; there is no synthetic Private fallback. The adapter calls the retained deep research engines and builds the same input contract used by individual research before calling `QFDecision34.assess()`.

The sequential batch controller guards generation, owner version, per-company abort/timeout and repeated submissions. Earlier success survives an individual failure; context invalidation clears all session results. It never changes active company selection or calls account writers. Shared assessment policy remains in Decision34, display in Workspace34/Guide30, orchestration in Study35. Legacy specialist engines remain available for supporting analyses and offline workflows; they do not override the primary disposition.

The existing complete local Private cleanup is shared by explicit sign-out and protected authorization rejection. Rejection invalidates browser epochs, clears imported/cached evidence and hides the owner workspace without submitting server revocation or record writes. Explicit sign-out retains its pending-auth wait and server-revocation sequence. Portfolio ResizeObserver callbacks store only widths and redraw from current authorized state; they retain no additional series cache and issue no provider requests.

### November 18 refinement

The current UI separates financial-health screening from research coverage and canonical disposition. Source mismatches, stale evidence, unavailable reads and processing failures have distinct explanations. Five-session ML is supplementary for long-term research. Hosted archive/factor file controls are removed; underlying offline engines remain tested. See [investment policy evidence](INVESTMENT_POLICY_EVIDENCE.md) for rule precedence, the inconclusive economic-performance verdict and a forward paper protocol.
