# QuantForge V5.8 — Recruiter Research Experience

Presentation-focused release building on the published V5.7.2 real-SEC-data demo (12 issuers). No changes to Supabase policies, Render backend, personal holdings, API secrets, or market feeds.

- Research-first homepage with direct paths to SEC Financials, quantitative-model simulations, and engineering methodology.
- New public **Methods & engineering** section: data lineage, as-of filing cutoff, formulas, missing data, fiscal-year comparability, model boundaries, security architecture, and implementation techniques.
- Cross-sector SEC quick links for Microsoft, Walmart, and Exxon Mobil. These set the existing 12-company selector; they do **not** create additional datasets.
- Direct public deep links (`#sec`, `#methods`, etc.), accessible navigation state and skip link, mobile-responsive layouts, and no external visual assets or scripts.
- Fixed a legacy private-workspace script overwriting all public status badges with `FICTIONAL DATA` after navigation. Public status labels remain accurate and private MFA login remains unaffected.
- No claims of audited investment performance; fictional/model inputs stay labeled and real SEC figures remain a build-time historical snapshot.

For publication, rebuild `public/index.html` with the **existing authentic** `web/site/sec_snapshot.json`. The SEC snapshot must not be replaced with fixture data. Run the full test suites and prepublication checker before committing.
