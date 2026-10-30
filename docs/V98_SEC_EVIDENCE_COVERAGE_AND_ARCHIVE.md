# V9.8 — SEC evidence coverage and versioned filing archive infrastructure

Baseline: production-verified V9.7 commit `5748324d9e5dffe8b8738725ebdb275064814924`.

## What V9.8 adds to the authenticated platform

The same completed Investment Research Hub assessment now produces an **all-selected-issuer historical evidence coverage audit**, rendered in the Hub, the Research Briefing, and Research Lab status, and included in a sanitized JSON export. V9.7 previously evaluated only the focus candidate's filing evidence. V9.8 audits **every currently selected investment** against the same scheduled 126-session training / 21-session evaluation boundaries and date-aligned prices.

Each issuer is individually checked for original reporting period, filing dates, SEC accession formats, source tags, free-cash-flow arithmetic, currency, disclosure ages, and the availability of two comparable annual statements. A dated report is counted as eligible only when the **existing V9.7 strict filing gate** accepts it at that decision boundary. Unsupported funds, stale filings, missing or inconsistent metrics, post-cutoff dates, and missing companies remain unavailable. The table shows scheduled/eligible/withheld decision windows, an observed **median fiscal-end-to-latest-contributing-filing lag**, issuer SEC source cutoff, and the most frequent source gap.

The cross-issuer count requires **every selected company** to pass at the same decision date. No incomplete-coverage window is silently dropped or converted into a performance claim; V9.7's candidate-specific historical replay remains separate. Changes to the selected investments or history invalidate both reports. HTML is escaped; sanitized exports exclude source accessions, raw SEC values, price histories, positions, balances, account identifiers and credentials. Existing MFA and provider boundaries are unchanged.

## SEC original-filing revision infrastructure (optional, local)

`tools/build_sec_filing_archive_v98.py` can preserve **up to 15 fiscal years** (configurable) of original/revised SEC Company Facts records per issuer: each fact is retained by `fiscal_end`, `start`, `filed`, `accession`, `tag`, `tag_priority`, and numeric value. It includes actual **10-K and 10-K/A** observations, validates issuer CIK, SEC accessions, US-GAAP annual duration, filing date and finite values; it does not coerce missing values into zero. The collector can read existing official Company Facts downloads from `--input-dir` or deliberately download a bounded set from SEC with `--download` and `SEC_USER_AGENT` identifying the requestor (at least 1.1 seconds between requests). It writes only under Git-ignored `data/` with atomic replacement; it never publishes a credential or accesses the private broker.

For example, in the developer's repository with `SEC_USER_AGENT` configured appropriately:

```powershell
.\.venv\Scripts\python.exe tools\build_sec_filing_archive_v98.py --download --max-issuers 25 --max-years 15
```

This command is **not run as part of the production installer**: it depends on live public SEC source responses and a deliberately configured truthful SEC user agent. The resulting `data/sec_filing_revisions_v98.json` remains local, **not bundled in the website or used by the V9.7 replay yet**. This is a reproducible research-data foundation for a subsequent independently verified archive-integration release. The current private V9.8 coverage UI uses the existing published SEC snapshot, so today's production archive count does **not** automatically increase to 15 years.

## Limits and checks

The published snapshot currently contains a short historical period for each company, potentially with later restatements. Even archived Company Facts can lack superseded original entries; an actual historical point-in-time model requires filing-version selection as of each decision date plus company universe reconstruction, total-return/corporate-action-adjusted prices, and tests for delistings. More facts do not automatically create historical alpha, future forecasts, or real-money suitability. The set of companies is still a present-day selection.

V9.8 adds tests for cross-issuer coverage, issuer-specific cutoffs, withholding on any missing company, future restatements, original-versus-amended filing records, invalid/mismatched CIKs, source integrity, public/private navigation, and sanitized reports. Full Python/Ruff/JS suites, deterministic build, public SEC readiness, CSP, secret scan, whitespace, exact-file inventory and GitHub CI are mandatory before publication. Verify authenticated MFA, provider access, and the linked live research session separately.
