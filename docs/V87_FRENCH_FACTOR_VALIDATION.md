# V8.7 — Independent daily three-factor research and validation

## Research question
How much of an observed U.S. equity candidate's daily **risk-free-adjusted excess price return** is associated with the market, size, and value research factors, and how stable are the estimated relationships on a subsequent chronological holdout?

## Source and import
Download **Fama/French 3 Factors [Daily] → CSV** from the [official Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html), extract the official ZIP locally, and import the CSV in Portfolio → Decision center → Candidate Dossier. The file remains in the browser's authenticated session, is never uploaded to the app's API, is not automatically fetched, and is cleared at sign-out or browser refresh. The user's imported file is **format-validated, not cryptographically source-authenticated**; no data-license rights are implied. The file's date range and observation count are visible.

The parser reads only `YYYYMMDD` rows with `Mkt-RF`, `SMB`, `HML`, `RF` columns and converts **percentage** factor returns into decimal returns (divide by 100). It rejects duplicate dates and unrealistic units, and excludes explicit missing codes `-99.99` or `-999`. Monthly rows do not qualify. Dates are strictly joined to daily candidate price-return endpoints with no carry-forward, interpolation, or fabricated factors.

## Specification and diagnostics
The Fama–French three-factor specification uses **actual factor portfolios**, not ETF-factor proxies:

`R_candidate,t - RF_t = alpha + beta_m (Mkt-RF)_t + beta_s SMB_t + beta_h HML_t + error_t`

Ordinary least squares (OLS) estimates the daily excess-return intercept (alpha) and exposures. For approximate statistical uncertainty, a Bartlett-weighted Newey–West heteroskedasticity/autocorrelation-consistent covariance with lag 5 is reported; a normal-approximation 95% confidence interval for alpha is multiplied by 252 to show a simple annual-rate approximation. This interval is **not** an exact guarantee or a future-return confidence band. R², adjusted R², and residual volatility are also provided.

## Forward holdout without temporal leakage
The first 70% of exact-date joined observations fit the coefficients, and the final 30% form a strictly later **holdout**. At least 126 training observations and 60 test observations are required, with at least 200 total matched returns. The model reports holdout RMSE and an out-of-sample R² relative to the training-set mean excess return. Negative holdout R² is allowed and indicates worse fit than that constant baseline.

**Important:** This is a stability check, **not a forecast** or investable trading backtest. Each later factor return is only observed contemporaneously; the ex-post holdout measures how well earlier exposures explain later realized returns, not whether those returns could be predicted in advance.

## Explicit constraints
- U.S. equity-session calendars only; crypto/mixed calendars are rejected.
- Loaded candidate **price returns may exclude dividends and splits/adjustments** depending on provider treatment. The historical factor series need not use identical return conventions.
- Factor library history can be revised (notably the CRSP CIZ transition described by the Data Library). Source-vintage precision is limited to the imported file.
- Non-synchronous observations, short samples, survivorship, factor instability, and collinearity can distort estimates.
- No portfolio orders, trade recommendations, cloud upload, storage, backend migrations, or changes to private holdings.

## Acceptance checks
Daily parsing, unit conversion, missing/duplicate dates, known-coefficient synthetic recovery, chronological splitting, holdout diagnostics, session invalidation, crypto exclusions, full Python/JavaScript suites, SEC readiness, CSP, and prepublication checks must all pass on the real checkout before any GitHub release.
