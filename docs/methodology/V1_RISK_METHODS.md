# QuantForge V1 — Quantitative methodology and independent validation needs

> **Archive notice:** This document describes a historical research milestone. For the current V5 personal desk and supported claims, see [README](../../README.md), [Status](../STATUS.md), and [V5 research-methods guide](QUANT_RESEARCH_METHODS.md).

## Source and observation timing

The input is the V0.2 **development-period** `prices.csv` produced from Tiingo `adjClose`: adjusted close as documented by its provider. Prices from 2019–2025 remain unused. Daily return \(r_t=P_t/P_{t-1}-1\). Present-day back-adjusted histories are **not** point-in-time snapshots. The provider's 8-ETF current selection is vulnerable to retrospectively selecting surviving and liquid names. Publication would require corporate-action spot checks and survivorship/inception assessment.

## Execution convention

Portfolios are **long-only, fully invested**, with max weight 35% for diversified portfolios, no margin or shorting, and equal weight/minimum-variance/shrunk minimum-variance/regularized mean-variance compared to SPY buy-and-hold. On an evaluation return dated \(t\), the allocation may use returns **only through \(t-2\)**, takes effect at the **\(t-1\)** adjusted close, and realizes the return from \(t-1\) close to \(t\) close. This is an **explicit one-session signal/execution delay**, not a claim to guaranteed execution at the closing auction. Adjusted closes are proxies for tradable prices. Initial cash deployment costs and scheduled rebalances reduce net wealth.

For target weights \(w^*\) and drifted pretrade holdings \(w\), traded notional is \(T=\sum_i |w_i^*-w_i|\), counting **both buy and sell legs**. Cost is \(c=T\times b/10{,}000\) for fee rate \(b\) bp per executed notional. Initial purchase has \(T=1\). A fully invested two-sided rebalance of 10% of capital sold and 10% bought has \(T=0.20\), **not 0.10**. Net return is \((1-c)(1+w^*\cdot r_t)-1\). Rebalancing occurs every 21 sessions (sensitivity: 63) and illustrative per-notional fees are 0/5/15 bp.

Portfolio weights are recomputed using a trailing 126-session estimation window. Shrinkage uses a predeclared **fixed 25%** blend of sample covariance and diagonal covariance; it is **not** a claim to estimate Ledoit–Wolf shrinkage. Mean–variance optimization uses capped annualized training means and risk aversion 5, subject to the same concentration and long-only constraints.

## One-session VaR and GARCH

The VaR target is the **net** daily return of the live-accounted equal-weight portfolio, not the earlier V0.2 frictionless return proxy. After the portfolio's 126-day initialization, all VaR methods wait another 252 daily return observations before evaluation. Baselines are historical loss quantile, Gaussian with sample mean and variance, and a Gaussian EWMA variance based on trailing squared returns.

GARCH(1,1) is Gaussian with an estimated constant return mean. In decimal return units, \(r_t=\mu+\epsilon_t\) and \(\sigma^2_t=\omega+\alpha\epsilon^2_{t-1}+\beta\sigma^2_{t-1}\). Positivity and \(\alpha+\beta<1\) are enforced by parameterization. The Gaussian conditional negative log-likelihood evaluates **each innovation against the variance computed before observing that innovation**, then filters the variance for the next observation. Estimation is on the last 252 daily returns and parameters are refitted every 63 observations; variance filtering incorporates intervening **past** innovations. Forecasts are evaluated on the same days as the three baselines. Fit failures are errors, never silently replaced with successful results.

Normal VaR uses \(\max(0,z_{0.95}\sigma_{t+1|t}-\hat\mu)\); Gaussian ES uses \(\max(0,\sigma_{t+1|t}\phi(z_{0.95})/(1-0.95)-\hat\mu)\). Both are loss-budget quantities expressed as a fraction of value, not dollar exposures. **Historical ES and modeled Gaussian ES are not statistically validated by VaR coverage tests.** Formal ES backtesting is future work.

## Coverage and forecast scoring

A loss exception is \(-r_t > \mathrm{VaR}_t\). V1 computes number and rate of exceptions, the Kupiec likelihood-ratio **unconditional coverage** p-value, the **exact binomial** p-value for marginal frequency, Christoffersen first-order exception **independence** likelihood-ratio p-value where estimable, and joint **conditional coverage** statistic. The independence calculation uses counts of transitions 00,01,10,11 for consecutive observed evaluation dates. Degenerate all-zero/all-one samples are marked **not estimable**; no arbitrary p-value is invented. LR reference distributions are asymptotic and can perform poorly on short tails (especially at 99%). This version only preregisters/report the **95%** set; 99% analysis requires a separate properly specified study.

Quantile (pinball) loss uses the 95th loss quantile, and QLIKE uses log(estimated variance) + realized return squared / estimated variance (a noisy one-day variance proxy), with numerical floors only for the log. Models can differ on VaR calibration and variance forecasting accuracy without translating into a better tradeable strategy.

## Analysis outputs and restrictions

Risk backtests, Sharpe-zero-risk-free proxy, covariance and correlation, and hypothetical stress sensitivity are **diagnostic development-window results**. Neither investment alpha nor causal predictive improvement is established. No 2019–2025 final holdout outcomes are reported. An alternative risk-free rate, financing and execution realism, ES calibration, parameter uncertainty, cross-period robustness, paired uncertainty testing, and the final working paper are not yet implemented/validated.

Reference points: Tiingo's `adjClose` documentation; the Basel Committee's messages on VaR exception-test limitations; ARCH/GARCH forecasting documentation from Kevin Sheppard's `arch` project. See authoritative documentation separately; this V1 uses a self-contained SciPy maximum-likelihood implementation with explicit unit tests rather than asserting equivalence to the third-party `arch` implementation.
