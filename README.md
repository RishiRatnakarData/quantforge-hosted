# QuantForge

**QuantForge 2.0 — completed local review implementation:** five shared research sections, explicit public/private data modes, retained numerical engines, source-aware charts, authenticated saved research and virtual-account history. See the [feature parity and acceptance report](docs/CODEX_REBUILD_PROGRESS.md). Publication and actual owner/provider acceptance remain separate.
**Financial research grounded in reported company data, quantitative models, and reproducible software engineering.**

QuantForge is a full-stack financial research platform combining SEC company fundamentals, statistical modeling, portfolio analytics, valuation scenarios, and historical strategy evaluation. It has two deliberately separate experiences:

- **Public research:** sourced, historical SEC financial statements and transparent *illustrative* portfolio and valuation models.
- **Private research:** an owner-authenticated, MFA-protected research workspace using eligible historical market data and virtual portfolio information. The private workspace has no real-money order execution.

[Public research website](https://quantforge-648.pages.dev/) · [Research methods](docs/methodology/QUANT_RESEARCH_METHODS.md) · [SEC and valuation methodology](docs/methodology/SEC_AND_DCF.md)

## Explore the public research

| Area | What it shows | Important boundary |
| --- | --- | --- |
| **Company financials** | SEC annual financials, growth, margins, cash-flow proxies, cross-company comparisons, and filing provenance | Reported figures and derived metrics are distinct from hypothetical scenarios |
| **Analysis dashboard** | Trends and comparisons of financial and statistical observations | Do not interpret displayed associations as investment predictions |
| **Portfolio simulator** | Interactive portfolios, allocations, and price-based examples | Uses illustrative/simulated market inputs, not account holdings |
| **Risk & allocation** | Covariance, volatility, risk contributions, allocation constraints, and stress illustrations | Results depend on assumptions and data coverage |
| **DCF scenarios** | Editable assumptions and discounted-cash-flow sensitivity | Scenario output is not an analyst target price or trade instruction |
| **Peer comparison** | Financial-feature comparison and similarity methods | Financial similarity does not establish future stock performance |
| **Research methods** | Model design, statistical validation, trade-offs, and code references | Read limitations and leakage controls alongside results |
| **Data & engineering** | Architecture, provenance, tests, CI, and privacy design | Technical checks do not certify predictive accuracy |

## Private research workspace

The private workspace provides an integrated investment research workflow, separated from the public demo and protected by authentication and MFA. It includes:

1. **Decision Center** — a consolidated research conclusion, eligibility and completeness measures, historical evidence screens, risk flags, and supporting rationale. Its traffic lights and 0–100 evidence-alignment index are **descriptive screening heuristics**, not calibrated return forecasts, probabilities, or buy/sell instructions.
2. **Companies** — named-company browsing, shortlist screening, company fundamentals, candidate evidence, and statistical factors.
3. **Research Methods** — market-history diagnostics, optimization, valuation scenarios, backtesting, walk-forward comparison, historical SEC coverage, and sensitivity studies.
4. **Portfolio & Reports** — virtual portfolio context, illustrative trade scenarios, research briefs, and protected saved notes.

**Data availability:** Standard research uses the application's published SEC snapshot and eligible authenticated market-history feeds. A deeper SEC original-versus-revised filing archive is kept off the public website and is not automatically accessible to the hosted browser. An optional local import supports advanced studies where available. Missing or stale inputs are not silently substituted.

## What the engineering demonstrates

| Discipline | Implementation |
| --- | --- |
| **Data engineering** | SEC Company Facts ingestion, normalization, fiscal-year and filing-date treatment, coverage checks, and provenance |
| **Statistics / quantitative finance** | Time-series analysis, covariance and portfolio risk, drawdown measures, constrained optimization, and baseline comparisons |
| **Financial analysis** | Growth and profitability, cash-flow measures, valuation sensitivity, and peer financial profiles |
| **Research validation** | Past-only evaluation windows, fee-aware historical comparisons, missing-evidence withholding, robustness checks, and reproducible outputs |
| **Full-stack software** | Python/FastAPI backend, browser-based interfaces, owner authentication/MFA, hosted deployments, automated regression tests, and CI |

## Data integrity and research limits

- **Historical financial statements:** SEC-reported figures are tied to issuer identifiers and annual filing periods. Revenue, margins, and cash-flow calculations must retain their source and transformation context.
- **Point-in-time work:** Filing availability matters. Fiscal year-end alone does not make a later filing known to a historical model; historical completeness and issuer-universe survivorship remain limits.
- **Historical price research:** Data eligibility, exchange/calendar differences, available intervals, and price-only returns may limit comparisons. Price-only returns can omit dividends and other economic effects.
- **Research scores:** Screening colors, model-completion percentages, and weighted evidence alignment are distinct measurements. They are not calibrated probabilities, investment suitability ratings, or predictions of future profits.
- **Hypothetical models:** Public simulated inputs, valuation assumptions, and hypothetical portfolio outcomes are labeled separately from observed SEC data and private provider observations.
- **No live trading:** Virtual trade scenarios and research actions are not real brokerage orders.

## Architecture at a glance

```text
PUBLIC RESEARCH
SEC Company Facts -> validated issuer snapshot -> Cloudflare Pages
                                     + public illustrative models

PRIVATE WORKSPACE (MFA required)
Browser -> Cloudflare /api proxy -> FastAPI / Render
                                  |-- Supabase authentication, RLS and notes
                                  |-- authorized market data / asset listings
                                  `-- SEC financial evidence and research methods

LOCAL, NONPUBLIC HISTORICAL DATA
SEC filing revision archive -> local coverage and lineage reports
                                  `-- optional owner-side advanced import

VALIDATION
Python + Node tests -> Ruff -> deterministic site build -> CSP/privacy audit
                    -> GitHub Actions -> deployment content verification
```

## Code structure

| Location | Purpose |
| --- | --- |
| `tools/build_unified_site.py` | Generates the hosted website and its three hashed-script CSP header |
| `web/site/` | Public/private frontend source and finance/research modules |
| `web/tests/` | JavaScript research, security, and UI-contract tests |
| `tests/` | Python computation, integration, and release-regression tests |
| `docs/methodology/` | Model assumptions, data definitions, and limitations |
| `docs/` | Release history and deeper technical reference material |

The repository contains historical release notes. Those documents are retained for traceability and should not be read as the current feature or verification status.

## Development and verification

From a configured developer environment, the principal checks are:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
node --test (Get-ChildItem web/tests -Filter '*.test.cjs' | ForEach-Object FullName)
.\.venv\Scripts\python.exe tools/build_unified_site.py
.\.venv\Scripts\python.exe tools/audit_public_bundle.py
.\.venv\Scripts\python.exe tools/prepublish_check.py
```

**Verification scope:** The last confirmed major release was published and CI-verified at commit `1e78dd45d6b74c5ce7582e493d4292a5878cc13a`. Deployment and test status for later changes must be checked against their own commits and CI runs. Owner-side MFA, provider, and saved-note acceptance remains a separate sign-off step.

---

*QuantForge is a research and engineering project, not an investment advisory or trading service. Historical or modeled observations do not guarantee future performance.*
