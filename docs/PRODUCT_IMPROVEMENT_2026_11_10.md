> Historical stage record. This work was published in `4fc1a46`; publication-pending wording below describes the earlier review stage. See [current release guide](GUIDED_RESEARCH_RELEASE.md).

# QuantForge next major product improvement — local review

Baseline: `da1f755cdc784e2fbd11413aea879bf5c34acf00`, clean `codex/quantforge-product-rebuild` checkout. This stage continues the locked November 9 product and the November 10 detailed request. No push, merge or deployment is authorized for this candidate; production remains the prior release until separate approval.

## Source-grounded gap inventory and resulting behavior

| Area | Reproduced or source-verified baseline gap | Implemented improvement / evidence |
| --- | --- | --- |
| Accepted virtual trade | An isolated POST recorded one trade, followed by a stale GET that returned zero trades and old cash | Accepted POST state is consumed immediately. Older versions and previous-session responses are rejected. Regression: `tools/smoke_product_v27.py` |
| Replay / uncertain response | No receipt-level replay identifier; unclear result after interrupted response | Stable request ID, bounded journal reconciliation, preview/commit shared decimal arithmetic; uncertain UI blocks another attempt until explicit refresh/review. Same ID with different transaction parameters rejects |
| Sells | Provider-wide selection included investments not owned | The reusable picker is restricted to positive owned positions for sells. UI and server reject excess units |
| Buying | Search + unrelated dropdown + generic confirmation; little fee/cash evidence | One name-first picker, fresh server-calculated quantity/fee/cash preview, 60-second expiry, explicit confirmation and immediate ledger/holdings update; >0.5% quote change requires a new preview |
| Picker | Different Explore/Compare/transaction selection handlers | `investment_picker_v27.js` is shared by all three, using the existing authorized adapters; exact-symbol/name ranking, explicit instrument/coverage metadata, keyboard selection, cancellation and stale-response invalidation |
| Selection limits | Compare could silently ignore duplicate/excess selections | Explicit already-selected and five-investment-limit feedback; same-date computations and basket reuse preserved |
| Public Explore | Synthetic company-associated prices dominated authentic financials | Default is actual SEC revenue/earnings, margin/growth and cash-generation charts, with keyboard/hover readouts. Synthetic paths remain labeled in Models/Compare/Portfolio demonstrations; no public observed-price feed added |
| Private Explore | Price/news context and notes competed on a long page | Normal Financials / Market history / Company briefing / News & filings views. Observed source/feed labels retained; notes remain beside briefing |
| Findings | Sparse observations with limited interpretation | Observation → why it matters → supporting evidence → limit, including sales, margin change, cash versus earnings, eligible observed drawdown and actual model/baseline results |
| News depth | API analyzed up to 50 headlines but returned three; frontend sliced again | Full bounded analyzed sample returned, deduplicated without collapsing distinct numeric headlines; distributions, dated count trend, topics/tone filters, six-record paging, conflict flag and supporting headlines |
| NLP uncertainty | Dictionary tone did not label qualifiers | Negation preserved; may/might/could/rumor/reportedly language is explicitly uncertain. Manually labeled examples test the baseline; no full-article or semantic-understanding claim |
| Public context | No licensed public news, empty context | Authentic accession-backed annual filing records from the existing SEC snapshot. Explicitly company filing context, not news sentiment or a live 8-K/10-Q feed |
| Peer scope | Ambiguous broader-industries checkbox | Labeled Same-industry / All eligible SEC-covered companies selector, separate from the main basket; fallback and accounting comparability disclosed |
| Peer units | Engine values in percentage points were multiplied by 100 again in shared table | Display uses engine units directly; selected and nearest-profile feature bars expose the ratios and fiscal ends |
| Account overview | Large mostly empty modal | Compact verified-session view, actual saved-research count/cash/positions, current observed-history status and functional contextual shortcuts |
| Portfolio organization | Repeated account figures and an unrelated fixed-basket planner mixed with current What If? | Shared quote loader produces the main marked-value/allocation summary; receipt activity has filter/paging, dates, units, prices/fees/cash impacts. Fixed-basket rebalance is retained as an explicitly synthetic Methods teaching example, with its original working calculator tested |
| Methods mathematics | Six brief static exhibits | Twelve worked views: returns, regression/covariance, portfolio variance, VaR/ES, drawdown, bootstrap sensitivity, logistic mapping, Brier/calibration, ratios, DCF, walk-forward and TF-IDF. Native MathML, adjustable examples, traces, charts/tables, evaluation, limits and exact source/test references |
| Methods Data | Mostly descriptions of ETL | Real normalized SEC input record, actual derived margin calculation, accession coverage counts, fiscal/filing distinction and issuer-specific/missing extraction cutoffs. No invented raw XBRL record or SQL/incremental-warehouse claim |
| Research case study | Valuable V8.2 report disconnected from shared Methods | Integrated prespecified MSFT/AMD/ADBE/AMAT financial study with real values, assumptions, source ledger, CSV/print and retained report link. Missing original cutoff metadata is disclosed, never inferred |
| Engineering | Text boxes and file references | Responsive connected public/private architecture diagram, curated real decimal/version-check excerpts, data contracts, auth/session/result handling, exact tests and eight existing evidence disciplines |
| Model evaluation | Feature and chronology details not prominent enough | Actual features, mature final-training count, held-out dates, disjoint windows and baseline contract beside Prediction Evaluation; original numerical/ML gates unchanged |
| Design | Inconsistent forms/cards, weak credit and some small labels | Shared tokens for surfaces/controls/gutters/charts, full-width mobile forms, coherent ledger/tables, purpose-grouped views, creator credit and arrow/Home/End keyboard navigation |

