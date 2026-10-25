# Release V4.4 — Current Investment Desk

This replaces the historical time-travel game as the **primary launch experience** without deleting the earlier modeling research. No new historical stock archive, ML model training set or research PDF is needed.

**New:** Current Alpaca IEX stocks & ETFs plus venue-specific crypto trades; local private SQLite virtual portfolio; current holdings; cash/transactions/cost basis; risk concentrations; optional position sizing; 5,000-path scenario model; explicit shock analysis; optional verified real V3 Microsoft SEC DCF; understated financial-terminal UI; simple math explanations and tests.

**Not new:** Real broker trading, guaranteed live quotes for all symbols, production public display rights, ML stock-price predictions, vetted financial recommendations, automatic daily market history.

**Tested here:** Full test suite passes with one DuckDB-dependent skip; JavaScript syntax checked; browser UI rendered with mocked fictional data; independent credentialed Alpaca verification still needed on Windows. Ruff unavailable in this environment: run `python -m ruff check .` after installing dev dependencies.

**Publishing:** Public GitHub may include source and synthetic tests. Private Alpaca API market data, keys, SQLite user records, and derived private quote exports must remain local. SEC DCF is a financial exercise, and 2019–2025 ETF holdout was not touched.
