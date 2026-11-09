# QuantForge | Source-level audit and consolidated upgrade

**Audited source:** ZIP Git archive comment `7f009f278f8d506d3f593ccbc5940c9131a9b306` (not inferred from the filename).
**Audit date:** 2026-11-07. **Scope:** static website source, site generator, SEC snapshot, private browser modules, hosted API, test cases and generated output.
**Live verification boundary:** The GitHub repository and public Cloudflare URL could not be read from the review environment. Static code inspection and local tests **do not establish** Cloudflare production parity, Render availability, an authenticated MFA pass, live Alpaca entitlements or Supabase persistence. Do not infer these from the generated-site hash.

## Executive disposition

**KEEP** the substantive methods, SEC metadata and privacy boundary. **FIX** hidden disclosure controls, public visibility of ML/NLP implementation, incomplete peer-comparison messages and repeated navigation/copy. The redundant status ribbon is suppressed visually; its event targets remain present for existing handlers. **REMOVE** the extra top status ribbon from visible navigation while retaining DOM targets. **MOVE** the private workflow-readiness/acceptance checklist and secondary research guide into Advanced Research. **MERGE** selected-company financial findings, downside history, experimental ML and dated headline summaries into one default Research results route. **REMOVE** duplicative visible introductions, not the computational engines. **ADD** a source-linked, synthetic-but-reproducible public classifier demonstration, explicit Brier/baseline evidence and new regression checks. **VERIFY** signed-in end-to-end behavior before describing this release as deployed.

These are *research screens*, not suitability scoring, probabilistic stock forecasts, a licensed research product or investment recommendations. The user's academic credential is in Statistical Data Science; financial applications are transparent applied project work, not credentialed professional equity research.

### Priority / risk register

| Priority | Source observation and why it matters | Decision | Implementation / outstanding check |
| --- | --- | --- | --- |
| P0 | The final generated private CSS had `#private-signed details>summary{display:none!important}`. It suppressed disclosure labels globally. This can make older advanced controls inaccessible. | **FIX** | Restore keyboard-visible summary labels in the generated stylesheet and stop forcibly expanding all Advanced disclosures; automated source/DOM check. Visually check mobile and keyboard navigation. |
| P0 | Historical Company Facts snapshot and personal observations use different provenance, dates and access constraints. | **KEEP / VERIFY** | No change to `web/site/sec_snapshot.json`, SEC parser, protected API or middleware. Verify SEC accession links on live UI. |
| P0 | The five-session classifier's former model-qualification gate could accept Brier improvement even with lower directional accuracy than its simple baseline. | **FIX** | Conservative screen now requires meaningful Brier improvement, no worse accuracy, and at least 12 held-out windows. This remains a heuristic, not a significance test. |
| P0 | Private news and quotes depend on authenticated provider entitlements; offline HTML cannot verify them. | **VERIFY** | Keep withhold-on-error behavior. Owner must run MFA + provider + notes browser acceptance. |
| P1 | Research default contained an oversized setup/readiness path and acceptance checklist despite the one-action flow. | **MOVE / FIX** | Readiness & acceptance moved to Advanced; redundant status ribbon visually suppressed. Existing element IDs and event handlers retained. |
| P1 | Saved reports included a secondary guided session summary plus historical report content. | **MOVE** | Guided explanatory worksheet moved to Advanced; notes and saved research remain under Saved Reports. |
| P1 | Public page proved portfolio math and SEC work but only mentioned ML/NLP in prose. | **ADD / MERGE** | Add public validation exhibit invoking exactly the same private pure classifier on deterministic synthetic input, dated test counts, model and baseline scores; link actual NLP backend source and tests. |
| P1 | Private ML comparison plotted accuracy but omitted the Brier scores used to decide whether its signal qualified. | **FIX** | Show numerical Brier and baseline alongside accuracy, test windows and dates. |
| P1 | Peer analysis is available for 91/94 snapshot companies, not every issuer; partial two-ratio financial comparisons have real limitations. | **KEEP / VERIFY** | Never impute ratios; show partial/sector fallback. Extend coverage for excluded issuers only with authentic filings in a separate data change. |
| P2 | Data & Engineering repeated private-method descriptions, competing with Research Methods. | **MERGE / REMOVE** | Methods owns algorithm explanations; engineering page retains architecture, lineage, source and CI evidence. |
| P2 | UI wording sometimes emphasizes navigation mechanics and project versions rather than the financial question. | **REWORD** | Simplify home introduction and research task labels; retain technical definitions near evidence. Further line-edit remains worthwhile after live review. |