## Source changes

New shared modules: `investment_picker_v27.js`, `portfolio_workflow_v27.js`, `explore_research_v27.js`, `news_context_v27.js`, `methods_lab_v27.js`, `research_design_v27.css`. They extend the existing app and private bridge; no new framework, independent provider pipeline, paid service, SQL migration or runtime dependency.

Backend: additive owner/MFA/action/origin-gated `POST /api/private/trade-preview`; `trade_terms` is the single Decimal calculation for preview and commit. The final commit revalidates a fresh quote, account version, owned units, cash and optional reference price. Original fee/quantity/cents conventions are preserved. Trade receipts retain price, fee, gross, cash impact, observation provenance and request ID. Reconciliation is bounded by the existing 80-receipt history; stale expected versions continue to protect older requests.

The existing deterministic builder bundles the additions into the same three protected scripts and injects the shared stylesheet. Every original numerical engine remains. Legacy UI tests were adapted to intentional new controls and destinations; accounting, chronology, isolation and source assertions were retained. The static case-study audit now checks links in both the template and shared Methods module.

## Verification

Baseline: 580 Python tests, 399 JavaScript tests. Candidate: **592 Python tests and 402 JavaScript tests passed**, together with all six new-product and all six preserved-engine browser journeys, A–D and the full-route matrix. Final verification results and exact artifact hashes are recorded in `PRODUCT_V27_REVIEW_FILES.json` and the local review gallery. Required checks include complete Python/Node suites, Ruff, all JS syntax, privacy/CSP, deterministic HTML/header pair, A–D journeys, full-route matrix, retained deep-engine journeys and new product journeys in Chromium/Firefox/WebKit at 1440px/390px.

New tests cover Decimal preview/commit conservation, replay reconciliation and mismatched IDs, insufficient funds/owned units, stale price/version, owner denial, hand-calculated worked mathematics, all source/test references, name ranking, stale picker responses, lost write response, stale refresh rejection, late response after logout, Methods mode isolation, news distribution reconciliation, qualifiers/deduplication, keyboard controls and case-study CSV.

Screenshots use authentic published SEC data and isolated fabricated owner/provider fixtures. They are not evidence of current live MFA, market entitlement or real account persistence. No owner credentials or real saved records were used or changed.

## Source and licensing decisions / remaining acceptance

- Public market examples remain synthetic; no paid or rights-uncleared price source was introduced. SEC annual filing context is not independent news sentiment.
- A live public 8-K/10-Q stream is not part of this candidate. The official [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) supplies the appropriate future submissions source and documents the browser CORS boundary; build/server collection and provenance would be needed. No fabricated events fill that gap.
- The [Alpaca news endpoint](https://docs.alpaca.markets/us/v1.1/reference/news-3) requires authentication and may offer content when available. This implementation intentionally analyzes headlines only; endpoint availability is not treated as a grant of public redistribution rights.
- Provider asset class/exchange/tradable metadata and name-based fund-like classification are distinct. A listing is not proof of subtype, SEC coverage, fresh quote, or history/news entitlement.
- Before an approved release: remote CI for this candidate, matched Pages/FastAPI deployment revisions and owner-controlled verification of real previews, buy/sell/funding, persistence and logout. Prior owner acceptance applied to `da1f755`, not these new changes.
