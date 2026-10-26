# QuantForge V6.3 — Private Portfolio Optimization & Risk Diagnostics

## Scope

Adds a historical-data-backed **Optimization** section to **My workspace**. The user first selects 2–5 eligible stock/ETF investments by company name in Market research and loads their actual authorized private Alpaca daily history. The Optimization section then calculates:

- **Minimum historical volatility:** constrained, long-only portfolio solved with projected-gradient optimization on a 20%-diagonally-shrunk sample covariance matrix.
- **Inverse-volatility allocation:** stand-alone-volatility risk-balancing heuristic, not equal risk contribution or risk parity.
- **Historical-return tilt:** a sensitivity scenario combining sample covariance with capped/shrunk relative historical mean returns. Not a forward expected-return forecast.
- **Position caps:** configurable 35%–100%, with mathematical feasibility checks (e.g. a two-asset portfolio cannot use a 35% maximum).
- **Diagnostics:** allocation and per-asset risk contributions, historical correlations, annualized volatility, empirical one-session 95% VaR and expected shortfall, in-sample compounded returns and drawdowns, effective diversification, worst rolling 5/20 sessions, and a sample risk-return trade-off visualization.
- **CSV export:** clicked explicitly by the owner; contains allocations and dates without credentials.

No additional credentials, provider integrations, services, database migrations, brokerage orders, portfolio edits, or synthetic data sources are introduced. Existing Supabase MFA and Alpaca history authorization boundaries remain unchanged.

## Methodology & limitations

Inputs are aligned, positive daily adjusted close prices supplied by the existing private `GET /api/private/history` endpoint. Computation is entirely in the authenticated browser after the historical API request. The current endpoint supports 2–5 U.S. stocks/ETFs, up to its existing two-year horizon; crypto historical integration remains separate work.

The covariance matrix is computed from simple daily returns and shrunk 20% toward its diagonal. The optimized weights are nonnegative, capped, and sum to 100%. Annualization uses 252 sessions. Mean return comparisons are **in-sample**, not predictive, and the allocation is calculated using the same period used to display descriptive performance. The tool assumes daily rebalancing in compounded returns and omits dividends, fees, taxes, trading frictions, survivorship bias, and provider gaps. Results must not be marketed as live performance or out-of-sample evidence.

The existing historical backtest tab is unchanged; a proper train/test walk-forward experiment is future work. The `private_optimizer.js` module is intentionally pure and network-free.

## Verification

```powershell
& .\.venv\Scripts\python.exe -m ruff check .
& .\.venv\Scripts\python.exe -m pytest -q
node --check web/site/private.js
node --check web/site/private_optimizer.js
node --test web/tests/demo.test.cjs web/tests/sec_analytics.test.cjs web/tests/private_optimizer.test.cjs
& .\.venv\Scripts\python.exe tools/prepublish_check.py
& .\.venv\Scripts\python.exe tools/build_unified_site.py
```

The builder bundles the optimizer into the existing third inline script, maintaining three CSP-hashed scripts. The website must be rebuilt after installation; the SEC snapshot is never modified.
