# QuantForge V2 — Advanced risk forecasting and numerical-finance methods

> **Archive notice:** This document describes a historical research milestone. For the current V5 personal desk and supported claims, see [README](../../README.md), [Status](../STATUS.md), and [V5 research-methods guide](QUANT_RESEARCH_METHODS.md).

## Primary development target

One-day variance/5% tail loss of the V1 **investable, net-of-stylized-cost** equal-weight portfolio. Do not substitute frictionless ETF-average returns. All predictions for date *t* use observations with timestamp at most *t − 1*.

## Chronological forecasting

**Ridge regression:** lagged absolute return, last squared return, historical realized-variance windows of 5/21/63 sessions, 21-session absolute/downside summaries and EWMA. Fixed alpha = 12; features standardized **inside** each historical training fold only. Predictor of `log(1 + 10,000 * r²)` is inverse-transformed to a nonnegative variance proxy (not an unbiased conditional-variance estimator). Fixed 63-session refit schedule and at most 756 prior sessions.

**Histogram gradient boosting:** same lagged feature set; fixed 60 iterations, 7 terminal leaves, min 20 observations/leaf, ridge-like L2 regularization. No final-holdout fitting/tuning; 63-session refit.

**Gaussian 2-state HMM:** fixed two states with state-conditional Gaussian return distributions, 15 Baum–Welch EM iterations on up to 504 historical returns every 126 sessions, deterministic start. E-step smoothing is restricted to the model's *past fitting window*. After fit, predictions use only forward-filtered state posterior at date *t − 1*, multiplied by the Markov transition matrix to estimate state probabilities for date *t*. VaR uses the predictive Gaussian-mixture 5th percentile, not a probability inferred from future regimes. Variance ordering gives names `low` and `high` each refit; identifiability, initialization and label instability remain limitations. A single start is **not** guaranteed to find the best likelihood solution.

**Metrics:** same-date VaR exception rates, Kupiec coverage, exception-independence tests, pinball loss at 95% loss quantile, and Gaussian model QLIKE on squared daily returns as a noisy variance target. These scores evaluate different objectives; do not claim model superiority solely from one loss. Backtests run only through December 31, 2018 (development). No proper multiple-testing-adjusted superiority test or final 2019–2025 confirmation is claimed.

## Mathematical-finance components

Black–Scholes–Merton uses hypothetical European options with continuous `r` and dividend yield `q`. Closed-form call and put formulas are:

\[C = S e^{-qT} N(d_1)-K e^{-rT}N(d_2)\]
\[P = K e^{-rT} N(-d_2)-S e^{-qT}N(-d_1)\]

where \(d_1=[\ln(S/K)+(r-q+\sigma^2/2)T]/(\sigma\sqrt{T})\), and \(d_2=d_1-\sigma\sqrt{T}\). Greeks are delta, gamma, vega per unit volatility, annual theta and rho per unit continuously compounded interest rate. At expiry or zero volatility some derivatives are undefined and are returned as NaN rather than fabricated finite values.

Separate risk-neutral Monte Carlo draws antithetic normal shocks and prices discounted payoffs with an approximate 95% confidence interval computed from independent antithetic **pairs**. This is a consistency check of Black–Scholes under its assumptions, not validation against exchange-traded options quotes. Option results use S=100, K=100, r=3%, q=1%, volatility=20%, maturity=1 year by default.

**Portfolio Monte Carlo:** iid Gaussian 21-session future simple-return scenarios from the most recent 252 development net portfolio returns. Report zero-drift and sample-drift versions separately and explicit seed/path count. Retain a caution that iid returns, estimated drift, static volatility and absent execution/liq/financing assumptions make the outcomes conditional *scenarios*, not reliable tail forecasts.

## Evidence boundaries and further work

SEC corporate-action timing, ETF universe selection, data-license restrictions, volatility predictive-interval uncertainty, more sophisticated regime optimization, realistic ES validation, additional stress frameworks and independent statistical significance tests remain open. This iteration deliberately does not inspect 2019–2025 holdout data or produce an investment recommendation. Research conclusions belong in a later review after outputs are reproduced and independently audited.

References: scikit-learn time-series evaluation guidance; classical Black–Scholes–Merton European option equations; see repo README's link list.


## V2.0.1 Ridge variance transformation and numerical diagnostic

Development runs revealed a large Ridge QLIKE score. The initial `log1p` target,
combined with `max(prediction, 0)` during inversion, mapped negative linear-model
predictions to a 1e-10 variance guard. V2.0.1 uses `log(r_t² + 1e-8)` as the
Ridge training target and `exp(prediction)` for strictly positive predictions,
clipped only for numerical guardrails. Boosting retains the previous log1p
transformation. This changes the Ridge specification; a good development score
must **not** be interpreted as independent evidence of model superiority.
`variance_forecast_stability.csv` quantifies forecast minima and near-floor hits.
A log-link targets a transformed squared-return proxy, not an unbiased conditional
variance, and requires further calibration studies. The 2019–2025 holdout has
not been opened or used for this change.
