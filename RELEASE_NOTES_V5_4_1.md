# QuantForge V5.4.1 — verification and privacy patch

- Fixed a `F841` Ruff violation in the SEC fundamental-peer analyzer.
- Fixed missing financial-metric counts (do not count nonmissing target data as missing).
- Added one model regression test and four prepublication scanner tests.
- Added `tools/prepublish_check.py` to CI for private data, obvious tokens, email contacts and Markdown links.
- Repaired historical-documentation relative links.
- Updated README/status/verification documentation using observed Windows results and accurate limitations.
- Does **not** modify SQLite schema, re-price virtual holdings, or execute trading orders.
- Previous authenticated Alpaca/SEC observations remain private and outside distributable source.
- Still requires user Windows lint/tests and actual GitHub Actions verification before publication.
