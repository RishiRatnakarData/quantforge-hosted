# QuantForge V4.4 — Explainable Technical & Interview Guide

## What I built (a 30-second explanation)

"QuantForge is a personal investment research and virtual-portfolio application. It retrieves timestamped stock/ETF and crypto observations from a read-only market-data API, tracks virtual transactions in a local SQLite database, analyzes exposure and concentration, and illustrates downside scenarios. I integrated my earlier SEC-based Microsoft DCF model. The finance math is in tested Python modules and the interface explains the assumptions. I intentionally separated personal licensed market data from public code."

This statement should be used only once you have run the functions yourself and understand the calculations; never pretend a simulated forecast is verified.

## Questions an interviewer might ask

**Why SQLite?** Local-first, transactional integrity, audit trail, no cloud bill, and private user holdings. A buy either updates cash, position and journal together or none of them.

**What's the difference between price and portfolio value?** A market observation is a quoted/traded asset price. Portfolio equity is **cash + Σ(quantity × latest observed price)**. The chosen trade price is a hypothetical last-trade fill—not executable NBBO.

**How does average cost work?** A new purchase adds (gross purchase value + fees) to aggregate book cost, divided by total units. A sale removes units at the current average cost and realizes proceeds minus fees and removed cost. This is a reporting convention, not FIFO tax accounting.

**What's the concentration algorithm?** Portfolio weight = position value / total equity. HHI = Σ(weight²) for invested positions, excluding cash except through its effect on weights. For a full-invested equally weighted portfolio of 4 assets, HHI is 4×(0.25²)=0.25. Correlated holdings and ETF overlap require separate analysis.

**How do you size a new position?** Compute the binding minimum of free cash after reserve, remaining single-position 25% capacity, and remaining crypto 15% capacity. Remainders below zero become zero. Treat the caps as configurable guardrail illustrations, not optimal portfolios or fiduciary advice.

**What is Monte Carlo?** Generate many independent random draws, combine one shared shock with asset-specific shocks, scale the simulated returns by ASSUMED volatility, and calculate simulated next-period portfolio losses. 95% VaR is the loss at the 95th percentile; expected shortfall is average loss in the worst 5% of runs. Without verified histories these estimates are hypothetical and should not determine real-money allocations.

**Why factor shocks?** A common market factor produces positive-semidefinite correlation by construction. When stocks and ETFs share factors, they may decline at the same time, unlike fully independent assets.

**Why separate data for stocks and crypto?** Crypto trades 24/7 and trades on fragmented venues; stocks have market sessions and IEX is only one equity exchange. Separate timestamps, assumptions, and market-data caveats are necessary.

**How does the DCF work?** Forecast EBIT, subtract taxes, add noncash depreciation/amortization, subtract CapEx and change in net working capital. Discount FCFF using assumed WACC; add discounted terminal value; subtract net debt; divide by the diluted share proxy. Explain uncertainty in WACC, CapEx and terminal growth. The V3 base result is not a recommendation.

**Where is machine learning?** Earlier V2 research modules implemented chronological model comparisons and forecasting under dated data; **the current-day desk does not deploy them as real-time stock-price predictions**. That's intentional: we chose data quality and honest model validation over unsupported forecasts. ML company comparisons can be added after cross-company SEC coverage and reproducible labels are established.

**What bugs/test cases matter?** Overspending, negative or NaN prices, forged or stale timestamps, future market data, symbol injection, short sales, cash reconciliation, fee application, zero positions, tampered valuation identities, and disclosure of API credentials. Automated tests are included.

## Explainable formulas

- Position value: `shares * last_price`
- Portfolio equity: `cash + sum(position_values)`
- Portfolio weight: `position_value / equity`
- Portfolio concentration: `sum(weight_i ** 2)`
- One-scenario portfolio loss: `sum(position_value_i * shock_i)`
- Max virtual buy budget: `max(0, min(cash - 5% equity, 25% equity - current_position, crypto_cap - current_crypto))`
- Base FCFF: `EBIT - operating_taxes + D&A - capex - change_in_operating_working_capital`

## What you should never claim

- "My app predicts which stock will go up."
- "This historical VaR is validated on current prices." (Not in current release.)
- "The Alpaca IEX latest trade is the consolidated best bid or ask."
- "The paper portfolio represents my real brokerage results."
- "The Microsoft DCF is a fair-value consensus or recommendation."
- "An unpublished research demo is independently peer reviewed."

## Career fit

- Finance/investment analyst: SEC statements, cash flow, valuations, exposure decisions.
- Risk/quant analyst: mathematical scenarios, constraints, correlation assumptions, reproducibility and model limitations.
- Data scientist/engineer: reliable API ingestion, schema checks, numerical testing, attribution and source segregation.
- Software engineer: local web API, typed business constraints, atomic state transitions, automated regression tests.

User practice task: simulate a $250 paper purchase, identify which table captures it, and explain how the transaction fee changes portfolio equity. Then test a BTC/USD quote and show why 24/7 timestamps differ from equity-market trading hours.
