# QuantForge V6.7 — Research integrity and model-risk visibility

V6.7 improves the **authenticated private research workspace**. It does not alter the public financial demonstration, change an Alpaca subscription, place orders, or modify Supabase portfolio state.

## Included

- **Deterministic SHA-256 fingerprint** of the exact selected, date-aligned in-memory market closes used by a walk-forward run. The versioned research manifest records instrument selection, observation count and dates, reported provider feed and calendar, annualization, requested period, fitting/evaluation windows, position cap, allocation rule, fees and virtual starting capital.
- **SEC annual baseline fingerprint** covering fiscal dates, reported revenue and FCF proxies. A versioned forecast manifest records the filing attribution, historical cutoff, horizon, growth/margin assumptions, discount rate, and terminal growth.
- **Visible model-risk warnings** in Valuation & peers: reported latest FCF/revenue margin versus assumed base margin; share of the discounted proxy due to terminal component; missing-value checks and a prominent warning about terminal dependence.
- **Visible walk-forward coverage and source checks:** number of aligned dates, underlying investments, evaluation windows, sample-size warnings and a shortened fingerprint.
- JSON research downloads add `manifest` and `modelRisk` objects while retaining `schema: quantforge.research.v1` for backward-compatible consumers.
- Export-time confirmation that loaded prices still match the calculated market fingerprint, including stale-data checks already present from V6.5.1.

## Source/data boundaries

Fingerprints **do not** authenticate market-data providers, verify accounting filings, prove prediction accuracy, or make reports independently reproducible without the original licensed price series. Raw Alpaca price arrays, access credentials, portfolio holdings and private notes are not included in new manifest fields. The SEC forecast is an assumption-based FCF-plus-terminal **proxy**, not enterprise/equity value or a price target.

## Validation

Run full Python tests (`python -m pytest -q`), Ruff, all `web/tests/*.test.cjs`, website build, prepublication checks, and GitHub CI. New integrity tests cover SHA-256 standard UTF-8 vectors, tampering, array ordering, missing prices, SEC revisions, terminal-share calculations and private-field exclusion.

The patch does not touch `web/site/sec_snapshot.json`, `cloud/api.py`, Supabase, Render configurations, authentication, or private account records. It adds a pure JS helper bundled inside the **existing three CSP-hashed scripts**.
