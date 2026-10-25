# QuantForge V5 — GitHub publication checklist

The goal is to publish **source code, mathematical methodology and fictional screenshots**, not a live personal portfolio or licensed market feed. The repository does not need a public hosted website.

## Mandatory prepublication scanner

From repository root, run `python tools/prepublish_check.py` (or the project virtual Python). It checks proposed Git files for obvious databases, licensed price CSVs, token-like strings, contact emails and broken links. The check is also part of CI. **It does not inspect screenshot pixels, past commits or provider permissions.** Stop if it reports any issue; do not bypass failures without investigating.

## Local technical checks

- [ ] `python tools/prepublish_check.py` passes from repository root.
- [ ] `python -m pytest -q` passes from a clean Python 3.12 environment.
- [ ] `python -m ruff check .` says `All checks passed!` after fixing any style warnings.
- [ ] GitHub Actions `CI` passes both supported Python versions and synthetic smoke-test jobs.
- [ ] Try **Browse → Compare → Research → Company financials** with fictional data; keep generated demo content labeled fictional.
- [ ] If testing live SEC, use local `SEC_USER_AGENT` and inspect the source year, CIK and filing date without copying confidential records into repository artifacts.

## Security and permissions

- [ ] Keep `.private/`, `*.sqlite3`, virtual positions, research notes, credentials, tokens, and local `.env` off GitHub.
- [ ] Do not publish captured Alpaca trade quotes/charts/results without permission from the current plan's terms.
- [ ] Do not publish historical Tiingo Starter source data, retained derived data or old output folders; review retention obligations separately.
- [ ] Confirm Git does not track any forbidden content:

```powershell
git status --short
git ls-files | Select-String -Pattern '\.private|\.env$|\.sqlite3$|outputs/|data/private|tiingo.*\.(csv|parquet|json)'
```

- [ ] Check `README.md`, screenshots **visually**, docs and prior Git history for copied private financial observations, personal SEC contact details or credentials. The scanner does not inspect pixels or old commits.
- [ ] Confirm the archived `.github/workflows/pages.yml` has **only manual dispatch** and contains no deployment or public data-upload step (or remove it).
- [ ] Decide separately whether and how to license the source; do not assume a source-code repository grants redistribution rights to third-party market data.

## Documentation accuracy

- [ ] Every screenshot says **fictional demo** when using synthetic values.
- [ ] Explain that live Alpaca equities are **IEX last-trade** observations (not consolidated quotes or execution prices).
- [ ] Explain that the desk's Monte Carlo volatility parameters are **assumed, not estimated**.
- [ ] Clearly separate research-only GARCH/HMM/ML modules from functionality actually used by the live UI.
- [ ] Do not claim a complete universe of listed securities, a generic DCF for every company, proven model alpha, or a finished research paper.
- [ ] State actual Windows test count, CI result and unverified external checks accurately.

## GitHub finishing steps

- [ ] Review [`docs/evidence/VERIFICATION_V5.md`](../evidence/VERIFICATION_V5.md).
- [ ] Add source/tests/docs + clearly fictional preview images; inspect the diff before commit.
- [ ] Confirm the repository landing README displays links and images correctly.
- [ ] Confirm no personal database, Alpaca key, SEC contact email or source data files are visible on GitHub.
- [ ] Update resume and portfolio only **after** the actual public repository is verified.
