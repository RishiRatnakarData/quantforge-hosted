# QuantForge V9.2 — Decision Center visual hierarchy and evidence review

**Baseline:** GitHub `main` at confirmed V9.1 commit `d63f61dcb7640a0a1d0741f9199369507f56a715`.

## Purpose

Improve investment research **usability and decision transparency**, while preserving the verified V9.0 deterministic research policy and V9.1 eligibility-aware model execution. The Decision Center guides the user from (1) investment selection, through (2) risk and horizon settings, to (3) one-click analysis. The result presents the conditional action and *why* before any technical tables. Earlier research pages remain available under Advanced Research Lab.

## New user experience

- Responsive three-stage research form: select by name, set explicit constraints, run analysis.
- Assessment hero with clear conditional action, reason, research date and no-trading context.
- Four status figures showing available evidence dimensions, completed model methods, caution dimensions and model failures.
- Supporting vs conflicting or cautionary findings in distinct visual panels.
- Seven categorized evidence panels with states, source and scope. No color-only status communication.
- A same-window price-only comparison for all 2–5 loaded investments: observed start/end change and historical maximum drawdown. It uses identical aligned dates and refuses invalid/mismatched series; it is **not** a stock ranking or forecast.
- Progressive disclosures for what could change the conclusion, limitations, explicit policy/contradictions, and the full V9.1 method execution ledger.

## Research-policy refinement

`private_decision_review_v92.js` is a pure, auditable post-policy review layer. It preserves the already-calculated V9.0 action except when the assessment is positive **and** a V9.2 hard gate identifies missing required evidence or a failed required V9.1 method. This is a conservative abstention safeguard; it introduces no arbitrary combined factor score, fitted probabilities, forecasts or portfolio orders.

Distinguish:

1. **Hard blockers:** Missing company fundamentals, history, candidate downside, priced portfolio context, or failed mandatory model, all of which can prevent a positive action.
2. **Cautions:** Observed downside and concentration threshold breaches, contradictory available evidence, and failed optional research models.
3. **Optional lenses:** Imported independent FF3 and multi-asset walk-forward, which do not constitute independently validated evidence of a specific stock's future return.

No live dataset was introduced. Historical comparisons use already loaded dated quotes; company valuation continues to use existing SEC and observed-quote calculations. No data is sent to a hosted AI service.

## Known limits and later work

- Only the *focus candidate* receives a full company-specific SEC, valuation and portfolio assessment. The other selected investments receive an **observed-price risk comparison**, not complete issuer-by-issuer SEC research or ranking. Comprehensive same-method issuer comparisons require a separate eligible acquisition/caching workflow.
- Policy thresholds remain **assumptions, not statistically calibrated predictions**. Backtested historical investment-policy outcomes and robust calibration are later work.
- A risk-aware comparison is not a comprehensive security ranking. No claim of optimal stock selection or investment suitability is made.
- User-visible acceptance requires real authenticated MFA, pricing/filings availability, and Cloudflare deployment checks; CI cannot substitute for these.

## Review/acceptance

1. Verify the exact clean V9.1 Git baseline and expected source hashes before installing.
2. Rebuild generated website using the existing CSP-preserving builder; ensure three protected scripts.
3. Run V9.2 unit/structural, full JS and full Python tests, Ruff, SEC/public security/prepublish checks.
4. Inspect the private Decision Center on mobile and desktop: compare two equity/ETF names with aligned history; confirm readable columns and caveats.
5. Test stale/invalid history, insufficient company financial information, impossible or excessive concentration, and optional factors missing or failing. Positive signals must abstain when mandatory gates fail.
6. Change candidate, risk settings and history range after a run; previous assessment must clear and not be reused.
7. Validate no brokerage transactions, credential transfer or automatic hosting costs. Publish only after successful local verification and user approval.
