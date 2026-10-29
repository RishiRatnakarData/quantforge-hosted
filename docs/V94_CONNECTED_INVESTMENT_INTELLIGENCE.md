# QuantForge V9.4 — Cross-investment research intelligence

**Baseline:** GitHub V9.3 `c668235b696574e1602103289943ed40bf16a5c4`.

## Product change

V9.4 closes an important gap between one deeply analyzed focus candidate and the other chosen investments. After the same authenticated Research Hub run:

1. **Comparative SEC fundamentals:** Examine revenue, year-on-year revenue growth, operating margin, and free-cash-flow margin across up to five selected investments when their annual records exist in the **public SEC snapshot**. Financial statement absence is explicitly shown, including ETFs, crypto, and securities outside the catalog. Unavailable and negative cash flows are never replaced with zero. No claim of synchronized fiscal years, identical industries, fair valuation, real-time financials, or market-wide ranking.
2. **Historical co-movement:** Compute logarithmic daily observed returns for the exact same valid 64–2500-session window and disclose average Pearson correlations with other selected instruments. Insufficient, duplicate, out-of-order, invalid, zero-variance, or mismatched histories fail closed. These are not holdings-weighted actual portfolio exposure measurements or forecasts.
3. **Policy sensitivity:** Reapply the existing V9.0 conditional investment rules under conservative, balanced, and growth-oriented risk preferences using precisely the **same** dossier, observed inputs, user horizon and constraints. Show whether the conclusion changes. Do not confuse sensitivity with empirical investment skill, forecast certainty or decision-policy backtesting.
4. **One linked experience:** Results appear with the completed assessment in Research Hub, in the same-session Research Briefing, and as a status link in Research Lab. A research-note export now includes the V9.4 **bounded comparative packet** alongside the existing V9.3 briefing.
5. **Privacy and reliability:** No new provider calls, paid APIs, saved portfolio values, raw provider price vectors, browser storage, advice services, or trading paths. Changing input selections/session/preferences clears both linked reports; opening a Lab route does not infer a new conclusion.

## Data provenance and scope

- Public issuer annual filings: the existing `window.QFPublishedSEC` SEC snapshot from the **public** compiled SEC research section, frozen at its recorded `as_of` date. This is not an authenticated per-issuer live refresh.
- Price correlations: an existing MFA-protected research session's *aligned* historical closing prices, summarized without exporting the price vectors or account positions.
- Rules: current deterministic research policy from V9.0 and the V9.1 model ledger; the primary proposed action still concerns the **single selected focus candidate**.
- SEC fiscal year-end dates, snapshot cutoff, missing financial metrics, and noncomparability remain visible.
- Correlation among selected research securities is an exploratory co-movement measure, **not** a substitute for true account-weighted diversification, cost sensitivity, expected returns, or professional suitability.

## Acceptance requirements

- One command from clean V9.3 SHA performs source preflight, backup, install, build, full Python/JS tests, Ruff, SEC/CSP/privacy checks, exact-file inventory, commit/push and exact-commit GitHub CI verification.
- Authenticated user must manually verify MFA, live provider quotes, selection, the Hub/Lab/Briefing hand-off, missing issuer behavior, and input invalidation after Cloudflare deployment.
- Must never autoplace a trade or claim that a positive action is supported by unavailable essential data.

## Remaining future improvements

This release does not yet implement out-of-sample historical **decision-policy** calibration, automatic real-time issuer filings, a market-wide cross-sectional ranking system, account-weighted scenario optimization across all candidates, persistent research history, or authenticated browser automation. These need separate methods, provenance, tests and acceptance before being claimed complete.
