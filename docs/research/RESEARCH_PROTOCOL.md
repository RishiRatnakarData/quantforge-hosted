# QuantForge Quantitative Risk Study — Preregistered Framework (Draft)

**Study status:** prospective design; no market dataset or advanced-model result validated. Lock the plan and precise data freeze before the first primary empirical run.

## Primary question and competing hypotheses

H0: An advanced, tuned forecast (GARCH/market-regime or parsimonious ML) does not materially improve one-day *out-of-sample* portfolio loss-risk calibration versus standard rolling historical, normal, and EWMA approaches when applied to the same test observations.

H1: At least one advanced forecast improves a preregistered proper or meaningful loss/risk scoring objective, not merely in-sample fit or headline Sharpe.

No finding is presupposed. Incremental improvements may disappear under regime changes, implementation friction, estimated-parameter noise, and multiple comparisons.

## Candidate sample and temporal boundaries

- Instruments: eight cross-asset ETFs SPY, IWM, EFA, EEM, IEF, TLT, GLD, LQD.
- Data: authorized verified dividend-adjusted market closes or total-return indices, as independently documented by the chosen vendor.
- Proposed observations: 2010-01-01 to 2025-12-31 (subject to verified vendor sample coverage).
- Development: 2010–2014 initial training, 2015–2018 model selection/diagnostic design, 2019–2025 untouched final holdout. **Changing these dates after seeing results invalidates the purported primary holdout.**
- Robustness windows: e.g. non-overlapping 2019, 2020–21, 2022–23, 2024–25; tag these predeclared segments without selecting based on model performance.
- Targets: daily return variance and one-day 95%/99% loss VaR. ES backtesting needs its own suitable score/test beyond a Kupiec VaR check.

## Forecast comparators

1. Rolling historical loss quantile and conditional tail average.
2. Normal VaR via rolling mean/std.
3. EWMA conditional variance + specified loss distribution.
4. Student-t or another defensible heavy-tail statistical model (if justified).
5. GARCH(1,1) and potentially a skew/heavy-tail version.
6. HMM regime-aware conditional forecast (state inference uses history only; never full-sample posterior labels).
7. Regularized and/or tree ensemble models on trailing price, realized-volatility and valid macro/factor features.

All methods use consistent forecast times, horizons, training samples, and allowed information. Internal cross-validation is chronological, with retraining schedule and model-selection rules declared before holdout review.

## Primary evaluation

- **Primary variance forecast score:** QLIKE on a well-defined nonnegative realized-variance proxy, with explicit small positive numerical floor; review assumptions on noisy daily return-square proxies.
- **VaR calibration:** observed exception fraction vs nominal, Kupiec unconditional coverage, Christoffersen independence/conditional coverage where sample size supports; supplement with a proper quantile (pinball) score and confidence intervals.
- **Expected Shortfall:** use an appropriate *jointly elicitable VaR–ES* evaluation or rigorous literature-supported backtest, not unconditional VaR coverage alone.
- **Economic usefulness:** compare costs, turnover, max drawdown, exposures and net return for predeclared control strategies. Do not claim better *returns* merely because a variance forecast is better.
- **Uncertainty:** paired test and/or blocked/bootstrap forecast-loss differences with sensitivity to serial dependence; disclose comparisons multiplicity and selection effects.
- **Negative-result policy:** publish non-improvement and material calibration/implementation problems rather than selectively choosing favorable dates.

## Portfolio construction controls

- Buy-and-hold and monthly 1/N, minimum-variance (and later shrinkage/robust MV) controls, fully invested, long-only.
- Default max-weight 35% for eight-ETF strategy, no leverage.
- Illustrative one-way cost 5 bps applied to 50% L1 turnover. Run 0/5/15 bps and 21/63-session rebalancing sensitivity.
- Benchmark SPY buy-and-hold aligned to same dates (single-asset benchmark module to be implemented in V1).
- Risk-free series uses actual available rates, aligned conservatively and point-in-time; the current M0 Sharpe proxy sets cash rate to zero and is not publication ready.
- Portfolio decisions at prior close, next-period implementation; no future prices or full-sample transforms.

## Potential failure modes and mitigation

- Hindsight ETF selection/survivorship and unavailable corporate actions: disclose and validate inception dates, test robustness on alternative legally available fixed baskets.
- Reconstructed historical adjusted levels: verify dividend/split adjustment conventions and reproduce spot checks against primary source/corporate actions.
- Macro revisions and releases: query ALFRED vintages and enforce release lag, without using current revised levels in 2010 signal features.
- Data-snooping: keep a genuinely untouched primary holdout, freeze search space, record all candidate experiments.
- Regime hindsight bias: compute filtered probabilities at time `t`, not smoothed probabilities using later states.
- Exception clustering: test independence, not simply unconditional rate.
- Small tail sample: cautious p-value interpretation and confidence bands; ES may be unstable at 99% with limited observations.
- Model comparability: same target, same calendar, same cost accounting, no midstream changes to universe/forecast horizon.

## Publication packet once complete

Dataset/sourcing audit; predeclared experiment identifiers; reproducible returns/features; model tuning and holdout tables; forecast calibration and uncertainty; strategy outcomes after costs; failures and limitations; 6–12-page working paper; dashboard panels linking to actual artifacts. SSRN publication would be a *preprint or working paper*, not a peer-reviewed publication.
