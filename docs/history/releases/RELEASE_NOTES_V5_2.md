# QuantForge V5.2 — SEC Company Valuation

- Generalized editable five-year FCFF DCF for individual SEC-listed U.S. companies when required annual facts are available. Missing/nonstandard disclosures block results rather than being invented.
- WACC/terminal-growth sensitivity, explicit five-year projections, retained source tag/filing accession, working capital and tax assumptions.
- Side-by-side SEC annual financial comparison (2–3 companies, with fiscal years and missing values shown).
- Kept the older verified Microsoft V3 model as a separate collapsible section.
- New read-only endpoints `/api/company-dcf` and `/api/company-comparables` with mock API and numerical unit tests.
- All Alpaca credentials, private SQLite data, paper ledger, and previously implemented V5.1 holdings/rebalancing behavior remain unchanged.

Actual-account SEC verification and Windows Ruff remain required; no calibrated fair price or investment recommendation is claimed.
