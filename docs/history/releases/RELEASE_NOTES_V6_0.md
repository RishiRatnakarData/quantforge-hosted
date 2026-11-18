# QuantForge V6.0 — Personal Workspace Foundations

This release separates the public research demonstration from the authenticated personal investment workspace without publishing private market feeds.

## Public interface

- Simplifies the homepage: removes the corporate-style marketing hero, walkthrough cards, audience-directed language, and repeated dataset-size slogans.
- Uses the project name `quantforge` without a trailing period.
- Keeps a single compact disclosure distinguishing SEC reported data, public model assumptions, and protected account data.
- Preserves existing 12-company SEC analytics, rankings, charts, filing sources, and CSV export.

## Private workspace

- Adds six authenticated sections: Portfolio, Virtual trading, Market research, Backtesting, Valuation & peers, and Settings & notes.
- Adds an MFA-protected historical research endpoint using read-only Alpaca historical SIP daily stock/ETF bars. Periods: 90, 180, 365, or 730 calendar days; 2–5 symbols; date-aligned observations; no historical bars loaded on page startup.
- Adds indexed stock/ETF price chart, historical equal-weight portfolio return statistics, annualized volatility, one-day empirical 95% VaR and expected shortfall, and historical maximum drawdown.
- Adds equal-weight buy-and-hold versus monthly rebalance comparison with user-specified virtual capital and hypothetical turnover fees. It is an illustrative backtest, not an executable strategy.
- Adds private SEC-backed company comparison and discounted five-year FCF-proxy sensitivity using the existing publicly sourced historical filings. Alpaca does **not** supply the fundamental financial statements or full DCF inputs. No per-share fair-value claim is made.
- Extends the virtual trading form to allow a manually entered U.S. symbol, using the existing authenticated read-only quotes and virtual ledger.
- Adds server-validated virtual cash deposits/withdrawals and reset with a separate confirmation, optimistic version checks, and a 100-event virtual capital audit trail. Reset preserves private notes and watchlist.
- No Supabase migrations, paid market-data tiers, brokerage orders, credential disclosures, or background polling.

## Data and analysis limits

- Alpaca Basic IEX latest-trade observations are not consolidated-market execution prices. Historical stock/ETF series come from eligible delayed SIP daily bars, use split-adjusted prices, and **exclude cash dividends**. Historical metrics are price-only, not total-return or predictive estimates.
- The historical strategy model uses same-day-close hypothetical fills, constant equal-weight allocations, and specified rebalance fees; it omits bid-ask spread, slippage, taxes, dividends, and real execution mechanics.
- The SEC cash-flow proxy (operating cash flow less capex) is not unlevered free cash flow to the firm. Model output is not a company equity valuation or stock price target.
- Crypto trading and latest observations remain available, but crypto historical modeling, user-configurable optimization, richer financial modeling, and extended personalized research workflows remain future integration tasks.

## Validation

- Focused security and UI regressions for authenticated history, virtual capital controls, the rebuilt site, and public/private separation.
- Mocked browser walkthrough covers navigation, private historical risk, backtesting, private SEC-based valuation, and settings.
- Run complete Python and JavaScript suites, CI, and verify live Render/Cloudflare deployment before marking the release complete.
