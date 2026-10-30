# QuantForge V13.0 — Evidence integrity and historical attribution

## Scope

This release unifies the previously deployed Research Hub assessment with historical point-in-time SEC replay, its 18 prespecified sensitivity variants, authenticated portfolio-risk readiness, and fee-aware observed-window attribution. It deliberately **does not** add an investment recommendation, forecast confidence score, automatic trade or brokerage endpoint.

## User-facing behavior

- **Integrated evidence console** appears in Research Hub, Research Lab status and Research Briefing; it stays withheld without a current authenticated assessment.
- **Five evidence gates:** method completion, required-method blocks, complete filing-date coverage, entire sensitivity grid, and matching private portfolio-risk availability.
- **Three classifications:** blocked, evidence-limited and evidence-complete. "Evidence-complete" means that the checklist is covered, **not** that an investment is attractive or that the strategy has predictive validity.
- **Observed-window attribution** computes successive after-fee wealth, maximum sampled-window drawdown, benchmark-relative win/loss counts, and selected-company concentration. All observations must be complete, date ordered and non-overlapping. No significance, bootstrap or probability-of-profit claims.
- **Export** includes only bounded classification, status, historical aggregates and limitations; excludes historical per-window records, raw SEC statements and private account data.

## Local source-chain validation

`python tools/audit_research_chain_v130.py` audits archived data and the V11.0/V12.0 offline reports for matching source digest, SEC cutoff, complete issuer/date matrix and preservation of unavailable checkpoints. This reads your previously created reports and writes one summary to ignored `data/`. Never put the archive or report in `public/` or commit it.

## Release and verification

The installer refuses to modify a checkout unless HEAD is a clean V12.0 main commit whose source file hashes match this package exactly and whose remote main SHA agrees. After a successful local lint/test/CSP/privacy pass it commits only the approved files and verifies GitHub CI and Cloudflare. The release does not verify live MFA authentication or browser input with Alpaca; those require separate acceptance. Once V13.0 is published, do not rerun its release installer.

## Limitations

Selected issuers are current and survivorship-biased. Original SEC filings may be absent from Company Facts. The observed comparison uses price-only non-overlapping holdout windows and excludes delistings, dividends, slippage, taxes and some boundary exposure. Evidence gates are diagnostic—not a claim of investment superiority, financial suitability or a validated forward-looking model.
