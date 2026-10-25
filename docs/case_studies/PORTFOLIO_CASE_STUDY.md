# QuantForge: recruiter-facing case study

**Problem:** Market-risk models can look impressive without being accurately calibrated or reproducible. Investors also need transparent scenario valuation rather than unexplained price targets.

**System:** Python tools collect official ECB euro-reference exchange rates and SEC company financial facts, validate data, run past-only statistical risk forecasts and three-case Microsoft DCF models, then compile an interactive static website with source fingerprints. The original more complex portfolio-optimization and options-pricing implementations remain available as inspectable code modules.

**Proof:** Review reproducible commands in README; run unit tests and GitHub Actions; explore the website's Markets, Risk, Valuation and Methodology tabs; inspect the source and its source-attribution evidence.

**Limits:** Reference rates are not tradable prices; currency risk is not ETF total return; the FX study is exploratory. Future earnings, WACC and terminal growth are analyst assumptions. No research paper is required and no result from a restricted Tiingo Starter dataset is republished.

**Status:** Software and offline validations complete locally; publish only after real ECB download and live Pages/CI verification on the owner's Windows machine.
