# V14.0 — Integrated private research workflow and browser acceptance

## Purpose

Move away from an accumulating sequence of disconnected research panels. The Research Hub now displays a five-stage workflow readiness view: authenticated session, selected issuers, aligned loaded prices, current assessment, and connected evidence review. Locally imported historical SEC facts are optional and never misrepresented as a complete point-in-time investable universe.

The V13.0 evidence-integrity console remains visible. Prior research computations, SEC filing audits, and sensitivity displays remain functional, but are placed in expandable **extended methodology** groups. DOM nodes are moved without recreation so existing IDs and delegated actions remain intact. The same grouping applies to the Briefing and Advanced Research Lab overview.

## Automatic checks and explicit limitations

- Five workflow stages are derived from current session variables and distinct source identities. Selected tickers and loaded history must refer to the same universe. Historical price dates must be strictly increasing, aligned, and positive; 64 observations are required for the workflow-readiness check. Invalid inputs never create a ready state.
- Invalidation of selected securities, loaded price history or assessment parameters updates the readiness display. The evidence review must match the original candidate and current linked briefing.
- The workflow helper is pure. It cannot query providers, access account credentials, place orders, or retain archival SEC records.
- Sanitized export includes readiness status/step booleans, never ticker identities, quantities, raw prices, account balances, or SEC facts.
- The compiled website retains the existing three CSP-hashed scripts, MFA boundary, and existing brokerage code. This release adds no backend endpoint or paid service.
- `tools/audit_private_workflow_v140.py` checks the static compiled page and writes `data/private_workflow_acceptance_v140.json` (Git-ignored). It explicitly labels live browser checks **not_verified** rather than declaring them passed from HTML and CI.

## Manual acceptance in the real authenticated browser — required before production signoff

1. Sign out, open a fresh browser session and sign in using the normal account credentials and authenticator app. Confirm the protected workspace is genuinely available only after verification.
2. Open My Portfolio and confirm real **authorized** brokerage paper/virtual holdings and quotes render. If API authentication fails, stop and record the error; do not paste tokens, full balances or private account information into support messages.
3. In the Research Hub, choose 2–5 company names, load their matching historical prices and run the complete assessment. Confirm the workflow moves through selection, history, and research without reusing stale data.
4. Import `data/sec_filing_revisions_v98.json` through the private browser file picker. Confirm coverage and withheld dates appear and imported raw records do not appear in browser storage or a public download. An archive may exceed the existing 24 MiB browser import limit; if so, report the exact validation message without bypassing safeguards.
5. Visit the Research Lab and Research Briefing: confirm the selected companies, candidate, model counts, evidence classifications and historical-source caveats are consistent. Expand the methodology groups and confirm historical tables and navigation buttons still work.
6. Save a short assessment in the MFA-protected archive, sign out, sign back in and verify that it persists; delete that assessment and verify deletion persists. Confirm signed-out UI no longer exposes private records or the local SEC import.

**Important:** This document is a set of acceptance procedures, not a claim that the tests have been performed. HTML compilation, headless unauthenticated Chromium smoke checks, and GitHub CI are insufficient to establish provider-side MFA and archive-note correctness.

## Release

Guard against publishing from any baseline other than **V13.0 commit `7416a0932d46104b17449e454d4a9b59795991ba`**. Check SHA-256 hashes of modified source and payload; install exact file inventory with backup. Run Ruff, full pytest, complete Node tests, deterministic site build, privacy/CSP audits and local workflow audit before committing. After push, verify matching GitHub CI and Cloudflare page. Do not rerun the installer after commit. Local SEC lineage checks are separate and never publish the source archive.
