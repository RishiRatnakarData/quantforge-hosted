# QuantForge — technical and investment interview defense guide

## Ninety-second explanation

QuantForge is a Python financial-research platform connecting statistical forecasting to actual risk evaluation and corporate valuation. The market branch estimates rolling one-day portfolio VaR using historical simulation, Gaussian, EWMA, GARCH and advanced regime/ML approaches, then validates chronology and compares calibration rather than simply optimizing in-sample returns. The portfolio engine accounts for trading delays, constraints, turnover and fees. The finance branch maps SEC financial statements to historical drivers, projects unlevered free cash flows and produces audited bear/base/bull DCF sensitivities. V4 unifies evidence, dashboards, a working-paper draft and an investment memo. The published V4 example is synthetic; live market-data claims require separate licensing.

## The strongest technical questions

**How did you avoid look-ahead bias?** The rolling model features and training cutoff must predate each forecast date. Execution weights are based on earlier information, not the close at which the evaluated return is realized. V4 rejects future-dated fit and filter columns.

**Why did simple EWMA outperform sophisticated models in earlier exploratory work?** More flexible models are sensitive to distributional assumptions, calibration, refit cadence and noisy volatility proxies. That prior exploratory analysis was not final holdout evidence and must not be publicly republished from Tiingo Starter data. A model's QLIKE, pinball loss, Kupiec p-value and independence diagnostic answer different questions.

**What's a VaR exception?** A day when realized portfolio loss exceeds a one-day predicted 95th-percentile loss threshold. Proper 95% VaR ideally produces near 5% exceptions without suspicious temporal clustering; it does not bound the magnitude of losses beyond the threshold.

**Why use bootstrap blocks?** Paired quantile losses are serially dependent. Resampling 21-session contiguous blocks gives descriptive uncertainty intervals that are less naive than iid resampling. This does not eliminate model-selection bias or turn development results into out-of-sample proof.

**Why separate EV and equity value?** The DCF capitalizes cash flows available to both debt and equity investors. Equity value equals enterprise value minus net debt, with disclosed adjustments or omissions for other non-operating claims and assets; per-share division uses a documented diluted-share proxy.

**How do CapEx and D&A affect FCFF?** EBIT(1-tax) + noncash D&A - cash CapEx - operating NWC investment. The sustained-35%-of-revenue CapEx stress recomputes all five years' FCFF and terminal value, holding other scenario assumptions fixed. It illustrates valuation sensitivity, not company guidance.

**What still limits your analysis?** The model assumes closing-price execution and simplified financing; SEC XBRL tags and diluted-share proxies require primary-filing diligence; market forecasting uses synthetic demonstration data for public distribution; neither option quote data nor independently licensed final holdout research has been completed.

**Why build a source manifest?** It makes a research run auditable: data origins, upstream exact file hashes, matching V1/V2 evidence, model windows, and DCF arithmetic are verified before reports are assembled. A SHA-256 checksum proves file correspondence, not validity or licensing.

**What was an engineering tradeoff?** The platform is deliberately local-first with a CLI and bundled offline Plotly dashboard, not a complex cloud API deployment. It keeps source, data quality, research methods and reports modular and easy for another developer to test.

## Never claim

Do not assert paid employment, professional investment performance, production trading infrastructure, independently verified return alpha, peer-reviewed publication, final ETF holdout testing, or publication rights you have not acquired. Results should be described according to the actual underlying data and validation evidence.
