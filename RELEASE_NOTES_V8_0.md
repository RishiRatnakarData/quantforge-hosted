# QuantForge V8.0 — Navigation and Reading-Flow Refinement

This is a **presentation/UX update**, not a model, database, market data, or authentication update.

## Changes

- The homepage leads with public, real historical SEC financial evidence before simulated portfolio examples.
- Three clear paths from Overview: reported company data; interactive, simulated model comparisons; private, MFA-protected research.
- Public model pages and documentation are grouped in collapsible navigation while all nine original routes/IDs are retained.
- Redundant hero buttons removed; long methodology descriptions and extra simulated portfolio examples available in clearly named expandable sections.
- Private Overview presents holdings/value before the V7.9 plain-language research guide.
- Nine private sections are grouped by portfolio, market strategies, and company/settings, with active groups automatically expanded.
- More consistent control sizes, chart/table sizing, responsive grid boundaries, mobile forms, and keyboard-focus indicators.

## Invariants

- No changes to MFA, API paths, Supabase policies, saved account data, analysis algorithms, mathematical formulas, or public SEC snapshot.
- V7.9 guidance is still rule-based and local, not an external AI conversation.
- Public portfolio/optimization/walk-forward/DCF examples remain identified as simulated/illustrative; reported SEC financial data is distinguished from them.
- No new external JS, CSS, APIs, paid dependencies, or secrets.

## Release validation

The release runner performs exact source-anchor checks, backups to a temporary folder, rebuild, Ruff, all Python and JS tests, public bundle and privacy audits, source dataset hash validation, and GitHub CI on the pushed commit. It does not weaken old tests. It stops before publishing if any validation fails.

## SEC expansion is separate

Once V8.0 is deployed, run the included SEC expansion script on the existing Windows checkout. It reads the V7.9 candidate list, fetches free SEC filings with a declared contact User-Agent, validates public annual data, runs all regressions, and conditionally publishes only `sec_snapshot.json`, the compiled public HTML, and CSP headers. Never publish account data or commercial market prices. Additional companies are **not included** until this separate job succeeds.

## Limitations

Responsive review used a static browser fixture from the supplied V7.9 source, not a live MFA session or actual published company dataset. The end-to-end Windows and Cloudflare deployments still require verification.
