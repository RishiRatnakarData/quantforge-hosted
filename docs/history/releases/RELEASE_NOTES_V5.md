# QuantForge V5.0 — Private investment workspace

Compared with V4.6.2 (the previously installed local version):

- Includes V4.7's searchable 259-entry company/ETF/crypto catalog and fictional demo support for all curated entries.
- Adds **Compare**: 2–4 independently evaluated investments, using equal hypothetical spend from the same unmodified portfolio. Source and timestamp for each observation.
- Adds a manually requested SEC **annual 10-K fundamentals** panel for U.S. stocks where standard company facts are available. Provenance, fiscal period, filing date, missing fields and assumptions displayed. Requires `SEC_USER_AGENT` (person/name + working email).
- Retains the Microsoft-specific SEC DCF report (requires previously verified V3 outputs).
- Retains the same SQLite paper ledger, user preferences and journal. **Always use the original `.private/alpaca.sqlite3` when upgrading.**
- Keeps real Alpaca market observations private and separate from the fictional standalone preview.

Validation in generation environment: 164 tests passed, one DuckDB-dependent test skipped. JavaScript syntax and offline browser interactions passed. `ruff` unavailable here; run `python -m ruff check .` on Windows. The real authenticated V5 SEC page has not been externally verified. Alpaca actual-account market data remains subject to plan/feed limits.
