# QuantForge final completion — living engineering record

Baseline: `94a95616618f273286a3f113dde31780e90f79ed`; clean checkout; review branch `codex/quantforge-final-24-issue-completion`. Main and the previous review branch are preserved. Latest main CI `42940896805` passed; current read-only health probe returned HTTP429/non-JSON challenge, so current API revision was not reverified. No owner credentials, real records or writes used.

The new Nov11 user request supersedes the previous release acceptance for the reopened Buy complaint. Earlier owner confirmation is historical evidence only. No push, merge or deployment is authorized for this stage.

Full locked Nov9 specification, old handover, written video findings, Nov11 24-issue audit and product/acceptance/career playbooks were read. References to older commits, routes and line numbers are treated as historical. No new video or installer is needed.

Baseline rerun: **592 Python passed (7 warnings), 402 JavaScript passed**. Project-local Python and existing browser dependencies retained; no install.

## Source-grounded initial coverage matrix

| ID | Baseline disposition | Current cause / evidence | Required correction or verification |
| --- | --- | --- | --- |
| QF-01 | partial | Accepted POST is retained, but an active ledger filter/page can still hide the new receipt. Safe codes are lost to generic 422 text. | Reset ledger to newest receipt; expose bounded failure codes; reproduce against isolated account. |
| QF-02 | present; reverify | Owned-only picker and server oversell guard exist; input does not expose maximum. | Add available/max quantity control and full-sale/refresh browser coverage. |
| QF-03 | partial | Explicit shared selection exists; leveraged subtype and exclusions are heuristic. | Keep explicit selection; distinguish leveraged names and explain unverified subtype. |
| QF-04 | partial | 80 receipts and paging exist; new receipt can be hidden by current filter/page. Quote provenance is only in preview. | Newest accepted row, highlight receipt, quote source/time and inspectable history. |
| QF-05 | partial | Server checks freshness; client masks specific rejected quote/budget conditions. | Allowlisted public error codes, inline remedy, rejected/expired preview tests. |
| QF-06 | partial | Trade request IDs and uncertain-write blocking exist; funding does not share that workflow. | Funding preview/replay protection; shared account busy/uncertain state and conflict tests. |
| QF-07 | open | Aggregate compares positive versus negative while ignoring neutral dominance. | Transparent sample/proportion/conflict rules and exact 1-positive/49-neutral regression. |
| QF-08 | partial | Full bounded sample, charts and paging exist; aggregate policy and source coverage need explanation. | Expose policy, sample coverage, source counts and dated tone proportions. |
| QF-09 | present; reverify | SEC-first public Explore and private market default exist. | Verify private default on symbol/mode changes; SEC-first public Compare and explicit synthetic subview. |
| QF-10 | partial | Shared picker exists in Explore/Compare/transactions, but Models and What If rely on setup elsewhere. | Mount same component/adapters in Models and portfolio scenarios; cross-page context tests. |
| QF-11 | present; reverify | Explicit peer scope and corrected percentage units exist. | Retest universe independence, missing dimensions and explanatory feature comparisons. |
| QF-12 | present; reverify | Compact account and contextual notes exist; funding remains beside recorded-history controls. | Move distinct funding workflow into transaction actions; retain compact account. |
| QF-13 | present; reverify | Native MathML, worked calculations, code excerpts and SEC case study are in-app. | Verify all Methods views and actual source/test references; add missing scientific/error evidence. |
| QF-14 | partial | Named Explore views exist; mode ribbon, source prose and long Compare flow still compete. | Compact mode/source hierarchy and named evidence subviews, retaining all analysis. |
| QF-15 | open acceptance gap | Prior tests cover 1440/390 only; no complete 320/tablet/200% zoom proof. | Five-width and zoom route/subview/component review, long/error/empty fixtures. |
| QF-16 | partial | Interactive charts and tables exist; fixed geometry and component clipping need stress review. | Check actual text size, labels, legends, focus/readouts and scrollable tables at all widths. |
| QF-17 | owner verification | Owner attested the previous release on Nov10, but latest complaint reopens Buy acceptance. Current health request returned 429 challenge. | No account writes; document current external uncertainty and request controlled acceptance only after local review. |
| QF-18 | present; reverify | Twelve worked Methods views exist with native formulas and traces. | Verify inputs/formula/visual/evaluation/code at current HEAD; improve NLP rule/error example. |
| QF-19 | partial | SEC lineage/table and case study disclose missing cutoffs; no compact complete quality dashboard. | Computed issuer/field/missingness/negative-FCF coverage and selected record lineage. |
| QF-20 | present; reverify | Four model categories and measured baseline/evaluation evidence exist. | Reverify measured windows, units, withholding, input selection and readable evaluation graphs. |
| QF-21 | documented boundary | Public annual SEC context exists; live filings/news redistribution not implemented. | Keep headline-only owner data; verify official source boundaries before any new feed; no feed added by default. |
| QF-22 | present; reverify | Sidebar creator credit and Methods motivation exist. | Retain visible credit and authentic motivation; inspect narrow/zoom states. |
| QF-23 | present; reverify | In-app source excerpts and research study avoid private GitHub dependence. | Verify publicly usable case study/CSV and no invented skills/visibility change. |
| QF-24 | open inventory gap | Legacy numerical modules/DOM remain for compatibility; original parity report exists. | Inventory actual routes/handlers/engines and tests; preserve computations, remove no engine merely for layout. |

