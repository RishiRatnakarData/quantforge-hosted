# QuantForge V6.5 — SEC forecasting and historical walk-forward validation

## Private financial projections
- In **Valuation & peers**, select a company by name and load SEC annual filings, then open **Multi-year SEC financial projections**.
- Projections begin from the latest reported SEC annual revenue and use **explicit user-entered** revenue growth, FCF margin, discount rate, terminal growth and a three-, five-, or seven-year horizon. The conservative/base/optimistic scenarios differ by fixed, visible growth and margin adjustments.
- The historical table retains the actual SEC reporting periods. Projections are **hypothetical**. Any valuation total is a **discounted FCF proxy**, not company market capitalization, enterprise value, equity value, or a price target. Financial margin assumptions use an operating cash-flow-minus-capex *proxy*, **not** unlevered FCFF. If reported FCF is unavailable, the FCF projection/valuation is suppressed; reported revenue can still be projected.
- This is scenario analysis, not a learned predictive model, and does not claim forecast accuracy. FCF margin changes, working capital, share counts, capital structure, taxation and dividends are not independently forecast.

## Private walk-forward evaluation
- In **Market research**, choose 2–5 assets **by name**, then load daily historical observations using your Alpaca connection. Open the new **Walk-forward** tab.
- Refit a minimum-volatility, inverse-volatility or return-tilt allocation using ONLY the immediately preceding training period (63, 126, or 252 observed aligned sessions). Test it over a subsequent 21- or 42-observation window, then roll forward. Windows do not overlap. At least two complete future-relative-to-fit windows are required.
- Compare against an **equal-weight benchmark rebalanced on the same schedule**, with the same cost-per-turnover rule, including initial deployment. Both portfolios are simulated without brokerage orders. Inspect compounded change, annualized volatility, maximum drawdown, empirical VaR/ES and modeled fees; export the rolling weights and their training/test boundaries as CSV.
- Crypto-only samples use 365 observation/year annualization; stock-only/mixed use 252 aligned observed sessions/year. No weekend stock-price fabrication. The equity history is split-adjusted and excludes dividend returns. Simulated rebalances occur at observed closing prices with fee assumptions, but not slippage, spreads, taxes or borrow costs. Corporate-action impacts may be imperfectly represented.
- This is **retrospective out-of-sample relative to each fit**, not a live forward track record. It is vulnerable to universe, period and model selection bias, survivorship bias, data-quality limits and hypothetical transaction-cost assumptions.

## Hosting, privacy, source boundaries
- These calculations run **only** in the browser after MFA unlock, reading the private history and SEC facts already obtained through the existing authenticated Render proxy. Neither new helper contains fetch/network calls or credentials.
- No backend endpoint, Supabase tables/RLS, Alpaca secret, stored positions, trades, notes, SEC snapshot, or public demo data are changed.
- Existing Cloudflare Pages CSP remains three hash-protected inline scripts. No additional paid provider or environment variable is needed.

## Verification
1. Run full local Ruff and pytest, all JavaScript suites, full website build, privacy prepublish check, and GitHub Actions before trusting publication.
2. Confirm Cloudflare production deploys the same commit; Render does not need a new release for this strictly front-end upgrade.
3. MFA sign-in; choose Microsoft or Apple via the company picker; load reported SEC statements, then run three financial forecast scenarios.
4. Select 2–5 investments in Market research (stocks or eligible crypto); load **one or two years**; try the new Walk-forward view and CSV export. Increase history if a 252-session training window cannot produce two complete test windows.
5. Confirm no virtual trades/capital changes occurred and that sign-out clears private results.
