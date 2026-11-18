# QuantForge V6.5.1 — Research selection clarity

This small interface release does not change investment algorithms, databases, API
credentials, or account portfolios.

- Moves the existing investment picker and history-load controls into one shared
  **Research investments** panel. It is visible in Market research, Optimization,
  Backtesting, and Walk-forward. Valuation retains its independent SEC-company selector.
- Shows separately the **selected investments** (requested by the user) and
  **loaded for analysis** (actual symbols and observed dates returned from Alpaca).
- Clarifies that the Walk-forward chart has two **portfolio** lines, each using
  all loaded assets—not one chart line per stock.
- Changing investment selections or historical period invalidates the previous
  loaded series, dependent results, and exports. Asynchronous responses from an
  obsolete selection/period are ignored rather than reinstated.
- Maintains the current three-script Content Security Policy, private MFA and
  data isolation, and source-backed research calculations.

## Install and verify

Run `apply_v651.py REPOSITORY_PATH --dry-run` on a clean V6.5 checkout first,
then run the installer without `--dry-run`. Rebuild the unified site, run the
complete Python suite and all six existing JavaScript suites plus
`web/tests/private_research_context_v651.test.cjs`, then run publication checks
before pushing. Verify the two-line Walk-forward explanation and selection
status after changing the period in the live authenticated website.