Machine-readable living register: `FINAL_24_ISSUE_REGISTER.json` (downloadable CSV is in the external review folder). Baseline HTML/CSP and screenshots are stored outside the repository under `QuantForge-final24-review`.

## Stage A — account correctness and source trace

Completed locally. Trace uses the original MFA bridge, fresh quote validation, Decimal calculations, optimistic concurrency and Supabase save response. No replacement numerical engine or independent provider loader. Record failing regressions and actual browser evidence here as each stage completes.


## Final local verification — November 12

The baseline reproduction accepts one Buy while the active funding filter and page 3 hide its receipt. The candidate resets to newest activity, keeps quote venue/time with the receipt and provides bounded actionable errors. Original fresh-quote, Decimal, owner/MFA, origin, version and Supabase compare-and-set checks remain. Funding now has server-calculated read-only preview, explicit confirmation, stable request IDs and shared busy/unknown-write recovery. A genuine competing-read/CAS test produces one accepted write and one conflict; replay reconciles without repricing. Existing bounded journals remain 80 trades / 100 capital events; they are not an unlimited audit store.

The same picker now reaches Models and Portfolio What If, with explicit duplicate/five-asset feedback. Public Compare starts with reported SEC financials; private Compare uses observed histories. Named evidence views preserve all analysis. The exact one-positive / 49-neutral headline case now reports Mostly neutral. Sample/conflict/uncertainty rules, dated tone proportions, source counts and ten synthetic hand-labeled teaching examples expose lexical limitations. These rules are descriptive, not calibrated probabilities or investment signals.

Methods adds computed SEC quality/lineage and authenticated write flow evidence while retaining twelve MathML studies, the SEC case study, source excerpts, motivation and creator credit. No new framework, paid dependency, SQL migration, provider feed or installer was introduced. The complete engine inventory records 65 JavaScript modules and 36 unchanged private-prefixed modules; compatibility handlers remain intentionally preserved.

Final suites: **613 Python passed**, **405 JavaScript passed**, Ruff passed; seven pre-existing Python deprecation warnings. All retained A-D, rebuild, completion and v27 journeys passed. New workflow acceptance passed Chromium, Firefox and WebKit at 320, 390, 768, 1024 and 1440 (15 combinations). The component matrix passed **444 named-view checks**, including all model result/evaluation/method views, twelve worked examples, table keyboard regions, clipped controls, page errors and actual chart text size. A separate genuine native Chrome **200% zoom** check passed 26 views (1424 CSS px / DPR 1 to 712 CSS px / DPR 2). The 720px/2x-density matrix is separately labeled equivalent reflow, not native zoom. Selected full/component screenshots were manually inspected; automated probes do not mean every screenshot was manually read.

## Published application inspection — separate from candidate acceptance

On November 12 the user signed in and completed MFA in their own Chrome session. Read-only inspection observed entitled Explore history/news, generated company analysis, Prediction baseline/withholding, Risk charts, three-company exact-common-date comparison, saved portfolio/ledger/holdings, successful Refresh account, owned-position Sell selection, Methods architecture and a correctly rendered native variance formula/trace/chart. No real account records were modified, exported or included in screenshots/logs. Explore displayed an IEX source label while Compare displayed a SIP source label; labels reflect each response, not a blanket feed entitlement claim.

Automated health probes returned an HTTP429 hosting challenge, but authenticated browser research loaded normally. Treat this as an automated-access limitation, not a demonstrated outage. The published frontend remains baseline 94a9561; backend revision was not independently reverified. Production note writes and Buy/Sell/funding persistence on this new candidate remain open acceptance gates after an approved release. Historical owner confirmations do not close these gates. No push, merge or deployment is authorized by this review stage.

## Source and product boundaries

Public context uses annual SEC Company Facts and attributable filings. SEC submissions/XBRL APIs and fair-access limits were checked against the [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) and [SEC webmaster guidance](https://www.sec.gov/about/webmaster-frequently-asked-questions). The annual snapshot does not provide a live 8-K/10-Q news stream or reconstruct every original point-in-time filing. Private headline access remains authenticated and bounded; no full-article redistribution or new public feed is inferred from access to an endpoint. See the [Alpaca news reference](https://docs.alpaca.markets/us/reference/news-3) and [historical news documentation](https://docs.alpaca.markets/us/docs/historical-news-data).

Missing SEC fields remain unavailable, leveraged/inverse name matching remains a disclosed heuristic, public price experiments remain synthetic, and model evidence does not establish future predictive skill. Actual owner history requires recorded marks; current holdings cannot manufacture past values or flow-adjusted returns.

## Review artifacts and approval boundary

The JSON issue register maps all 24 items to actual implementation, tests, evidence and remaining production gates. Its CSV copy and screenshot gallery are outside the repository to preserve the existing publication privacy rule rejecting extra datasets. Final test logs, baseline failures, before/after screenshots, five-width component evidence and native zoom proof are in the external QuantForge-final24-review folder. The source manifest hashes raw and LF-normalized review files, excluding itself; the local commit identifies the complete reviewed tree. Remote CI has not run for this candidate because it has not been pushed.
