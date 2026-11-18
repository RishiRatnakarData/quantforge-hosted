# QuantForge 5.1 — Portfolio intelligence

- Private, dated ETF constituent CSV import with source metadata and input validation.
- ETF issuer weight look-through into direct and indirect stock exposure, explicitly showing **unknown** fund holdings.
- Known-minimum ETF-to-ETF constituent overlap; not a correlation estimate.
- Read-only rule-based rebalancing across existing assets and cash, with 5 bp hypothetical fees and fractional share rounding.
- Existing investment research, SEC financials, Alpaca data and private paper ledger retained; **no automated orders**.
- New tests: `tests/test_v51_portfolio_intelligence.py`.

The current `V5.1` functionality is a portfolio planning layer. Advanced historical optimization, generalized DCF and empirical ML remain future integration work.

The ETF CSV is provided by the user from an issuer or appropriate source; nothing is bundled or retrieved automatically. Do not commit private `.sqlite3` or source ETF files to GitHub.
