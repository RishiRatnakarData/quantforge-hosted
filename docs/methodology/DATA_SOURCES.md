> **HISTORICAL V0-V3 DOCUMENTATION, SUPERSEDED FOR DATA RETENTION:** Current Tiingo Starter terms prohibit saving provider data and derived products. Do not follow the previous Tiingo download/cache instructions; use [V4 data-rights guidance](../publication/DATA_LICENSE_AND_PRIVACY.md) or, from `docs/`, see `publication/DATA_LICENSE_AND_PRIVACY.md`.

# Data Provenance, Licensing, and Point-in-Time Reference

This document is a **source assessment**, not confirmation that an API call, purchase, or license has occurred.

| Data | Candidate | Verified public capabilities | Unresolved checks |
|---|---|---|---|
| Company filings/XBRL | SEC EDGAR / `data.sec.gov` | Company Facts and filing/submissions APIs | XBRL tags, amendments, corporate action dates, API fair use, actual retrieval |
| Economic data/vintages | St. Louis Fed FRED/ALFRED | observation vintages (`realtime_start` / `realtime_end`) and economic-series endpoints | registered key, release timing, revisions, data provider-specific license |
| Factor research | Kenneth R. French Data Library | US 3-/5-factor daily returns, archive files | CIZ post-2024 methodology, provider redistribution permission, correct percentages and factor-release as-of |
| Equity/ETF historical total return | commercial/authorized CSV source to be chosen | configurable CSV adapter supports vendor-specific adjusted levels | **Not yet selected**: dividend adjustment, historical depth, delistings, rate limits, trading permission, redistribution |
| Local analytics | DuckDB/Parquet and SQLite | columnar analytical SQL and interoperable export | full DuckDB branch to verify with installed dependencies |

**Official references:**

- SEC APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC declared User-Agent: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- FRED/ALFRED real-time periods: https://fred.stlouisfed.org/docs/api/fred/realtime_period.html
- FRED vintage dates: https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
- Kenneth French Data Library and CIZ migration: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- DuckDB Parquet operations: https://duckdb.org/docs/stable/data/parquet/overview

## What a research-safe daily price file requires

An original authorized source; acquisition timestamp; stable instrument identifiers; dividend and split adjustment rules; currency; exchange calendar; delisting/death of instruments; explicit handling of non-trading dates; and rights to use the data for non-commercial research. Never silently equate *split-adjusted* with *total return*. No free provider has been declared suitable solely because downloads exist.

A row's `date` represents the **session close's observation date**. A strategy that trades at that same close must not claim to know the close ahead of time. Baseline implementation acts after earlier observation and uses the next period return. Any price-level methodology with recalculated adjustments must account for hindsight and ensure return ratios are appropriate to the time being simulated.

### Macro and factor timing

ALFRED's real-time-vintage dates preserve revisions, but data observation dates and historical release dates differ. Same-day macro events need publication-time knowledge, often a conservative next-session lag. Factor series may be published or revised after their constituent period; do not act on a factor estimate before its actual availability. Archive methodology can change historically (e.g., CRSP FIZ→CIZ process after December 2024), so pin provenance.

### SEC date distinction

SEC `end` fiscal period, `filed` acceptance filing date, frame, fiscal year, fiscal period, accession number, and amended form are **not interchangeable**. Tie a model as-of date to accepted publicly available reports; never treat a fiscal quarter's ending-day number as known on that day.

### Public repository policy

Do not commit commercial downloads, API keys, FRED credentials, private input datasets, or unlicensed vendor data. Keep only small internally simulated demonstrations and derived output where permitted. Use `.env` untracked; never hardcode authentication credentials.
