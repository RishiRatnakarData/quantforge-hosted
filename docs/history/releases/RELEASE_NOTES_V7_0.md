# QuantForge V7.0 — Investment Research Shortlist & Public Project Case Study

## Personal investment research (owner-only)

- New **Investment ideas** tab: a click-to-select stock/ETF shortlist of up to ten candidates.
- Starts with a diverse illustrative research universe; owner can remove items and browse eligible Alpaca securities by company name.
- Historical market observations retrieved **on demand** through the existing MFA-protected endpoint in groups of up to five, with feed and as-of consistency checks. No automatic broad Alpaca universe scans.
- Balanced, growth, and risk-aware research lenses: **transparent heuristic** combining past period return, 63-observation trend, realized annualized volatility, and historical maximum drawdown. Scores are 0–100 prioritization indices, **not expected return, success probability, investment advice, price targets, or buy timing**.
- Optional SEC EDGAR annual financial context (YoY revenue growth and free-cash-flow proxy/revenue), fetched privately using the existing cached SEC API; missing values remain unavailable. SEC metrics are displayed separately and are not implicitly treated as a stock-price valuation.
- Easy links to deeper SEC valuation and virtual quote/trading screens; **no automatic transactions, real orders, Supabase writes or new account permissions**.
- Limits: price-only observations (no dividends), potentially IEX-only single-exchange coverage, historical survivorship and selection biases, limited universe, no live depth/order execution, no analyst-estimate consensus, incomplete valuation/sector normalization, and no guarantee of future performance. ETFs do not have comparable corporate statements. SEC responses on free Render may take time.

## Public experience

- Personal-project-first headline and four substantive competency case studies: SEC data engineering, risk/optimization, rolling evaluation, and secure full-stack engineering.
- Public/private architecture section explaining Cloudflare Pages, FastAPI, Supabase/MFA, SEC, Alpaca, data provenance and test boundaries.
- Existing genuine SEC financial statements and fully labeled simulated public models remain unchanged.
- No corporate/recruiter-directed copy, fabricated results or private provider data.

## Validation and installation

- V7.0 pure calculations: 6 Node.js tests; 4 Python integration/source checks. Existing V6.9 JavaScript suite retains its tests.
- Compiled public site keeps **three CSP-protected inline scripts**.
- Guarded installer performs dry-run semantic-anchor checks and transactional source backups; stops on unknown modifications.
- Local full Python suite, lint, public-bundle integrity, all JavaScript tests and GitHub Actions are required before publication.
- No new API keys, environment variables, database schema changes or Cloudflare proxy changes.
