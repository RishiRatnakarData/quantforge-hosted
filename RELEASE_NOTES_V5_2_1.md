# QuantForge 5.2.1 — SEC D&A gap correction

- Expands compatible full-year US-GAAP D&A tag coverage in the current-company DCF.
- Adds optional user-specified D&A / sales percentage for SEC reporting gaps. This is clearly labeled as an assumption, never a reported fact.
- Reports meaningful missing-data instructions rather than `missing ... da`.
- Adds tests for alternate tags, explicit assumptions, range validation and provenance.
- Corrects source import order for Ruff.
- No changes to the portfolio database, market feed, virtual trades or valuation of prior archived SEC runs.
