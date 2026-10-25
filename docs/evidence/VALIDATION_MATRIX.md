> **V1.0 addendum (October 22, 2026):** See `docs/V1_WINDOWS_RUNBOOK.md` and `docs/STATUS.md`. V1 uses a separate net-of-fees backtester and longer 252-session risk evaluation with GARCH and Christoffersen diagnostics. The checks below describe earlier V0.2 components unless explicitly updated; actual-market V1 has not yet been executed in this environment.

# QuantForge Evidence / Verification Matrix

The following distinctions prevent local tests from being confused with validation of the eventual empirical financial research.

| Contract | Evidence | Current result | Required next gate |
|---|---|---|---|
| Unique date/symbol, positive finite prices | `test_contracts.py` | local unit tested | market provider source certification |
| No implicit fill of cross-sectional data | `test_contracts.py` | local unit tested | calendar and suspension/delisting treatment |
| Return arithmetic | fixed calculation unit tests | local unit tested | SQL equivalence + corporate-action spot checks |
| Historical VaR/ES definitions | arithmetic and tail-order tests | local unit tested | independent implementation validation |
| EWMA newest-observation weighting | unit test | local unit tested | backtest stability and distributional checks |
| Rolling forecasts avoid future returns | future data mutation tests | local unit tested | full V1 chronological CV/feature/release timestamps |
| Kupiec coverage handles extreme exceptions | zero/all exceptions test | local unit tested | conditional coverage and small-sample uncertainty |
| Optimization respects bounds and full investment | optimizer tests | local unit tested | covariance robustness / inference |
| Trading costs reduce strategy equity | zero/positive fee comparison tests | local unit tested | fee and benchmark sensitivity |
| Portfolio timing avoids obvious lookahead | lag assertion and future perturbation tests | local unit tested | data-vintage and corporate-action replay |
| Full deterministic *synthetic* research pipeline | `test_integration.py` + generated output check | local passed | reproduce on clean Windows/CI |
| SQL backed analytics | SQLite observed; optional DuckDB code | partial: SQLite tests run | **DuckDB/Parquet CI / Windows execution not observed locally** |
| Provider APIs | FRED and SEC mocked payloads/headers | mocked only | real authenticated calls, response schema, fair-access limits |
| Fama–French daily ZIP parsing and ex-post factor betas | synthetic archive and exact known-coefficient tests | unit tested | real downloaded archive and publication timing |
| SEC as-of filtration | filing amendments and as-of unit tests | unit tested | actual fiscal tags/accounting reconciliation |
| US exchange-specific sessions | XNYS calendar and exact requested coverage audits; mocked provider tests | implemented/fixture tested | confirm with live provider data and historical special closings |
| Actual market input returns | Tiingo EOD adapter with private cache, SHA-256 source manifests and `adjClose` | mocked adapter + end-to-end CLI test passed | **live historical prices not downloaded/evaluated** |
| GARCH, HMM, factors, options, DCF | reserved packages and research design | not implemented | V1, V2, V3 implementations |
| Research dashboard | standalone Plotly synthetic HTML | local rendered file produced | real figures; UX and V4 features |
| Working paper and financial memo | research protocol/design only | not written | after fully verified empirical results |
| GitHub Actions | workflow file included | **not yet run in user's GitHub repo** | push and inspect latest job logs |

## Before each milestone delivery

1. Install pinned-compatible dependencies in a clean environment.
2. Run `python -m pytest -q` and `ruff check .`.
3. Execute a full CLI synthetic smoke run; visually inspect output files.
4. Verify generated manifest and hash; verify no secrets/data in git index.
5. Compare SQL with Python and check key financial identities.
6. For empirical releases, reconcile all analysis claims to outputs and source dates.
7. Push only after local validation; separately inspect **latest** GitHub Actions job before claiming cloud success.
8. Update this matrix, README, architecture, research protocol and status from observed evidence.

### Local build evidence

For V0.2, the authoring-container run reported **61 passed, 1 skipped** (DuckDB unavailable). The integrated Tiingo CLI was run with *mocked* provider records, not actual live data. The 330-day simulated demo completed. The corresponding Python wheel was built and inspected. Ruff, full DuckDB/Parquet execution, live data retrieval, GitHub Actions, and Python 3.12 V0.2 installation remain to be verified. Separately, the user validated V0.1.1 on Windows: 51 tests, Ruff after a local formatting fix, and DuckDB/Parquet demonstration outputs.

Do not convert simulated results into resume metrics or purported financial strategy performance.

## V3.0 validation scope (2026-10-22 release)

| Validation | Evidence | Limit |
|---|---|---|
| SEC source semantics | annual flow 330–400 days, exact June fiscal end, form 10-K/A, filed <= as-of, USD/shares unit, accessions | Live Microsoft API not executed locally |
| Historical financial identities | balance sheet A=L+E, required concepts, reported effective tax rate, CFO minus cash CapEx and analyst ratios | Selected standardized tags must be verified against 10-K |
| Forecast cash flow | EBIT*(1-tax) + D&A – capital spending – change operating NWC | Cash tax, margin, reinvestment and other drivers are assumptions |
| WACC and terminal value | CAPM, after-tax debt, capital mix, 5 discrete periods, Gordon growth and PV checks | Inputs are not live-observed WACC; no independent analyst review |
| Equity value / share | enterprise less net debt, divided by explicitly labeled diluted weighted-average shares | Financing leases, excess assets, stock option dilution require future review |
| Corporate source snapshot | SEC User-Agent declared, CIK validation, immutable SHA-256 snapshot | No live provider HTTP test in this local environment; mocked integration only |
| Output pipeline | complete fictional SEC-shaped fixture, dashboard, memo, raw/audit CSVs, manifests | Synthetic evidence cannot support any MSFT price target |
| Existing V0–V2 regression | full pytest suite included and runnable without private Tiingo data | Full DuckDB verification and Ruff require Windows environment |
| Published GitHub Actions | workflow includes new V3 demo and artifact checks | GitHub Actions not yet executed or confirmed |
