# QuantForge V8.4 — Private Investment Decision Center (local review)

The new private Decision Center combines analyses already completed in the authenticated session. It adds no new predictive scoring model, broker order route, external AI request, or data export.

## Where the evidence comes from

The existing investment screening, portfolio optimizer, past-only walk-forward backtest, robustness tests, SEC valuation research, and virtual purchase-impact calculator remain separate sources of truth. The Decision Center reads their current outputs and checks selected versus loaded investments, observed dates, quote completeness, and agreement between fitted and subsequently evaluated measures.

**Evidence coverage** is a count of available analysis categories, not confidence, investment probability, or a readiness score for buying. A highlighted next step is a research task, not a recommendation to trade. A higher screening score is not a return forecast. Available SEC cash-flow data alone do not establish a stock-price target.

## Private workflow

After MFA authentication, open Portfolio → Decision center or the shortcut on Overview. Run **Assess current evidence**. The display provides the observed investment universe and historical period, measured comparisons, contradictions, missing analyses and shortcuts to the original methods. The result is recalculated only on request and cleared when the user navigates back to the Decision Center or invalidates research.

## Important limits

This tool does not know the user's taxes, debts, emergency reserves, full exposure across accounts, current executable quotes, personal suitability, or future market returns. Historical returns are price-only and may omit dividends, bid/ask spread, slippage and taxes. Backtests can suffer selection bias and do not prove statistical alpha. No autonomous buy/hold/sell orders are produced.

## Acceptance after full local tests

Check Ruff, all Python and JavaScript regressions, the SEC readiness audit, CSP, and publication privacy. No source dataset, private account state, authentication settings, or broker integration is modified. The supplied source-only fixture cannot confirm authenticated live functionality: this requires a separate deployment followed by a real MFA session review. Check that missing quote data suppresses position weights, changed investment selection invalidates old model results, and research step buttons navigate rather than trade. Sign out and verify private content disappears.
