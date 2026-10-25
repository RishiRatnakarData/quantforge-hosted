# Portfolio mathematics — V5 personal desk

All dollar outcomes here are **virtual**. Market observations are last trades, not executable broker quotes. The ledger uses artificial fee and fill assumptions and is not tax accounting.

## 1. Value, allocation and P&L

For position *i*, quantity `q_i`, last observed price `p_i` and average entry cost `c_i`:

```text
position_value_i = q_i × p_i
portfolio_equity = cash + Σ position_value_i
holding_weight_i = position_value_i / portfolio_equity
unrealized_pnl_i = position_value_i − q_i × c_i
return_since_start = portfolio_equity / initial_virtual_cash − 1
```

The last item is **not** a time-weighted investment return and should not be confused with fund performance. Cash contributes to the denominator, but cash is not counted as an investment holding in the HHI sum.

## 2. Virtual trade accounting

**Buy:** user supplies total cash budget `B`, which includes an **assumed** one-way fee of **5 basis points**, `f = 0.0005`. Quantity is rounded down to 8 decimal places:

```text
q_buy = floor_8dp(B / (price × (1 + f)))
gross = round_cents(q_buy × price)
fee = round_cents(gross × f)
cash_debit = gross + fee ≤ B
```

The updated average cost includes purchase fees. A sell accepts units rather than a cash budget; `gross = units × last_price`, net proceeds are `gross − assumed_fee`, and realized P&L uses the average purchase cost of the units sold. Cash and holdings updates occur in a SQLite `BEGIN IMMEDIATE` transaction. No shorts, borrowing, margin, broker routing or exact market execution are modeled.

## 3. HHI holding concentration

```text
HHI = Σ w_i²  for noncash positions i
```

Example: Two holdings at 40% each and 20% cash produce `0.4² + 0.4² = 0.32`. HHI increases as capital becomes concentrated in fewer holdings, but it does **not** capture covariance, market beta, liquidity, or the risk of holding mostly cash.

## 4. What-if purchase and preferences

The user selects a hypothetical budget. The app estimates shares, fee, remaining cash, and before/after symbol weight. Warnings depend on saved **exploration settings**, not an optimizer trained on personal risk data:

| Setting | Single-name guideline | Total crypto guideline |
| --- | ---: | ---: |
| Cautious | 12% | 5% |
| Balanced | 20% | 10% |
| Adventurous | 30% | 15% |

The cash reserve is editable. An additional optional `position_capacity()` calculation uses **different fixed defaults**—25% single holding, 15% crypto, 5% cash reserve. Neither set is enforced by the trade ledger; they are transparent informational flags.

The decision preview's **single-position** decline assumptions are −30% for individual stocks, −20% for ETFs and −40% for crypto. It shows both the modeled total loss of the resulting position and the incremental scenario loss attributable to the new amount. These are deterministic shocks, not modeled probabilities.

## 5. Portfolio stress tests

The portfolio-level report includes two separate deterministic scenarios:

```text
scenario_A_loss = 0.20 × total_stock_and_etf_value + 0.40 × total_crypto_value
scenario_B_loss = 0.35 × largest_single_holding_value
```

The portfolio level uses a −20% shock for **all** stocks/ETFs, while the single-stock **decision-preview** uses −30%. These are separate what-ifs with different assumptions and should not be combined or described as estimated expected losses.

## 6. Monte Carlo risk — current desk

There is **no calibrated returns history** in the live desk. Instead, the engine simulates 5,000 scenarios with a fixed pseudorandom seed and **assumed** annual volatilities:

| Asset class | Assumed annual volatility `σ` | Shared-factor variance fraction `a` | Time scale |
| --- | ---: | ---: | --- |
| Individual stock | 35% | 0.60 | 21/252 trading sessions |
| ETF | 20% | 0.75 | 21/252 trading sessions |
| Crypto | 80% | 0.20 | 21/365 calendar days |

For simulation `j` and asset `i`:

```text
Z_i,j = sqrt(a_i) × common_j + sqrt(1−a_i) × independent_i,j
terminal_value_i,j = current_value_i × exp(−0.5σ_i² t_i + σ_i sqrt(t_i) Z_i,j)
portfolio_loss_j = current_equity − (current_cash + Σ terminal_value_i,j)
```

The shared factor induces positive dependencies. Cash is held constant. Because the lognormal drift is set to `−σ²t/2` before the random shock, terminal asset values have the same **modeled arithmetic expectation** as starting values in this idealized construction; it is not a statement about real expected returns.

```text
VaR_95 = max(0, empirical 95th percentile of portfolio_loss)
ES_95  = max(0, mean(losses ≥ empirical 95th percentile))
Pr(loss) = fraction of simulated losses > 0
```

These are **hypothetical simulation outputs**, not statistically backtested VaR/ES forecasts. The engine mixes an equity 21-trading-session horizon and a crypto 21-calendar-day horizon; this is a deliberate modeling simplification and must not be presented as a perfectly synchronized calendar forecast. 5,000 samples give visible Monte Carlo noise even with a fixed seed.

## 7. Compare investments

Given symbols A/B/C and budget `B`, evaluate each as a distinct hypothetical purchase from **the same unchanged base portfolio**, with identical notional spend. The app computes position weight, fees, resulting cash and assumed stress loss separately. It does **not** buy anything or stack the hypothetical rows. Since stocks, ETFs and crypto have different shock assumptions, their stress losses should not be treated as measured comparative risk scores.

## 8. Important omissions

No earnings forecast, ETF total-return history, risk-free yield modeling, tax-lot accounting, bid/ask spread, market depth, live execution, volatility calibration, liquidity model, realized alpha estimate, or personal suitability recommendation is implemented in this desk layer. Historical backtesting and ML research are documented in [the separate research methodology](QUANT_RESEARCH_METHODS.md).

**Implementation:** `src/quantforge/desk/engine.py`, `companion.py`, `comparison.py` and `tests/test_investment_desk.py`.
