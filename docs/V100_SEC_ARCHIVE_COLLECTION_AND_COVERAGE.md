# QuantForge V10.0 — Historical SEC filing collection and measured coverage

## Baseline and goals

Baseline: V9.9 commit `97c4ff3240810d9591a4b25eb5e28eaf85afe180`, already released with GitHub CI and Cloudflare-content verification. V10.0 makes the archived filing workflow practically usable for the currently supported SEC issuer set while keeping raw downloads outside the published website and outside MFA-protected brokerage/notes APIs.

1. **Resumable official-source collection.** `tools/build_sec_archive_v100.py` obtains SEC Company Facts by CIK (max 100 current reference issuers, up to 15 fiscal years by default). Every response must match the source CIK and contain US-GAAP facts. Verified raw responses are cached in `data/sec_companyfacts_cache/`. Reruns reuse this cache; explicit `--refresh` replaces verified cached responses. Requests are sequential with a 1.2-second normal spacing, exponential backoff for transient errors and a truthful `SEC_USER_AGENT` with a contact email. No API key or paid data service is required. Failures are reported by issuer, not silently filled.
2. **Existing schema / private importer compatibility.** Each accepted response passes the V9.8 annual-fact extractor and the independent V9.9 archive auditor. The resulting `data/sec_filing_revisions_v98.json` uses the same verified revision schema already recognized by the V9.9 browser file picker. It records original and amended source versions *to the extent present in SEC Company Facts* and preserves reported filing dates, accessions and concept tags.
3. **Measured offline historical readiness.** `tools/report_sec_archive_v100.py` produces JSON and CSV under ignored `data/` showing the fraction of Jan 1 / Jul 1 checkpoint dates supported by two complete, consecutive 10-K fiscal periods for each issuer. Optional `--symbols AAPL,MSFT` returns the number of dates simultaneously covered by every member of that research selection. Missing issuers remain in the denominator. The report omits raw statement values and any private portfolio data.
4. **Connected browser readiness.** Once the user imports the local archive in the MFA-protected Research Hub, `private_archive_quality_v100.js` reports source-fact count, imported issuer coverage, eligible/checkpoint dates for selected companies and reasons for missingness. The Hub, Lab, and Briefing reuse the same in-memory import; the sanitized briefing JSON includes coverage counts, not raw filings, accessions, prices, holdings or account identifiers. Import is optional and never transmits source files to a backend or saves them in browser storage.

## Run and acceptance

The guarded V10.0 release validates its exact V9.9 baseline and staged files, runs Ruff and both complete regression suites, deterministic CSP website generation, SEC case-study readiness, security and prepublication checks, commits/pushes only approved files, watches GitHub CI, and checks production HTML. **Only after publication** does it attempt local SEC data collection, provided a truthful `SEC_USER_AGENT` is already set or can be constructed from the developer's configured Git name/contact email. If collection is unavailable, the completed code release is still valid: no fabricated archive is reported. Local archive collection is independently repeatable without rerunning the Git release.

To resume or collect after the release, with `SEC_USER_AGENT` configured locally, run:

```powershell
.\.venv\Scripts\python.exe tools\build_sec_archive_v100.py --max-issuers 100 --max-years 15
.\.venv\Scripts\python.exe tools\validate_local_sec_archive_v99.py
.\.venv\Scripts\python.exe tools\report_sec_archive_v100.py --symbols AAPL,MSFT
```

Use the generated `data/sec_filing_revisions_v98.json` file in the private Research Hub's existing **Local SEC archive JSON** file picker. Validate the imported issuer count, source cutoff, per-issuer coverage, and withheld historical periods before interpreting results. Sign out and verify that imported data clears; a saved briefing must not contain the archive's raw statement values.

## Explicit limitations

* Current supported issuers were selected today, not reconstructed as of every historical trade date. Delistings, membership changes, tender offers and survivorship bias are not resolved.
* SEC Company Facts may omit earlier original values later replaced by amendments; filing-date eligibility is not proof of complete historical source history. Fiscal calendars, tag taxonomy and reporting conventions vary across companies.
* Reporting is an **evidence coverage diagnostic**. It is not a full backtest of every QuantForge model, an unbiased model-selection experiment, a forecast or a recommendation.
* The V9.9 restricted historical rule uses selected price-only data with disclosed simplified fees; it does not reconstruct dividend/corporate-action-adjusted total returns, bid–ask spreads, taxes or market impact.
* Real SEC access is subject to the SEC fair-access policy. This tool must not run under a fictitious User-Agent. Bulk retrieval or later research commercialization may have separate rights and attribution requirements.
* Code deployment is independently tested by GitHub CI and Cloudflare content checks; protected MFA, live providers, archive import and deletion remain browser acceptance checks.

The archive, cached source responses, coverage report and any contact information used for fair access stay outside the published Git stage. No automatic brokerage actions are implemented.
