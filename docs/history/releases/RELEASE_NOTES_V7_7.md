# QuantForge V7.7 — Public Quantitative Research Lab

## Why this release exists

V7.6 established a professional presentation, reviewed SEC comparison, implementation references and grouped private navigation. V7.7 adds **interactive, computed public exhibits** so a visitor can interpret findings instead of reading descriptions of private models.

## New public research lab (`#lab`)

1. **Reported SEC financials:** choose from the existing reviewed 12-company SEC Company Facts snapshot. Inspect annual revenue, derived annual change, reported operating income margins, a bar chart, margin trend, fiscal dates, and a source link. Missing records remain unavailable; no published financial facts are replaced by examples.
2. **Constrained optimization:** reproduce synthetic return observations from a fixed seed; compute the sample covariance matrix with 12% off-diagonal shrinkage; solve for long-only, fully invested, capped minimum-variance weights. Compare weights and in-sample annualized volatility with equal weighting. A user can change concentration limits and see all results recalculate.
3. **Walk-forward research:** train only on preceding observations, refit in non-overlapping 20-session test windows and compare minimum-variance versus rebalanced equal weight. Turnover and basis-point costs are included in reported simulated wealth, and the chart and per-window table expose the chronology. Training-window length and fee inputs are adjustable.
4. **Technical evidence:** links lead to the public model source/tests, SEC pipeline, and existing private optimizer/walk-forward code for independent inspection. Five research disciplines are shown explicitly without claims of professional work experience or investment performance.

## Separation of evidence

- **Historical observed values:** the source-controlled, reviewed public SEC snapshot already in the deployed application, loaded at build time. Each company fiscal-year result is from the snapshot; code computes ratios and trends. Do not mistake it for real-time market pricing.
- **Synthetic financial time series:** deterministic return generation for five *generic baskets*, explicitly not actual traded assets, private Alpaca data or historical investment returns. Simulated out-of-sample results are not empirical evidence of outperformance.
- **Authenticated research:** **unchanged**. No files in `cloud/`, `functions/`, Supabase, private model scripts, `sec_snapshot.json`, or existing portfolio records are updated.

## Files

Existing source files updated: `web/site/site.template.html`, `web/site/app.js`, and `tools/build_unified_site.py`.

Added: `web/site/public_lab_v77.js`, `web/tests/public_lab_v77.test.cjs`, `tests/test_public_lab_v77.py`, and these release notes.

## Validation gates

Offline checks supplied with the patch: ten Node.js model tests plus four static Python tests, JavaScript syntax, a desktop/mobile browser smoke test (1440px and 390px), and no client-side exceptions/overflow in that isolated fixture. The fixture-only browser preview does not reproduce real SEC facts or the entire website.

**Required before publishing:** run the release script on the real clean V7.6 Git checkout. The script compares exact source hashes, checks that the official SEC snapshot is unchanged, rebuilds all three CSP-protected scripts, audits the bundle, runs Ruff, the full Python and JavaScript suites, prepublish privacy checks, and only then commits/pushes. GitHub CI must pass, then verify Cloudflare deployed the matching commit and visually inspect real SEC figures.

## Interpretation and methodology limits

The public optimizer uses a shrinkage-adjusted sample covariance and projected gradient method to minimize in-sample variance under constraints; no claim of global optimality under arbitrary financial objective functions is made. Walk-forward separation reduces direct training/test overlap, but synthetic experiments cannot establish live performance or eliminate selection bias. Each selected basket is hypothetical; this research lab is not a recommendation to buy or sell securities.
