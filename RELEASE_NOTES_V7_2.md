# QuantForge V7.2 — Private Investment Decision Brief

## What changed

- The owner-only **Investment ideas** tab now shows a compact **Investment decision brief** after an authenticated, on-demand historical price comparison.
- Summarizes the top three **research priorities** within the selected universe, with rank sensitivity across Balanced, Growth and Risk-aware perspectives. The 0–100 scores remain **observed-price heuristics**, never predicted returns, investment recommendations, price targets, buy timing, or guarantees.
- Computes daily-return Pearson correlations **only** for pairs whose underlying calendar dates align exactly, and warns about omitted pairs or undefined variance. Does not fabricate a diversification benefit from differently timed series.
- Flags higher historical volatility, large drawdowns, negative momentum, negative available SEC FCF-proxy margins, correlated candidates, and overlap with already-held **virtual** investments.
- Any current virtual-holding concentration is derived from observed quotes when all positions are priced; otherwise account percentages are explicitly unavailable. No virtual trades or state mutations occur.
- Downloadable JSON brief includes research priorities, market/SEC summaries, assumptions, limitations and correlations, **without** raw Alpaca price arrays, virtual positions, portfolio cash or private account notes.
- Clears the brief on selection/period changes, when loading new data, after failures, and at sign-out. All authentication and ownership controls remain on the existing private API.

## Scope and limitations

- This is **historical, educational decision support**, not personal financial advice or a forecast. The data does not establish intrinsic market value, future expected returns, immediate buy/sell timing, personal investment suitability, tax impact, or executable quotes.
- SEC fundamentals are observed historical context; company and ETF financial statements are not directly comparable. IEX-only histories are not consolidated SIP coverage, and price-only returns omit dividends.
- No brokerage orders, database migrations, credentials, new public API, or Render/Cloudflare service changes. Existing public technical showcase remains intact.
- Pure analysis: `web/site/private_decision_v72.js`, with `web/tests/private_decision_v72.test.cjs` and `tests/test_private_decision_v72.py` for regression coverage.
- Existing `tools/build_unified_site.py` bundles the analysis module into the existing private JavaScript group; compiled HTML still has **three CSP-hashed script elements**.

## Verification

Run `python tools/build_unified_site.py`, `python tools/audit_public_bundle.py`, `python -m ruff check .`, `python -m pytest -q`, all `node --test web/tests/*.test.cjs`, and `python tools/prepublish_check.py`. Publish only after the local gates and both GitHub Actions Python versions pass. Verify with actual Alpaca access in the deployed private workspace.