## Data integrity and actual feature inventory

- The reviewed published SEC snapshot contains **94 companies**, `as_of=2026-10-25` and `expanded_as_of=2026-10-27`. The dataset is historical Company Facts, not a realtime quote feed or reconstructed point-in-time data warehouse. `web/site/sec_snapshot.json`, `tools/build_public_sec_snapshot.py` and `web/site/sec_analytics.js` include issuer identifiers, fiscal ends, metric records and filing evidence.
- Executing `web/site/sec_peer_model.js` against the published snapshot yields **91/94** eligible issuer comparisons, both for editorial same-industry groups and the broad universe. **LHX** and **MS** have no eligible recent annual revenue in this peer model; **PNC** has insufficient comparable ratios. **NVDA** and **KLAC** return three-ratio Technology peers; **AMZN** returns three-ratio discretionary peers; **AAPL** can return four-ratio peers. Bank examples **BAC/JPM** typically produce only two ratios. These are tested calculations on the static snapshot, not a claim all issuers have four dimensions.
- The financial-comparison algorithm uses shared available ratios, median centering, standardized and clipped z-values, a Euclidean distance and editorial sector groups. It is **not** a trained supervised ML predictor. Zero imputation is avoided. Mixed fiscal-year-end dates and business-model comparability remain limitations.
- `web/site/private_predictive_ml_v180.js` computes lagged returns, 20-session realized volatility and drawdown, fits L2-penalized logistic regression on mature prior five-session outcomes, and scores later non-overlapping five-session windows against a historical base-rate baseline. Its results are **classification experiments**, not future share-price paths. Sample counts and dates matter; tests from synthetic inputs prove algorithm behavior, not live investment skill.
- `cloud/news_intelligence_v180.py` groups selected issuer headlines using **TF-IDF cosine lexical similarity** to explicit topic vocabulary and scores financial **tone by lexicon/negation**. Optional local FinBERT is conditional and may be absent; nothing indicates always-on embeddings, LLM reasoning or calibrated market-sentiment forecasting. The endpoint is protected by `owner` MFA checks in `cloud/api.py` before provider access.
- Actual SQL work exists in the wider Python application (`src/quantforge/desk/quant_portfolio.py`, `src/quantforge/desk/engine.py`, `src/quantforge/desk/portfolio_intelligence.py`); the public hosted site's in-browser SEC snapshot is JSON and should not be described as a SQL database. CI, deterministic site compilation and CSP are real engineering evidence, but uptime/deployment claims need independent verification.
- Valuation on the public site (`web/site/model.js`) uses **illustrative company inputs**, a five-year cash-flow DCF and a WACC/terminal-growth guard. It is not a historical/consensus-based stock price target. Company financials page separately uses reported SEC data; never equate these model sources.

## Public: page-by-page, block-level decisions

Every subsection below refers to observed source/generator structures and tests; rendered browser appearance is **not** signed off.

### 1. Overview (`#page-overview`)

