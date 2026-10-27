# QuantForge V7.9 — Private Research Guide and scalable public SEC coverage

## Private research guide (new)

Adds **Your research, explained** to authenticated Overview. On request it creates a local, readable report combining:
- Virtual cash, priced holdings and concentration (withheld if any quote is missing).
- Investment selection vs loaded history; dates, symbols, and relevant caveats.
- Actual completed optimization and walk-forward output, including checks when in-sample and later-window results disagree (not invented results).
- Currently loaded SEC company financials, valuation-scenario status, screening results, modeled purchase-impact results, robustness checks, and limitations.
- Clear next-step links to existing investment screening, market data, optimization, walk-forward, and valuation tools.
- Two optional beginner context selections and a glossary.

The explanation is deterministic, not a generative AI chatbot, and it has no external AI network requests or fees. Its next steps are for further *analysis*, not automatic buy/sell decisions. It generates only after MFA and a user click, clears on logout and core research changes, does not persist reports, and never mutates virtual holdings.

## Public SEC expansion (new infrastructure)

The public SEC company selector now supports name/ticker search and a variable-size public snapshot. A standalone Python maintainer tool downloads, validates, and adds verified annual SEC Company Facts using the official free, keyless service with a declared contact User-Agent and rate-limited requests. A candidate file and detailed instructions are provided. **The bundle does not include new SEC observations; the existing verified 12-company data remains unchanged until the developer runs the importer on a networked machine, validates the result, and publishes it.**

New extra issuers are excluded if comparable annual 10-K revenue data or a SEC ticker/CIK match is missing. Metrics, dates, missing fields and filing-level lineage are never synthesized. Different issuer fiscal periods and snapshot cutoffs remain an explicit limitation.

## Security and release boundaries

- No Render, Supabase, Alpaca, account, MFA, brokerage order, or private state schema changes.
- Three CSP-hashed compiled inline scripts preserved. New module is prepended to the pre-existing private script bundle.
- Original 12-company minimum is still required; build verification now permits additional audited issuers.
- No paid data access, third-party AI provider, new server route, or credential configuration required for V7.9 application installation.
- GitHub CI and real market/SEC retrieval must be checked on the user's actual repository. Offline tests do not establish successful live deployment or additional real company coverage.
