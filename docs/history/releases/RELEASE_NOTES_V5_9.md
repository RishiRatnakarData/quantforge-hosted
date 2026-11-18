# QuantForge V5.9 — SEC Analytics Explorer

The public SEC Financials tab now includes a true historical filing-based revenue bar chart, an interactive 12-issuer ranking by annual revenue, YoY growth, operating margin, or free-cash-flow proxy, and inspectable filing tags, dates, and accession identifiers.

Visitors can export all 12 issuers and up to three fiscal years as a source-backed CSV, including SEC field tags and accession provenance. Exports occur entirely in the browser, without external data-provider requests or authentication.

## Evidence and guardrails

- Inputs are the existing fixed-as-of SEC Company Facts snapshot generated at build time. No new API keys, calls, live quotes, or private data are required.
- Issuer annual reporting periods are **not synchronized**. Rankings are a descriptive demonstration, not an industry-adjusted or point-in-time investment signal.
- Missing operating income, margin, or cash-flow values remain unranked, never replaced with zero.
- Cash-flow proxy is cash from operating activities less PP&E purchases, **not** unlevered FCFF.
- The private Supabase + MFA + Alpaca workflows are unchanged.
- The existing three-script CSP is preserved by bundling the pure SEC calculations into the app script.

## Test coverage

`node --test web/tests/sec_analytics.test.cjs` validates rankings, fiscal-year ordering, missing values, CSV completeness, and spreadsheet-formula protection. Python source tests guard bundling, CSP, and published-data separation.
