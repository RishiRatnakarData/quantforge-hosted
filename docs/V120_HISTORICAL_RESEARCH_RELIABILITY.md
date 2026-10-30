# QuantForge V12.0 — Historical Research Reliability and Fixed Sensitivity Study

## Purpose

V12.0 combines three practical research improvements: (1) transparent execution cost accounting in the V11 point-in-time cross-company screen, (2) a *prespecified* 18-scenario sensitivity matrix, and (3) a local historical SEC issuer/date reliability audit. These are not investment recommendations and cannot initiate trades.

## Corrected V11 execution convention

For each non-overlapping evaluation interval, the decision uses only archived SEC filing facts available no later than its decision boundary, as well as trailing historical prices. Outcomes run from the **next close** to the test-window's last close. Both model and equal-weight benchmark enter and fully liquidate each interval. Each invested model interval pays proportional entry and exit costs; the benchmark pays equal-weight entry and exit costs each interval. Cash windows pay no trading cost. This deliberately models **flat exposure between intervals**, not continuous possession of a self-financing portfolio. Boundary-day returns, dividends and spread/slippage remain unmeasured. Thus V11 result values can change when rebuilt under the corrected accounting convention.

## Prespecified robustness study

The fixed 18 combinations are **2 evaluation lengths** (10, 21 observation sessions), **3 trailing drawdown screens** (15%, 25%, 35%), and **3 transaction fees** (0, 10, 30 basis points per trade side). Training is 126 observations, the same dated archive and selected 2–5-company universe are used. The model compares a restricted revenue-growth/FCF-margin/price drawdown rule versus interval equal-weight benchmarks. No hyperparameter optimization or "best setting" is offered. Scenario comparisons across different holdout lengths have different investment periods and must not be ranked by headline cumulative return.

If any scheduled interval lacks complete, dated SEC evidence for one of the selected issuers, performance for that scenario is withheld. The interface shows all 18 outcomes or why each is unavailable, including missingness. This is descriptive sensitivity, not a cross-validated prediction claim or a statistical significance test.

## Local 94-issuer reliability report

`tools/assess_sec_reliability_v120.py` rebuilds V11's January/July filing eligibility panel from the already-collected V10 archive, validates issuer-date matrix completeness, detects look-ahead filing dates, then writes the following exclusively under ignored `data/`:

- `data/sec_reliability_v120.json`: total issuer/date denominator, availability by year, missingness classification, and per-issuer reliability summary.
- `data/sec_reliability_issuers_v120.csv`: per-company coverage, earliest/latest qualifying checkpoint, longest continuous run, later-version windows, median filing delay and leading missing evidence.

The offline archive, SEC financial figures and historical prices are **not added to Git**. A late or missing company remains in the historical study's denominator; low coverage is reported, not hidden. Later versions of facts do not necessarily represent accounting corrections.

## Browser and publication boundaries

The existing private MFA-protected Research Hub, Research Lab and Briefing receive a new read-only panel. Raw imported SEC data remains in the browser session. The short export includes only policy scenario results and stated limitations; it omits account positions, credentials, SEC source facts and raw historical closes. A logout or invalidation clears the connected findings as in V11.0. The new helper does no network requests, persistent storage, MFA changes or order calls.

The guarded installer requires exact `main` commit `0e9a1ef4b6b79ad4d143e0a7bbd3128d6e558c05`, a clean tree, expected source SHA checks, deterministic three-script CSP build, all Python/JS tests, Ruff, public/privacy audits, exact approved changed paths and successful GitHub CI before declaring a release. If code publication succeeds but the local archival report fails, rerun **only** `python tools/assess_sec_reliability_v120.py` from the configured venv; never replay the release installer.

## Known limitations and acceptance

Current universe is selected from today's supported companies, creating survivorship bias; SEC Company Facts does not guarantee retention of all superseded original filings. Historical delistings, distributions, corporate-action adjustment reliability, bid/ask costs, slippage, broker implementation and taxes are not reconstructed. The study is not a full decision-policy replay and does not measure future predictive validity. Automated CI/CSP cannot prove live MFA or live provider/browser behavior; those require separate manual acceptance. This release does not introduce any paid service.
