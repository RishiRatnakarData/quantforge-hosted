# V5.4 — SEC fundamental similarity and outlier exploration

## Purpose

**Research → Company peers (ML)** compares an individual U.S. public company's annual financial profile with a small, **explicitly selected** group of companies using on-demand SEC EDGAR Company Facts. This is an *unsupervised descriptive analysis*; it does not rank investment opportunities, forecast returns, claim fundamental comparability across every industry, or execute trades.

## Evidence and feature engineering

A separate SEC request supplies each issuer's latest available annual 10-K US-GAAP facts through the existing `SECResearch` implementation. Each source record retains its fiscal year-end and revenue filing date. The model uses five variables:

| Metric | Formula / source | Caveat |
| --- | --- | --- |
| Revenue growth (%) | 100 × (latest annual revenue ÷ adjacent previous annual revenue − 1) | Only when adjacent ~12-month years exist |
| Operating margin (%) | 100 × operating income ÷ annual revenue | Company accounting can differ |
| Net margin (%) | 100 × net income ÷ annual revenue | Unusual items can dominate |
| Free-cash-flow margin (%) | 100 × (operating cash flow − capital expenditure) ÷ revenue | Not a standardized GAAP reporting line |
| Long-term debt/assets (%) | 100 × reported long-term debt ÷ reported total assets | Excludes short-term liabilities; not comparable across all sectors |

No price, future earnings, stock-return labels, or Alpaca private quote data enter this model. Fiscal years may be different across issuers; they are explicitly shown. A missing metric is **not silently treated as zero**. Each company must have at least 4 of the 5 features available. Remaining single-metric gaps are replaced by the *within-selected-group median*, and the imputation count and target-specific imputations are displayed. Issuers with greater missingness, unmatched identifiers, duplicate CIK/share classes, or unsupported SEC facts are excluded with reasons.

## Similarity calculation

For companies `i`, metrics `j`:

```
center_j = median(feature_j among valid companies)
scale_j  = IQR(feature_j) (RobustScaler's zero-IQR handling)
z_ij     = (feature_ij − center_j) / scale_j
d(i, target) = sqrt(sum_j (z_ij − z_target,j)^2)
```

`sklearn.preprocessing.SimpleImputer` and `RobustScaler` are fit **only to the current selected group**. Constant features are omitted, and at least three varying features are required. The displayed five nearest peers minimize the resulting Euclidean distance. The *distance is not a probability, valuation gap, expected return, or stock recommendation*. It changes if the comparison group or included metrics change.

## Outlier exploration

When at least **12 distinct companies have usable SEC facts**, `IsolationForest` (256 trees; reproducible seed 341; `contamination="auto"`) produces a score per company. The UI displays only the **rank within the selected group** (rank 1 is relatively most unusual). No fraud, distress, credit-risk, or financial-health classification is inferred. Below 12 companies, the outlier diagnostic is unavailable rather than manufacturing a result.

**Important validation distinction:** This data has *no ground-truth stock-outcome or anomaly labels*. Therefore, neither the similarity distances nor the IsolationForest rank has supervised cross-validation accuracy, predictive power, backtest alpha, sensitivity, or specificity. Anomaly ranking is sample-relative, not a calibrated statistical p-value.

## Stability checks

To assess feature sensitivity, re-evaluate the closest peer after omitting each feature once. Report the count of trials in which the nearest company is unchanged. This is a **feature-ablation sensitivity check**, not out-of-sample prediction validation. Stable ranks under one deletion do not imply financial validity or future performance.

## Data limitations and safeguards

- Annual 10-K records only; different companies' fiscal end dates can differ by months.
- Peer groups are curated convenience sets, not verified industry-index membership or statistically random samples. The target is included even if it is not part of the selected group.
- Financial-sector balance sheets and accounting are often not comparable with technology/consumer issuers. The Finance preset requires special caution.
- Selecting mostly similar companies can make an outlier rank look persuasive even if the whole group is unrepresentative.
- SEC alternate facts, amendments and issuer-specific tags may cause omissions. The original accession and filing should be consulted for material conclusions.
- This local analysis fetches SEC public filings on demand; no private portfolio balances or broker credentials are sent to the SEC and no issuer-level ML output is posted publicly.
- This is a screening/research aid. It is not an investment recommendation, audited fundamental model, or production ML alert.

## Implementation and verification

| Component | Path |
| --- | --- |
| Feature engineering, peer distances, feature drop diagnostics, anomaly rank | `src/quantforge/desk/fundamental_ml.py` |
| SEC annual input and provenance | `src/quantforge/desk/sec_research.py` |
| Local HTTP endpoint | `POST /api/ml-peers`, `src/quantforge/desk/server.py` |
| Research UI | `src/quantforge/desk/investment_desk.html` |
| Synthetic fixtures and verification | `tests/test_v54_fundamental_ml.py` |

Unit/API tests use **fictional financial statements**. They verify reproducibility, duplicate issuers, missing evidence, minimum peer count, model-data limits, that the local API never mutates virtual holdings, and honest disabling of the outlier diagnostic on inadequate samples. **Authenticated live multi-issuer SEC requests still need testing on the user's Windows setup.** The full suite in the build runtime yielded `193 passed, 1 skipped` (the skipped optional DuckDB-dependent test).
