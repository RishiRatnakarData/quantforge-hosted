# QuantForge V8.2 — SEC financial research case study

## Research question

What do historical SEC 10-K financial statements show about annual revenue growth, operating profitability, and cash generation for four illustrative public companies?

**Public report:** `public/research-case-study.html` (linked from the website's **Research methods** page).  **Source ledger:** `public/research-case-study.csv`.

## Sample and source boundaries

The four issuers are chosen *before calculating the comparison*: **MSFT, AMD, ADBE, AMAT**. This is a qualitative illustration of a technical research pipeline; it is not representative sampling, stock selection, or a buy/sell recommendation. The source is the existing `web/site/sec_snapshot.json` file assembled from SEC EDGAR Company Facts. Its wider catalog contains 94 issuers in V8.1.1. Each issuer retains its own reported fiscal-end periods and, where recorded, an extraction cutoff; missing original-issuer cutoff metadata is explicitly disclosed rather than guessed; no new filings or prices are downloaded when this report is built.

## Equations and definitions

- Year-over-year revenue change = `(most recent annual revenue / preceding eligible annual revenue - 1) * 100`.
- Operating margin (%) = `annual operating income / annual revenue * 100`.
- Cash-flow proxy = `NetCashProvidedByUsedInOperatingActivities - PaymentsToAcquirePropertyPlantAndEquipment` (with the source tag fallback and statement-derived fact selection already completed by the existing SEC importer).
- Cash-flow proxy margin (%) = `cash-flow proxy / annual revenue * 100`.
- Net margin can be calculated as `annual net income / annual revenue * 100`, but net-income-derived investment predictions are **not** made in this case study.

Missing inputs remain **Not reported**, and inputs failing provenance or reconciliation checks block publication. Negative cash flows/margins stay negative. Outputs use as many as three eligible SEC annual periods per company; different issuers may have different fiscal year-end dates. The case-study generator does not silently fill gaps, pull stock prices, or use the owner’s private portfolio.

## Data lineage and reproducibility

The CSV ledger records each issuer, annual period, value, SEC US-GAAP source tag, filed date, 10-K accession, issuer extraction cutoff (blank where unrecorded) and official SEC Company Facts URL. Derived cash-flow values are marked as proxies, with their component source rows. The report includes the SHA-256 digest of the input snapshot. The generator uses only Python's standard library, has no network calls, and is deterministic for identical snapshot bytes.

To reproduce from the repository root:

```powershell
.\.venv\Scripts\python.exe tools\build_v82_case_study.py --repo .
.\.venv\Scripts\python.exe tools\audit_v82_readiness.py --repo .
.\.venv\Scripts\python.exe -m pytest -q tests\test_v82_case_study.py
```

## Analysis boundaries

This is a retrospective, *as-of-snapshot* comparison; Company Facts can contain revised or restated statements filed later than the fiscal year. It is **not** point-in-time information available to a trader at that fiscal-year-end date. Business-model differences, accounting choices, nonidentical fiscal periods, and annual-only reporting make ranking companies by any one measure inappropriate. No dividends, stock split adjustments, benchmark returns, capital-market pricing, valuation or predictive model are inferred from the filings.

The separate public **Analysis dashboard** contains explicitly simulated model exercises; it must not be represented as the performance of these real issuers. The private MFA workspace and its own historical price research are entirely outside this case study.

## How to explain it in an interview

1. **Data engineering:** describe source provenance, validation, atomic snapshot creation upstream, and deterministic downstream reporting.
2. **Analytics/BI:** explain the difference between accessible numerical tables and readable charts, how missing data is presented, and why fiscal years cannot blindly be aligned.
3. **Finance:** walk through operating margin and the FCF proxy; explain why positive FCF is not equivalent to a stock being cheap.
4. **Data science/quant:** explain how snapshot-time restatements can leak future information into historical strategies, and why real-company SEC fundamentals must be separated from simulated portfolio outcomes.
5. **Software engineering:** discuss immutable source checks, safe HTML escaping, CSV formula defenses, unit tests, public CSP and CI gating.

## Unresolved limitations

There is no audited point-in-time SEC vintaging service, monthly/quarterly comparability engine, dividend-adjusted market history licensed for public display, or live financial recommendation engine. Do not imply those exist. The SEC snapshot is a dated historical sample, not a continuously refreshed market-data service.

### Legacy source-date limitations

Certain original catalog entries include an accession number but do not separately store a metric-level XBRL `end` date. The source ledger leaves `source_period_end` empty for those entries, retains the catalog's `fiscal_end` grouping, and labels the missing verification in `period_end_verification`. A mismatched *recorded* XBRL period end is rejected. Independently check the SEC filing for any metric whose source period was not recorded in the local snapshot before citing it as independently period-verified.
