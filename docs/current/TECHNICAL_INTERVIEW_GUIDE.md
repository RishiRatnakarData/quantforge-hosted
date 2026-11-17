# Technical learning and interview guide

## A defensible introduction

“I built a financial research application that connects traceable SEC fundamentals, statistical experiments and a protected virtual portfolio. The Public experience demonstrates the methods with reported statements and labeled synthetic market paths. The Private experience uses authenticated provider data and persisted owner records. I designed the system to withhold unsupported conclusions, preserve provenance and test both arithmetic and user workflows.”

Do not claim a profitable trading system, calibrated return forecasts, complete market coverage or a full institutional valuation platform. A strong engineering story is demonstrated judgment about evidence and limitations.

## Five-minute demonstration

1. Search a company in Public Explore. Explain which facts came from SEC filings and which market path is a synthetic teaching fixture. Inspect a fiscal period, accession and missing value.
2. Compare compatible companies. Inspect common dates, differences in fiscal year, a return distribution and historical correlation.
3. Open Models Prediction → Evaluation → Method. Explain the baseline, mature-label training boundary, Brier error and why a model score is not a probability of profitable trading.
4. Open a valuation sensitivity and portfolio scenario. Change an assumption and explain the mechanism, units and missing claims.
5. Open Methods Engineering and describe the API/authentication boundary and reproducible tests. An authorized owner can separately show My Briefing, a financial shortlist, saved research and a read-only virtual account.

Use Public or clearly labeled isolated fixtures for screenshots shared with employers. Never expose owner notes, holdings, email addresses, credentials or entitled market-data exports as career evidence.

## Architecture and authentication

**Problem:** Share a useful demonstration while protecting personal research and licensed data. **Inputs:** static statements, owner identity, provider credentials kept server-side and versioned state. **Method:** a shared client, same-origin Pages proxy, Vercel FastAPI, Supabase identity/MFA and provider adapters.

**Undergraduate explanation:** The browser is an untrusted client. A hidden button is not authorization; the API checks the owner and MFA every time a protected endpoint is called. Restoring a session asks the server whether a previously verified session is still valid.

**Advanced defense:** The proxy uses an exact upstream allowlist and server-only authentication header; client headers cannot assert privileged identity. Session-cookie protections, origin checks, no-store responses, generated CSP, account versions and replay IDs address different risks. A valid request can still lack provider entitlement. Missing data is distinct from missing authentication. The new universe endpoint calls the existing owner guard before any provider read.

**Test/limitation:** Hosted API and proxy tests exercise denials, malformed origins, stale sessions, MFA assurance and version conflicts. Browser fixture sign-in is not independent live MFA acceptance. The infrastructure depends on free-tier quotas and third-party availability.

Source: [API](../../cloud/api.py), [proxy](../../functions/api/[[path]].js), [new API guard cases](../../tests/test_consolidation_financial_v34.py).

## SEC ingestion and data engineering

**Problem:** A number without units, period or filing lineage is not a defensible financial observation. **Inputs:** SEC Company Facts, issuer CIK, annual tags, period boundaries and filing dates. **Method:** bounded annual selection, explicit tag priority, null preservation and source ledgers; dynamic reads respect configured SEC identification and request pacing.

**Undergraduate explanation:** Annual revenue is a flow over a year; cash is a stock at one date. An annual weighted-average diluted share count is another type of quantity. Combining different types because they are all numeric creates misleading ratios.

**Advanced defense:** Company Facts can include later restatements and differing revenue concepts. An as-of cutoff and accession ledger improve traceability but do not magically recreate all original filings. New screening checks accession/period consistency and stable growth tags. Margins above 100% trigger source-comparability review rather than an attractive rank. This is a conservative exclusion heuristic, not a universal accounting identity or proof that the raw fact is wrong.

**Test/limitation:** Annual-duration, future-filing, issuer mismatch, missing capital, mixed accession and weighted-versus-instant share cases are deterministic tests. Whole-market financial coverage and industry-normalized total revenue are not claimed.

Source: [annual ETL](../../tools/build_public_sec_snapshot.py), [live fundamentals](../../cloud/sec_fundamentals.py), [capital extraction](../../cloud/valuation_market_v73.py).

