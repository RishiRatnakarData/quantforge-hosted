# QuantForge V5.7 — Public SEC Financials (limited real-data case study)

This public feature is **not** a second private investment desk. It is a small audited SEC filing exhibit for 12 named U.S. companies (MSFT, AAPL, NVDA, GOOGL, AMZN, META, COST, WMT, KO, JNJ, XOM, CAT). It does not publish Alpaca data, trade history, API tokens, owner information, or private Supabase state.

## Data origins and interpretation

- **Real inputs:** annual US-GAAP facts from the SEC Company Facts API, limited to 10-K / 10-K/A records with 330–380-day reporting periods filed no later than the selected as-of date. Data retrieved by the authorized maintainer **only at build time**, not from a public browser.
- **Public computed figures:** revenue growth, operating margin, and a simple free cash flow proxy = net operating cash flow − reported cash property/equipment purchases (not unlevered FCFF). Missing SEC concepts remain unavailable.
- **Interactive stress test:** a hypothetical change in operating margin (percentage points) applied to the latest reported revenue. This is **not a forecast, valuation, or investment recommendation**.
- **Synthetic modules retained:** public example Portfolio, Quant, DCF, and fictional company peers. The public financials do **not** feed these panels. The secure owner-only workspace remains separate.
- Sector labels are editor-defined broad groupings, not SEC classifications. Comparisons across sectors are exploratory, not strict economic peers.
- Company fiscal year-ends are not synchronized. Comparisons show actual year-end dates and should not be treated as exact same-period peer results.

## How to build with authentic SEC data

In the repository's PowerShell terminal:

```powershell
$env:SEC_USER_AGENT = Read-Host 'SEC User-Agent (project name plus your working contact email)'
.\.venv\Scripts\python.exe tools/build_public_sec_snapshot.py --as-of 2026-10-25 --output web/site/sec_snapshot.json
.\.venv\Scripts\python.exe tools/build_unified_site.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_public_sec_snapshot.py tests/test_hosted_web.py
.\.venv\Scripts\python.exe tools/prepublish_check.py
```

- `SEC_USER_AGENT` is read from the process environment, sent to the SEC as required by its access policy, and **not written into the public JSON**.
- Never place credentials or personal account data in `web/site/sec_snapshot.json` or `public/index.html`.
- Confirm all 12 SEC requests succeed. On API error or insufficient eligible revenue filings, the generator stops rather than silently inventing figures.
- The JSON file is a deliberately small public snapshot of government disclosure facts and includes CIK/source URLs, per-metric accession numbers, filing dates, and selected reporting periods.
- `python tools/build_unified_site.py` inlines only the public snapshot; there are still three CSP-hashed scripts and no browser requests to the SEC or Alpaca.
- If the JSON is missing, the SEC tab says **No SEC snapshot published**. It never fabricates a substitute.
- A rebuilt website needs a new commit/push for Cloudflare deployment. Render's private API does not require changes for this feature.

## Review checklist before commit

1. Open the generated snapshot and confirm tickers and annual data agree with SEC Company Facts. In particular, compare the latest revenue and operating income to the corresponding annual filing.
2. Verify each CIK and source URL, annual end date, fiscal label, accession, and `filed` date.
3. Check that missing cash-flow or capex data is represented as null, not zero.
4. Run Python tests, Node.js demo tests, Ruff, and the privacy checker.
5. Confirm **Public SEC Financials** is clearly real, while **Public Portfolio/Quant/Valuation/Peers** remain clearly simulated; **My workspace** continues to require MFA.
6. Confirm CSP still blocks unapproved scripts and `ALPACA_`, `SUPABASE_`, API keys, and user email addresses do not appear in the built HTML.
7. Verify Cloudflare deployment and manually test the company selector and margin stress control.

Sources: [SEC EDGAR API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [SEC developer resources](https://www.sec.gov/about/developer-resources).
