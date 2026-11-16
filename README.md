# QuantForge 2.0

QuantForge is a financial research and software engineering project built to explore company financials, statistical uncertainty and hypothetical portfolios. It demonstrates applied statistical data science through traceable inputs, retained numerical engines, reproducible evaluation and an authenticated private experience.

[Public application](https://quantforge-648.pages.dev/) · [Current product and reliability release](docs/FINAL_RELEASE32.md) · [Research methodology](docs/methodology/QUANT_RESEARCH_METHODS.md)

## One application, five sections

| Section | Working research flow |
| --- | --- |
| Explore | Name search, source-labeled interactive history, SEC financial trends and filing lineage, evidence-backed briefing, balance-sheet evidence, guided investigation and versioned private thesis journal |
| Compare | 2–5 names, common-date normalized paths, financial contrasts, distributions, correlation, risk/return, sortable tables and safe CSV |
| Models | Prediction, Risk, Valuation and Strategy Testing; each has Results / Evaluation / Method with baselines, accessible equations, sensitivity and limitations |
| Portfolio | Overview, What If? and Portfolio Analysis; constrained allocations, covariance, Monte Carlo scenarios and authentic recorded virtual-account marks |
| Methods | Overview, Data, Statistical Methods and Engineering; walkthrough, SEC lineage, visual architecture and seven inspectable technical disciplines with source/test references |

Fresh visitors and the clickable brand open a compact, chart-free Home inside Explore. Its shared name/ticker suggestions select a company directly. Company selection carries across sections. Private company notes belong in Explore; virtual funding, holdings and transactions belong in Portfolio.

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

The published baseline `4fc1a46` passed 613 Python / 413 JavaScript tests and candidate/main CI before this improvement assignment. These are historical baseline counts, not claims about an untested candidate. Current release evidence, verification scope and deployment identifiers are recorded in [the release guide](docs/GUIDED_RESEARCH_RELEASE.md) and the external release record for the final SHA. Private automated writes use isolated fixtures; real owner persistence remains separately controlled.

## Guided investment research

Explore separates reported annual financials, authenticated observed market history, evidence-grounded briefing and private saved research. The guided process connects business understanding, financial performance, valuation assumptions, historical risk, alternatives and a revisitable investment thesis. No score, Buy/Hold/Sell verdict or personal allocation recommendation is generated.

The balance-sheet exhibit adds cached, source-linked SEC instant facts at covered annual fiscal ends. Ratios require compatible same-accession inputs. Missing concepts remain null; current/noncurrent long-term debt components are not labeled complete total debt. Quarterly/TTM reconstruction, verified fund holdings/fees and a full diluted-share valuation bridge remain outside this release.

Theses use the existing MFA-protected notes store. Revisions append records; original notes and timestamps remain. A full 100-note archive refuses new records instead of silently truncating history. Review dates do not create scheduled reminders.

News/headline tone has been retired from normal public/private UI and request paths because it demonstrated limited investment decision value. SEC filing provenance remains attached to financial evidence. Experimental NLP implementations and regression fixtures remain in source; the authenticated archival API remains owner-gated for compatibility and is not called by the product.

## Historical engineering evidence

Earlier audit documents describe their stage at the time they were written. The November 10 work and November 12 final-24/quality work were subsequently published in `4fc1a46`; their former “unpublished” labels do not describe current production. Retained records: [24-issue register](docs/FINAL_24_ISSUE_REGISTER.json), [engine parity](docs/FINAL_24_ENGINE_PARITY.md), [quality review](docs/QUALITY_REVIEW_2026_11_12.md).

Private Company briefing automatically synthesizes covered financial evidence, observed downside, existing held-out predictive evaluation and virtual-holding context. Optional tab-local research preferences frame questions without creating suitability scores. Login waits for bounded health readiness before submitting credentials once; it does not replay uncertain logins or account mutations. See [the current release guide](docs/FINAL_RELEASE32.md) for implementation and acceptance boundaries.

Current deployment source and rollback: [Vercel recovery guide](docs/VERCEL_RECOVERY_DEPLOYMENT.md). Historical Render availability documents do not describe the recovered routing.
