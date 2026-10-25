# V5.2: Company DCF and comparable fundamentals

## Scope and data

Valuation loads the chosen US-listed company's most recent standard **10-K US-GAAP Company Facts** via `SECResearch`, after validating the ticker against the SEC CIK directory. No price history or Alpaca order feed is needed for financial statement modeling. It requires revenue, operating income, separately identifiable depreciation/amortization, PP&E capital expenditure, year-end cash, current debt, **unambiguously noncurrent** long-term debt, and fiscal-year **weighted-average diluted shares**. Short-term investments are incorporated if identifiable; otherwise the omission is disclosed. It does not silently replace missing mandatory values or assume that an ambiguous debt tag is noncurrent debt.

Records must be annual, plausible 330–400-day periods, filed by the date of the request, with fiscal period selection and individual concept, filing date, and accession retained. A facts API is not a presentation of the audited statements; data may include subsequent amendments and different filings. **Review the issuer's 10-K** before relying on any calculation. Bank, insurance and REIT accounting often makes this conventional FCFF model inappropriate.

## Forecast and valuation

Default forecast duration: five fiscal years. Model inputs for revenue growth, operating margin, assumed operating cash tax, discount rate (WACC), terminal growth, and the working-capital increment are **editable analyst assumptions**. WACC is supplied, not learned from the observed company or CAPM regression. All percentages are checked for finiteness and plausible bounded ranges.

For fiscal year `t`:

- `Revenue_t = Revenue_(t-1) × (1 + assumed growth)`
- `EBIT_t = Revenue_t × assumed margin`
- `D&A_t = Revenue_t × (reported D&A / reported revenue)`
- `CapEx_t = Revenue_t × (reported CapEx / reported revenue)`
- `ΔNWC_t = (Revenue_t - Revenue_(t-1)) × assumed incremental NWC %`
- `FCFF_t = EBIT_t − max(EBIT_t,0) × cash tax rate + D&A_t − CapEx_t − ΔNWC_t`

Negative EBIT receives **no modeled tax credit**. D&A and CapEx ratios are historical proxies, not management forecasts. Working-capital change is an explicit approximation, *not a directly observed 10-K change*.

- `PV_explicit = sum(FCFF_t / (1 + WACC)^t)`
- `Terminal value at t=5 = FCFF_5 × (1 + g) / (WACC - g)`
- `EV = PV_explicit + Terminal value / (1 + WACC)^5`
- `Net debt = short-term debt + noncurrent debt − cash − [short-term investments if available]`
- `Equity value = EV − net debt`
- `Illustrative value/share = equity value / latest annual diluted weighted-average shares`

Terminal FCFF must be positive; WACC must exceed terminal growth. Shares are an **annual proxy**, not precise filing-date shares. Every model output explicitly states that it is illustrative, **not a fair-market-price claim or recommendation**.

## Sensitivity

A 3×3 sensitivity grid changes WACC by ±1 percentage point and terminal growth by ±0.5 percentage points. Other assumptions are fixed. Numerically invalid cases are shown as unavailable, not as artificial numbers. The interface shows the explicit five-year cash flows, reported concept provenance, and the share of estimated enterprise value attributable to terminal value. High terminal-value dependence is an indication that the model depends heavily on unverified long-term assumptions.

## Comparables

Two or three U.S. companies may be placed side by side using **reported annual revenue, growth, operating margin, net margin, FCF, and long-term debt**. The displayed year is per-company; differing fiscal calendars and accounting conventions matter. Missing fields stay blank. This is descriptive financial comparison, not a ranking algorithm.

## Limits, testing and next development

Unit tests cover FCFF algebra, enterprise/equity reconciliations, discount and terminal-growth monotonicity, SEC provenance, missing and ambiguous facts, and local HTTP read-only endpoints. No live SEC account call is asserted until it is tested on Windows. Unlike historical quant experiments (GARCH, HMM, Ridge/boosting), this is a deterministic scenario model, not predictive machine learning. Neither DCF nor company comparisons modify your SQLite portfolio or send a trade.


### Depreciation and amortization (V5.2.1)
The SEC Company Facts API may not provide a standardized full-year D&A fact even when
an annual 10-K discusses depreciation, amortization **and other**. Such a mixed line
is not automatically equivalent to D&A. The model first checks comparable annual
US-GAAP D&A concepts. When unavailable, it stops unless the user explicitly enters
a D&A-as-percent-of-revenue scenario assumption in **Additional assumptions**.
The output labels that amount as a user assumption, excludes it from SEC provenance,
and does not substitute zero. For Microsoft FY2026, the 10-K cash flow statement
reports **$38.534B of depreciation, amortization and other**, and the PPE note cites
**$34.3B depreciation expense**; these are different concepts and neither is
silently used as a standardized full D&A fact. This makes the DCF a sensitivity
experiment, not a validated investment valuation.
