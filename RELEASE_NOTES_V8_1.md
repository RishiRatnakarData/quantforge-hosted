# QuantForge V8.1 — Research-first layout, SEC charts, and private decision workflow

**Release scope:** Information architecture and source-backed charting. This does not add a chatbot, a new data provider, or brokerage trading.

## Public website

- The Start page introduces the product in two sentences and offers direct entry points into **Company financials**, **Analysis dashboard**, and **Private workspace**. The 94-company SEC count is read from the published dataset, not hard-coded into the page.
- The old architecture explanation and supplementary simulated portfolio widgets are moved out of Start into **Data & engineering** and **Portfolio simulator**, respectively. Their existing IDs are retained for compatibility.
- Left navigation reads **Start here / Company financials / Analysis dashboard**, with collapsible **Model demonstrations** and **Research & code** groups. The nine existing page route IDs remain unchanged.
- SEC company financials still show reported annual revenue, KPI values, provenance, CSV export, and tables. New charts cover SEC-reported **operating margin**, **net income**, and **free cash flow proxy**. A separate bar visualization covers the selected cross-company comparison metric.
- An *optional* revenue-growth scenario compounds a **user-entered** rate from the newest eligible reported annual revenue; all hypothetical years are labeled and styled differently. It is **not** an earnings forecast, price target, market-data forecast, or evidence of future performance.
- A selected issuer's prior scenario is cleared when a different issuer is chosen. Missing metrics are not imputed, and negative FCF remains negative.

## Private workspace

- On wide screens, navigation is now an in-workspace left-hand rail; on smaller screens, the three existing grouped menus remain responsive. Existing tab IDs, callbacks and authentication boundaries are unchanged.
- **Overview** now contains the portfolio summary, holdings and concentration, and three clear task shortcuts. It does **not** contain a research calculator.
- **Virtual trades** owns actual quote observation, simulated trade recording, **proposed purchase impact**, and **virtual cash balance** controls.
- **Research guide & notes** (same stable internal `settings` tab ID) owns the rule-based, plain-English explanation, a glossary, and saved notes. The report collects existing model outputs; it does not place trades, call an AI provider, or make buy/sell recommendations.
- Existing Investment screening, Market data, Optimization, Backtests, Walk-forward, Valuation, and MFA flows remain separate and maintain their existing IDs.
- The shared selected-vs-loaded investment control remains visible in the four historical research tabs and does not move to Overview.

## Files and safety

Changed: `web/site/site.template.html`, `web/site/app.js`, `tools/build_unified_site.py`.
Added: `web/site/sec_visuals_v81.js`, `tests/test_v81_structure.py`, `web/tests/v81_charts.test.cjs`, `RELEASE_NOTES_V8_1.md`.
Compiled during local validation: `public/index.html`, `public/_headers`.

Unaffected: all private APIs, Supabase authentication and MFA, Alpaca credentials, portfolio persistence formats, historical-price research models, SEC snapshot files and importers. The public scripts remain in the existing three CSP-hashed inline script slots.

## Verification boundary

The package passed 11 focused Python checks and 6 focused pure-JavaScript tests in an isolated subset of the source repository. **The full V8.0 project and the 94-company dataset are available on the owner's Windows checkout, not within this packaging environment.** Run `run_v81_local.ps1` for the full Python, JavaScript, publication-privacy, source integrity and CSP checks before considering V8.1 validated. No release script automatically publishes without a separate explicit publication command.
