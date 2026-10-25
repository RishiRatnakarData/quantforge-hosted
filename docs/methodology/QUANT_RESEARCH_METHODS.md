# Statistical, ML and quantitative-finance research

This file documents QuantForge's **separate experimental research modules**. They are not a live stock-picking engine, not a personalized model trained on the owner's portfolio, and not validated trading signals.

## Research integrity and evaluation clock

The historical strategy work uses chronological features, lagged trading signals and fixed train/validation boundaries. Forecasts for return at date `t` use information available through `t−1`. The development research period ended in 2018; the originally reserved 2019–2025 holdout is **not claimed as an evaluated final result**. Vendor data restrictions prevent publicly distributing earlier Tiingo inputs or their derived outputs. Synthetic fixtures and tests provide public implementation evidence instead.

| Component | How it works | Purpose | Limit |
| --- | --- | --- | --- |
| Historical VaR/ES | Percentiles and tail means of trailing returns | Empirical loss-budget baseline | Stationarity and limited tail samples |
| Gaussian VaR | Sample mean/volatility and normal quantile | Parametric comparator | Distributional assumption |
| EWMA | `λ=0.94` exponentially weighted squared returns | Recency-sensitive volatility | Zero-mean/normal-tail approximation |
| GARCH(1,1) | Positive constrained `ω + α ε² + β σ²` recurrence | Conditional-volatility model | Distribution/convergence assumptions |
| Ridge regression | Lagged volatility features, chronological rolling fit, regularization | Regularized variance proxy | Variance target transformations/QLIKE stability |
| Histogram gradient boosting | Lagged volatility features with fixed model complexity | Nonlinear variance proxy | Overfitting and limited validation horizon |
| Gaussian HMM | Two Gaussian states, Baum–Welch fitting, forward filtering, predictive mixture | Explore regime-sensitive risk | States and initialization can be unstable |
| Five-factor regression | Regress ETF/portfolio returns on matched Fama–French factors | Descriptive systematic exposures | No causal claims |
| Minimum-variance allocation | Constrained covariance quadratic program | Diversification benchmark | Estimation error and turnover |
| Black–Scholes & Greeks | Risk-neutral European option pricing and sensitivities | Numerical finance validation | Stylized European market assumptions |
| Monte Carlo | Fixed-seed simulated return or payoff paths | Distribution/scenario studies | Inputs and iid assumptions dominate output |

## Mathematical definitions

For simple asset returns `r_t = P_t/P_(t−1) − 1`, define one-day loss `L_t = −r_t`:

```text
historical_VaR_α = max(0, quantile_α(L))
normal_VaR_α     = max(0, z_α × sample_std(r) − sample_mean(r))
EWMA_variance_t  = Σ λ^k × r_(t−1−k)² / Σ λ^k
GARCH_variance_t = ω + α × ε_(t−1)² + β × variance_(t−1)
```

Expected shortfall averages losses in the upper tail with implementation-specific handling of fractional ranks. Coverage exception on day `t` is `L_t > VaR_t` (strict inequality). Diagnostics include Kupiec unconditional coverage, the exact binomial marginal test, and first-order independence/conditional coverage when estimable. A single coverage p-value is not proof of good forecasting.

The investment-research Ridge and boosted models fit features such as trailing 5/21/63-session variance, downside summaries, absolute returns and EWMA **only from prior observations**. Models train and refit chronologically, with scalers fitted to each training fold. Scores include Gaussian variance QLIKE, VaR exceedances and pinball loss. V2's revised log-variance target stabilized a numerical QLIKE issue, but **it did not establish a superior real-world tail-risk predictor**. Report both favorable and unfavorable metrics.

The HMM computes filtered state probabilities from **past observations**, then applies the transition matrix and a predictive Gaussian mixture. A two-state solution is a modeling device; its high/low volatility state assignments have uncertainty and the local optimum depends on initialization.

Constrained minimum-variance portfolio allocation solves:

```text
minimize     wᵀ Σ w
subject to   Σ w_i = 1,
             0 ≤ w_i ≤ max_weight
```

A small diagonal covariance regularizer handles poor numerical conditioning. Backtesting compares model-free allocations and uses explicit rebalancing costs and lagged positions. Historical results are not evidence that a future trading strategy will outperform.

The Black–Scholes–Merton call formula with dividend yield `q` is:

```text
C = S exp(−qT) Φ(d1) − K exp(−rT) Φ(d2)
d1 = [ln(S/K) + (r−q+σ²/2)T] / (σ sqrt(T))
d2 = d1 − σ sqrt(T)
```

European puts and Delta/Gamma/Vega/Theta/Rho are also implemented. Antithetic Monte Carlo pricing is checked against the closed form under the **same** assumptions; this verifies numerical consistency, not empirical options-market accuracy.

## How to audit the implementation

| Method | Code | Existing detailed notes |
| --- | --- | --- |
| Historical/EWMA/GARCH coverage | `src/quantforge/risk/` | [`V1_RISK_METHODS.md`](V1_RISK_METHODS.md) |
| Ridge/boosting, HMM | `src/quantforge/forecasting/advanced.py`, `src/quantforge/regimes/markov.py` | [`V2_ADVANCED_METHODS.md`](V2_ADVANCED_METHODS.md) |
| Portfolio optimization/backtests | `src/quantforge/portfolio/`, `src/quantforge/backtesting/` | [`FINANCIAL_MATH.md`](FINANCIAL_MATH.md) |
| Five-factor regression | `src/quantforge/factors/french.py` | [`V1_RISK_METHODS.md`](V1_RISK_METHODS.md) |
| European options | `src/quantforge/derivatives/black_scholes.py` | [`V2_ADVANCED_METHODS.md`](V2_ADVANCED_METHODS.md) |

## What is **not** supported by current evidence

No verified live prediction accuracy, no production ML trade signal, no reliable alpha claim, no optimized crypto allocation, and no passed untouched final holdout test. A code implementation plus synthetic tests demonstrates engineering competence and mathematical understanding, **not** forecast efficacy.