## Statistical ML and leakage

**Problem:** Test whether past price features explain later direction better than a simple historical-frequency baseline. **Inputs:** positive dated equity closes; lagged 5/20/60-session log returns, 20-session volatility and 40-session drawdown. **Method:** L2 logistic regression, expanding chronological training and five-session nonoverlapping test outcomes.

**Undergraduate explanation:** Logistic regression forms a weighted combination of standardized features and maps it through a sigmoid. L2 regularization discourages extreme coefficients. If tomorrow's outcome is used to train yesterday's model, the apparent success is leakage.

**Advanced defense:** A training label is admitted only when its entire five-session future outcome has matured by the test feature date. Standardization uses the training set only; values are clipped to ±5. The implementation uses 260 fixed gradient steps, learning rate 0.085 and coefficient 0.16, without claiming tuned optimality. A chronological holdout avoids random-shuffle leakage, but overlapping training examples, selected instruments and hyperparameter choice still limit inference.

Brier score is the mean of (score − binary outcome)²; lower is better. Accuracy is the share of correctly classified outcomes. A high constant-class accuracy can reflect imbalance rather than skill. The baseline's expanding positive-outcome frequency is therefore important. Three score bins describe historical reliability; they do not establish future calibration.

The new deterioration review compares early and recent mean paired losses against that same baseline. Both halves require 12 disjoint tests. A reversal from improvement below −0.005 to disadvantage above +0.005 withholds direction. It is descriptive; a confidence interval, hypothesis test or proven regime change must not be implied.

**Test/limitation:** Mature-label boundaries, invalid inputs, fixed baseline comparisons, deterministic results and constructed deterioration examples are tested. Tests do not establish profitable forecasting. Five-session direction omits spread, execution, dividends, taxes and future regime changes.

Source: [classifier](../../web/site/private_predictive_ml_v180.js), [original regression tests](../../web/tests/private_predictive_ml_v180.test.cjs), [deterioration cases](../../web/tests/consolidation_model_v34.test.cjs).

## Risk and uncertainty

**Problem:** Describe variability and loss in the observed sample without pretending they bound future risk. **Method:** log returns, annualized sample variability, empirical tail measures, drawdown, rolling windows and moving-block bootstrap sensitivity.

**Undergraduate explanation:** Standard deviation measures fluctuation around the mean. Drawdown measures decline from a previous high. VaR is a loss quantile; expected shortfall averages observations in the bad tail. They answer different questions.

**Advanced defense:** Square-root annualization assumes an aggregation convention that can be unreliable under dependence and changing regimes. Empirical tails are noisy in short samples. Moving blocks retain some local dependence unlike independent resampling, but remain conditional on the historical sample and block choice. Neither an observed maximum loss nor a bootstrap range is a future guarantee. Equity sessions and crypto calendar days cannot be silently mixed in multi-asset annualization.

Source: [risk](../../web/site/research_models_core_v22.js), [comparison calculations](../../web/site/research_compare_portfolio_v21.js), [risk regression tests](../../web/tests/research_models_core_v22.test.cjs).

## Optimization and backtesting

**Problem:** Explore how covariance, constraints and trading costs affect hypothetical allocations. **Method:** retained constrained optimizers, equal-weight and passive comparisons, seeded Monte Carlo scenarios, chronological walk-forward and fixed robustness cases.

**Undergraduate explanation:** Portfolio variance is wᵀΣw. Combining assets can reduce variability when their moves are imperfectly correlated. Fitting the lowest historical variance weights does not guarantee the lowest future risk.

**Advanced defense:** Covariance estimates can be unstable; constraints and regularization trade flexibility for robustness. Separate in-sample fit from rolling held-out performance, use common evaluation dates and account for fees. Leave-one-window-out sensitivity asks whether a conclusion depends on one period; it is not a cure for universe selection, survivorship or repeated experimentation. ETF co-movement is not fund look-through diversification. Missing correlations for any held name cannot satisfy an explicitly selected all-holdings overlap rule.

