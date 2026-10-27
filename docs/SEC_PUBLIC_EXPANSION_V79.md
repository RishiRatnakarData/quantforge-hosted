# QuantForge V7.9 — Public SEC company expansion

## Why this can be free

SEC EDGAR Company Facts supplies public US-GAAP 10-K observations with no paid subscription or API key. SEC does require a declared User-Agent and compliance with fair access. Its host does **not** support browser CORS. Generate and validate a static snapshot server-side, then publish it on Cloudflare; never ask public visitors to call the SEC directly.

Authoritative SEC references:
- https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- https://www.sec.gov/about/webmaster-frequently-asked-questions

## Covered and uncovered data

- Eligible US-GAAP annual 10-K (not 20-F), qualifying roughly full-year fiscal durations, filed before the batch's processing cutoff.
- Annual revenue, operating income, net income, operating cash flow and cash PP&E purchases where reported; FCF proxy is cash operations minus cash PP&E purchases.
- Preserve accession IDs, tags, filing dates, source URL, and explicit nulls. Different issuers' fiscal periods and snapshot cutoffs may differ.
- No stock-price history, market capitalization, forecasts, analyst targets, dividend adjustments, or equity fair-value estimates. Those would require separate data and accounting.
- Some companies will be skipped because they lack compatible annual filings, use different filing forms, or tag their statements differently. The SEC ticker directory is not a guarantee of usable XBRL data.
- The initial 12 reviewed companies remain unchanged; additional rows have per-company `as_of` timestamps and `sector: Not classified` until a verified classification is supplied. Do not imply the whole combined snapshot has been freshly reviewed on the same date.

## Expand after V7.9 source and CI validation

From VS Code PowerShell, run in the existing QuantForge project directory:

```powershell
$contact = Read-Host 'Email address to identify your SEC research client'
$env:SEC_USER_AGENT = "QuantForge Research ($contact)"
Remove-Variable contact

.\.venv\Scripts\python.exe tools/extend_public_sec_v79.py `
  --symbols-file docs/SEC_V79_CANDIDATES.txt `
  --max-new 100 --min-new 1 --delay 1.2

Remove-Item Env:SEC_USER_AGENT

.\.venv\Scripts\python.exe tools/build_unified_site.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/audit_public_bundle.py
.\.venv\Scripts\python.exe tools/prepublish_check.py
```

**Do not push** if any validation fails. The earlier repository tests were written around a 12-company dataset, and some may need to be updated to check *at least the twelve original issuers* rather than an exact count. Preserve their checks for CIK, source URLs, dates, missing data, and public/private separation; never remove data integrity tests just to pass CI.

Review `git diff -- web/site/sec_snapshot.json`; a larger static file is expected, but it must contain only public SEC fields and no private account, quotes, API credentials, or user data. No new market-data licenses are required for published SEC records, subject to the SEC's published reuse policy and rights of any third-party elements.

The importer is intentionally a command-line maintenance job, not a public request endpoint. Do not add unauthenticated, unbounded SEC proxying on Render or Cloudflare.

## Updating and scaling beyond the first batch

Use a maintained list of desired ticker candidates, split into batches, or refresh from the SEC ticker directory. There is no hard 12-company limit in the V7.9 site. This is not universal live coverage: a static site only displays companies whose filings were downloaded, validated, and published. A future scheduled CI workflow may refresh the snapshot, but it should include SEC rate limits, caching, a secret contact identity, pull-request review, and an audit of GitHub Actions free-tier quotas.

Data coverage and data freshness are distinct: increasing the company universe does not automatically refresh all existing issuers. Refreshes should be tracked per company and the site should show that date.
