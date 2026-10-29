# QuantForge V9.5 — Portfolio Exposure, Past-Only Policy Audit & Research Session History

**Baseline**: V9.4, `cf1ce7f08afe1d6968d014575cfbef94953a40e2`.

V9.5 extends the same authenticated Research Hub assessment and its connected Research Briefing. It does **not** create a competing investment recommendation, transmit trades, or change brokerage/portfolio data.

## New capabilities

1. **Actual portfolio weights and historical risk**: uses current private virtual account cash, all nonzero holdings, dated quotes, and aligned loaded market history. Complete, valid, recent quotes are mandatory for weights. Full-market-history coverage of *every* held asset is mandatory for portfolio-weighted volatility, historical 95% one-day VaR/expected shortfall, and static-weight maximum drawdown. The calculation assumes today's weights are held constant over the prior window. It is **not** realized account performance and does not include dividend cash flows, fees, financing, or cash interest. A 5% cash-funded candidate what-if is shown when the available cash and history support it. Missing inputs block the dependent result.
2. **Historical risk-screen diagnostic**: at each chronological evaluation point, the price-only drawdown gate is computed from a **previous** 126-observation training window, then the next 21 observations are evaluated. Test windows are disjoint. Results report pass/blocked counts and ex-post observed returns. This does **not** reproduce the complete SEC-based decision engine, actual trade fills, or selection across issuers. It is not calibrated predictive validation.
3. **SEC-backed cross-company cash-flow scenarios**: for each selected issuer with complete, recent annual reported revenue and positive annual free cash flow, show FCF/revenue, FCF/net income (when net income is positive), and illustrative 10×, 15×, 20× annual FCF capitalizations. Figures are aggregate *pre-debt/pre-cash*, not equity values, share prices, official market valuation multiples, intrinsic value, or forecasts. Negative or missing FCF is withheld. Dates and source labels are retained.
4. **Session research journal**: last eight completed assessment summaries, displayed only in the authenticated browser session. Cleared on logout, explicit Clear action, or reload. This is intentionally **not durable cloud storage**; stable owner-only research-history persistence needs separate authenticated server/data policy work. The existing briefing export remains available and now includes only a sanitized V9.5 diagnostics-availability summary; never actual balances, holdings, weight vectors, raw prices or portfolio risk values.

## Integrated views

- Research Hub: new diagnostics follow the full assessment and V9.4 cross-company evidence.
- Research Briefing: the same diagnostics and a session-history list, not a separately generated recommendation.
- Research Lab: existing models remain available and unchanged; the Research Hub remains their shared orchestrator.
- Stale-state protection: changes to history, selection, inputs, quotes, and account load invalidate the current report. Old journal records are snapshots only and are not shown as current assessment.

## Safety & acceptance

- No automatic live or paper orders, no new network/provider/AI service, no account mutation or change to MFA.
- Keep the exact three CSP-protected compiled scripts and public/private partition.
- Pure calculations export only non-account diagnostics readiness metadata.
- Guarded release checks exact previous commit, origin, source hashes, modified-file inventory, build hashes, Ruff, full Python/JavaScript suites, SEC/CSP/privacy audits, and staged Git whitespace before publication.
- GitHub CI and the Cloudflare deployed HTML must be verified separately from authenticated live provider testing.

## Manual browser acceptance after deployment

- Sign in with MFA; run Research Hub assessment with holdings fully covered by 2–5 loaded investments and current quotes. Check cash/position weights and comparison against the cash-funded candidate scenario.
- Add (or select) holdings not present in the loaded universe. Check that **full** portfolio risk is withheld rather than computed from only covered holdings.
- Check past-only window audit, SEC scenario coverage and missing/negative FCF displays. Change research inputs to ensure current diagnostics clear while historical session summary remains clearly archival.
- Download briefing and confirm no private account values, raw prices or allocation weights; sign out and confirm private UI/journal cleared.

Future: a fully point-in-time fundamental decision-policy backtest, validated cross-issuer valuation using consistently sourced shares/quotes/debt, and durable MFA-bound research history should be designed and tested separately.
