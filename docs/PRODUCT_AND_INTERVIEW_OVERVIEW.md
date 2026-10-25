# The QuantForge product thesis and interview walkthrough

## Actual problem

A beginner sees ticker symbols, prices, investing jargon, and trade buttons before they understand what they would own. QuantForge helps them reason about **one proposed investment** using their stated goals, potential cash needs, portfolio holdings and modeled downside *before* they practice a virtual order.

## Five-minute demo for a hiring manager

1. Show **My home**: choose investment horizon and personal tolerance for possible loss; point out local privacy and why no real-money linking is needed.
2. Click **Explore an idea**, enter `VOO`, `$500`, and explain how to interpret the fund description, last observed price, time, source and cash left over.
3. Open the what-if: the proposed holding's share of portfolio comes from 
   `value_of_prior_holding + net_new_paper_purchase` divided by `portfolio_equity - assumed_fee`. Explain dollar shock and guideline flags; they do not decide on the user's behalf.
4. Enter `BTC/USD` and contrast a crypto scenario and why an equity earnings-based DCF is inappropriate for crypto.
5. Record a **virtual** transaction and show cash reconciliation, average cost, allocation and HHI concentration (`sum(weights squared)`); check the portfolio is never allowed to overspend or short.
6. Show the Microsoft FY2026 DCF if attached from the independently audited V3 SEC study, and disclose sensitivity to the terminal value and assumed capital expenditure intensity.
7. Open **My notes**, explain why preserving the reason for a decision can be more useful than adding a speculative AI stock prediction.
8. Open source/tests for `desk/companion.py`, `desk/engine.py`, `desk/server.py` and SEC valuation; emphasize tests of errors, incorrect data, stale market observations, privacy and math.

## How this is not just a brokerage clone

The product interaction begins with *why are you investing?* and *how would this change your portfolio?*, not order placement. The external data provider is a replaceable, read-only input; all personal decisions and computations run privately.

## Finance / quantitative concepts to defend

- **Weighted positions**: holdings value / current total (includes cash).
- **What-if costs**: paper fee is paid from cash and reduces total portfolio equity; don't implicitly create money.
- **Concentration**: HHI measures concentrated holdings, but it is not a full risk measure and understates overlap when separate ETFs own the same companies.
- **Dollar shocks**: if an asset drops 30%, a position of $1,000 loses $300, all else equal. The scenario is chosen, not estimated, and can be exceeded in real markets.
- **Monte Carlo**: seeded shared factor + idiosyncratic factors creates a positive-semidefinite covariance; class volatilities are *assumed*, never described as estimated from actual fresh price history. VaR/ES are conditional on those assumptions.
- **DCF**: forecast unlevered FCFF, WACC discounting, terminal value and enterprise-to-equity reconciliation; show why assumptions matter more than decimals in the output.
- **ML**: earlier HMM/volatility/optimization research modules exist, but don't say they forecast live stocks. ML is not used for investment recommendations in this release because credible training/history and proper validation were not part of this scope.

## Known limitations and next genuine product tests

Conduct a usability session with at least three novice users. Check whether they can: explain an asset's nature; name one portfolio consequence; identify data's freshness; and distinguish a simulated what-if from a prediction. Record findings and use them to prioritize future product work. The private Alpaca data feed must be verified locally with the user's own keys. A real public authenticated deployment requires security and data licensing work separate from this local-first implementation.
