# QuantForge V6.8 — Strategy robustness & benchmark research

This upgrade applies only to the MFA-gated private research interface.

## Additions

- **Longer evaluations:** the existing **Research investments → Period → 2 years** option now has a clear callout in Walk-forward robustness. It uses whatever aligned history Alpaca actually supplies; longer coverage is not promised where providers lack observations.
- **Passive benchmark:** equal-dollar buy-and-hold on the same out-of-sample dates, with a one-time entry fee and no later rebalancing. Distinct from the existing equal-weight **rebalanced** benchmark.
- **Matched-date model robustness:** run preselected minimum-variance, inverse-volatility, and historical-return-tilt allocations on identical training/evaluation boundaries. Also run a feasible tighter weight cap and higher trading fee when possible. Scenarios are never ranked to choose a post-hoc winner.
- **Leave-one-window-out concentration:** compare benchmark-relative compounded returns after omitting each entire historical evaluation window, without claiming independence or statistical significance.
- **Private JSON export:** calculations, summary, assumptions, limitations, and V6.7 price-series SHA-256 fingerprint. Does **not** export raw provider price series, account holdings, tokens, or notes.

## Safety & methodology

All calculations are performed locally on previously loaded price arrays. The same symbols, date boundaries, and annualization convention apply across scenario variants. Tests reject stale, discontinuous, non-finite or misaligned observations. Alternative objective methods may lead to different weights; these are sensitivity analyses, not an out-of-sample model-selection procedure. The reported 'out-of-sample' results are retrospective rolling-origin evaluations, **not** a live trading record, statistical proof of alpha, or a prediction. Prices exclude dividends; simulated trading costs omit spread, slippage, taxes, and corporate-action accounting.

## Files

- `web/site/private_robustness_v68.js`: pure research calculations.
- `web/site/private.js`: authenticated UI wiring and stale-data guard.
- `tools/build_unified_site.py`: private UI and CSP-safe bundling (3 inline script hashes).
- `web/tests/private_robustness_v68.test.cjs` and `tests/test_private_robustness_v68.py`: regression tests.

No changes to cloud API, Render/Supabase/Alpaca settings, stored virtual account state, public SEC snapshot, or GitHub CI settings. Full local checks and GitHub Actions remain mandatory.
