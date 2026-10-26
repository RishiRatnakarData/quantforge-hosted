# QuantForge V5.7.1 — Cross-Industry SEC Financials

- Extended the small public real-financials panel from 3 to **12 named companies**: MSFT, AAPL, NVDA, GOOGL, AMZN, META, COST, WMT, KO, JNJ, XOM, CAT.
- Uses the same free and unauthenticated SEC `data.sec.gov` Company Facts API. No new paid or private API, credentials, or live price redistribution.
- SEC requests are sequential and gently rate-limited; financial facts are downloaded by the developer at build time, then embedded in the static public site. Recruiters' browsers do not fetch from the SEC.
- The browser's company selector is derived from the verified dataset rather than hardcoded.
- Cross-company table identifies **editorial** broad sector groupings and fiscal year-end differences. A cross-sector comparison is descriptive, not a proper matched-industry valuation.
- The site builder validates the full symbol set, SEC CIKs, provenance URLs, and presence of two or more annual periods before publishing.
- The simulated Portfolio / Quant / DCF / peers components and the MFA-protected private workspace are unchanged.

To update an existing V5.7 working tree, apply the patch, rerun `tools/build_public_sec_snapshot.py` with the existing `SEC_USER_AGENT` convention, rebuild the website, and run tests. Do not publish without checking the real financial values.
