# QuantForge V5.3.1 — Historical data usability hotfix

- Free IEX feed is selected by default for historical stock/ETF bars. Historical SIP remains optional when accessible.
- HTTP status codes and generic safe diagnostics now appear for failed Alpaca requests. Provider response bodies, credentials and URLs are never displayed.
- Fixed Ruff E731 (`objective` now uses `def`).
- Added mocked HTTP 403/network failure tests; adjusted historical-feed default test.
- Does not change your local database, analysis formulas, portfolio holdings, or brokerage connectivity.