| Block / visible wording | Decision | Rationale / exact direction |
| --- | --- | --- |
| “Financial research, built from the data up.” opening | **KEEP / REWORD** | Strong credible headline; supporting sentence now names reported data, statistical experiments, and portfolio scenarios rather than repeating generic category words. |
| Historical SEC company count and date cue | **KEEP / FIX** | Dynamic count from `sec_snapshot.json`; make the snapshot date visibly separate from current market quotes. |
| Four route cards: Company financials; Analysis dashboard; Risk and allocation; Research methods | **KEEP** | Direct task-oriented entry points. Avoid increasing card count. All use `data-go` navigation. |
| Featured full SEC case study + source ledger | **KEEP / VERIFY** | High-value project evidence; verify all linked figures, downloadable CSV, and report generation from unchanged snapshot. See `tools/build_v82_case_study.py`. |
| Research data source shortcut + GitHub link | **KEEP / REPOSITION** | One concise provenance cue is valuable; use deeper page for lengthy model caveats. Confirm public repository visibility before relying on GitHub links. |
| Hidden legacy home portfolio highlights | **KEEP HIDDEN** | Preserve script targets for compatibility, but don't add an extra duplicated hero. |

**Visitor takeaway:** sourced financial evidence + statistical methodology + clean engineering navigation, not claims of stock-picking mastery.

### 2. Company Financials (`#page-sec`)

| Block | Decision | Rationale / action |
| --- | --- | --- |
| Page headline, three quick-pick issuers (Microsoft, Walmart, Exxon) | **KEEP** | Domain-diverse entry points; clarify periods/sector editorial nature. |
| Company name search, actual SEC issuer selector, covered-company count | **KEEP / FIX** | Search should not require ticker knowledge. Verify empty-filter message, 94-issuer coverage and names with long labels on mobile. |
| Annual revenue trend, operating-performance charts | **KEEP** | Specific evidence for ETL, time-series exploratory analytics and financial-statement literacy. Fiscal-year labels and units must remain visible. |
| Optional revenue-growth scenario (currently `<details>`) | **MOVE / CLEAR LABEL** | It is hypothetical, not SEC-reported. Keep after actual financial charts with an explicit scenario label; no projection should overwrite observed values. |
| Reported annual figures + margins and FCF proxy | **KEEP** | Distinguish operating cash flow minus cash PPE purchases from enterprise free cash flow. Preserve `null` for unavailable inputs and negative cash flows. |
| Cross-company comparison, CSV export | **KEEP / VERIFY** | Useful analyst/BI affordance; check company comparability, sorted years, escaping, CSV header/units and long labels. |
| Filing provenance and SEC source tags disclosure | **KEEP** | Primary data integrity control; click SEC source, confirm accession/filing metadata, and preserve authenticity. |

**Do not:** treat absent SEC tags as zero, infer a fiscal year's filings were public at year end, or claim consistent standardized financial categories across all industries.

### 3. Analysis Dashboard (`#page-lab`)

| Block | Decision | Rationale / action |
| --- | --- | --- |
| Analysis heading and SEC financial comparison exhibit | **KEEP** | Multi-company observations distinct from a single-company financial drilldown. |
| Five-investment *synthetic* allocation case with position cap and transaction-cost selectors | **KEEP / DISTINGUISH** | Legitimate reproducible numerical optimization; no actual past market returns shown. |
| Training-window selector, auto-recalculate action, optimizer output | **KEEP** | Demonstrates evaluation settings and parameter sensitivity; hidden trigger button stays accessible by selector changes. |
| Walk-forward comparison of equal weight vs constrained strategy | **KEEP / CLARIFY** | Both paths come from the same synthetic asset universe, in later windows after training and with modeled costs; no market outperformance claim. |
| Source, model and test links | **KEEP** | Essential recruiter technical evidence; check all links are publicly accessible. |
| Overlap with Risk and Allocation and detailed Research Methods | **MERGE CONCEPTUALLY** | Dashboard should answer “what changes under assumptions?”; Risk page should answer “what is the exposure and downside?”; Methods explains algorithms. |

### 4. Portfolio Simulator (`#page-portfolio`)

