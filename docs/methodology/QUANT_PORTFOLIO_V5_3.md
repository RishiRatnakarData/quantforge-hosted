# QuantForge V5.3 — Portfolio covariance, risk contribution, optimization, scenarios

**Scope:** Private personal finance research. The Quant tab is read-only. No brokerage orders or edits to virtual trades. These calculations are not investment recommendations or expected returns.

## Data and provenance

A Quant dataset is obtained in either of two ways:

1. **Fetch from Alpaca:** select 2–3 U.S. stocks or ETFs by name. The local Python process requests up to 400 calendar days of personal historical daily bars for each ticker, with `adjustment=all`; IEX is the default; SIP remains an explicit alternative. A Basic account may have access to older SIP history but may be denied depending on subscription. IEX includes only one trading venue. Data access is not guaranteed, and errors are shown directly, not silently replaced. Crypto historical-fetch is not implemented in V5.3.
2. **Import CSV:** `date,symbol,close`, one daily close per ticker per date, at least 91 dates per ticker, maximum 12 tickers. Enter a provider or dataset source. If historical crypto is included, keep the source and dates appropriate. Use split/dividend-adjusted closes to avoid false returns from corporate actions. The app cannot verify externally sourced CSVs.

The latest import replaces the previous research evidence in the same **private SQLite** portfolio database. API credentials remain in the local Python process and are never stored in the research database. **Never commit user data, Alpaca feeds, derived proprietary return outputs, or secrets to GitHub.**

`examples/fictional_adjusted_prices.csv` is completely fictional and intended only for QA. Never describe its metrics as historical market evidence.

## Input checks

- Strict ISO calendar dates; positive finite closing prices; reject duplicates, extreme jumps that may signal unadjusted stock splits, future observations and malformed columns.
- Per-asset log daily returns `r_(i,t) = ln(P_(i,t)/P_(i,t-1))` are computed **before** joining each asset's return dates. The analysis then keeps their **intersection** and requires at least 90 overlapping return dates.
- Missing returns are not filled with zeros, forward prices, or interpolation. Crypto can trade seven days while stocks do not. Joint-analysis timestamps use overlapping dates only, and annualization is 252 for any stock/ETF basket and 365 for all-crypto baskets. These are approximations, not a unified trading calendar.
- The app warns if the latest imported price is more than 30 days old. The input period, source, overlapping sample size and last date are visible.

## Covariance and correlation

The algorithm fits the Ledoit–Wolf shrinkage covariance estimator to overlapping daily log returns. Compared with an unregularized covariance matrix it can improve numerical conditioning with a limited sample; it does **not** make the observations more representative of the future.

For covariance matrix `Σ` and diagonal standard deviations `σ_i`:

`corr(i,j) = Σ_ij/(σ_i σ_j)`.

Annualized volatility of weights `w` is `sqrt(A × wᵀΣw)`, where `A` is the annualization-day convention above. The report displays covariance-derived correlations, annual volatility, and per-asset risk contributions.

Marginal contributions to risk are `Σw / sqrt(wᵀΣw)` and component contributions are `w_i × (Σw)_i / sqrt(wᵀΣw)`, scaled by `sqrt(A)` to annualized percentage points. They sum to portfolio volatility (within rounding). A negative component can occur when an asset hedges risk, and is not necessarily an error.

## Optimization (read-only hypothetical allocation)

Minimize

`wᵀΣw + λ × Σ_i (w_i - w_baseline,i)^2`

under:

- `sum_i w_i = 1`, `w_i >= 0` (long-only, fully invested model basket);
- `w_i <= user_max_single_asset`;
- `sum_{i in crypto} w_i <= user_crypto_cap`.

The default regularization weight `λ = 0.003` penalizes a large change from the baseline. SciPy SLSQP solves the constrained problem. Constraints are checked **after** solving and an infeasible portfolio produces an error, never a fabricated result.

If exactly the selected symbols comprise the user's virtual holdings, the baseline is the portfolio's existing **invested-sleeve** weights, normalized to sum to 100% **excluding cash**. Otherwise it is an explicitly **equal-weight illustrative basket**. Model budget defaults to $10,000 and can be changed. The optimizer does not use current prices to execute trades, and it does not include tax lots, spreads, brokerage fees, cash interest, or realized capital gains. Its objective is *not* forecast return maximization.

The half-sum of absolute weight changes is shown as **one-way turnover**. It is not a dollar order list; use the separate read-only Rebalance tool for that purpose.

## Monte Carlo and stress comparison

For each basket, 3,000 paths of 21 daily steps are generated from a multivariate normal daily *log-return* covariance (`Σ`); daily shocks are independently resampled but correlated across assets. The historical mean is deliberately replaced with zero **assumed expected arithmetic return** (the code subtracts half the per-asset variance from simulated log returns). Each day assumes constant-mix portfolio weights, so outcomes implicitly include daily rebalancing without transaction fees.

Using the user-entered hypothetical budget, report 5th/50th/95th-percentile terminal values, probability of loss **within the model**, and loss-tail measures:

- `VaR_95` is `max(0, 95th percentile of loss distribution)`.
- `ES_95` is `max(0, mean(loss | loss >= that percentile))`.

A separate hard-coded scenario assumes stocks and ETFs decrease 20% and crypto decreases 40%. This is **not** a forecast or estimate of how an actual bear market would affect correlations.

Existing Portfolio risk uses a **separate, uncalibrated, assumption-driven** one-factor simulation. V5.3's Quant tab uses *imported historical covariance*; the two models must not be treated as the same calculation.

## Validation and limitations

Tests cover input validation, duplicate dates, atomic database replacement, non-overlapping histories, infeasible allocation limits, portfolio-weight normalization, optimization constraints, repeatable simulations, Euler volatility contributions, API privacy and preservation of paper holdings, and mocked Alpaca history access.

Risks include data availability/licensing, survivorship bias, corporate actions, feed coverage, volatility regime change, finite-sample uncertainty, overlapping-date selection, daily rebalancing assumptions, Gaussian tail misspecification, price discontinuities, and estimation error. No trading alpha, backtest outperformance, model calibration, or investment suitability is claimed. The selected model is an educational financial engineering analysis, not an investment recommendation.
