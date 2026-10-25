# V5.4 — Fundamental ML peer research

- Adds **Company peers (ML)** inside **Research**; no new marketing dashboard or separate training course.
- Selects relevant named company groups and reads latest annual SEC Company Facts on demand.
- Feature engineering: revenue growth, operating margin, net margin, free cash flow margin, debt/assets ratio.
- Robust-scaled Euclidean nearest peers, peer feature comparison, missing-value audit, and leave-one-feature-out neighbor stability.
- Exploratory IsolationForest rank for **at least 12** valid issuers; no buy/sell ratings or predictive-accuracy claims.
- Doesn't change any paper trades, saved allocation targets, portfolio history, or existing Alpaca data.
- Detailed technical method: [`docs/methodology/SEC_FUNDAMENTAL_ML_V5_4.md`](docs/methodology/SEC_FUNDAMENTAL_ML_V5_4.md).

## Windows upgrade from V5.3.1

1. Stop the private server using **Ctrl+C**.
2. Extract the V5.4 upgrade into your existing `quantforge-financial-research` root; do not replace `.private`, `.venv`, or personal credentials.
3. Run:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m quantforge investment-desk --db .private\alpaca.sqlite3
```

4. Under **Research**, open any SEC-reporting U.S. stock (for example, MSFT). Expand **Company peers (ML)**, select Technology, and click **Compare company profiles**.

`SEC_USER_AGENT` must be set using your own identification; no need to enter it again if still present in the same PowerShell session. The first multi-company request may be slower because SEC issuer facts are retrieved sequentially. An individual company may be excluded when standard tags are missing. The model refuses to show an outlier rank with fewer than 12 valid issuers.

## Evidence

- `193` tests passed and `1` optional DuckDB-dependent test skipped on the build runtime (synthetic/mocked inputs).
- JavaScript syntax verified; authenticated live SEC peer analysis and Windows Ruff need local confirmation.
- No claim of actual stock prediction, alpha, buy ratings, or measured anomaly-detection accuracy.