| Block | Decision | Rationale / action |
| --- | --- | --- |
| Collapsible legacy sample preview + redundant cross-links | **MOVE / REDUCE** | Keep source compatibility if used, but do not make it the first task or duplicate page navigation. |
| Virtual portfolio totals, cash and positions | **KEEP** | Concrete portfolio arithmetic; clearly label sample prices and virtual units. |
| Record virtual buy/sell and 0.05% fee | **KEEP** | Zero real brokerage orders; check insufficient cash, missing holdings, invalid amount, units and sign. |
| Illustrative ETF overlap | **KEEP / LABEL** | Not authentic ETF constituent holdings; risk of misinterpretation if source label is lost. |
| Target-weight rebalancing inputs and plan | **KEEP / FIX** | Validate totals and feasibility; keep controls tied to the actual example holdings. |

### 5. Risk & Allocation (`#page-quant`)

| Block | Decision | Rationale / action |
| --- | --- | --- |
| Hypothetical budget, asset choices, max single-asset weight | **KEEP** | Constrained optimization shows statistics/algorithms and finite-cap guard. |
| Crypto allocation ceiling and multivariate return simulation | **KEEP / LABEL** | Scenario assumptions, not a risk model calibrated on a live portfolio. |
| 276 simulated sessions / 1,800 Monte Carlo paths | **KEEP / VERIFY** | Numbers are hardcoded UI descriptions; assert they match source generation; random-seed and repeatability matter. |
| Optimization and modeled-downside outputs | **KEEP / CLARIFY** | Explain volatility, drawdown and stress in one sentence, with numerical units and basis. |
| Chart-only interpretation | **FIX** | Keep explanatory text beside observed modeled result, not only a legend or a disconnected method page. |

### 6. DCF Scenarios (`#page-valuation`)

| Block | Decision | Rationale / action |
| --- | --- | --- |
| Three-company illustrative model selector | **KEEP / REWORD** | UI should read “Example company assumptions” (not true SEC valuation). Source `model.js` has illustrative facts; selection deliberately limited. |
| Revenue growth, WACC, terminal growth, operating margin | **KEEP** | Real pedagogical sensitivity model; WACC must exceed terminal growth; report assumptions and five-year unit definitions. |
| Forecast cash flows, terminal value, discounting and sensitivity | **KEEP / CLARIFY** | Negative cash flow or equity values must not be presented as a trade target; terminal-value share is sensitive to assumptions. |
| Price/fair value language | **VERIFY** | Public result should not imply a current quote, analyst forecast or consensus price target. Source model uses scenario inputs. |

### 7. Peer Comparison (`#page-ml`)

| Block | Decision | Rationale / action |
| --- | --- | --- |
| SEC issuer selection, within-group toggle | **KEEP** | Name-based eligible selection, with documented editorial grouping and fallback. |
| Standardized financial-feature distance | **KEEP** | Transparent unsupervised descriptive similarity (not a trained company-return model). All peers use the same selected 2–4 ratios. |
| Distance graph, ratios and comparable-universe message | **KEEP / FIX** | Show eligible count, excluded count, ratio dimension, selected fiscal ends and broad-group fallback; never show “94 comparable” when only 91 eligible. |
| Issuers LHX, MS, PNC; partial cases NVDA/AMZN/KLAC and banks | **VERIFY / DATA IMPROVEMENT LATER** | Withhold eligibility when source facts cannot support comparison. Next data release may safely improve coverage only by fetching authentic SEC records and retesting. |

### 8. Research Methods (`#page-systems`)

| Block | Decision | Rationale / action |
| --- | --- | --- |
| Research introduction, static architecture flow | **KEEP / SHORTEN** | Data → validation → models → evaluation reads well; avoid redundant multi-paragraph disclaimers. |
| Featured reported-SEC case-study link and ledger | **KEEP** | Empirical evidence rather than algorithm name-dropping. |
| Long source-backed six-method atlas | **KEEP / REORGANIZE** | Financial ratios; covariance; optimization; walk-forward; DCF; provenance. Method → evaluation → limitation → source/test. |
| **New** price-direction held-out evaluation | **ADD** | Runs actual `private_predictive_ml_v180.js` on deterministic **synthetic** dated series; reports accuracy and Brier vs a baseline, test windows/dates. Not a market skill proof. |
| **New** lexical topic grouping and headline tone evidence | **ADD** | Explain TF-IDF, cosine, lexicon and negation; link Python source/test. FinBERT is optional, not claimed to run by default. |
| SEC revenue-growth and margin comparison exhibit | **KEEP** | Source-linked arithmetic, not return predictability. |
| Optimization, validation, valuation and screening technical sections | **KEEP / COLLAPSE REDUNDANCY IN FUTURE** | Deep source evidence still valuable. Replace old recursive “open” links with direct specific destinations where feasible. |
| Engineering/source/test reference cards | **KEEP** | Credibility depends on real links and test coverage; validate public repo access. |

