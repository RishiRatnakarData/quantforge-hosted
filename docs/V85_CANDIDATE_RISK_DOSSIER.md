# QuantForge V8.5 — Candidate-Specific Risk & Valuation Dossier

## Research question
For a candidate in the current loaded investment universe, what do observed price history, reported SEC financials, relative price behavior, and hypothetical portfolio losses reveal — and what evidence is still missing?

## Access
Available only in the MFA-protected private workspace, **Portfolio → Decision center → Candidate risk, valuation and portfolio scenarios**. First select 2–5 investments by name in Market data and **Load market history**. Then choose one candidate from the populated dropdown. The dossier is generated on explicit request.

## Financial measures
* **Observed price changes:** loaded-window compounded price return and trailing 63-session price change, neither a forecast.
* **Downside:** annualized daily-return sample standard deviation (252 or 365 per provider's `sessions_per_year`), historical worst peak-to-trough drawdown, empirical daily 5% loss quantile (VaR) and mean return in the worst 5% (expected shortfall). Price-only, in sample.
* **Peer-relative sensitivity:** candidate daily-return covariance with the equally weighted *other selected investments*, divided by that peer basket's sample variance. This is *not* broad-market beta, Fama–French factor analysis, causal attribution, or a predictive risk premia estimate. Correlation and in-sample R² accompany it. Missing denominator variance suppresses it.
* **SEC statements:** latest reported comparable annual revenue growth, operating margin, and operating-cash-flow-minus-capex proxy margin, with missing numbers suppressed. Annual growth requires comparable fiscal-year ends.
* **Market-priced valuation:** reuse the V7.3 issuer-validated, date-validated price/share/SEC bridge for P/S, positive P/FCF, and FCF yield. If SEC/price/share observations are missing, stale or unsuitable (for example ETFs), those ratios stay unavailable. This is not a DCF, intrinsic-value target, or a buy/sell rule.
* **Portfolio stress:** -20% isolated candidate price shock applied to the existing virtual position weight, and to hypothetical additional cash-funded investments equal to 5% and 10% of current virtual portfolio value. Requires complete and not older than seven-day quote dates for all held positions, sufficient cash for added allocations, and valid account data. Reports percentages only, not private balances.

## Integrity and privacy
The pure calculation module makes no network, storage, export or broker order calls. The private UI uses three already-existing authenticated API GET routes only after user action: SEC company, SEC valuation capital, and observed market quote. A request is discarded if the user signs out, the session changes, the selected investments change or the loaded history changes. Source strings are escaped before HTML insertion; private account balances, position quantities and raw close arrays are not included in the dossier report.

## Limitations and evidence requirements
The relative peer basket is a user-selected convenience comparator. Peer selection biases estimates; sample tails are fragile; equity price observations omit dividends and taxes; broad shocks assume independent instant changes that markets rarely exhibit; observed ratios do not establish fair value. A next phase may add separately sourced market/industry and Fama–French factor series with dated provenance, adjusted returns and out-of-sample stability checks, but this release does not claim to have those inputs.

## Acceptance
After installing locally: run full Ruff, Python and JS regressions, check CSP hashes and SEC static audit. After CI and a protected Cloudflare deployment, log in with MFA, load 2–5 comparable histories, choose candidate, analyze, then change the history selection and verify the dossier clears. A basic static Python HTTP server cannot serve the authenticated `/api` routes. Check a crypto/ETF or company without comparable SEC data produces 'Unavailable'. Confirm no order or virtual transaction occurs. Commit/push only after visual review.
