# QuantForge V8.2 — End-to-end functional acceptance checklist

**Before testing production:** Confirm both Python CI jobs passed for the new V8.2 commit, and Cloudflare **Production** shows a successful deployment for the same commit. GitHub CI success by itself does not prove deployment.

## A. Public research case study — no login

- [ ] Open **Overview → Research methods → A financial research case study**. The case study opens at `/research-case-study.html` and provides a link back to Research methods.
- [ ] Four issuers appear: Microsoft (MSFT), AMD, Adobe (ADBE), Applied Materials (AMAT), each with original SEC Company Facts source URL.
- [ ] Confirm each issuer's fiscal-year end, recorded extraction cutoff (or an explicit missing-data label), and filing accession references; differences in dates are disclosed, not silently aligned.
- [ ] The growth/margin/cash-generation bar charts are legible on desktop and phone. Negative bars, missing values, zero baselines and accompanying tables behave honestly.
- [ ] Download `/research-case-study.csv`; open it and inspect SEC source-tag, filed-date, accession, and FCF proxy lineage. No personal holdings, credentials, or private portfolio content.
- [ ] No claims of live stock prices, real backtest returns for these four stocks, earnings forecasts, or investment recommendations.
- [ ] Browser devtools Console has no error; responsive 1440/800/390 widths show no page-level overflow.

## B. Public interactive analysis — no login

- [ ] SEC company selector accepts company names, including AMD and Adobe; original 94 companies remain.
- [ ] Switch revenue / operating margin / net income / free cash flow. Compare chart values to original annual tables and fiscal periods.
- [ ] Test hypothetical revenue scenario at -5%, +5%, and 0%, with 1/3/5-year horizons and change issuers between scenarios. Forward numbers are clearly hypothetical.
- [ ] Compare multiple companies: source years, missing data, CSV export, and visual table units agree.
- [ ] In **Analysis dashboard**, adjust optimizer constraints and run walk-forward illustration. Check two curves are distinct strategies, use all selected investments, and are called simulated.
- [ ] Verify GitHub source/test links and explicit SEC-versus-simulation disclaimers remain visible.

## C. Private authenticated workflow — owner only; do not upload personal screenshots

- [ ] MFA sign-in requires password and valid six-digit authenticator verification. A private route opened in a fresh logged-out browser does not reveal holdings.
- [ ] Overview shows saved virtual holdings, invested/cash/concentration values and shortcuts; refresh does not silently reset balances.
- [ ] Virtual trades lets you obtain a dated price and test proposed purchase impact without mutating holdings. Actual *virtual* trade requires separate explicit action.
- [ ] Investment screening works by company name; no need to memorize ticker symbols.
- [ ] Market history: select investments by name, choose range, load, verify **Selected investments** and **Loaded for analysis** show distinct, accurate data and date coverage.
- [ ] Change selection or date period; old optimization, backtesting and walk-forward data must be invalidated rather than reused.
- [ ] Run optimization and walk-forward; inspect training/test window chronology, cost reporting, and two strategies using the same selected investments.
- [ ] Valuation: compare SEC dates and observed market price dates; missing facts suppress questionable valuation. Scenario assumptions are visibly user-entered.
- [ ] Research guide & notes: reports explain facts versus limitations, saved notes persist, glossary is useful; exports exclude private holdings/credentials where promised.
- [ ] Sign out, sign in again with MFA, and verify correct restoration. Test an expired session without revealing private state.

## D. Engineering and privacy audit

- [ ] Run `python tools/build_unified_site.py`, `python tools/build_v82_case_study.py --repo .`, `python tools/audit_v82_readiness.py --repo .`.
- [ ] Run Ruff, complete Pytest, complete Node `web/tests/*.test.cjs`, existing `tools/audit_public_bundle.py` and `tools/prepublish_check.py`.
- [ ] Verify `web/site/sec_snapshot.json` remains unmodified; new report is pure static HTML/CSV and contains no external JavaScript.
- [ ] Confirm only intended paths were committed, no `.env` or API keys, no private account research artifacts, no paid-data redistribution.
- [ ] Inspect Cloudflare production and GitHub commit equality. If the site is different, do not claim deployment success.

## What automated tests do **not** prove

The new static audits cannot independently confirm the owner's MFA login, personal account persistence, live upstream provider availability, browser accessibility across every device, or all production proxy behavior. Those require the owner to perform the checklist above on the deployed service. Record **pass/fail + short observation** for each and fix only confirmed issues.

- [ ] For original catalog issuers, verify the `source_period_end` and `period_end_verification` CSV columns: absent source periods must remain blank and explicitly unverified, while present periods must match `fiscal_end`.
