# QuantForge V8.6 — Benchmark / ETF proxy / valuation sensitivity

## Scope

Adds an optional, entirely client-side research appendix to the authenticated **Portfolio → Decision Center → Candidate Dossier**. Does not add a public route, provider endpoint, trade action, account data export, or credentials.

### Inputs

Existing loaded 2–5-investment common-date history, an already chosen candidate, optional explicitly selected broad-market ETF (SPY, VTI, VOO, IVV) **already loaded in the history**, optional one or two already-loaded ETF proxies (IWM, IWD, IVE, IWF, IWO, QQQ, VTV, VUG, VB, VBR), existing V7.3 valuation bridge where available, and 1-year / 3-year scenario horizon.

### Models

- **Market ETF beta:** OLS slope of candidate daily price returns on the explicit market ETF's daily price returns. No inferred benchmark from the other selected companies. Displays price-only correlation, R², and comparison dates.
- **Optional multi-proxy regression:** OLS on (a) market ETF return and (b) each selected proxy ETF's return *minus the market ETF return*. This is a descriptive, ETF-based return sensitivity regression, **not Fama–French SMB/HML**, not economic alpha and not expected-return forecasting. In-sample adjusted R² and residual annualized volatility provided; singular/collinear designs are withheld.
- **Rolling risk:** Trailing 63-session annualized volatility, peak-to-trough maximum drawdown, underwater-session durations, and the worst *observed* 20-session price change. Equity-session scaling only.
- **Valuation sensitivity:** conditional arithmetic from the observed quote and observed P/S when SEC annual revenue and share count passed the previous validation bridge. Revenue-growth assumptions: -5%, +5%, +15% per year. Terminal P/S assumptions: 70%, 100%, 130% of observed P/S. Uses constant share count; relative price ratio = `(1+growth)^years × terminal_multiple/current_multiple`. The implied prices are conditional outputs **not fair value**; no dividends, financing, dilution, terminal discounting or taxes.

### Why this is bounded

No Fama–French factor library or true broad-index total-return feed is installed. The loading panel only appears when the user has included a valid explicit ETF in the same downloaded history as the candidate. The full factor data pipeline (risk-free series, market excess returns, period harmonization, official factor-file provenance, error covariance diagnostics) is an independent future milestone. No claims of CAPM alpha or predictive performance.

### Acceptance

1. With a loaded candidate but no broad-market ETF: market comparison withheld with a clear instruction; downside and valuation remain available.
2. With SPY in the loaded history: market ETF regression available when at least 126 aligned daily returns are present.
3. Add IWM, IVE to the selected 2–5 investments to optionally estimate ETF-spread proxy exposures. Duplicate and highly collinear proxies are rejected.
4. Compare 1- and 3-year P/S scenarios; unavailable valuation bridges never generate invented target prices.
5. Sign out or change investment/history settings: previous report clears and no data remains in the DOM.
6. No transactions, new public exports or background provider calls occur from the model code.

### Validation limits

The source-only development fixture does not contain all private API/Cloudflare integration components. The Windows installer must run the full project Python/JS tests, public static rebuild, SEC integrity, CSP and privacy audits before any commit. Live MFA, API access, and Cloudflare deployment require separate authenticated review.
