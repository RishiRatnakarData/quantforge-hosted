# QuantForge V7.4 — Private Portfolio Allocation What-If

## Scope

A **read-only, hypothetical proposed-purchase** view in `My workspace → Portfolio` using private Alpaca last-trade observations and the owner's existing saved virtual portfolio. This module does not place brokerage orders, record virtual trades, alter virtual cash or holdings, or change authentication or server endpoints.

## Workflow

1. In **Investment ideas**, choose stocks/ETFs by name using the existing directory. These and current holdings are available as candidates in **Portfolio → Portfolio allocation what-if**.
2. Select a candidate, choose a hypothetical USD spending budget no larger than virtual available cash, and click **Analyze proposed purchase**.
3. QuantForge requests current private quote observations for each held investment and the candidate (eight symbols per API call). Missing, invalid, future-dated, or more than seven-day-old quotes prevent misleading calculations.
4. Compare before/after portfolio weights, cash, proposed units, largest-position concentration, and HHI including cash. Total equity is conserved, assuming prices do not move and ignoring trading frictions.
5. If **Investment ideas** includes identically dated historical price observations for every existing holding and the proposed candidate, a separate **static-weight historical volatility comparison** is displayed. Otherwise, it is unavailable with a concrete reason.
6. Optionally export a sanitized JSON research summary. It deliberately excludes actual cash dollars, holdings inventory, individual values, proposed purchase budget, exact units and raw provider prices.

## Important model boundaries

- This is a **hypothetical cash-funded purchase**, not optimization, a price target, a future-return forecast, a tax calculation or an execution quotation.
- This version does not model bid/ask spread, commissions, slippage, taxes, liquidity, sector overlap, ETF constituent look-through or corporate actions.
- Alpaca IEX observations may not be consolidated market prices; quotes can be unavailable outside trading hours.
- The historical volatility sensitivity treats observed **price-only** returns and current/static weights. It does not claim that volatility will remain constant.
- Large concentration, missing historical series and stale quotes are explicitly cautioned.

## Security and delivery

- No new backend endpoint, permission, database table, API key or subscription.
- Safely bundles with the existing private CSP script; generated site remains on three CSP-matched scripts.
- Guarded installer validates the current repository, V7.3 marker, private source insertions and SEC snapshot; makes backups and refuses double-installation.
- The user's machine is the final quality gate: Ruff, full Python and JavaScript tests, privacy and bundle audit, GitHub CI, and live sign-in/portfolio verification.
