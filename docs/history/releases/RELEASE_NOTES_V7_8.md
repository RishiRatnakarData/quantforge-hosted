# QuantForge V7.8 — Website editorial and navigation refinement

## Purpose

Make public and private QuantForge pages easier to navigate, clearer about analytical findings, and more credible to finance, data, and engineering reviewers. This is a content and interface-label update, **not** a change to financial calculations or authentication.

## Public website

- Replaces the broad homepage claim with a concrete explanation: historical SEC company financials, portfolio-risk models, and strategy testing.
- Renames **Research lab → Analysis dashboard**; **Quant → Risk & allocation**; **Research systems → Research methods**; **Methods & engineering → Data & engineering**, and clarifies simulation-only model pages.
- Adds explicit categories for real SEC annual figures versus synthetic portfolio returns and simulated walk-forward paths, in the dashboard itself and on the homepage.
- Rewrites section intros and finding labels to describe what a visitor can inspect, compare, and verify.
- Preserves all public route IDs, including `#lab`, so existing links continue to work.
- Keeps source and test references, real reported issuer data, numeric models, and tables.

## MFA-protected private workspace

- Keeps the original nine tab IDs and functionality but uses more direct labels: Overview, Virtual trades, Investment screening, Market data, Optimization, Backtests, Walk-forward, Valuation, Notes & account.
- Simplifies selected-vs-loaded historical investment instructions, strategy-evaluation descriptions, trade simulations, and valuation-source explanations.
- Makes action labels more specific (e.g. Calculate impact instead of Analyze proposed purchase).
- Updates runtime status/instruction strings in the existing client only. No fetch paths, private state schemas, backend methods, MFA logic, database policies, market-data handling, or financial calculations are changed.

## Upgrade options

This package can apply to a **verified clean V7.6** checkout or a **verified clean V7.7** checkout. If V7.7 is absent, the release carries forward the V7.7 public analysis dashboard and tests as part of the same guarded installation. The installer refuses unexpected source hashes or an unclean repository. The authentic SEC snapshot stays in the user's existing repository and is never replaced.

## Offline validation and limits

- Focused editorials and structural regression checks: **21 Python tests passed** (using a temporary copy of an unchanged V7.6 public-evidence module that exists in the real repository).
- V7.7 financial computation and V7.8 navigation checks: **13 JavaScript tests passed**.
- Modified Python modules compile and modified JavaScript files pass Node syntax checks.
- Exact-source installer branch simulation: performed separately for V7.6 and V7.7.

The uploaded releases are patches rather than the complete Git checkout. Therefore, the full repository test suites, authentic SEC snapshot integration, security bundle audit, GitHub CI, and deployment must be verified by the supplied release script on the user's actual Windows repo. These cannot be claimed as passing from an isolated offline test.

## Privacy and data accuracy

Public historical company data remains drawn from the reviewed SEC Company Facts snapshot. The public portfolio and walk-forward inputs remain synthetic. The private workspace continues to use only authorized historical market observations and the user's virtual portfolio state. No brokerage orders are placed by QuantForge.
