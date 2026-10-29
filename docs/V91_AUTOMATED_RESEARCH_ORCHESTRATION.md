# QuantForge V9.1 — Evidence-linked automated orchestration

**Baseline:** Verified GitHub V9.0 commit `d731555d3f9f46883218ad0c15c2e529ee17d82b`.
**Release:** Local installer and validation only. No commit, push or deployment is part of this patch.

## Product behavior

The private Decision Center now runs an eligibility-aware research workflow using the existing model implementations. It loads the selected 2–5 investments and runs only methods supported by the aligned historical observations and configured constraints. The candidate-specific dossier remains mandatory; individual portfolio analyses are optional, and model failures are recorded rather than silently treated as successful.

The automatic run coordinates these already-existing calculations:

1. Authenticated, aligned historical closes and metadata;
2. Constrained in-sample optimization (when feasible);
3. Historical buy-and-hold versus periodic equal-weight rebalancing;
4. Chronological rolling walk-forward testing (when enough past observations exist);
5. Multi-asset robustness sensitivity (only after sufficient successful test windows);
6. Candidate SEC fundamentals, dated observed-price valuation context, downside statistics and virtual portfolio fit;
7. Existing rolling-risk, ETF benchmark/proxy and optional valuation sensitivity evaluations;
8. Official Fama–French three-factor analysis **only when factors have already been voluntarily imported**.

The original V9.0 deterministic investment policy remains in control of the proposed action. The V9.1 orchestrator does **not** average model scores, fit a predictive price model or invent performance probabilities. It records *which* models ran and their scope, input history dates, provenance, success or unavailability. Required data-acquisition and candidate-research failures withhold a favorable proposed action; optional research failures do not fabricate outputs.

## Implementation contract

- `web/site/private_research_orchestrator_v91.js` is a pure planning, execution-ledger and reconciliation module. It contains no I/O, storage or broker routes.
- `web/site/private.js` reuses existing model functions. It does not create parallel research calculators or new financial datasets.
- Outcome categories are **completed**, **failed**, **ineligible**, and **skipped**. A pending outcome blocks final report publication.
- A post-analysis, progressively disclosed panel shows the model execution ledger and source/date/sample coverage.
- Explicit candidate, selection, policy, period and authenticated-session changes invalidate a running report. The loading state no longer strands the Analyze button after those changes.
- SEC source data, rendered CFA/FF3 labels, current MFA route and the virtual brokerage order interface remain unchanged.
- The compiled site still consists of three CSP-hashed scripts, with the pure orchestrator inserted in the private bundle. No additional external service is used.

## Limits

- This increment orchestrates existing interactive research modules and normalizes their **completion and provenance**. It does not yet transform every specialist model's metrics into a universal standardized numerical evidence schema; V9.2 should extend comparable fields and decision-policy calibration.
- An optional model's completion does not automatically become independent positive support for a single stock. Multi-asset backtest performance, ETF proxy regressions, rolling risk and FF3 exposures require domain-appropriate interpretation.
- Some analysis choices use the current Research Lab's user-set parameters. The ledger reports completed method scope; it is not yet a full set of model assumption snapshots or a persisted research archive.
- Provider availability, Cloudflare deployment, live MFA, SEC/quote freshness and the user's actual portfolio can only be verified through authenticated live acceptance testing.
- No investment trade is placed. Research is conditional and not guaranteed to predict outcomes.

## Local acceptance

1. Start from the exact V9.0 commit and clean working tree.
2. Apply the guarded V9.1 installer. It verifies baseline file hashes, backs up changed files, builds the existing public site and runs the complete test and security suite. It **never** commits or deploys.
3. Inspect the Decision Center with MFA. Compare a liquid company and a relevant broad-market ETF using an adequate 1–2 year window.
4. Verify the execution ledger: completed versus unavailable models, same selected universe, observed dates and optional FF3 import.
5. Test no-FF3, inadequate history, impossible cap and unavailable SEC/quote scenarios. Ensure positive investment assessments are withheld without required data.
6. Change candidate and policy during an in-progress run and verify that the stale result is not published and the button can be used again.
7. Visit Advanced Research Lab to confirm each original model and chart remains accessible and no transaction occurs.

## Releasing

A successful local install is not proof of Cloudflare deployment. Review the diff, commit **only** approved source/tests/docs and generated public files, push, verify CI on the exact SHA and separately verify Cloudflare and authenticated private behavior.
