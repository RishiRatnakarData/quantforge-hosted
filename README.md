> **V5.6.1 hosted MFA security upgrade:** See [Windows/deployment guide](docs/MFA_UPGRADE_V5_6_1.md). The public demo is unchanged; the private workspace now requires an authenticator code and Supabase AAL2 RLS. The source archive alone does not deploy these changes.

## Optional hosted website (V5.6 staging)

One Cloudflare Pages website supports a no-login **fictional public demo** and an
owner-only **My workspace** backed by Render, Supabase Auth and protected read-only
Alpaca market data. **Not deployed yet.** Hosted quant/valuation/peer calculations
currently use synthetic browser methods; the extensive Python models are in the
local application and are not claimed to power those hosted panels.

[Free hosting, security, and setup instructions](docs/HOSTED_WEBSITE_V5_6.md)

# QuantForge — Personal Investment Desk

A local Python application for my own stock, ETF, and cryptocurrency research. I built it to make investment comparisons, portfolio exposure, company financial statements, and financial risk easier to analyze without placing real brokerage orders.

**Python · NumPy · pandas · SciPy · scikit-learn · SQLite · SEC EDGAR · Alpaca Market Data · pytest · GitHub Actions**

[Features](#features) · [Verified results](#verified-results) · [Screenshots](#screenshots) · [Architecture](#architecture) · [Quantitative methods](#quantitative-methods) · [Run locally](#run-locally) · [Technical documentation](#technical-documentation)



## V5.4.1 — Release verification and privacy checks

Clean-up release: correct a missing-value counter in the ML peer table, remove an unused local, fix documentation links, and add an offline **prepublication check** to CI. This does not change saved virtual holdings or place brokerage orders.

Before publishing source, run `python tools/prepublish_check.py`. It catches obvious private datasets, local databases, secret-looking tokens, personal contact emails and broken Markdown links. **It cannot inspect the contents of screenshots or previous Git history; manual review is still required.**

[Windows/local evidence and outstanding checks](docs/evidence/VERIFICATION_V5_4.md) · [GitHub publication checklist](docs/publication/RELEASE_CHECKLIST.md)

## V5.4 — SEC fundamental ML peers

Under **Research → Company peers (ML)**, compare a stock's latest SEC 10-K financial profile against a selected group using five standardized fundamental ratios. The view displays the closest companies, fiscal dates, missing-data evidence, and a leave-one-feature-out stability check. **IsolationForest is a sample-relative exploratory outlier ranking only** and is unavailable with fewer than 12 complete-enough issuer records. No investment recommendation or live return prediction is produced.

[ML methodology and limitations](docs/methodology/SEC_FUNDAMENTAL_ML_V5_4.md) · [V5.4 release notes](RELEASE_NOTES_V5_4.md)


## V5.3 — Quantitative portfolio research

Open **Quant** to analyze an imported historical daily closing-price dataset or fetch personal Alpaca historical daily bars for selected U.S. stocks and ETFs. The analysis shows correlation, Ledoit–Wolf covariance, portfolio risk contributions, constrained minimum-variance weights with turnover regularization, and paired Monte Carlo downside scenarios. **These are estimates conditional on the supplied data and assumptions, not stock recommendations.** Existing Portfolio VaR is still a different, assumption-based model.

The app runs with **no historical data** until you import or fetch it explicitly. Use `examples/fictional_adjusted_prices.csv` solely for demonstration. The dataset is entirely fictional. Real personal data and private licensed market observations must not be committed.

[Technical methodology](docs/methodology/QUANT_PORTFOLIO_V5_3.md) · [Release notes](RELEASE_NOTES_V5_3.md)


## Project overview

QuantForge combines a private, forward-only paper portfolio with on-demand financial research. It retrieves the **last observed** market trade from an authenticated provider, calculates the effect of a hypothetical investment, and keeps the portfolio, watchlist, and research journal in a local SQLite database. Financial statements are loaded separately from public SEC filings when requested.

The quantitative research modules cover risk estimation, allocation, volatility forecasting, regime models, Monte Carlo, options, and discounted cash flow. **The live desk does not present those historical ML experiments as verified real-time trading signals.**

## Verified results

| Area | Evidence | Qualification |
| --- | --- | --- |
| Code quality | **165 automated tests passed** on Windows / Python 3.12 for V5.0; **171 passed** on Windows for V5.1; **175 passed** on Windows for V5.2; **186 passed** on Windows for V5.3; **194 passed, 6 non-blocking warnings** on Windows for V5.4; V5.4.1 includes an ML display correction and publication guard tests | Live IEX history, SEC DCF and 12-company SEC peer analysis were checked on Windows. GitHub Actions and publication remain unverified |
| Lint | V5.4 Windows Ruff found one unused local variable (`F841`) | Removed in V5.4.1; run a new Windows Ruff check before publishing |
| Market-data connection | Authenticated Alpaca IEX MSFT last-trade observation displayed in the local app | Venue-specific observation, not consolidated executable market price |
| Investment directory | 259 curated stocks, ETFs, and crypto assets | Curated lookup, not every exchange-listed security |
| **Historical covariance and optimization** | 275 overlapping MSFT/VOO return dates in an observed private IEX historical fetch; risk and constrained portfolio comparison | On-screen annualized volatility: baseline 18.8%, constrained 18.4%; model is not predictive and proprietary price data are not published |
| **Fundamental peer ML** | Windows live 12-company SEC analysis completed for MSFT; nearest peers and sample-relative outlier rank displayed | 12-company sample; similarity is descriptive, not evidence of predictive accuracy or economic equivalence |
| Comparison | Two to four **independent**, equal-budget hypothetical allocations | Not a ranking, return prediction, or investment advice |
| SEC fundamentals | Parsed 10-K US-GAAP fields, provenance, missing-value behavior | Authenticated Microsoft FY2026 SEC panel was confirmed on Windows; other issuers require separate verification |
| Microsoft valuation | On-demand MSFT DCF returned **$85.51/share** with user-entered 10% D&A/sales, 5% revenue growth and 10% WACC | Hypothetical illustration; terminal value was **71.3%** of EV, not a verified fair value |

## Screenshots

Both screenshots use **fictional demonstration prices**. They are screenshots of the interface, not actual current financial data or reported investment performance.

| Comparing investments | Company research |
| --- | --- |
| ![QuantForge equal-budget fictional comparison](docs/images/v5_compare_fictional.png) | ![QuantForge company research fictional preview](docs/images/v5_research_fictional.png) |

![QuantForge V5.1 portfolio planner and ETF look-through, fictional portfolio](docs/images/v5_1_portfolio_fictional.png)

![QuantForge V5.3 historical quant analysis — entirely fictional price evidence](docs/images/v5_3_quant_fictional.png)

## Features

| Workspace | Function |
| --- | --- |
| **Browse** | Search investments by full name or ticker; filter companies, ETFs and crypto |
| **Research** | Inspect source/timestamp of a market observation, see proposed purchase size and portfolio effect |
| **Compare** | Model the **same** hypothetical dollar spend on 2–4 different assets from the same starting portfolio |
| **Company financials** | Request selected SEC annual 10-K financial facts and ratios with filing metadata |
| **Portfolio** | Local paper buys/sells, allocations, cost basis, unrealized/realized P&L, concentration, ETF holdings look-through, read-only rebalancing and stress scenarios |
| **Valuation** | Compute an illustrative issuer-specific 5-year FCFF DCF from SEC facts with editable assumptions, sensitivity, annual fundamentals comparison; optionally load older Microsoft V3 DCF |
| **Quant** | Private user-supplied price history or historical Alpaca bars; correlation, risk contributions, constrained optimization and distributional scenarios |
| **Watchlist and journal** | Preserve ideas, research notes and virtual transaction history on the local machine |

### Boundaries

- **Not a brokerage:** no live orders, brokerage balances, deposits or automatic trade execution.
- **Not an AI stock picker:** no claims of profitable predictive models, guaranteed returns or precise future prices.
- **Not a market-data redistributor:** private licensed vendor observations and personal positions are never part of the repository.
- **Not a complete ETF screener:** an ETF price cannot establish its holdings, fees or diversification. ETF constituent look-through requires dated user-supplied issuer CSVs; missing coverage stays unknown.

## Architecture

```text
Browser (localhost:8765)
   |  local HTTP endpoints; no API secret in client JavaScript
   v
Python request handlers (desk/server.py)
   |-- Browse / Research / Compare --> catalog + Alpaca market observations
   |-- Portfolio / Journal -------> SQLite paper ledger + private notes
   |-- ETF holdings / targets ----> user-imported CSV + overlap / read-only rebalance
   |-- Risk calculations ---------> deterministic stress + Monte Carlo
   |-- Quant history -------------> Alpaca bars or private CSV + shrinkage covariance / optimization
   |-- Company financials --------> SEC company tickers + Company Facts (on demand)
   |-- Company DCF / ratios ----> on-demand SEC annual concepts + user assumptions
   `-- Microsoft V3 DCF ------> validated external V3 report (optional)

Independent research modules:
  data -> returns/validation -> rolling VaR/GARCH/ML/HMM -> backtesting
                                      |-> options / Monte Carlo / factor analysis
                                      `-> scenario-based DCF
```

The investment desk binds to **127.0.0.1**. Demo and live market-data modes are separate, and the local ledger does not place orders with Alpaca.

[System architecture and data flow](docs/architecture/TECHNICAL_DESIGN.md)

## Quantitative methods

| Concept | Implementation in QuantForge | What it answers / caveat |
| --- | --- | --- |
| **Portfolio allocation** | Holding value divided by total marked equity | Where the virtual capital is concentrated |
| **ETF constituent look-through** | Direct stock exposure + ETF position value × imported constituent weight; known lower-bound ETF overlap | Identifies indirect company concentration; requires dated CSV and exposes missing coverage |
| **Rule-based rebalancing** | Target percentages including cash; sell-first, cash-constrained buys with hypothetical 5 bp fees | Read-only virtual trade plan; not order execution or an optimal trading strategy |
| **HHI concentration** | `sum(weight_i²)` for noncash holdings, with cash included in the equity denominator | Measures concentration; **not** a covariance-based risk estimate |
| **Stress tests** | Holdings shocks: stocks/ETFs −20%, crypto −40%; largest holding −35% | Dollar loss under stated **hypothetical** assumptions |
| **Monte Carlo** | 5,000 seeded, one-factor lognormal terminal-value scenarios | Illustrative 95% VaR/ES from **assumed**, not market-estimated, volatility |
| **Position preview** | Virtual shares, 5-bp hypothetical fee, before/after weights, saved preference flags | Consequences of a purchase, not a recommendation |
| **Investment comparison** | Same virtual budget and same unmodified starting portfolio | What differs in allocation/rule exposure if only one alternative is purchased |
| **SEC financial analysis** | Annual revenue, margins, operating cash flow and CapEx, annual growth when periods align | Supports financial review; missing disclosures aren't imputed |
| **DCF** | Five-year FCFF forecast, assumed WACC, terminal value, net-debt-to-equity bridge | Sensitivity to **explicit analyst assumptions**, not a fact about market price |
| **Quant history/optimization** | User-imported or personal IEX daily bars; Ledoit–Wolf covariance, correlation, risk contribution and SLSQP constrained variance objective | Sample-dependent; models assume fixed covariance and omit fees and taxes |
| **Fundamental ML peer matching** | SEC annual financial features, robust scaling, Euclidean peer distance, sample-relative IsolationForest and feature ablation | Explains a small chosen peer set; **not** stock-return prediction or anomaly accuracy |
| **Advanced research** | Rolling historical/normal/EWMA/GARCH VaR, HMM regimes, Ridge/boosted volatility, factor regression, optimization and Black–Scholes | Separate offline experiments; **not** production live trade signals |

Read the derivations and implementation choices: [general-company DCF](docs/methodology/GENERAL_COMPANY_DCF.md), [personal portfolio mathematics](docs/methodology/PORTFOLIO_DECISIONS.md), [ETF look-through and rebalancing](docs/methodology/ETF_LOOKTHROUGH_AND_REBALANCING.md), [research/ML methods](docs/methodology/QUANT_RESEARCH_METHODS.md), and [SEC valuation](docs/methodology/SEC_AND_DCF.md).

## Run locally

Requirements: **Windows PowerShell and Python 3.12** recommended; `pyproject.toml` supports Python 3.11–3.13.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

**Fictional demo** (no credentials):

```powershell
.\.venv\Scripts\python.exe -m quantforge investment-desk --demo --db .private\demo.sqlite3
```

Open `http://127.0.0.1:8765/`. The demo prices are fictional and should never be represented as live quotes.

**Private Alpaca observations** (credentials entered locally, never hardcoded):

```powershell
$env:ALPACA_API_KEY_ID = Read-Host "Alpaca key ID"
$sec = Read-Host "Alpaca secret" -AsSecureString
$env:ALPACA_API_SECRET_KEY = [System.Net.NetworkCredential]::new("", $sec).Password
Remove-Variable sec
$env:SEC_USER_AGENT = Read-Host "SEC User-Agent (your name and email)"
.\.venv\Scripts\python.exe -m quantforge investment-desk --db .private\alpaca.sqlite3
```

SEC is optional: `SEC_USER_AGENT` is required **only** when using the company's SEC panel. Virtual buys require a sufficiently recent observation (15 minutes for U.S. securities; 5 minutes for crypto). Previously saved portfolios depend on continuing to use the **same** `.private` database path. Stop with **Ctrl+C**.

For the separate, previously completed Microsoft V3 DCF, add `--sec-dir <path-to-your-verified-V3-output-folder>` to the start command.

Before GitHub publication:

```powershell
.\.venv\Scripts\python.exe tools\prepublish_check.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

The preflight is an additional safety check, **not** authorization to publish licensed market data or proof that the models predict returns.

## Technical documentation

- [Current architecture and API boundaries](docs/architecture/TECHNICAL_DESIGN.md)
- [Portfolio math, stress tests and simulations](docs/methodology/PORTFOLIO_DECISIONS.md)
- [GARCH, Ridge/boosting, HMM, factors, optimization, options and backtesting](docs/methodology/QUANT_RESEARCH_METHODS.md)
- [Generalized company DCF, five-year projections, WACC and sensitivity](docs/methodology/GENERAL_COMPANY_DCF.md)
- [SEC accounting extraction and Microsoft DCF methodology](docs/methodology/SEC_AND_DCF.md)
- [Current V5.4 validation evidence and unresolved checks](docs/evidence/VERIFICATION_V5_4.md)
- [Data licenses, credentials and privacy](docs/publication/DATA_LICENSE_AND_PRIVACY.md)
- [GitHub publication checklist](docs/publication/RELEASE_CHECKLIST.md)
- [Current implementation status](docs/STATUS.md)

## Limitations

Market trade observations are venue-limited and may be stale. No historical price-series calibration is used in the personal desk's risk simulation. Stress outcomes, trading fees, risk limits, and DCF assumptions are illustrative. The SEC company-facts API does not replace independent filing review, and its selected financial fields may be reported in different amended filings. The generalized DCF depends on strict standardized SEC facts and assumed future inputs; unsupported issuers produce missing-data messages rather than prices. Earlier quantitative research is a separate track with recorded out-of-sample limitations. The current application is personal and local; no public web service is offered.

The repository is suitable for technical inspection, **not** for publishing its original owner's financial records, credentials or licensed market-data outputs. No source data or private database is required to run the fictional demo.
