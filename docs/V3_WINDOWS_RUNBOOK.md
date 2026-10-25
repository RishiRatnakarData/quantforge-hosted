> **HISTORICAL V0-V3 DOCUMENTATION, SUPERSEDED FOR DATA RETENTION:** Current Tiingo Starter terms prohibit saving provider data and derived products. Do not follow the previous Tiingo download/cache instructions; use [V4 data-rights guidance](publication/DATA_LICENSE_AND_PRIVACY.md) or, from `docs/`, see `publication/DATA_LICENSE_AND_PRIVACY.md`.

# QuantForge V3.0 — Windows SEC & DCF runbook

## Scope and acceptance

V3 adds the **Microsoft corporate-finance branch** to the existing QuantForge risk platform. It does not modify the V0–V2 portfolio training and evaluation outputs or open the reserved ETF final holdout. Local synthetic tests are not evidence that the live SEC mapping matches Microsoft's latest original statements. Live results must be reconciled to the 2026 10-K before entering the final research presentation.

This is a distinct **as-of October 22, 2026** valuation snapshot, not an attempt to backtest 2019–2025 ETF returns. Microsoft FY2026 ended June 30, 2026. Data selection requires SEC 10-K or 10-K/A facts **filed by the cutoff**, complete annual periods (330–400 days), matching 2026-06-30 annual context for flow variables, instantaneous year-end context for balance variables, and a traceable accession, unit and SEC tag.

## Installation in PowerShell

Unzip V3 into a **new folder**, then open its inner `quantforge-financial-research` directory in VS Code. Do not overwrite your validated V2 folder or private Tiingo data. No virtual-environment activation is necessary:

```powershell
Test-Path .\pyproject.toml
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

`Test-Path` must return `True`. If Ruff reports import-order issues, use `python.exe -m ruff check src tests --fix`, then rerun both lint and tests. Report any other error instead of applying unsafe fixes automatically.

## Run the complete *fictional* demonstration first

```powershell
.\.venv\Scripts\python.exe -m quantforge v3-demo --as-of 2026-10-22 --output outputs/v3_demo
Start-Process .\outputs\v3_demo\valuation_dashboard.html
```

**Everything in `v3_demo` is fictional data**, not Microsoft reported revenue or a share price estimate. The mocked Company Facts payload has `FAKE-DEMO-*` accessions, and the memo/dashboard display the simulation label prominently. The deterministic fixture tests arithmetic, filing-lag rules, report consistency and edge-case checks without requiring SEC network access.

## Run real published Microsoft SEC financials

The SEC public Company Facts API needs **no API key**. It asks scripted users to identify their agent including a contact email. This is distinct from your private Tiingo token.

```powershell
$env:SEC_USER_AGENT = Read-Host "SEC User-Agent (e.g. QuantForge Research your-email@example.com)"

.\.venv\Scripts\python.exe -m quantforge v3-sec `
  --as-of 2026-10-22 `
  --output outputs/v3_sec_msft

Start-Process .\outputs\v3_sec_msft\valuation_dashboard.html
```

Replace the example email with an address where the SEC can contact the data consumer. The string is only transmitted in the request header and not copied to report files. Keep the old V2 Tiingo credentials private. The SEC snapshot is cached under `data/private/sec` with a content-addressed filename and recorded SHA-256. The request makes one Company Facts API call. Respect SEC fair-access policies: don't automate repeated requests unnecessarily.

**If a required live SEC concept is absent:** the program refuses to create a valuation rather than substituting zero. Historical D&A is optional because the latest forecast D&A is an explicitly modeled assumption and Microsoft's reported cash-flow row bundles “depreciation, amortization, and other.” It saves `sec_fact_audit.csv` and `sec_financials.csv` before stopping, so you can inspect selected and missing tags. This is *not* a model failure; standardized Company Facts may omit company-specific XBRL extensions. Only add mappings after checking the actual filing and taxonomy semantics.

To list missing tags after a failed run:

```powershell
Import-Csv .\outputs\v3_sec_msft\sec_fact_audit.csv |
    Where-Object { $_.fiscal_year -eq '2026' -and $_.status -eq 'missing' } |
    Format-Table metric,alternatives -AutoSize
```

Replay an existing immutable SEC snapshot without a new request:

```powershell
Get-ChildItem .\data\private\sec\*.json
.\.venv\Scripts\python.exe -m quantforge v3-sec `
  --snapshot ".\data\private\sec\CIK0000789019_companyfacts_YOUR_HASH.json" `
  --as-of 2026-10-22 `
  --output outputs/v3_sec_replayed
```

Replace `YOUR_HASH` with the real filename listed in the first command. `--snapshot` has no network operation.

## Evidence to inspect

```powershell
Get-Content .\outputs\v3_sec_msft\financial_statement_audit.json
Import-Csv .\outputs\v3_sec_msft\historical_fundamentals.csv | Format-Table -AutoSize
Import-Csv .\outputs\v3_sec_msft\dcf_scenarios.csv | Format-Table scenario,wacc,terminal_growth,intrinsic_value_per_share_usd -AutoSize
Get-Content .\outputs\v3_sec_msft\INVESTMENT_MEMO.md -Encoding UTF8
Get-Content .\outputs\v3_sec_msft\manifest_v3.json
```

Opening UTF-8 markdown via VS Code prevents PowerShell console encoding from corrupting long punctuation. Validate the source tags and 2026 financial anchors in `docs/methodology/V3_SEC_REFERENCE_CHECKS.md` before describing outputs as SEC-reconciled.

**Historical data:** no automatic use of market prices, observed beta, yields or financing costs is implied. The assumptions are explicit in `configs/valuation_assumptions.json` and are copied into each run. No observed share price is used, so this is a model-implied intrinsic value estimate, **not upside/downside, a consensus forecast, or advice**.

## Deliverables

- `sec_financials.csv` — annual income/cash-flow/balance data, USD millions and ratios
- `sec_fact_audit.csv` — every concept, SEC tag, form, accession and filing date or missing-tag status
- `historical_fundamentals.csv` — selected trend/ratio table
- `forecast_drivers.csv` — five forecast periods by scenario, NOPAT, CapEx, D&A, ΔNWC, FCFF
- `dcf_scenarios.csv` — PV of cash flows, terminal value, enterprise/equity bridge, implied per-share value
- `dcf_sensitivity.csv` — WACC-by-terminal-growth sensitivity
- `valuation_assumptions.json` — frozen assumptions copied from the model config
- `valuation_dashboard.html` — offline interactive statement/forecast/sensitivity report
- `INVESTMENT_MEMO.md` — automatically reconciled narrative and limitations
- `financial_statement_audit.json`, `manifest_v3.json` — audit and provenance

## Remaining quality gates before public publication

1. Independently compare selected SEC concepts to Microsoft's actual audited 2026 consolidated statements and corresponding reporting definitions.
2. Resolve absence of standardized GAAP tags using traceable original disclosure, without fabricating values.
3. Evaluate whether D&A tag actually reflects the full noncash item needed for FCFF; the company statement says "depreciation, amortization, and other."
4. Reconcile weighted-average diluted versus current diluted outstanding shares; review equity-linked awards, leases and excess investments.
5. Test WACC, capex and terminal assumptions and document source support; avoid pretending illustrative CAPM inputs came from observed market data.
6. Confirm reproducibility after version locking, publication terms, and passing GitHub Actions; **do not claim CI passed before checking it.**

### Primary references

- SEC Company Facts specification: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC fair access/User-Agent guidelines: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- Microsoft's 2026 Annual Report: https://www.microsoft.com/investor/reports/ar26/
