# QuantForge 2.0

QuantForge is a financial research and software engineering project built to explore company financials, statistical uncertainty and hypothetical portfolios. It demonstrates applied statistical data science through traceable inputs, retained numerical engines, reproducible evaluation and an authenticated private experience.

[Public application](https://quantforge-648.pages.dev/) · [Current feature parity and acceptance](docs/CODEX_REBUILD_PROGRESS.md) · [Research methodology](docs/methodology/QUANT_RESEARCH_METHODS.md)

## One application, five sections

| Section | Working research flow |
| --- | --- |
| Explore | Name search, source-labeled interactive history, SEC financial trends and filing lineage, evidence-backed briefing, dated private news and contextual saved research |
| Compare | 2–5 names, common-date normalized paths, financial contrasts, distributions, correlation, risk/return, sortable tables and safe CSV |
| Models | Prediction, Risk, Valuation and Strategy Testing; each has Results / Evaluation / Method with baselines, accessible equations, sensitivity and limitations |
| Portfolio | Overview, What If? and Portfolio Analysis; constrained allocations, covariance, Monte Carlo scenarios and authentic recorded virtual-account marks |
| Methods | Overview, Data, Statistical Methods and Engineering; walkthrough, SEC lineage, visual architecture and eight inspectable technical disciplines with source/test references |

The clickable brand opens a compact Home inside Explore. Company selection carries across sections. Private company notes belong in Explore; virtual funding, holdings and transactions belong in Portfolio.

## Honest data modes

**Public:** Historical SEC Company Facts are real reported financial observations. Market-path demonstrations are deterministic synthetic inputs, explicitly labeled as such. They are not actual company stock prices or evidence of market predictive skill.

**Private:** Owner identity and Supabase authenticator MFA gate eligible Alpaca history, quotes, asset listings and news. Provider entitlement, dates and feed conventions remain visible. Version-checked Supabase state supports notes, saved briefings and virtual transactions. There is no real-money order execution.

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
| NLP | [Sparse TF-IDF, cosine topics and negation-aware lexical tone](cloud/news_intelligence_v180.py) | [Text and endpoint fixtures](tests/test_news_intelligence_v180.py) |
| Software and cloud | [FastAPI](cloud/api.py), [same-origin proxy](functions/api/[[path]].js), [deterministic builder](tools/build_unified_site.py) | [Owner/MFA/API](tests/test_hosted_web.py), [snapshot accounting](tests/test_valuation_snapshots.py), [three-browser acceptance](tools/smoke_completion_browser.py) |

Methods → Engineering presents the same evidence in the running application, without requiring repository access. The repository remains private; historical release documents are retained for traceability rather than describing the current navigation.

## Architecture and deliberate choices

```text
SEC Company Facts → validated annual snapshot → public static research
Synthetic paths  → reproducible public numerical experiments

Browser → Cloudflare same-origin proxy → FastAPI / Render
                                      ├─ owner + authenticator verification
                                      ├─ Supabase RLS / versioned virtual state
                                      └─ entitled Alpaca assets, prices and news

Eligible inputs → retained pure engines → scoped evidence → shared five-section UI
```

Native JavaScript avoids a framework rewrite; native MathML avoids an external equation script. The static build retains three CSP-hashed scripts. Provider credentials and owner state stay outside public assets. Optional revision archives and daily FF3 data are bounded, local-to-session inputs; routine research does not require uploads. ETF proxy factors are not official Fama–French factors.

## Evaluation and limitations

Logistic direction is not a dollar-price forecast. Accuracy, Brier, calibration counts and a historical-frequency baseline describe later test windows, with weak signals withheld. Historical covariance fits are separate from rolling out-of-sample diagnostics. Selection, survivorship, fees, price adjustments, dividends and regime changes limit backtests. Circular moving-block intervals describe historical volatility sensitivity, not calibrated future loss bounds.

DCF discounts an operating-cash-flow-minus-capex proxy under explicit assumptions. It does not establish FCFF, enterprise value, equity value or a fair share-price target. Current SEC snapshots do not establish what an original filing said at every past decision date. Missing values remain unavailable rather than zero.

## Verification

Use this checkout's configured `.venv`, not an interpreter from an older checkout:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
node --test (Get-ChildItem web/tests -Filter '*.test.cjs' | ForEach-Object FullName)
.\.venv\Scripts\python.exe tools/build_unified_site.py
.\.venv\Scripts\python.exe tools/audit_public_bundle.py
.\.venv\Scripts\python.exe tools/prepublish_check.py
.\.venv\Scripts\python.exe tools/smoke_completion_browser.py
```

The current candidate passes 580 Python and 399 JavaScript tests, plus the original A–D journeys, full-route browser matrix and completed-engine journeys in Chromium, Firefox and WebKit at desktop/mobile widths. Private automated journeys use isolated fixtures, never real credentials or account writes. GitHub Actions and deployment evidence must be matched to the release SHA; automated tests do not certify live provider entitlement or owner persistence. Those remain separate owner checks.
