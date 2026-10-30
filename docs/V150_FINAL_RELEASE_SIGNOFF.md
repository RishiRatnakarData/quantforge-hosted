# QuantForge V15.0 — Release quality, evidence scope, and manual signoff

## Platform scope

QuantForge combines a public research exhibit based on historical SEC company facts with separate simulated examples and an MFA-protected private workspace. The public page now makes the separation explicit: **SEC-reported**, **illustrative/modelled**, and **private/authenticated**. The multi-year SEC revision archive collected during V10.0 remains in Git-ignored `data/` and is *not* embedded in the public website.

Historical quantitative comparisons describe the supported sample and price-only returns, not predictive accuracy, a complete historical investable universe, or future investment performance. No new brokerage order endpoint or automatic trading capability is introduced.

## Final local release requirements

A guarded V15.0 installer checks the published V14.0 commit `14432b357b4dfb44cc0365dc0626400c6cee4ed3`, the clean checkout, approved file hashes and inventory, and existing local source assets. Before publication it requires deterministic compilation, full Python and Node regression suites, Ruff, SEC readiness, CSP/private-bundle security, publication privacy, and `tools/audit_release_v150.py`. CI must pass on the exact pushed commit; Cloudflare HTML is then compared against locally compiled content. The local SEC lineage panel is rechecked, but no raw SEC archive is published.

`tools/audit_release_v150.py` writes `data/v150_release_contract.json` (ignored). It verifies the three CSP-hashed scripts, public provenance descriptions, six owner-manual acceptance controls and no regressions in critical private-workspace markup. The report always labels live checks **not independently verified**.

## Required real-browser acceptance — user-attested, not independently verified

Open the live private workspace and complete the six checks in the **Live browser acceptance checklist** under the V14.0 workflow readiness panel. Select **Passed manually**, **Failed / needs work**, or **Not tested** for each. Export the sanitized status JSON if you need a record. It contains only six status codes, not account balances, tickers, prices, note bodies, or credentials. It is not persisted in public storage.

1. **MFA:** sign out and sign in from a new session, complete the real authenticator challenge.
2. **Provider:** verify authorized virtual positions and live market quotes from the connected Alpaca provider. Do not share account identifiers or credentials.
3. **Research:** choose 2–5 investments by name, load aligned observations, and run a complete Research Hub analysis. Confirm stale selections invalidate previous findings.
4. **Historical archive:** import the local SEC archive `data/sec_filing_revisions_v98.json`; check actual filing coverage and withheld windows. Never bypass the import size limit. Failure of a too-large file must be recorded as **failed**, not passed.
5. **Consistency:** compare current candidate, selection, model results and limitations across Hub, Lab and Briefing; test expanded methodology sections.
6. **Saved-note lifecycle:** save a research note, sign out, sign back in, confirm persistence, delete the note, verify deletion persists and signed-out data is not visible.

The six recorded statuses are **owner-reported**, not automated proof. Even all six marked passed is labelled *self-attested complete*, never independently verified.

## Exit criteria

Feature-complete means automated regression, CI and production parity checks pass, no critical defects are known, and actual authenticated acceptance has been completed. If live authentication, import, quote, or research-note tests fail, the release may be technically deployed but **must not be described as end-to-end signed off**. Fix confirmed defects in a narrow hotfix without automatically adding more models or platforms.
