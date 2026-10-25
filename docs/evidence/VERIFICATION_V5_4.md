# V5.4.1 verification record and remaining publication checks

## 1. User-observed Windows results (October 2026)

These observations were reported from the user's local Windows computer; they are **not a reproducible audit of external markets or filings**, and private provider data are intentionally excluded from the repository.

| Test | Observation | Interpretation |
| --- | --- | --- |
| Python package | `quantforge-financial-research==5.4.0` installed | Installed successfully from upgrade ZIP |
| Test suite | `194 passed, 6 warnings` on Python 3.12 | Automated unit/integration checks passed; deprecation warnings remained |
| Ruff | One `F841` unused `active` variable in `fundamental_ml.py` | V5.4.1 removes it; new Windows lint rerun required |
| Local server | Private Alpaca mode started on `127.0.0.1:8765` | Personal localhost process, not a public service |
| Market data | MSFT Alpaca IEX last-observed trade appeared | Feed/timestamp-specific observation, **not** consolidated live market price |
| SEC statements | MSFT FY2026 revenue about $331.84B; displayed filing metadata | User interface field extraction worked; independent filing audit still recommended |
| DCF | MSFT $85.51/share; growth 5%, WACC 10%, terminal growth 2.5%, **user-assumed** D&A 10% of revenue | Scenario output only; terminal share of enterprise value 71.3%; neither current price nor audited fair value |
| Historical data | MSFT/VOO personal IEX historical fetch: 552 prices, 275 matching returns over 2025-09-22 to 2026-10-23 | Real personal source retrieval worked but cannot be redistributed |
| Quant result | $10k hypothetical basket; baseline MSFT/VOO 50/50 → constrained 47.8/52.2; annual volatility 18.8% → 18.4%, 21-day 95% VaR $880.61 → $862.34 | Historical covariance plus assumed scenario model; **not** performance or generalizable risk improvement |
| SEC ML | 12 technology-company fundamentals analyzed; MSFT closest peers Apple, Applied Materials, Qualcomm, IBM, Adobe | Small, nonrandom descriptive peer set. Rank 6/12 (most unusual=1) and stability 3/5 are not predictive validation |

## 2. V5.4.1 source changes

- Remove an unused ML intermediate variable that caused the Windows Ruff failure.
- Correct the count of missing ML metrics so an observed target value is not counted as missing.
- Add a regression test for the missingness count.
- Add a source prepublication scanner, negative tests and CI check.
- Repair two broken historical-documentation links, and update status/README evidence to reflect later Windows checks.

## 3. What the tests do *not* establish

- Accuracy of stock returns, future volatility, covariance stability, or model-derived investment advice.
- Statistical detection of fraud or distress: IsolationForest has no labeled anomalies or predictive performance here.
- Validity of the DCF's financial-input selection, capital structure, or 10% D&A assumption beyond a mathematical scenario.
- Broad market representation from the IEX venue, rights to redistribute Alpaca or Tiingo data, or the completeness of ETFs' underlying holdings.
- Continuous live operation, a public hosted application, independently validated GitHub Actions CI, or security review of prior Git history.

## 4. Remaining checks before GitHub

1. On Windows, install V5.4.1, run `python -m ruff check .`, `python -m pytest -q`, and `python tools/prepublish_check.py` using `.venv\Scripts\python.exe`.
2. Run a fictional demo end-to-end. Inspect the screenshots and docs manually for identifying details or private market observations.
3. Review any historical price/ETF holdings caches outside the repository for provider retention rights.
4. **Rotate credentials if previously exposed.** A scanner cannot remove secrets from previously pushed Git commits.
5. Check all files Git would publish with `git status --short`, `git ls-files`, and `git diff --cached --stat`. Verify ignored databases/exports aren't already tracked.
6. After pushing to GitHub, confirm CI passes on the actual commit; verify README screenshots and relative links online.

Source publication can proceed only after those checks; this document is not a claim that the project is already public.
