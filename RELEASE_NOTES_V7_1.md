# QuantForge V7.1 — Public Research Systems Exhibit

## Why
The owner-only workspace has materially deeper analytics than the simplified interactive public demos. Visitors should be able to assess the statistical and software engineering work without obtaining private market-data access.

## Changes
- Add public **Research systems** navigation and technical page with four visual algorithm walkthroughs (constrained optimization, rolling walk-forward evaluation, SEC forecast sensitivity, explainable investment scores).
- Document mathematical formulations, risk warnings, validation invariants and data-source lineage; diagrams are explicitly illustrative and do not reproduce a private research session.
- Add an above-the-fold public-homepage feature preview with a direct link to the new page.
- Expand Methods & engineering with a prominent deep-dive link and a test-quality matrix.
- Add source-level tests and retain three CSP-hashed built scripts with no new private APIs.

## Boundaries
No private holdings, confidential observations, API tokens, authenticator secrets, or raw licensed prices are exposed. No Render, Supabase, SEC snapshot, MFA, virtual-trading or Alpaca changes.

## Acceptance
Run Ruff, full pytest, all Node tests, bundle builder and CSP audit, privacy prepublish and GitHub CI before publication. Verify homepage, Research systems, interactive demo navigation and small-screen layout on the deployed Cloudflare site.
