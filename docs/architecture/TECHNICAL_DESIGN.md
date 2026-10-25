# QuantForge V5 — Architecture and execution model

## Scope

A **single-user local application** plus independent Python quantitative-research modules. No cloud service, multiuser authorization, live broker integration or server-side hosted personal portfolio.

| Component | Source | Responsibility |
| --- | --- | --- |
| UI | `src/quantforge/desk/investment_desk.html` | Compact workspace, interactive form controls, optional detailed financial views |
| HTTP API | `src/quantforge/desk/server.py` | Local routing, argument validation, provider injection, security checks |
| Market observations | `desk/market.py`, `live/provider.py` | Alpaca IEX stock/ETF last trades and venue-specific crypto observations; demo substitutes unmistakably fictional values |
| Investment directory | `desk/catalog.py` | Curated 259-entry lookup by full name, symbol and category |
| Paper ledger | `desk/engine.py` | Atomic SQLite virtual buy/sell, average cost, ledger queries, mark-to-market and risk summaries |
| Private preferences/journal | `desk/companion.py` | Saved goals, horizon, comfort, cash reserve, watchlist and timestamped notes |
| Comparison | `desk/comparison.py` | Independent equal-budget what-ifs, computed without changing actual virtual holdings |
| SEC fundamentals | `desk/sec_research.py` | On-demand SEC ticker resolution and 10-K US-GAAP extraction with source accession/date metadata |
| Microsoft valuation | `desk/valuation.py`, `valuation/dcf.py` | Verify & display optional V3 outputs; forecast/discount cash flows only in separate analytical research track |
| Research modules | `risk/`, `forecasting/`, `regimes/`, `portfolio/`, `derivatives/`, `factors/` | Offline statistical/numerical experiments with explicit backtesting boundaries |
| Tests | `tests/` | Validation, failed inputs, cash accounting, provider mocks, SEC fixtures, modeling invariants |

## Market-data and transaction clock

1. UI requests a symbol, full company name, or comparison group.
2. Market adapter returns the most recent supported provider trade with **source and timezone-aware timestamp** (or fictional demo value).
3. Portfolio or decision calculations use this observation as an **approximate mark**, not an executable price or guaranteed fill.
4. **Virtual trade** requires quote age ≤900 s for stocks/ETFs or ≤300 s for crypto, a matching ticker and an expected-price deviation ≤1%. Stale observations may be researched but not used for a virtual fill.
5. The paper transaction is recorded in the **local SQLite database only**. No request goes to Alpaca's brokerage order API.

The server listens on `127.0.0.1:8765`, checks request Host/Origin for local access, limits JSON request sizes and avoids logging URL query strings. These are local safeguards, **not** a public-app authentication system.

## Persistent vs ephemeral data

| Information | Location | GitHub publication policy |
| --- | --- | --- |
| Virtual trades, cash, preferences, watchlist, research notes | `.private/*.sqlite3` (or user-selected SQLite path) | **Never commit** |
| Alpaca credentials | Current PowerShell environment variables | **Never commit** |
| Alpaca market observations | Memory / responses used locally; no quote-history database | **Do not publish vendor-derived snapshots** |
| SEC user agent / contact details | Current process environment | **Never commit** |
| SEC Company Facts JSON | Session-only in-memory cache in V5 interactive view | Only cite public filing data with context; no personal cache bundled |
| Demo snapshots | Fictional fixture generator and screenshot previews | Publish when conspicuously labeled **fictional** |
| SEC V3 valuation source output | User-controlled external folder; ignored output by default | Publish only after separate provenance/reuse review |

## Research track vs live desk

The current investment desk does **not** call historical GARCH, HMM, Ridge or boosted-forecast models to decide whether to buy a stock. These methods remain independently implemented research modules. This separation avoids representing academic proof-of-concept metrics as real-market advice. A future validated, licensed historical data feed would be necessary before integrating empirically calibrated risk/ML into the live experience.

## Dependency and execution boundaries

- Python 3.12 on Windows is the tested personal environment; CI targets Python 3.11 and 3.12.
- SQL persistence: `sqlite3` standard library; cash and quantities use `Decimal` before conversion to UI float.
- Numerical methods: NumPy, pandas, SciPy, scikit-learn; DuckDB/Parquet for older research artifacts.
- External services: Alpaca data endpoints when credentials exist; SEC EDGAR when user expressly requests 10-K company facts.
- CI builds reproducible synthetic runs independent of private accounts.

## Publication cleanup

There is a legacy `.github/workflows/pages.yml` from earlier site prototypes. **It is not part of the personal desk design and should not deploy the private app.** Remove or disable it before public GitHub release; see [publication checklist](../publication/RELEASE_CHECKLIST.md). Earlier historical website/FX files are separate legacy experiments, not the deployed QuantForge V5 UI.

## V5.2 SEC company models

Read-only `/api/company-dcf` and `/api/company-comparables` use the authenticated SEC user-agent, on-demand SEC Company Facts cache and local computation. The DCF module `desk/company_models.py` separately identifies observed annual accounting facts and analyst scenario assumptions. Fail closed on mandatory missing/ambiguous fields; output concept provenance, per-year FCFF and a 3×3 WACC/terminal growth sensitivity matrix. Neither endpoint touches brokerage or portfolio ledger state. See [methodology](../methodology/GENERAL_COMPANY_DCF.md).
