# Numerical Conventions in the Implemented M0 Prototype

> **Archive notice:** This document describes a historical research milestone. For the current V5 personal desk and supported claims, see [README](../../README.md), [Status](../STATUS.md), and [V5 research-methods guide](QUANT_RESEARCH_METHODS.md).

All risk metrics are daily loss fractions. A 0.025 VaR means a modeled one-day loss budget of 2.5% at the chosen confidence; **not** an assertion that this is a guaranteed worst outcome.

## Returns

`r_{i,t}=P_{i,t}/P_{i,t-1}-1`. Values are ordinary arithmetic returns. No imputations are made. Daily panel must contain every requested symbol on every observed date; date-range selection is not an implicit liquidity imputation.

## Historical risk

Loss `L_t=-r_t`. 95% VaR is the 0.95 empirical quantile of losses. It is floored at zero by the project's nonnegative loss-budget convention. Historical ES is the mean of the largest 5% empirical losses, with fractional last order statistic when needed; also floored at zero. Both correspond to simple-return loss magnitude over one daily holding interval. Small tail windows are noisy.

## Normal risk

`VaR(alpha) = max(0, z_alpha * s - mean(r))`, where `s` is sample standard deviation (`ddof=1`). This is a normality assumption, **not** a nonparametric guarantee.

## EWMA

`EWMA variance = sum(lambda^(n-1-i) * r_i^2) / sum(lambda^(n-1-i))` over trailing observations, with newest index highest weight; baseline `lambda=0.94`. EWMA-normal VaR is `z_alpha*sqrt(EWMA variance)`, floored at zero. It assumes zero conditional mean and normal conditional shocks. Use data only through the day preceding the forecast.

## Coverage

Exception means realized `-r_t` **strictly greater** than forecast `VaR_t`; equality is not an exception. Kupiec likelihood-ratio test compares `p_hat = number_exceptions / N` to nominal `1-alpha`, using chi-square(1) approximate reference. It does not check serial independence. In small samples, zero exceptions and very few tails can make asymptotic interpretations fragile.

## Portfolio optimization

`min_w w' Σ w` subject to `sum(w)=1`, `0<=w_i<=max_weight`, with an explicit positive diagonal numerical regularization. Historical sample covariance only uses trailing realized returns, never a full evaluation-period fit. Solver success and constraints are verified.

## Portfolio performance accounting

At rebalance, `turnover_t = 0.5 * sum(abs(target_weights - previous_post_drift_weights))`. One-way cost fraction `cost_t = turnover_t * transaction_cost_bps / 10000`.

For the day's returns vector `r_t`, pre-return active weight vector `w_t`, and prior wealth `W_(t-1)`:

`gross_t = dot(w_t, r_t)`

`net_t = (1-cost_t)*(1+gross_t)-1`

`W_t=W_(t-1)*(1+net_t)`

After the close, updated drifted weights are `w_(i,t+)=w_(i,t)*(1+r_(i,t))/(1+gross_t)`.

At evaluation inception, funding is normalized to wealth=1 and entry trading costs are omitted consistently across strategies. No leverage/short positions. No price impact or tax modeling; costs are an explicit modeling assumption, not measured live slippage. Training ends before each evaluation return.

## Risk-adjusted returns and drawdown

`annual_return = W_end**(252/N)-1`, `annual_vol = sample_std(daily_net)*sqrt(252)`, `Sharpe_zero_rf = mean(daily_net) / std(daily_net) * sqrt(252)`. The *zero-risk-free-rate* assumption is explicit and **not** the appropriate risk-free-adjusted comparison for final empirical claims.

`drawdown_t = W_t/max_{s<=t}W_s - 1`, including the normalized start capital. Max drawdown = lowest drawdown. Relative capital used; not a forecasted loss budget.

## Excluded until later milestones

This file does not claim GARCH validation, HMM regimes, mean-variance expected return optimization, factor betas, Black–Scholes, Monte Carlo, any completed DCF calculation, VaR independence test, or published test-set inference.
