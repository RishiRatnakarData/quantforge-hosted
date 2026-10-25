# Verification record — V5.0 (October 24, 2026)

This page separates **user-observed results on Windows**, **synthetic unit tests**, and **unverified external behavior**.

## Observed on the user's Windows installation

| Check | Evidence | Status |
| --- | --- | --- |
| Python editable install | `pip show quantforge-financial-research` printed `Version: 5.0.0` | Passed |
| Unit/integration suite | `python -m pytest -q` printed **165 passed, 6 warnings** | Passed |
| Code style | `ruff check . --fix` flagged one `E731` lambda assignment in SEC parser | **Needs clean rerun after the provided `def` correction** |
| Prior live provider connection | QuantForge V4.6.2 displayed a user-observed MSFT Alpaca IEX last trade | Passed for that observation; not a guarantee of ongoing feed access |
| Full V5 live SEC retrieval | No confirmed user-provided evidence of a successful on-demand company-fundamentals request yet | Open |
| V5 UI | Prior fictional offline browser walkthrough and API smoke tests were performed; Windows end-to-end SEC/Compare interaction still needs confirmation | Partially validated |

The **six deprecation warnings** were from NumPy/pandas/exchange-calendar compatibility paths and did not fail tests. They should be reviewed with dependency upgrades, not suppressed to imply zero warnings.

## What the tests show

The suite exercises portfolio transactions and failure cases, simulated quote freshness, directory entries, equal-budget comparisons, mocked SEC Company Facts extraction, domain and chronological constraints, model numerical identities, and synthetic offline pipelines. Tests do **not** establish accurate real-world return forecasts, market-data availability, distribution rights, or a public deployment.

## CI promotion criteria

Before describing the GitHub release as independently validated, run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m quantforge investment-desk --demo --db .private\ci-manual.sqlite3
```

Then confirm GitHub Actions **CI** is green. Use a separate fictional `.private` database for local demonstration. Confirm SEC is optional and absent credentials do not block demo. Inspect the screenshots and source-data labels. Never commit any `.private` database.
