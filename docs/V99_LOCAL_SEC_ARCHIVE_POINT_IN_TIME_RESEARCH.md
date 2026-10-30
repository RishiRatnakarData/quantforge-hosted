# QuantForge V9.9 — Original-filing archive integration and dated evidence replay

## Baseline and scope

V9.9 upgrades the production-verified V9.8 Investment Research Hub with **explicitly imported local SEC Company Facts revision archives**. Existing public SEC snapshots, historical tests, V9.6 saved assessments, Alpaca virtual brokerage, and MFA routing remain unchanged.

The V9.8 archive collector (`tools/build_sec_filing_archive_v98.py`) retains multiple source filings for each reported annual metric under Git-ignored `data/sec_filing_revisions_v98.json`. V9.9 now makes that artifact useful to a human-authenticated research session. The archive is **not** embedded in the public Cloudflare site, uploaded to Render, transmitted to third-party models, or persisted in browser storage. The owner explicitly selects a local JSON file. Sign-out invalidates imports and outstanding file-read responses; changed investment selections or model inputs invalidate the linked results.

### Supported research workflow

1. Sign into QuantForge's existing private workspace with MFA.
2. In **Investment Research Hub**, choose and load the 2–5 investments, then run the connected research assessment.
3. Optionally download SEC Company Facts from an authorized developer machine using the existing V9.8 collector with a genuine `SEC_USER_AGENT`, or use a previously collected official-source archive.
4. Run the offline validator before importing:

   ```powershell
   .\.venv\Scripts\python.exe tools\validate_local_sec_archive_v99.py
   ```

5. Select `data/sec_filing_revisions_v98.json` in the new **Optional local SEC archive** file chooser. QuantForge verifies source shape, as-of cutoff, filing date, reference CIK, fiscal durations, and conflicting duplicates. The comparison is then linked to the Research Hub, Research Briefing and Research Lab status. Changing research inputs requires a new assessment; clearing the import removes the local archive from browser memory.

The existing V9.8 collector can be run separately if desired:

```powershell
.\.venv\Scripts\python.exe tools\build_sec_filing_archive_v98.py --download --max-issuers 25 --max-years 15
.\.venv\Scripts\python.exe tools\validate_local_sec_archive_v99.py
```

**Do not run the archive download without a truthful SEC User-Agent and permission to use the official SEC endpoint.** It is intentionally excluded from automatic release and CI. The archive currently covers only the first N companies in the configured seed list, not the historical complete investable universe. If it omits one of your selected companies, that company is shown as unavailable rather than being silently removed from the model.

### Historical selection of each financial fact

At each **decision date**, for every selected issuer, select only 10-K/10-K-A annual facts whose **filing date is on or before the decision**. For each fiscal period and metric, choose the latest eligible filing version; if a preferred-tag value is ambiguous at the same filing date, withhold that field. Require revenue, operating cash flow and capital expenditures in two consecutive, timely annual periods before calculating revenue growth and free-cash-flow margin. Historical prices must remain aligned, complete and unaltered; the return evaluation uses next-session price execution and later non-overlapping test windows.

The V9.9 report contains issuer-by-issuer scheduled versus eligible decision dates and a count of dates that used a later archived filing version. Cumulative historical returns are **withheld** unless every selected issuer has eligible evidence for every scheduled decision date. When all dates are covered, the displayed comparison is a **restricted revenue-growth/FCF/drawdown rule** versus a price-only passive baseline with stated transaction costs—not an evaluation of every automated QuantForge model or a stock-return prediction.

### Provenance and privacy

* Verified source CIKs are checked against the site's published issuer registry. Bad identifiers, future filing dates, conflicting facts, duplicate periods and oversized archives fail closed.
* The file is read locally using the browser's file picker; neither the raw archive nor its filings are exported in JSON research summaries or saved as notes.
* Sanitized research exports contain coverage counts, company symbols, a small set of restricted-policy summary metrics and limitations. They exclude raw SEC values, filing accessions, market prices, holdings, balances, share quantities, private credentials and account identifiers.
* No brokerage orders, model-hosting calls or account mutations are invoked by the archival research calculations.
* The offline archive validator does not contact SEC or any provider. A valid archive structure is **not** a guarantee of historical completeness; SEC Company Facts may exclude overwritten original facts.
* The selected stock universe is known today; delisted issuers, point-in-time constituent universes, dividend/corporate-action price adjustments, bid/ask spreads, taxes, slippage and market impact are not reconstructed. Historical correlations and returns are descriptive, not estimates of future profit.

### Acceptance and release boundary

The guarded V9.9 installer verifies a clean V9.8 GitHub main with the exact V9.8 source hashes. It stages only the nine documented source/generated paths, runs early whitespace checks, Ruff, the full Python and JavaScript suites, SEC audit, CSP/public bundle and prepublication secret checks, deterministic site rebuild, then commits/pushes and verifies CI and live Cloudflare HTML. No server secrets, private database records or raw local SEC archives are staged or committed.

**Browser acceptance remains separate**: MFA sign-in, a complete data-backed research assessment, optional archive import and coverage, Research Lab/Briefing parity, sign-out clearing, and historical provider availability require human verification on the live authenticated website.
