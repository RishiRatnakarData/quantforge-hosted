# ETF Look-through and Portfolio Rebalancing (V5.1)

## Status and scope

Both algorithms are available in the local **Portfolio** screen. All trades in a rebalance plan are **read-only suggestions** for the user's existing virtual positions. Planning does not place an Alpaca order or update the SQLite paper ledger. The user may separately record virtual trades using the existing purchase and sale controls.

**ETF holdings are not available from an ETF price quote.** The app needs a dated constituent holdings CSV downloaded from the ETF issuer or another source the user is entitled to use. No proprietary holdings files are included in the repository. The local CSV is stored only in the user's private SQLite portfolio database.

## ETF holdings import

The import supports CSV fields `Ticker` (or `Symbol`) and `Weight (%)` (or `weight_pct`). The weight is a **percentage**, not a fraction. A fund with a 6% holding should contain `6`, not `0.06`.

Example of **fictional demonstration-only input**, not actual ETF constituents:

```csv
Ticker,Weight (%)
MSFT,6
AAPL,5
```

The Portfolio screen requires a fund symbol, **as-of date**, issuer/source description and CSV. The importer rejects malformed inputs, negative weights, percentages above 100, duplicate rows pushing the total above 100.25%, future dates, and unknown or unsupported ETF symbols. Some provider CSVs contain additional preamble lines; the parser locates a recognizable header within the first 120 lines. Rows lacking identifiable symbols are excluded from identified coverage, not silently allocated to other holdings.

**Known exposure to company `c`:**

\[
E_c=V_c^{\mathrm{direct}} + \sum_{f\in \mathrm{ETFs}} V_f\, h_{f,c}
\]

where `V` is a position's current marked dollar value and `h` is the imported ETF constituent's weight as a fraction. Portfolio exposure percentage equals `100 * E_c / portfolio equity`.

**Unknown exposure** for ETF `f` is `V_f * (1 - sum of identified constituent weights)`. ETF holdings with no import are **100% unknown**, not 0% exposure. Imported fund coverage and unknown dollars are shown explicitly. Cryptocurrency exposure is excluded from stock/company look-through.

**Known minimum ETF-to-ETF overlap** (as percentage points of fund holdings):

\[
O_{A,B}=100\sum_{c\in H_A\cap H_B}\min(h_{A,c},h_{B,c})
\]

This quantity measures known common constituent weights. If constituents are missing, the overlap is only a **lower bound**. It is not price correlation, portfolio covariance, a prediction, or proof that the remaining stocks are independent. The two funds' holdings dates may differ; inspect source and timestamp before using results.

## Rule-based rebalancing

The form lists currently held assets **plus cash**. The user specifies target weight percentages summing to 100%, with no new unheld securities added automatically. The paper ledger's quote observations remain unchanged. Asset value at the observed last-trade price is `q * P`; original equity is `cash + sum(q * P)`.

1. Target marked asset value is `equity * target_pct / 100`.
2. Sell (fractional) quantity of over-target holdings **first**, never exceeding held quantity; credit proceeds minus a simulated **5 basis point fee**.
3. Compute required buys for under-target holdings and reserve the user-selected target cash amount. Scale buys proportionally if fees or cash limit the budget.
4. Round shares down to 8 decimal places, dollar proceeds and fees to cents. Never permit negative projected cash; report estimated gross values, fees, after-plan cash and residual target drift.
5. Do **not** execute anything. A preview can be recalculated when prices or targets change.

Because we use a one-pass sell-first/buy-second approximation, fees, rounding and cash constraints can cause small deviations from targets. The app reports the maximum difference in percentage points. The result is not an optimal execution algorithm and does not account for bid/ask spreads, tax lots, taxes, slippage, market-hours constraints, share minimums, or venue-specific fractional-share restrictions. Users should not assume paper-trade execution at last observed prices.

Targets are user-selected, not financial advice. The planner **does not automatically enforce** the separate preference-based cash buffer, crypto limit or single-asset guardrail; the user must choose targets consistent with their preferences.

## Tests and limitations

`tests/test_v51_portfolio_intelligence.py` verifies CSV parsing, data provenance, partial coverage, direct-stock plus fund-stock overlap, ETF-pair lower bounds, rounding/fees/cash conservation, no ledger writes, zero-position portfolios, read-only HTTP routes and invalid requests. The existing suite continues to validate portfolio risk, SEC, data engineering, and earlier research modules.

All holdings data are **user-provided and not independently audited**. Staleness, issuer format variation, missing company identifiers, derivatives, bonds, cash holdings, share classes and corporate actions can make the reported overlap incomplete. Only equity tickers that can be identified by symbol are included; the user must evaluate fund holdings quality before making decisions.