**Methodology weakness not fixed by UI:** Current historical classifier supports an exploratory holdout, but lacks uncertainty intervals, multiple-regime repetitions and economic P&L after costs. Brier comparison without a significance/robustness study is not enough to call predictive skill validated.

### 9. Data & Engineering (`#page-methods`)

| Block | Decision | Rationale / action |
| --- | --- | --- |
| Four-stage engineering guide | **KEEP / REWORD** | Point to actual SEC ingest, normalization, statistics and deployment code instead of labels alone. |
| Duplicated private-model and NLP introductory panels | **MERGE / REMOVE** | ML/NLP technical proof now belongs under Research Methods. Consolidated short “Trace a result to the code” handoff remains. |
| Data lineage with dataset date, issuer coverage, source evidence | **KEEP** | Highlight annual XBRL/Company Facts, fiscal period, CIK, accession and unchanged snapshot. |
| Reported vs calculated vs simulated source classification | **KEEP** | Essential for avoiding misrepresentation in every other page. |
| Public simulator/risk/DCF/peer source map | **KEEP** | Show which page is an actual SEC observation versus an illustrative numerical example. |
| Architecture: Cloudflare Pages, scoped edge proxy, FastAPI/Render, owner MFA | **KEEP / VERIFY** | Source-backed architecture, not independent proof of production uptime/security posture. |
| Engineering CI checks, validation and privacy controls | **KEEP** | Python/JS test suites, code generation, CSP hash audit and privacy checker. Document which tests are automatic versus owner manual. |

### Shared public UI and additional research case-study page

Navigation has nine explicit public routes with active states and history handling in `web/site/app.js` (KEEP). The research case study is a dedicated generated HTML and CSV export; preserve both. Use real page headings, accurate metric units, contextual labels and tested escape handling. Responsive CSS exists but browser visual QA and accessibility audit remain *open*; no claim that keyboard navigation, table overflow or graph reading is perfect. GitHub source links also require an actual public-access check.

## Private: screen-by-screen functional disposition

The source generator (`tools/build_unified_site.py`) assembles an MFA-gated private section from many older research modules. Current everyday top navigation is **Research**, **Portfolio**, **Saved reports**, **Advanced research**; old screens still exist as specialized internal destinations. “Visible by default” is distinct from existing hidden/legacy module code.

