# QuantForge V5.7 — Public SEC Financials

- Added an intentionally limited public financial exhibit for 12 named U.S. issuers across technology, communication, consumer businesses, healthcare, energy, and industrials.
- Annual SEC 10-K disclosures, filing dates, accession IDs, and source URLs are generated offline using `tools/build_public_sec_snapshot.py`; no hidden API requests from recruiters' browsers.
- Public interactive outputs: reported revenue, operating margin, annual FCF proxy, fiscal-year comparisons, and a hypothetical margin-stress control.
- Public fictional Portfolio/Quant/DCF/Peers remain unchanged. No claim that those examples are derived from real market observations.
- Private Alpaca and Supabase data remain in the existing MFA-secured owner workflow; no new authentication or database migration.
- **Before publishing actual real-company figures**, generate `web/site/sec_snapshot.json` from the SEC, review it, and rebuild `public/index.html`. Without the file, the public page shows a truthful unavailable-data state.

See [complete SEC public-demo runbook](../../PUBLIC_SEC_DEMO_V5_7.md).
