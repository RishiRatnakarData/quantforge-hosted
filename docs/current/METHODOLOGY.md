# Current research methodology

## Evidence and financial comparability

SEC annual facts retain fiscal periods, filing dates, CIK and accession lineage. Cash-flow proxy means operating cash flow minus cash PP&E purchases. It is not FCFF or cash distributable to shareholders. Missing observations stay unavailable. No TTM series is inferred from annual facts. Current snapshots can contain later restatements and do not constitute a complete original-filing archive.

The new financial screen requires matching filing accessions for revenue, operating income, operating cash flow and capex, compatible available source periods and consistent revenue tags across growth periods. A margin above 100% is a review anomaly, not automatically an error or proof of business strength. It withholds financial-screen inclusion while preserving the reported facts. Matching tags do not prove that a revenue concept covers all business lines; industry comparability and primary statements still require review.

Shortlist filters and single-field ordering are deterministic research rules, not fitted forecasts. The five-name limit is a presentation constraint. No whole-universe investment-strategy advantage has been backtested. Eligibility reflects covered issuers and cached provider listing support, not liquidity, suitability or permission for a particular real order.

## Statistical ML

The hosted model is fitted L2-regularized logistic regression for the sign of a five-session close-price change. Its five features are lagged 5/20/60-session log returns, 20-session variability and drawdown from the preceding 40-session high. Each expanding fit standardizes on its training observations and clips standardized features to ±5. Gradient descent uses 260 steps, learning rate 0.085 and L2 coefficient 0.16; these are fixed implementation choices, not claims of optimal hyperparameters.

At each held-out feature date, training labels must have fully matured by that date. Test dates advance five sessions, avoiding overlapping five-session test outcomes. The baseline is the expanding historical positive-outcome frequency. Accuracy measures classification; Brier score measures squared probability-score error. Neither measures tradable excess return.

The existing exploratory signal screen requires at least 12 held-out windows, Brier improvement greater than 0.005 and accuracy no worse than baseline. A new descriptive chronological review splits those same tests in half. Each period needs at least 12 disjoint matured windows. An earlier paired Brier advantage below −0.005 followed by recent disadvantage above +0.005 withholds direction. It is not a significance test or a tuned regime detector. Small samples are explicitly insufficient. Three model-score bins are descriptive, not independently calibrated probabilities.

## Risk, optimization and evaluation

Historical log-return variation, empirical 95% loss quantile, expected shortfall and peak-to-trough drawdown describe the observed sample. Equity and crypto single-asset annualization use their own calendars. The volatility moving-block bootstrap measures sensitivity within historical observations, not calibrated future risk. Mixed-calendar portfolio comparisons require compatible inputs rather than silently aligning incompatible observations.

Retained constrained covariance optimization and seeded Monte Carlo experiments illustrate allocations and scenario distributions. In-sample optimization is separated from walk-forward evaluation with passive benchmarks and fees. Correlation is historical co-movement; incomplete coverage of held positions cannot establish diversification. Fixed robustness cases and leave-one-window-out diagnostics do not eliminate selection bias or establish a deployable market-wide strategy.

## Valuation and decision rules

Price times dated instant common shares approximates market capitalization. Annual diluted weighted-average shares are an EPS denominator and cannot replace an instant fully diluted share count. Cash and long-term-debt components require the same period and accession before an indicative enterprise subtotal. Leases, other borrowing, preferred stock, minority interests and investments can remain absent; a full enterprise/equity/share-price bridge is withheld.

Cash-flow DCF outputs are sensitivity scenarios driven by explicit growth, margin, discount and terminal assumptions. They are not independently estimated fair stock prices. Price/cash-flow ceilings are user-selected research conditions. Current assessment coverage uses a 550-day financial review policy and seven-day historical research window; these are disclosed application policies. Transaction-quality observations retain stricter 900-second stocks/funds and 300-second crypto safeguards, independently enforced by the server preview.

A proposed addition is illustrative: for selected cash amount A and 5-basis-point fee assumption, gross addition is A/1.0005; new concentration uses dated marked holdings and reduces account value by that fee. Exact tradable units, rounding, cash, account version and freshness must be rechecked by the existing server preview. Research calculations never authorize an order.

## NLP and offline work

Headline topic/tone and lexical analysis are retired from normal product views and request paths, while their protected archival endpoint, offline implementations and tests remain. They are exploratory descriptions, not verified investment sentiment forecasts. Offline Python AR/GARCH, factor, backtesting, option and integrated workflows remain tested research capabilities; their existence does not imply execution in each browser assessment. Optional imported filing archives and factor files are local session inputs, not independently authenticated data merely because a schema validates.

Source and checks: [current assessment](../../web/site/research_decision_v34.js), [ML](../../web/site/private_predictive_ml_v180.js), [risk](../../web/site/research_models_core_v22.js), [valuation](../../cloud/valuation_market_v73.py), [decision regressions](../../web/tests/consolidation_decision_v34.test.cjs), [financial/API guards](../../tests/test_consolidation_financial_v34.py), [model diagnostic tests](../../web/tests/consolidation_model_v34.test.cjs).

## Additional annual-ratio and evaluation provenance

The annual FCF proxy requires compatible CFO/capex source accessions, periods and available filing dates. Price/sales requires reported revenue lineage. Approximate market-cap/annual-net-income requires positive annual income, matching revenue accession and dated source evidence. Negative income yields no earnings multiple. Current common shares are not diluted weighted-average EPS shares. No four-quarter TTM roll-forward or complete equity value is fabricated.

Prediction Results identify L2 logistic classification, the existing five features, five-session outcome, actual training-feature dates and latest matured outcome. Interpretation distinguishes insufficient, exploratory, historically favorable and deteriorating evidence. Evaluation still reports chronological held-out results, baseline and Brier loss. A favorable historical diagnostic cannot establish calibrated profit probability or a multi-year investment edge.
