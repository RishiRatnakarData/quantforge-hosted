# QuantForge V9.7 — SEC Filing-Date Gated Historical Decision Audit

Baseline: V9.6 `cf790f01715fd98de0db08c11279c6932cea166e`.

## Delivered

The completed Investment Research Hub assessment now connects to a new historical *filing-date-aware* audit. The module is pure and runs entirely within the existing three-script, CSP-hashed private site. No backend or brokerage changes are needed. The Research Lab and evidence Briefing refer to the **same completed candidate, universe, market history and SEC snapshot**, and the JSON export includes a bounded, sanitized summary. Selection, price inputs and assessment changes continue to invalidate all linked results.

1. **SEC evidence timeline.** For every scheduled historical decision, verify that two comparable fiscal-year reports were public before the decision close. Annual fiscal-end dates do not substitute for filing dates. The revenue, operating cash-flow and capital-expenditure values must have valid SEC accession numbers and dated per-metric source records, and disclosed FCF must reconcile to cash flow less capex. Later filed restatements are **not** backdated into earlier decisions. Missing or stale facts are ineligible, not zero.
2. **Past-only restricted decision rule.** At each 126-session lookback boundary, apply a transparent rule: annual revenue increased, FCF margin is positive, and trailing maximum drawdown respects the current research drawdown constraint. When eligible, invest in the focus candidate for the next fixed 21-session evaluation interval or remain in cash. Selection and thresholds are explicitly not optimized. The outcome uses prices only **after** the signal boundary (idealized next-close execution), plus position-change fees.
3. **Evidence coverage and fail-closed reporting.** Count all planned evaluation intervals, eligible intervals and withheld intervals; show the latest dated decisions with SEC filing and accession provenance. If even one scheduled interval is missing eligible historical SEC information, **do not claim total rule returns or compare performance**. This prevents silently evaluating only favorable windows.
4. **Sanitized briefing export.** The export contains coverage, policy assumptions and aggregate outcome only when the audit is complete; no raw market prices, brokerage balances, positions, provider credentials or account identity. The private in-browser audit table can show SEC accession IDs.

## Important limits

This is **not** a full historical replay of all QuantForge models or a fully reconstructed point-in-time investment database. The published SEC snapshot holds a limited set of recent annual facts selected at the snapshot's cutoff. Earlier filings superseded by later restatements may not be present. Company coverage is a retrospectively selected sample; changing issuer universes, dividends, financing, taxes, splits, corporate actions, delistings, market impact and slippage have not been modeled here. The risk rule was selected knowing the past, so test windows do not independently establish predictive skill. Idealized next-close execution may not be achievable. The passive comparator is evaluated on the identical sampled windows, not a complete continuous portfolio return series.

**Prerequisites:** The latest loaded price history must contain at least 180 strictly increasing matched-date observations, two to five selected companies and the chosen candidate. SEC date-specific evidence must be complete. One-year price histories or companies with insufficient dated reporting will often show *withheld* rather than an overall return. A future enhanced version requires versioned historical SEC filing datasets, corporate-action-adjusted total-return data, and an as-of universe.

## Acceptance in a signed-in browser

Complete MFA; select two or more companies; load dated prices and run the Research Hub; inspect **What could the model actually know then?** in both Hub and Briefing; check Research Lab status; compare withheld counts for short/incomplete data; change inputs and ensure the audit clears; export the briefing and check the `filingTimelineV97` summary without account data; verify ordinary notes and saved research behavior are unchanged. Successful CI and HTML hash checks do **not** prove live MFA/provider functionality.
