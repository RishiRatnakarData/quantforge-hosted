# SEC statement extraction and Microsoft DCF

QuantForge has two distinct financial-analysis paths: (1) an **on-demand annual SEC fundamental viewer**, and (2) an **optional, previously researched Microsoft financial model and five-year discounted cash flow valuation**. The annual viewer does not calculate a generic intrinsic stock price.

## A. On-demand SEC annual fundamentals (V5 interactive desk)

**Source:** SEC EDGAR issuer ticker mapping and XBRL Company Facts (`data.sec.gov`). An identifying `SEC_USER_AGENT` email is supplied in the local process, not GitHub. Endpoint facts are cached in memory for the session.

The parser accepts annual **10-K / 10-K/A** US-GAAP facts with a start/end duration of 330–400 days. It chooses the newest supported fiscal end for revenue and attempts to align other statement concepts to the same fiscal end. Assets/debt use matching **instant** end-date records. Annual revenue growth is calculated only for adjacent periods (~330–400 days between year-ends). Source accession, fiscal end and filing date are returned for audit.

| Metric | Computation | Caveat |
| --- | --- | --- |
| Revenue growth | `(revenue_t/revenue_(t−1)) − 1` | Only comparable adjacent annual periods |
| Operating margin | `operating_income / revenue` | Annual US-GAAP tag must be available |
| Net margin | `net_income / revenue` | Accounting earnings, not cash flow |
| Simplified free cash flow | `cash_from_operations − cash_PP&E` | Not unlevered FCFF, excludes some noncash/reinvestment complexities |
| Total assets / long-term debt | Reported 10-K instant facts | Not a full liquidity/leverage assessment |

If a fact is unavailable the app returns a missing value; it does not guess. **Independent filing reconciliation remains necessary** because XBRL taxonomies, amended filings, context and company-specific tags differ. No automatic cross-filing audit is claimed for the V5 browser.

## B. Microsoft five-year DCF (separate V3 source workflow)

The prior Microsoft study used an SEC Company Facts extraction with an **October 22, 2026** information cutoff and an explicit five-year cash-flow model. This workspace only loads the V3 result from a user-selected folder and verifies its source manifest; it does not silently substitute a simulated SEC input.

### Earnings to enterprise value

```text
forecast_revenue_t = prior_revenue × (1 + assumed_growth_t)
EBIT_t = forecast_revenue_t × assumed_operating_margin_t
FCFF_t = EBIT_t × (1 − assumed_cash_tax_rate)
       + assumed_depreciation_and_amortization_t
       − assumed_capital_expenditures_t
       − forecast_change_in_operating_working_capital_t

cost_of_equity = risk_free_rate + beta × equity_risk_premium
WACC = equity_weight × cost_of_equity
     + debt_weight × pretax_cost_of_debt × (1 − tax_rate)
terminal_value_5 = FCFF_5 × (1 + terminal_growth)/(WACC − terminal_growth)
enterprise_value = Σ FCFF_t/(1+WACC)^t + terminal_value_5/(1+WACC)^5
equity_value = enterprise_value − net_debt
implied_value_per_share = equity_value / diluted_shares_proxy
```

All financial-statement dollar values in the V3 model are **USD millions**, and diluted shares are in **millions**. The diluted-share input is a historical weighted-average proxy, not a spot share count. Net debt is an explicitly simplified debt-minus-cash-and-short-term-investments bridge. WACC must be greater than terminal growth.

### Previously observed FY2026 Microsoft inputs

The independently documented annual-report reference includes:

| FY2026 statement value | USD billions | Interpretation |
| --- | ---: | --- |
| Revenue | 331.839 | Reported revenue |
| Operating income | 155.237 | Reported operating income |
| Operating cash flow | 182.935 | Cash from operations |
| Capital expenditure (PP&E purchases) | 115.948 | Cash PP&E investment |
| Simplified FCF | 66.987 | Operating cash flow minus PP&E purchases; **not** forecast FCFF |

These are **published historical company statement figures used as comparison anchors**, not QuantForge's assumed future cash flows. See [`V3_SEC_REFERENCE_CHECKS.md`](V3_SEC_REFERENCE_CHECKS.md) for the fuller statement audit.

### Scenario sensitivity and limitations

The model runs separate five-year bear/base/bull driver arrays for revenue growth, operating margins, CapEx, D&A, working capital, cash taxes and discount rates. It additionally varies WACC and terminal growth. These projections are assumptions, **not fitted forecasts**. A substantial portion of terminal-value-driven estimates depends on extrapolated cash flows and `WACC − g`; the sensitivity matrix is more informative than any single per-share number.

Other limitations: restricted standardized SEC tags; cash-flow D&A lines can include other items; the statement reconciliation needs independent source-filing review; share-count proxy, CAPM beta, risk premium, financing weights, tax treatment and future capital intensity are not market-estimated in this research prototype. **Do not equate a DCF scenario with a current stock recommendation.**

**Implementation:** `src/quantforge/desk/sec_research.py`, `financials/annual.py`, `valuation/dcf.py`, `research/v3.py`. See also [`V3_SEC_REFERENCE_CHECKS.md`](V3_SEC_REFERENCE_CHECKS.md).
