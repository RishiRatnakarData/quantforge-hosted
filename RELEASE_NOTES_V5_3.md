# QuantForge V5.3 — Quantitative portfolio research

Adds a separate **Quant** tab without changing the existing virtual ledger, SEC DCF, or current quote endpoints.

- Import private historical close-price CSV evidence (date/symbol/close) or request historical daily bars for U.S. stocks and ETFs from a user's Alpaca API session.
- Historical covariance and correlation using Ledoit–Wolf shrinkage with strict overlapping return dates.
- Risk contribution decomposition, risk-constrained portfolio weight suggestions with a turnover penalty, feasibility validation.
- Equal-budget baseline and constrained model comparisons, 21-day Monte Carlo modeled VaR/expected shortfall and stress scenarios.
- Detailed method, assumptions, dates, source provenance and warnings; no automatic orders or real-return forecasts.
- `examples/fictional_adjusted_prices.csv` for demonstration and regression testing only.

**Upgrade from V5.2.1**: stop the running app, extract the upgrade ZIP into the existing `quantforge-financial-research` directory, then run `python -m pip install -e ".[dev]"`, `python -m ruff check .`, `python -m pytest -q`. Restart the existing private database. The CSV and actual historical data stay private; do not publish them to GitHub.

V5.3's sample statistics are not real history. Alpaca historical data availability is dependent on the user's plan and network. Crypto requires a CSV in this version.
