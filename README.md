# QuantForge 2.0

QuantForge is a financial research and software engineering project built to explore company financials, statistical uncertainty and hypothetical portfolios. It demonstrates applied statistical data science through traceable inputs, retained numerical engines, reproducible evaluation and an authenticated private experience.

[Public application](https://quantforge-648.pages.dev/) · [Current product](docs/current/PRODUCT.md) · [Architecture](docs/current/ARCHITECTURE.md) · [Research methodology](docs/current/METHODOLOGY.md) · [Technical interview guide](docs/current/TECHNICAL_INTERVIEW_GUIDE.md) · [Release status](docs/current/RELEASE_STATUS.md)

The seven authoritative current documents are this README and the six documents in [docs/current](docs/current/ARCHITECTURE.md). Start with [Product](docs/current/PRODUCT.md), [Methodology](docs/current/METHODOLOGY.md) and [Deployment/security/rollback](docs/current/DEPLOYMENT_SECURITY_ROLLBACK.md). [Documentation index](docs/README.md) identifies historical development records. Repository visibility remains private; no public-source licensing or market-data redistribution permission is implied.

## One application, five sections

| Section | Working research flow |
| --- | --- |
| Explore | Name search, source-labeled interactive history, SEC financial trends and filing lineage, evidence-backed briefing, balance-sheet evidence, guided investigation and versioned private thesis journal |
| Compare | 2–5 names, common-date normalized paths, financial contrasts, distributions, correlation, risk/return, sortable tables and safe CSV |
| Models | Prediction, Risk, Valuation and Strategy Testing; each has Results / Evaluation / Method with baselines, accessible equations, sensitivity and limitations |
| Portfolio | Overview, What If? and Portfolio Analysis; constrained allocations, covariance, Monte Carlo scenarios and authentic recorded virtual-account marks |
| Methods | Overview, Data, Statistical Methods and Engineering; walkthrough, SEC lineage, visual architecture and seven inspectable technical disciplines with source/test references |

Fresh visitors and the clickable brand open a compact, chart-free Home inside Explore. Its shared name/ticker suggestions select a company directly. Company selection carries across sections. Private opens My Briefing, with Research an Investment and My Portfolio as the three primary tasks. Its financial shortlist discloses exact SEC/provider coverage and source-comparability exclusions; individual assessments apply only explicitly selected conditions. Private company notes belong beside company research; virtual funding, holdings and transactions belong in Portfolio.

## Honest data modes

**Public:** Historical SEC Company Facts are real reported financial observations. Market-path demonstrations are deterministic synthetic inputs, explicitly labeled as such. They are not actual company stock prices or evidence of market predictive skill.

**Private:** Owner identity and Supabase authenticator MFA gate eligible Alpaca history, quotes and asset listings. Provider entitlement, dates and feed conventions remain visible. Version-checked Supabase state supports notes, saved briefings and virtual transactions. **No live trading:** all transactions are virtual; there is no real-money order execution.

Recorded virtual-account history starts only when the owner requests server-verified marks. Deposits and withdrawals change contributed capital; they are not gains. Unrecorded historical account values and unsupported time-weighted percentage returns are not fabricated. A missing provider disables the affected output instead of substituting simulated private data.

## Technical evidence

| Discipline | Implementation | Reproducible checks |
| --- | --- | --- |
| SEC data engineering | [Snapshot ETL](tools/build_public_sec_snapshot.py), [financial transformations](web/site/sec_analytics.js) | [Snapshot validation](tests/test_public_sec_snapshot.py), [metric fixtures](web/tests/sec_analytics.test.cjs) |
| Analysis and communication | [Shared research flow](web/site/research_app_v20.js), [comparison and portfolio arithmetic](web/site/research_compare_portfolio_v21.js) | [Numerical comparison tests](web/tests/research_compare_portfolio_v21.test.cjs) |
| Statistical ML | [L2 five-session direction classifier](web/site/private_predictive_ml_v180.js) | [Mature-label, chronological and baseline tests](web/tests/private_predictive_ml_v180.test.cjs) |
| Statistics and risk | [Returns, volatility, VaR/ES, drawdown and moving blocks](web/site/research_models_core_v22.js) | [Numerical and input guards](web/tests/research_models_core_v22.test.cjs) |
| Financial scenarios | [Cash-flow proxy DCF and rate sensitivity](web/site/research_models_core_v22.js) | [Scenario calculation tests](web/tests/research_models_core_v22.test.cjs) |
| Optimization and backtesting | [Constrained optimizer](web/site/private_optimizer.js), [rolling allocation](web/site/private_walkforward_v65.js) | [Optimizer](web/tests/private_optimizer.test.cjs), [forecast/walk-forward](web/tests/private_research_v65.test.cjs) |
| Archived experimental NLP (retired from product) | [Sparse TF-IDF, cosine topics and negation-aware lexical tone](cloud/news_intelligence_v180.py) | [Text and endpoint fixtures](tests/test_news_intelligence_v180.py) |
| Software and cloud | [FastAPI](cloud/api.py), [same-origin proxy](functions/api/[[path]].js), [deterministic builder](tools/build_unified_site.py) | [Owner/MFA/API](tests/test_hosted_web.py), [snapshot accounting](tests/test_valuation_snapshots.py), [three-browser acceptance](tools/smoke_completion_browser.py) |

Methods → Engineering presents the same evidence in the running application, without requiring repository access. The repository remains private; historical release documents are retained for traceability rather than describing the current navigation.

## Architecture and deliberate choices

```text
SEC Company Facts → validated annual snapshot → public static research
Synthetic paths  → reproducible public numerical experiments

Browser → Cloudflare same-origin proxy → FastAPI / Vercel Hobby (recovered API)
                                      |-- owner + authenticator verification
                                      |-- Supabase RLS / versioned virtual state
                                      `-- entitled Alpaca assets and prices

Eligible inputs → retained pure engines → scoped evidence → shared five-section UI
```

Native JavaScript avoids a framework rewrite; native MathML avoids an external equation script. The static build retains three CSP-hashed scripts. Provider credentials and owner state stay outside public assets. Optional revision archives and daily FF3 data are bounded, local-to-session inputs; routine research does not require uploads. ETF proxy factors are not official Fama–French factors.

## Evaluation and limitations

Logistic direction is not a dollar-price forecast. Accuracy, Brier, calibration counts and a historical-frequency baseline describe later test windows, with weak signals withheld. Historical covariance fits are separate from rolling out-of-sample diagnostics. Selection, survivorship, fees, price adjustments, dividends and regime changes limit backtests. Circular moving-block intervals describe historical volatility sensitivity, not calibrated future loss bounds.

DCF discounts an operating-cash-flow-minus-capex proxy under explicit assumptions. It does not establish FCFF, enterprise value, equity value or a fair share-price target. Current SEC snapshots do not establish what an original filing said at every past decision date. Missing values remain unavailable rather than zero.

## Verification

Use an existing Python 3.12 environment with the project's dependencies. The recovery checkout does not contain its own `.venv`; the commands below assume an activated environment:

```powershell
python -m ruff check .
python -m pytest -q
node --test (Get-ChildItem web/tests -Filter '*.test.cjs' | ForEach-Object FullName)
python tools/build_unified_site.py
python tools/audit_public_bundle.py
python tools/prepublish_check.py
python tools/smoke_completion_browser.py
```

Local consolidation acceptance passed 651 Python and 466 JavaScript tests, lint/privacy/CSP/determinism checks and all 17 browser scripts. The new workflow matrix uses three engines and five widths with zero fixture-account writes. Exact-head CI and production acceptance remain separate release gates; current evidence is linked from [Release status](docs/current/RELEASE_STATUS.md). Private automated writes elsewhere in retained tests use isolated fixtures; live owner verification is read-only.

## Research and limits

One current assessment connects compatible annual financials, observed downside, held-out model diagnostics, observed-price ratios and actual virtual exposure. Optional explicit conditions can produce conditional research actions; they do not infer suitability, demonstrate profitable investing or execute a transaction. The universe screen is a disclosed financial filter, with at most five principal candidates and inspectable exclusions. It has no validated whole-market investment advantage.

Balance-sheet ratios require compatible filing accessions. Missing concepts remain null. Annual diluted weighted-average EPS shares are distinguished from instant common shares; complete enterprise claims, quarterly/TTM reconstruction, verified fund look-through and full diluted per-share valuation remain unsupported.

Thesis revisions append records and preserve earlier text/timestamps. A full 100-note archive refuses additions rather than silently truncating. Review dates are on-demand prompts, not scheduled alerts. Recorded virtual-account values are owner-requested marks; capital contributions are separate from gains.

Headline NLP is retained as tested archival/offline research, not a current recommendation input or normal product view. The original statistical, ML, optimization, backtesting and NLP engines remain in source. Their execution boundaries are explained in [Methodology](docs/current/METHODOLOGY.md) and the [Interview guide](docs/current/TECHNICAL_INTERVIEW_GUIDE.md).

Historical development records remain in [the documentation index](docs/README.md). Current operations use [Deployment, security and rollback](docs/current/DEPLOYMENT_SECURITY_ROLLBACK.md); older Render or candidate descriptions do not override it. Repository visibility remains private pending a separate authorized decision on history metadata, licensing, provider rights and untrusted preview isolation.

## Bounded company research

In Private My Briefing, **Analyze shortlisted companies** runs one to five selected financial-screen candidates, three by default. Studies run sequentially and independently of the open company. Each displays progress, a canonical research disposition, supporting and opposing evidence, dates and incomplete coverage. A failed provider request for one name preserves other results. Opening full research refreshes that company; batch cards are dated session snapshots, not saved recommendations or background alerts.

[Company-study adapter](web/site/research_study_v35.js) reuses the existing deep engines and [single assessment authority](web/site/research_decision_v34.js). Account-version, source-universe, assumptions, authentication and mode transitions invalidate session results. The workflow does not write notes, cash, holdings or transactions. [Adversarial tests](web/tests/definitive_batch_v35.test.cjs) and [three-browser journey](tools/smoke_definitive_v35.py) cover partial failure and late responses.

Annual earnings multiples require compatible reported net-income lineage. They approximate market capitalization divided by annual net income, not diluted-EPS P/E or intrinsic value. Unverified TTM and the complete enterprise-to-diluted-equity bridge remain explicitly unavailable. Public Home is search-first; Explore highlights precede charts; model interpretation precedes evaluation metrics. Technical depth remains available in supporting evidence and Methods.

Protected HTTP 401/403 responses immediately clear local Private evidence and cancel pending studies through the existing client cleanup. Provider/network failures retain their separate incomplete/failed states. This does not submit server logout or modify owner records. Portfolio charts remeasure visible pane widths without fetching additional prices; selected Methods controls retain readable hover contrast.
