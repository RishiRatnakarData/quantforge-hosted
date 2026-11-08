# Predictive research, semantic themes, and sentiment

QuantForge runs the following **private, read-only** analyses when the owner selects 2–5 companies and presses **Analyze companies**. No orders are sent. These models do not certify investment merit or expected profit.

## Price-direction model: what is actually trained

`web/site/private_predictive_ml_v180.js` fits L2-regularized logistic regression to historical, authenticated Alpaca daily closes. It estimates a **five-session direction class**, not an exact future price or dollar return. Fixed features are lagged 5-, 20- and 60-session log returns, 20-session realized return volatility, and 40-session trailing drawdown. Training history is never constructed from future observations. The model standardizes features using each training slice only and fits with deterministic gradient descent. Zero, non-finite, duplicate, out-of-order, and insufficient price histories fail closed.

Evaluation begins in approximately the last quarter of the observed session dates. Every evaluation date is five sessions apart; all labels used for fitting have already matured by that evaluation date. This avoids overlapping **test horizons**. The model is refitted on expanding eligible past data for each evaluation. The fixed, no-tuning benchmark is an expanding historical positive-return base rate. We report the number and dates of held-out windows, five-session directional accuracy, and Brier scores for both models.

A positive directional message is suppressed unless there are at least ten held-out windows and the model beats the base-rate benchmark on Brier score. This is only a minimal research screen, **not** scientific proof of predictive skill: no transaction costs, dividends, cross-universe calibration, confidence intervals, or persistent live validation are established. Even a historical pass may fail badly later. The internal classifier score is uncalibrated and is never shown as an investment-success probability. Equity instruments are required; crypto histories are refused by this particular experiment.

## Financial news: source and provenance

`GET /api/private/news-research` is behind the existing proxy secret, owner identity, and authenticator verification. The API obtains up to 50 dated headlines for 1–5 owner-selected symbols using the server-side Alpaca market-data credentials and the documented news REST endpoint. It does not download full article content, store headlines in public assets, publish account credentials, or modify trades. The response is capped, filtered for the selected issuers, source-stamped and date-checked. News access may be unavailable depending on the account's data entitlements; that produces an unavailable state, not an invented sentiment score.

`cloud/news_intelligence_v180.py` groups dated headlines into broad subjects by **TF-IDF cosine similarity** to a fixed, transparent finance-theme vocabulary. This is lightweight statistical NLP; it is not a claim of transformer-level semantic understanding. The default sentiment method is a bounded financial-word dictionary with basic negation handling, clearly labeled **not a trained ML sentiment model**.

If an owner separately provisions an authorized local pre-trained FinBERT directory and its optional Python dependencies, set `QF_FINBERT_LOCAL_DIR` on the private API. The service uses `local_files_only=True`; it never initiates a model download or external AI-provider call. This mode performs pre-trained transformer sentiment inference on the same dated headlines, labeled separately in results. Its output must be tested against labeled financial text before production use as a predictive signal. Default operation does not require optional heavy transformer dependencies or a new paid API.

## Model-claim boundaries and career proof

- The static public site describes these methods but contains no private quotes, news, positions, or fabricated machine-learning validation metrics.
- News tone is **context**, never a free-standing stock recommendation or a causal explanation of price movement.
- Chronological, non-overlapping evaluation and comparison against a simple baseline are required before describing even a limited model signal.
- The investment assessment's hard risk gates still control the final decision. A price-direction experiment cannot override missing SEC evidence or a violated position/risk constraint.
- Additional production research would include point-in-time issuer membership, unbiased headline timestamps, news-label verification, rolling/repeated out-of-time validation, calibration, regime stability, transaction fees/spread, ablations, and prospective monitoring.

## Verification and sign-off

Tests: `web/tests/private_predictive_ml_v180.test.cjs`, `tests/test_news_intelligence_v180.py`, plus the existing full Python/JavaScript and public CSP/privacy suites.

Manual authenticated acceptance still required: MFA login; news entitlement and correct dates; Alpaca historical bars; one-click multi-company run; weak-signal treatment; no unexpected advanced panels on the main page; browser back/forward; saved notes; sign-out. No authenticated acceptance is claimed by the offline build.
