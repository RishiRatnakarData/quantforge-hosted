# QuantForge V6.4 — Private multi-asset research

This update extends the **owner-only** Market research, Backtesting and Optimization views to supported Alpaca USD crypto pairs alongside U.S. stocks and ETFs. Investment selection remains browse-by-name; no ticker memorization is required.

## New capabilities

- Read-only private historical daily crypto close bars via Alpaca's `/v1beta3/crypto/us/bars` endpoint, including guarded pagination, input allowlists, and a 10-minute bounded cache.
- 2–5 asset comparisons across selected stocks, ETFs and crypto, aligned to **observed common dates**, never fabricated stock weekend prices.
- Crypto-only returns use **365 UTC daily observations/year**; stock-only and mixed portfolios use **252 aligned market sessions/year** for annualization. Mixed weekend crypto movements are represented in the next shared observation, not as separately filled stock prices.
- Per-asset historical change, annualized volatility, maximum drawdown and worst aligned daily return.
- Clearly labeled *hypothetical* broad-market, crypto-only, and stock-only one-day stress comparisons. These fixed shocks are neither predictions nor historical events.
- Existing optimization and historical backtest workflows accept mixed assets after the private history is loaded. No holdings, virtual cash, trades, RLS, authentication, or SEC facts are changed.

## Data and modeling boundaries

Data come from the owner's Alpaca paper API configuration; requests must pass the existing Supabase-owner + MFA checks. Crypto bars use Alpaca US crypto aggregates on the UTC calendar. Stock bars are split-adjusted SIP daily prices and **exclude dividend returns**. No live price redistribution to the public, real brokerage orders, or investing recommendations. Prices are **not assumed synchronized across weekends**. Neither optimization nor backtesting is out-of-sample; no claims of predictive accuracy.

Stock and crypto data availability are subject to the owner's free plan, venue access, market-data outages, history depth and API rate limits. A missing or thin history results in an error rather than invented observations. More crypto pairs may require extending the existing virtual-ledger allowlist in a later release.

## Production verification

1. Deploy backend (Render) and frontend (Cloudflare Pages) from the same new GitHub commit.
2. MFA sign-in -> Market research -> Browse investments -> Supported crypto -> select Bitcoin and Ethereum -> 1 year -> Load market history.
3. Compare a stock/ETF plus a cryptocurrency; confirm common observed sessions and both assets appear on the chart.
4. Run Optimization and Backtesting using the selected observations; confirm allocations and no portfolio changes.
5. Sign out, confirm private endpoints reject unauthenticated requests.

No new environment variables, keys, tables or subscriptions are required.
