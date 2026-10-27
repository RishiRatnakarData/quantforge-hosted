# QuantForge V7.3 — SEC Market-Price Valuation Context

## Scope

A private, authenticated comparison of selected US-GAAP company disclosures with an observed Alpaca market quote. This is not a brokerage recommendation or a price-target model.

The user selects the company by name under **Valuation & peers**, runs its existing SEC scenario, then clicks **Compare observed market price**. The market quote is retrieved through the existing owner-verified `/api/private/quotes` endpoint; share count, cash and separated current/noncurrent long-term debt are retrieved on demand through a new MFA-protected `/api/private/valuation-capital` endpoint. The SEC requests use the same throttled and agent-identified SEC client and cache results for six hours.

## Metrics and definitions

- **Estimated market capitalization** = observed share price × reported point-in-time common shares outstanding.
- **Price / annual FCF proxy** = estimated market capitalization ÷ reported annual (operating cash flow − cash capital purchases). Only calculated for positive FCF.
- **Annual FCF proxy yield** = annual FCF proxy ÷ estimated market cap. Can be negative; this is **not** a dividend yield.
- **Market capitalization / revenue** = market cap ÷ annual reported revenue.
- **Indicative EV (partial)** = market cap + both current and noncurrent long-term debt − balance sheet cash. Shown only if all three balance-sheet components have the **same SEC period end**; this is not a complete enterprise value.

No `per-share fair value`, `undervalued`, `upside %`, or buy/sell score is computed. The existing hypothetical five-year DCF uses operating cash flow minus capex, **not unlevered FCFF**, and cannot legitimately be called enterprise value without additional adjustments. Market prices can be IEX-only rather than consolidated, and quotes, shares and annual filings are not necessarily contemporaneous.

## Fail closed

Missing, zero, negative, stale or misidentified quote/shares prevent market-cap multiples; missing or stale annual financials prevent relevant annual ratios; missing balance-sheet components prevent indicative EV. SEC facts are selected by filing and observation date with no fabricated zero. The new report does not contain private holdings, cash balances or credentials.

## Security, impact and validation

- Existing authenticated owner check and Cloudflare proxy secret protect the new GET route.
- The owner-only frontend invokes the new endpoint solely after a user clicks the button.
- No account database schema changes, virtual portfolio writes, new API keys, public licensed quote data, or real orders.
- `cloud/valuation_market_v73.py`, `web/site/private_value_v73.js`, their Python/JS unit tests, owner-protected route, and private workspace UI.
- Run Ruff, complete Python and JavaScript tests, unified website builder, CSP security audit, prepublication checks and GitHub Actions before deployment.