**Test/limitation:** Numerical constraints, equal-weight baselines, transaction fees, date alignment and engine retention are tested. A selected-basket allocation experiment does not validate the new financial screener as a market-wide investment strategy.

Source: [deep adapter and retained engines](../../web/site/research_deep_v25.js), [current rule tests](../../web/tests/consolidation_decision_v34.test.cjs).

## Valuation and financial judgment

**Problem:** Separate market price, accounting performance and assumed future value. **Method:** dated price/common-share multiples, annual cash-flow proxy and scenario DCF sensitivity, with missing-claim gates.

**Undergraduate explanation:** A good business can be expensive. Discounting converts assumed future cash flows to present value. Changing growth, margin, discount rate or terminal assumptions can change that value materially.

**Advanced defense:** Operating cash flow less capex is not a complete unlevered FCFF model. A full enterprise bridge needs all relevant claims and investments, and a diluted per-share bridge needs appropriate share evidence. An annual EPS denominator is not an instant fully diluted share count. Combining cash and debt from different filings can be inconsistent even when their date matches. The current application deliberately withholds unsupported full equity/share-price outputs.

**Test/limitation:** Same-period/different-accession cases, future filings, stale shares, absent diluted facts and positive-denominator multiples are tested. A user-chosen price/cash-flow ceiling is a rule assumption, not an objectively correct intrinsic value.

Source: [valuation extraction](../../cloud/valuation_market_v73.py), [ratio calculations](../../web/site/private_value_v73.js), [valuation regressions](../../tests/test_market_value_v73.py).

## Screening and one current assessment

**Problem:** Prioritize research without manufacturing certainty from a weighted score. **Method:** exact eligible-universe financial filters followed by individual source-qualified assessments. A single current report joins facts, risk, value, model limitations and actual virtual exposure under explicit optional conditions.

**Undergraduate explanation:** Filtering is not prediction. An issuer can pass the business screen and still fail a price, risk or concentration condition. A missing input cannot count as a favorable zero.

**Advanced defense:** Financial filters are disclosed deterministic judgments; they have no demonstrated out-of-sample excess-return advantage. We order by one visible quantity rather than claiming a statistically justified composite score. Per-company evidence is keyed by company revision and owner version. Repeated identical in-flight studies share work; stale responses cannot overwrite a new context. Rules are tab-local, clear on mode exit and never infer suitability.

**Test/limitation:** Tests cover strong-but-expensive, price momentum with weak fundamentals, drawdown and concentration breaches, unknown fund evidence, stale observations, malformed deterioration flags, incomplete correlation, zero candidates and changed filing concepts. Browser tests verify default briefing, navigation, private cleanup and zero account mutations across three engines and five widths.

Source: [decision engine](../../web/site/research_decision_v34.js), [workspace](../../web/site/research_workspace_v34.js), [browser acceptance](../../tools/smoke_consolidation_v34.py).

## Virtual-account correctness and NLP

Virtual account value, deposits and profit are distinct. Decimal fees, average-cost basis, expected versions, replay IDs and explicit preview/confirmation preserve bookkeeping. Legacy positions without recorded basis cannot have invented cost or P&L. Recorded account marks are owner-requested snapshots; time-weighted percentage returns need valuations at external flows and are withheld when unsupported.

Headline NLP describes covered text with source/topic/tone limitations. A lexical method can misread negation, context or sarcasm; a topic label is not an alpha forecast. Retained offline NLP/statistical workflows should be demonstrated with their actual inputs and tests rather than presented as stronger hosted models.

## Questions to rehearse

- Why is an authentic SEC source insufficient to guarantee a comparable ratio?
- How do you know each training label existed at the evaluation date?
- Why compare Brier error as well as accuracy? What would proper calibration validation require?
- Why is a 550-day financial policy different from a 900-second transaction quote rule?
- How could a strategy beat equal weights in one sample and still have no demonstrated edge?
- What happens when a provider fails midway through company research or the owner signs out?
- Which features run in the normal hosted application, and which remain offline experiments?
- What evidence would be needed before calling this a complete valuation, suitability or profitable trading system?

Good answers identify an implementation, a test and a remaining limitation. They do not replace missing empirical evidence with stronger wording.
