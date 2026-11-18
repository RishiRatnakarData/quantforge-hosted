# QuantForge V8.2 — Reproducible SEC case study and end-to-end readiness

## New public artifact

- Historical SEC financial case study for MSFT, AMD, ADBE and AMAT, generated from the **existing 94-company SEC snapshot** in the exact checkout being released. The build never downloads financial data or modifies the source JSON.
- Accessible latest-period comparison table, three compact SVG bar charts with negative/positive and missing-value handling, and issuer-level multi-year tables.
- Downloadable CSV metric ledger including SEC US-GAAP tags, filed dates, accessions, SEC Company Facts official URLs and issuer extraction cutoffs where recorded; missing cutoffs are explicitly noted and never inferred.
- Filing-backed, generated observations plus balanced cross-company comparison limitations. No market-price claims or predictions.
- Public **Research methods** page gets one case-study card linking to the new static HTML and CSV; no public navigation or private workspace tabs are rearranged.

## New validation

- Eleven pure-Python test cases including data math, source reconciliation, escaping, CSV injection, reproducibility, duplicate avoidance, and actual-source integration.
- New read-only V8.2 static readiness audit covering nine public routes, private view presence without accessing holdings, immutable-source hash, three-script CSP boundary, and the case-study link/output.
- Live-owner manual checklist for public research workflows, MFA, virtual trades, historical research, valuation and glossary/report accuracy.

## Important boundaries

- The report is **as-of-snapshot**, not a point-in-time historically investable dataset; previously filed restatements can appear.
- Comparisons are descriptive and business/fiscal-year differences matter; there is no claimed live market-price feed, stock-price prediction or investment recommendation.
- Private authentication, provider credentials, APIs, market-price engines and portfolio records are completely unchanged.
- No new dependencies, paid providers or scheduled workers.

## Local and CI validation

The Windows runner will verify baseline commit, clean Git checkout, V8.1.1 source markers, the 94-company public snapshot, report generation, link audit, Ruff, full Python/Node regression tests, security and publication checks, and exact-file staging. Push is permitted only after all local checks pass; matching GitHub CI must still pass before release completion can be claimed. Cloudflare production and private MFA functional acceptance require separate checks.

## V8.2 SEC issuer cutoff compatibility (revised package)

- Handles older original issuer records where `as_of` was never recorded. The report explicitly displays **Not recorded in the source snapshot**, and leaves the corresponding CSV `issuer_as_of` cell blank.
- Retains strict validation of nonmissing dates, recorded SEC filing accessions, annual data, source URLs, and numerical reconciliation. No SEC amounts, source JSON, or private data are changed.
- Adds two regression cases for missing metadata and invalid nonmissing cutoff types; validates the revised package using a 94-issuer synthetic installation fixture.

## Legacy SEC provenance compatibility (V8.2 correction)

Some original 12-company records lack metric-level `sources[metric].end` even while recording the source accession and grouping the metric under an annual `fiscal_end`. The generator now accepts only **unrecorded** metric source periods; when a source-period end is actually recorded, it must match the fiscal end. The HTML flags unverifiable per-metric period ends and the CSV explicitly distinguishes `fiscal_end` from `source_period_end` using `period_end_verification`. No missing filing periods or issuer extraction dates are fabricated. The SEC snapshot remains byte-identical.
