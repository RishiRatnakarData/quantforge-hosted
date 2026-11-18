# QuantForge V6.1 — Private Asset Browser

The authenticated workspace now includes a click-to-select investment directory backed by Alpaca's paper trading Assets API. It is separate from the public SEC filing demonstration.

- Browse active eligible U.S. stocks and ETFs by **company/fund name**, A–Z, category, and pagination. Search is optional; no ticker typing is necessary.
- Choose investments directly for virtual quotes/trades, or build a 2–5-stock research basket for private historical analysis and backtesting.
- A small Popular view accelerates navigation; **All stocks & ETFs** queries the full eligible directory instead of the curated examples.
- A Supported crypto view covers the seven USD pairs implemented in QuantForge's existing virtual ledger, where returned by Alpaca. Broad crypto historical analysis is a separate future milestone.
- Provider directory results are cached server-side for one hour. Only sanitized names, symbols and exchanges are sent to the authenticated owner. No brokerage orders, credentials, private holdings or market price feeds are exposed publicly.
- Existing Supabase schema, historical SEC snapshot, MFA enrollment, saved portfolio state, private Alpaca keys and pricing calculation code remain unchanged.

## Important boundaries

An Alpaca-listed security may lack a recent IEX trade or sufficient SIP price history; selection does not guarantee a quote, current virtual trade, or history result. A virtual fill is still blocked for a stale quote. This release is an asset discovery improvement, not a claim of full brokerage order support.

## Verification

Run the full Python suite, JS syntax and existing 15 JS tests, publication safety checks, and GitHub CI before deployment. In the hosted site, sign in with MFA, select a company by name from Popular or All stocks & ETFs, request a quote, and choose two different names for historical research. Do not need to place a virtual trade to validate the picker.