| View / element | Decision | Default journey and retained behavior |
| --- | --- | --- |
| Login → authenticator enrollment/6-digit verification | **KEEP** | Owner-only authentication; no bypass and no copying secrets. Missing-factor handling and signout remain backend responsibilities. |
| Research: chosen-company chips + name browser | **VISIBLE / KEEP** | Choose 2–5 named equity/fund investments without ticker memorization. Preserve 2–5 validation, unique IDs, remove chips, invalidation on change. |
| Research: one “Analyze companies” control | **VISIBLE / KEEP** | Calls `runResearchOSV90`: loads dated history, optimizes, backtests, evaluates walk-forward/robustness, retrieves SEC and quotes, evaluates each company, summarizes side-by-side; optional methods marked unavailable when not eligible. |
| Research: required result + color-coded comparative cards | **VISIBLE / FIX** | Present strengths, objections, rule breaches, unavailable evidence and common historical downside. A single green pass is a conditional *research screen*, not a buy recommendation. |
| Research: optional settings, candidate preference, risk thresholds | **MOVE** | Still used by engine; all controls and exact IDs now on Advanced Research. Default settings apply automatically to main button. |
| Research: original detailed model report, technical hub outputs, optional SEC filing revision import | **MOVE** | Preserve method calculators, original accession/fiscal checks, scenario traces and optional archive, not daily UI. |
| Research: price-direction model | **VISIBLE / FIX** | Actual logistic-regression experiment; now shows directional accuracy and **Brier error** versus baseline with held-out dates/counts; only a conservative baseline-clearing result is labeled exploratory. |
| Research: dated headline topics and tone | **VISIBLE / KEEP** | Fetch after core research if entitled; show up to two attributed headlines/company and topic/tone. No fabricated news when API unavailable. |
| Workflow readiness and live-browser verification panel | **MOVE** | Included under Advanced Research; do not require checklist or local SEC archive before routine company research. |
| Portfolio (`home`) | **VISIBLE / KEEP** | Virtual totals, cash, holdings, position weights. Separate from research setup; no live orders. |
| Virtual trade and proposed allocation (`trade`) | **ADVANCED / KEEP** | Price/time-stamped virtual buys/sells and hypothetical impact stay available via internal navigation. No direct brokerage trading. |
| Saved reports (`settings`): saved archive, session journal, notes | **VISIBLE / KEEP** | Saved notes are owner-protected; journal is session-local; explicitly distinguish which persists. |
| Saved reports: optional guided suitability-style summary | **MOVE** | Secondary worksheet is in Advanced, preventing competing recommendations and repeated setup. |
| Research Lab / `lab` | **ADVANCED / KEEP** | Main home for model settings, source traces, optional archive, acceptance, and the complete underlying calculators. Restored accessible `<details>` labels, closed by default rather than automatically expanded. |
| Candidate/factor research (`candidate`) | **ADVANCED / KEEP** | SEC dossier, ETF-proxy regressions, optional officially imported daily FF3. Do not call ETF proxies “official FF factors.” |
| Market history (`research`) | **ADVANCED / KEEP** | Dated data, correct selection/loaded distinction and source limits. |
| Optimization (`optimization`) | **ADVANCED / KEEP** | Constrained covariance portfolio estimates and diagnostics. |
| Buy/hold vs rebalancing (`backtest`) | **ADVANCED / KEEP** | Historical strategies, observed prices, data selection and modeled fees. |
| Walk-forward (`walkforward`) | **ADVANCED / KEEP** | Past-only fits, separate test windows and baseline comparison. |
| SEC valuation (`valuation`) | **ADVANCED / KEEP** | Explicit assumptions and missing observed inputs. |
| Screening (`ideas`) | **ADVANCED / KEEP** | Separate historical filter, not a duplicate primary company-comparison instruction. |

**Remaining private architectural debt:** There are many historical modules and conditional routes. Their computational capabilities are preserved by design in this release, but a future refactor should extract shared data-loading and evaluator contracts rather than deleting engines or using CSS to hide errors. The first option is useful, second is unsafe. Full authenticated browser acceptance remains required.

## Employers: demonstration/evidence matrix

