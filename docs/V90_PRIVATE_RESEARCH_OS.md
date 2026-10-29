# QuantForge V9.0 — Private Research Operating System (first working increment)

**Baseline:** V8.7, commit `9b2805ca6ecc6b89e577b2cbc747d2ad1e110d59`.
**Status:** Local review only, not published or deployed by the installer.

## Why this change

The old private Decision Center displayed analyses already run manually and accumulated more and more specialist models inside one page. V9 reorganizes the owner workspace around research decisions, without losing the underlying methods or MFA protection.

## New private information architecture

1. **Decision Center** (first view after MFA): One-click eligible analyses; candidate chosen by company name; configurable risk approach, horizon, concentration and historical-drawdown screens. Conditional assessment with counterarguments, data quality and model provenance.
2. **Explore Investments:** Existing owner-only screening and company browser.
3. **My Portfolio:** Existing virtual holdings, prices, cash and *separate, explicit* virtual transaction UI.
4. **Advanced Research Lab:** Existing price-history, company dossier/FF3 import, SEC valuation, optimization, backtests, walk-forward and robustness. The long candidate/factor panel is moved out of Decision Center.
5. **Research Settings & History:** Existing guide, notes and controls. Persistent report history is **not** added in this increment.

All historical DOM anchors and specialist model controls remain accessible. Public pages are unchanged in their source template.

## One-click automated analysis

The Decision Center uses the existing user-selected 2–5 investment universe; if none is selected and 2–5 nonzero virtual holdings exist, it proposes that universe automatically. Users can choose investments by company name through the existing browser.

When Analyze is pressed, an MFA-protected session:

- Fetches fresh, selection-matched market history through the existing authenticated endpoint, for the chosen 6-month, 1-year or 2-year period.
- Runs the existing constrained optimization and eligible chronological walk-forward models, including robustness checks when enough evaluation windows exist.
- Runs existing company-specific risk, observed-price valuation, SEC fundamentals and ETF-proxy analysis, making only the provider requests that those already tested methods need.
- Uses the independent FF3 sample *only if previously imported voluntarily*. It never silently uploads or downloads third-party factor data.
- Reconciles the results through a **pure deterministic policy module** (no API calls or state mutation), and presents one proposed action, reasons for and against, model-by-model coverage, missing data and next steps.

**Scope limitation:** This is the working foundation of automated research, not universal data collection or a trained stock-prediction model. Screening across an entire watchlist, full valuation scenario-grid orchestration, persisted research histories and AI-assisted natural-language planning remain future increments. A private quote, issuer or SEC lookup may fail on free data providers; the decision engine must withhold conclusions when mandatory data is absent.

## Decision policy: explicit screens, not trained predictions

A decision requires matching, fresh daily price history; SEC company metrics with an eligible reporting period; a fresh observed quote; historical downside statistics; and a usable priced virtual portfolio. Unavailable or stale mandatory inputs return **Insufficient evidence**.

Current customizable screens:

| Input | Default | Alternatives |
|---|---:|---|
| Risk approach | Balanced | Conservative, growth-oriented |
| Horizon | 1–5 years | Under 1 year; 5+ years |
| Single-name concentration | 20% | 10%, 35% |
| Maximum observed drawdown | 25% | 15%, 40% |

These are **owner-configured research thresholds**, not empirically calibrated financial advice. Other valuation-screen assumptions (P/S bands, positive FCF yield) are descriptive defaults, shown in the evidence trail; they do not estimate fair value. Risk flags and hard gates override positive findings.

Possible outcomes: `Insufficient evidence`, `Research further before adding`, `Avoid adding for now`, `Hold / avoid increasing`, `Hold / monitor`, `Review / consider reducing exposure`, `Consider a small position (conditional)`.

Cross-model reasoning does not count correlated metrics as independent votes or treat multi-asset strategy backtest outperformance as evidence of future returns for the individual candidate. A consideration is not an order, and the virtual broker route is **never called** by the orchestrator or policy.

## Privacy and engineering contracts

- All Decision Center content remains inside the authenticated private panel. Login and MFA are unchanged.
- No backend schema, security route, account table, brokerage API, credential, SEC snapshot or public data contract is changed.
- The report exists in browser-session memory; it is invalidated when private account state, selected research, candidate or screen settings change, and on logout.
- No paid AI API, telemetry, client storage, hidden trade, or third-party factor export is added.
- The compiled site maintains the existing three CSP-protected inline scripts. The new pure policy module is concatenated inside the existing protected private bundle.
- Strict output escaping applies to all model-generated/source strings before HTML rendering.

## Acceptance tests

1. After MFA, Decision Center is the first visible private view. All previous specialist routes still work.
2. User selects a candidate by **company name** and clicks one button. Eligible models run in sequence; failing or stale sources are disclosed, never made up.
3. Altering the drawdown or concentration ceiling can change the proposed action in tests.
4. Stale quotes, stale returns, mismatched selections, unavailable SEC facts or unpriced holdings prevent an unsupported add recommendation.
5. Missing FF3 data is an optional evidence gap, not a fabricated factor loading.
6. A generated assessment never calls a virtual/live trade endpoint.
7. All existing Python/JS suites and full SEC/public/CSP/privacy release gates pass on the actual local repository **before publication**.

**Not a recommendation to trade.** Conditional research outputs are subject to model bias, omitted costs and uncertainty. All portfolio actions remain user-controlled.
