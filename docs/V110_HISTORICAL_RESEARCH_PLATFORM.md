# QuantForge V11.0 — Historical Research Platform (major integrated milestone)

**Upgrade baseline:** Published V10.0 `30e8b3f4720c185a51419ec34ae032d220a2757d`. This release deliberately groups a historical issuer-quality panel, controlled archived-filing comparison, and a connected private investment-research interpretation in one release rather than adding a standalone dashboard. V10.0 previously collected 94/94 currently supported issuers, 10,928 source facts, and 1,358 fiscal periods locally. V11.0 does not embed those records in the public site or GitHub.

## A. Offline 94-issuer point-in-time evidence panel

The new `tools/historical_sec_panel_v110.py` independently validates the locally collected `data/sec_filing_revisions_v98.json` and today's `web/site/sec_snapshot.json` before processing. It checks January 1 and July 1 dates (2011 onward by default). For **every** reference issuer at **every** date it reports:

- Whether two consecutive and reasonably fresh annual financial reports were available, based only on filed dates at the checkpoint.
- If ready, the observed as-filed annual revenue growth, operating-cash-flow-minus-capex margin, fiscal year, latest filing date and presence of later recorded versions.
- If unavailable, the explicit reason. No missing issuer or year is silently discarded.
- By checkpoint: eligible count and share of the entire reference universe, positive-growth-and-cash-flow screens, median reported ratios, top-five historical reported-metric screens *among currently supported issuers*, and missingness reasons.

Writes only Git-ignored `data/sec_historical_panel_v110.json` and `.csv`, with atomic replacement. These ratio observations are research output, **not** historically investable portfolio returns, ex-ante security universe reconstruction, a fair-value prediction, or an original-filing completeness certification. The tool avoids any live SEC request and does not expose private account details.

## B. Multi-company historically eligible screening comparison

The pure browser-only `private_historical_panel_v110.js` checks an imported SEC archive against the SEC snapshot and the exact already-loaded 2–5-company dated price universe. For each chronologically scheduled evaluation window:

1. Use only company facts filed **on or before** its decision date. Require two consecutive fiscal years, valid positive revenue and coherent FCF. Record the absence of evidence for *every issuer*, including missing selected companies.
2. Use trailing *historical* prices to evaluate a named drawdown constraint (no future prices in the screen).
3. Among positively growing, positive-margin, drawdown-eligible selected companies, pick the largest positive FCF margin (growth and then symbol tie breaks). If none qualifies, hold illustrative cash.
4. Evaluate the subsequent price-only close-to-close movement, starting at the **next close**. Apply disclosed transaction fee assumptions to the restricted screen, including candidate switches; compare with an equal-weight reset benchmark using the exact same observation windows and illustrative turnover fees.
5. If a **single scheduled window** has incomplete issuer evidence, withhold **all cumulative investment-performance numbers**. Detailed coverage counts and missingness remain visible.

The new output is read-only, sanitized in JSON export, and wired to the **Research Hub → Research Lab → Research Briefing**. The selected stocks, prices, provider credentials, holdings, quantities, raw SEC source values, and SEC file accessions are never exported by the new module. File import remains local to the authenticated browser session, never uploaded. Existing MFA, Alpaca virtual account, and note storage are unchanged.

## Critical scientific and investment limitations

- The set of currently supported/selected companies is a **survivorship-biased present-day universe**. Historical delistings, membership selection and unavailable assets are not reconstructed. Historical screens may be chosen after viewing data.
- SEC Company Facts may lack superseded originals. Restatement markers can represent later reporting versions rather than an accounting restatement. Fiscal calendars, tags, cash-flow reporting and comparable accounting periods can vary.
- These are restricted, *illustrative* screen policies, not a point-in-time re-run of the entire QuantForge Research Hub policy and not evidence of alpha, forward prediction, investment suitability or a recommendation.
- Evaluation omits dividends, corporate-action adjustment guarantees, taxes, borrowing, execution slippage and market impact. Window-boundary day movements are omitted consistently on both sides. Trading-fee models are illustrative, not actual brokerage commissions.
- The local 94-issuer panel reports **financial evidence**, not realized stock returns across all 94 companies. Only the user-selected 2–5 investments can have price-based historical comparisons, and only when all sample dates and archival facts are eligible.
- If the SEC archive is not found locally, the release still publishes correctly but the post-release offline study is reported as unavailable. **Do not rerun the publishing script** to regenerate data.

## Re-running local evidence study (without repeating publication)

```powershell
$repo = "$env:USERPROFILE\source\QuantForgeHosted\quantforge-financial-research"
& "$repo\.venv\Scripts\python.exe" "$repo\tools\historical_sec_panel_v110.py"
```

Use `data/sec_filing_revisions_v98.json` in the private Research Hub file picker and rerun a 2–5-company assessment with aligned dates. The private interface uses the imported archive until the page is refreshed or the user signs out. It does not automatically read the local filesystem.

## Acceptance and release boundaries

A clean V10.0 commit, exact source hashes, deterministic protected site build, nine-file approved change inventory, Git whitespace preflight, full Ruff + Python and JavaScript tests, CSP/public privacy audits, GitHub CI and Cloudflare production HTML matching are all enforced before treating the upgrade as released. The offline evidence panel runs only after source publication and is recorded separately. Authenticated live browser workflows remain a separate acceptance check.
