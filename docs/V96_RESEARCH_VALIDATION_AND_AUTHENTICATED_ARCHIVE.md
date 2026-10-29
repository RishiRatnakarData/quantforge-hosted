# QuantForge V9.6 — Historical Risk Validation, Company Cash Flow & Saved Research

Release base: V9.5 commit `3a6b480d465a15685df9f5d55fd9842f5214defa`.

## What is implemented

The private Research Hub now includes a connected evidence section shown in the Research Hub and Briefing, with a status note in the Research Lab. After a completed, current assessment it uses precisely its selected candidate, historical sample, virtual account, current quotes, and the separate SEC snapshot. Existing V9.5 computations are retained; V9.6 methods cannot change the Decision Center's primary action or place orders.

1. **Historical risk-policy comparison**. A rolling drawdown screen uses the previous 126 observations for each decision and then evaluates nonoverlapping 21-session later windows. The rule allocates 100% to one candidate or 100% to cash. It deducts user-visible 10-basis-point turnover charges, and compares against passive historical holding with one entry charge, including total observed window returns and maximum drawdowns. It is NOT the complete investment policy historically replayed. The comparison omits dividends, cash interest, taxes, slippage, corporate actions and survivorship corrections; selecting a rule after seeing history introduces selection bias.
2. **Cross-company cash-flow quality**. SEC-reported FCF margin, year-over-year FCF change, reported capex intensity and CFO/net-income coverage display separately for each eligible company and fiscal year. Negative metrics remain negative; missing/invalid/future/old financials are withheld. No implied stock target or fair value is produced. Issuer fiscal periods differ.
3. **Portfolio-weighted stress ladder**. When all current virtual holdings have fresh quotes and the exact matched historical series, the screen compares 2%, 5% and 10% cash-funded candidate exposures, with weighted historical volatility and historical expected shortfall. Partial-account datasets are rejected. These are scenarios, not executed broker orders or realized returns.
4. **Durable, opt-in research archive**. On pressing **Save current assessment**, a bounded summary is stored through the existing MFA-protected `private/notes` endpoint with optimistic concurrency (`expected_version`). Delete is per-entry, confirmation required. Regular notes are preserved and not replaced; the system refuses new saves if the notes limit is reached. The archive persists only to the extent the existing backend's notes storage persists. It does not keep the entire briefing, portfolio values, holdings, raw quotes, or price histories; recent *session* history from V9.5 remains separate. No new database, key, cloud service or provider subscription is needed.

## Privacy and operational boundaries

- No trading or portfolio mutation is triggered by the pure V9.6 module.
- No localStorage, IndexedDB or unauthenticated persistence for account research.
- The existing `private/notes` API is a backend dependency; a successful full release or HTML deployment alone **does not prove authenticated saving or loading works**. A user-signed-in MFA browser test is required.
- A report is invalidated on changes to selection, parameters, quotes or market history using the existing V9.0 mechanisms. Explicitly saved *historical* summaries remain identifiable as archived research, not current advice.
- Exported V9.6 summary intentionally excludes private portfolio allocations, risk metrics, raw observed returns, account amounts, and credentials. On-screen data are private.
- Three inline JS scripts with CSP hash enforcement retained. No paid APIs added.

## Live acceptance checklist

Sign in with MFA; load at least two selected companies and a dated price sample; run one assessment; compare the new Hub / Lab / Briefing evidence; test an incomplete holding's market data (the portfolio stress should be withheld); save one assessment; reload/sign out/sign back in; confirm the saved summary remains; delete it; check ordinary notes unchanged. This requires a live authenticated session and is not covered by offline unit tests.
