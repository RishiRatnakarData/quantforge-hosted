# Historical Stock Replay — Financial Mathematics, Event Sequence, and Constraints

> **Archive notice:** This document describes a historical research milestone. For the current V5 personal desk and supported claims, see [README](../../README.md), [Status](../STATUS.md), and [V5 research-methods guide](QUANT_RESEARCH_METHODS.md).

## Why this simulator exists

The user chooses securities and a cash budget at a prior historical session. The engine displays observed prices only through that session. If they queue an allocation then advance, the engine trades at the next observed session's adjusted opening price, not the already-known price at the decision time. These are simplified deterministic cash-accounting rules; they do not constitute actual trading instructions.

## Financial state

At market session `t`, the portfolio consists of a cash account `C_t`, fractional shares `q_{i,t}` for each stock `i`, and market close `P^C_{i,t}`. Its marked-to-close wealth is

`W_t = C_t + sum_i q_(i,t) * P^C_(i,t)`.

A target allocation `w_i` is between 0 and 1, and `sum_i w_i <= 1`. The remaining percentage is uninvested cash. Negative weights and borrowing are rejected.

An order queued at the closing observation for date `t` executes at opening observation for date `t+1`, `P^O_{i,t+1}`. The cash account is marked to zero interest. All stock trades can be fractional. The benchmark is an independent buy-and-hold SPY position purchased at the same first observed next opening, with the same initial wealth and assumed trading cost.

## Transaction costs

The default fee rate is **5 basis points per side** (0.05% times the absolute traded notional). For a prospective target allocation, the engine solves

`investable = W_open - fee_rate * sum_i |target_i * investable - current_shares_i * price_open_i|`.

Then `target_shares_i = target_i * investable / price_open_i`. The difference from existing shares is the executed buy or sell quantity. Fees reduce investable wealth, so allocations are self-financing. Calculations are iterative with a convergence check; the long-only allocation limit must remain satisfied. The ledger records the execution date, symbol, side, adjusted price, shares, and fee.

## Risk statistics

For each **observed** portfolio close, compute `r_t = W_t/W_(t-1) - 1` (no cash flow after initial funding). Annualized historical volatility is `sample_std(r_t) * sqrt(252)`. Max drawdown equals `min_t W_t/max_{s<=t}(W_s) - 1`. Portfolio return is `W_last/W_start - 1` and the SPY buy-and-hold comparator uses its own equivalent initial wealth.

These formulas describe *realized sample variation*, **not** worst-case achievable loss or a future confidence interval. The Python reference simulator and browser replay are designed with the same accounting conventions. The Python suite independently checks next-open execution, cost deduction, cash-only outcomes, chronological order, rejection of leveraged weights, and invariance of past wealth to future-data mutation.

## Data-quality caveats

The CC0-labeled Kaggle set contains prices retrospectively adjusted for splits and dividends. Adjusted opening prices are useful **proxies for total-return replay**, but are not actual point-in-time tradeable opening quotes. The dataset does not reconstruct a proper cash-dividend and share-split ledger. A fixed set of successful companies in 2014–2017 is subject to survivorship and retrospective selection bias. These make results **exploratory**, not validated historical investment profitability.

The simulator excludes taxes, commission minimums, market impact, trading halts, partial fills, order rejections, fractional-share restrictions, and cash funding interest. Dates are *observed sessions*; there is no weekend interpolation. A historical risk result should never be presented as a guarantee of future investment performance.

## Live data is a separate display mode

The current-stock explorer uses TradingView's own embedded widgets with the vendor's branding. It does not scrape widget data, and the site's local historical simulation never implies that TradingView API access exists. For newer replay history, the engine accepts a user-provided CSV when the user independently has the necessary rights. Private CSV uploads remain local and are refused by the public site workflow.

## Source licensing and release process

The historical archive is described as CC0 by its Kaggle uploader; an archive SHA-256 is recorded before extracting asset bars. The source is [Huge Stock Market Dataset](https://www.kaggle.com/datasets/borismarjanovic/price-volume-data-for-all-us-stocks-etfs). The CC0 label is a source assertion and does not independently prove the uploader's chain of title. The uploader lists the final observation date as 2017-11-10. The public Pages workflow checks an explicit source-type/publication gate and refuses both the synthetic and private modes. The SEC-based Microsoft data is a distinct V3-origin module and must pass independent accounting checks before being shown.
