# QuantForge V6.6 — Research Diagnostics & Local Exports

This version extends the authenticated private research tools with diagnostics over already-loaded price and SEC-company data. It adds no market-data requests or new backend routes. The existing virtual holdings, trades, notes, cash, MFA, SEC public snapshot, credentials and Supabase schema are unchanged.

## Walk-forward evaluation

- Per-window optimized and equal-weight compounded returns, benchmark-relative percentage-point difference, and **both strategies' rebalance fees**. Window returns include the fee charged at that window's first rebalance.
- Fees are charged on absolute dollar turnover; per-window fees are reconciled against the total modeled fees. An inconsistency causes the diagnostic to stop rather than present fabricated totals.
- Allocation stability (one-half the sum of absolute weight changes between fitted weights), cap-binding frequency and number of outperforming windows. Allocation stability is **not** transaction-dollar turnover.
- On-demand transaction-cost sensitivity at 0 bps, the selected fee, and selected fee + 15 bps (capped at 100). All comparisons use the **same investments, training/test windows, objective, and cap**. This is a historical counterfactual, not a market execution model.
- A local JSON research report covering parameters, model outputs, window dates, fees, source, limitations and selected symbols. Raw market-bar feeds, private holdings, credentials and notes are intentionally excluded.

## SEC projection diagnostics

- Hypothetical discounted cash-flow-proxy sensitivity grid: 5 revenue-growth assumptions by 5 discount-rate assumptions, holding margin, horizon and terminal-growth inputs fixed. Invalid assumptions or missing comparable reported FCF remain unavailable rather than becoming zero.
- Observed SEC annual revenue-growth range presented separately from forecasts; **three annual periods are not evidence of forecast accuracy**.
- A separate local JSON report of observed annual SEC financials, hypothetical projected scenarios, assumption grid, provenance and limitations.

## Boundaries

The discounted model is a simple cash-flow proxy and **not** enterprise value, equity value, share-price target or a prediction. Walk-forward evaluation is a retrospective selected-sample simulation, not live trading or conclusive evidence of future returns. Prices exclude dividends, slippage, market-impact and taxes; SIP versus IEX coverage differs. Neither diagnostic triggers brokerage orders or modifies the virtual portfolio.

## Files changed

- `web/site/private.js` — authenticated diagnostics, UI rendering, controls and export handlers
- `web/site/private_walkforward_v65.js` — per-window transaction-cost bookkeeping
- `tools/build_unified_site.py` — new controls and script bundling under existing three-script CSP
- `web/site/private_diagnostics_v66.js` — pure diagnostic computations
- `web/tests/private_diagnostics_v66.test.cjs` and `tests/test_private_diagnostics_v66.py` — automated regression coverage

No environment variables, external services, migrations or dependencies are required.