| What a visitor can actually inspect | Capability | Concrete evidence | Roles | Remaining limitation |
| --- | --- | --- | --- | --- |
| Annual SEC records, revenue/margin/FCF and filing source | Ingestion, validation, derived metrics, data lineage | `web/site/sec_snapshot.json`, `sec_analytics.js`, `tools/build_public_sec_snapshot.py`, SEC tests | DE, BI, DS, finance analytics | Snapshot timing/issuer quality, incomplete fiscal comparability; no live provider claim |
| Company financial charts, tables, CSV, case study | EDA, business metrics, reporting/visual communication | `app.js`, `sec_visuals_v81.js`, `public/research-case-study.html`, CSV | Analyst, BI, consulting, DS | No claim of causal drivers or future price returns |
| Comparable financial-profile distance with visible missingness | Standardization, nearest neighbors, missing-data design | `sec_peer_model.js`, peer tests; 91/94 on snapshot | DS, applied statistics, equity analytics | Descriptive unsupervised; dimension changes across peer groups |
| Portfolio scenarios and optimization, sensitivity | Covariance, constrained numerics, risk | `model.js`, `public_lab_v77.js`, `private_optimizer.js` and tests | DS, quantitative analytics, risk | Public simulated data, not live expected risk |
| DCF scenario/terminal value | Applied financial math, numerical sensitivity | `model.js`, SEC/DCF methodology, regression tests | Finance analytics, risk, DS | Illustrative assumptions and limited historical anchoring |
| Held-out model vs baseline, dated windows and Brier | ML feature design, regularization, chronological evaluation | `private_predictive_ml_v180.js`, new `public_model_evidence_v181.js` and tests | DS, ML, statistics | Synthetic public demo not measured real-market performance; no calibration certainty |
| Headline topics and rule-based tone | Tokenization, sparse TF-IDF similarity, transparent lexicon | `cloud/news_intelligence_v180.py`, `tests/test_news_intelligence_v180.py` | NLP, DS, AI systems | Depends on private Alpaca news entitlement; no default transformer semantics |
| Authenticated virtual account, protected API, CSP, CI | Web/software engineering, security boundaries and tests | `cloud/api.py`, `functions/api`, `build_unified_site.py`, `.github/workflows/ci.yml` | SE, DE, full stack | Source controls not independent penetration test or live acceptance |
| SQL-backed offline finance utilities | SQL, data persistence, analytical query | `src/quantforge/desk/quant_portfolio.py`, `src/quantforge/desk/engine.py` | DE, analytics, SE | Not equivalent to saying public Cloudflare website is SQL-backed |

## Defensible interview framing

> “QuantForge is a financial-data and modeling project built around SEC filing provenance, statistical comparisons, constrained portfolio scenarios and chronological evaluation. I implemented and tested a five-session logistic-regression direction experiment against an expanding historical-frequency baseline, plus transparent TF-IDF headline topics and lexical sentiment. The public ML exhibit uses synthetic inputs to demonstrate the algorithm without disclosing authenticated data or claiming live predictive accuracy. Private research is MFA-protected and uses provider observations when available. The value is the reproducible workflow and explicit model limitations, not a claim to predict profitable trades.”

Be prepared to explain standardization, why fiscal and filing dates differ, mean/covariance risk, Brier versus classification accuracy, exact chronological cutoff logic, transaction-cost effects, and why a dictionary sentiment score is not a return forecast. Avoid representing the application as a professional quant fund, or suggesting that finance is the degree field.

## Release validation and outstanding acceptance

**Reproducible in this review environment:** Current ZIP archive comment SHA, 94 company snapshot, 91/94 peer eligibility, local deterministic site build, three CSP-protected scripts, bundle/privacy audit, JavaScript regressions and targeted Python tests. The full Python suite was also run with `PYTHONPATH=src` against a temporary local Git snapshot; note that the review environment lacks `duckdb`, so one test is skipped. The local Git snapshot is only a validation fixture, not the user's Git HEAD.

**Must run in user's checkout:** exact Git baseline and clean working tree, payload hashes, Ruff, Python and Node suites including optional dependencies, deterministic rebuild and CSP audit, private privacy checks, Git diff/whitespace and exact change list. After push: match GitHub Actions run to the new commit, confirm Cloudflare serves byte-identical built HTML, and confirm Render deployed the API change if any (this release has no API modification).

**Must verify manually in authenticated browser (no secrets exported):** fresh MFA; same named selection for all five company results; ability to analyze 2, 3 and 5 companies; missing quotes/SEC/news fail closed; actual ML sample counts/dates and headline sources; run-progress/selection invalidation; portfolio virtual balances and saved-note persistence; mobile/tablet layout, keyboard navigation, SEC-source links, actual live companies and case-study download. Private service acceptance is not asserted by offline tests.

**Cost:** This release does not add paid AI APIs, paid news providers or new cloud infrastructure. Optional local FinBERT remains off unless explicitly provisioned.
