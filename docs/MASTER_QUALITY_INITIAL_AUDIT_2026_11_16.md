# QuantForge 2.0: initial reality-based audit

Reviewed November 16, 2026. Baseline Git main `53a8bd0`; live recovery and local recovery source are separate from that commit. This records what existed before the product changes in this review.

## Priority findings

| Priority | Observed deficiency | Evidence and consequence |
|---|---|---|
| P0 | Working recovery not reproducible from main | Hosted recovery has an uncommitted exact-origin proxy patch; API package is outside Git. A main build can restore Render-only routing. |
| P0 | Local provider cache enters release preflight | Baseline pytest: 634 pass, 2 fail. Both failures identify an unignored Wrangler account-cache file. No credential values were printed or committed. |
| P1 | Remote source identity unavailable | Direct and proxied health return `shared-research-v25`, but `revision: not-reported`. Local package/source comparison is evidence, not remote commit attestation. |
| P1 | Stale transaction refusal lacks context | Server correctly enforces 900-second equity/fund and 300-second crypto thresholds; UI exposes neither available timestamp nor observation age/source. |
| P1 | Hosted cost basis initialized but not maintained | `default_state` contains `cost_basis`; trade commit changes holdings/cash and receipts but never updates that field. Offline SQLite accounting is deeper than the hosted account. Do not infer legacy basis from the bounded 80-receipt display. |
| P1 | Crypto risk annualized as equity risk | Single-asset volatility, rolling volatility and sample-sensitivity code multiply variance by 252 irrespective of a crypto daily calendar. |
| P1 | Private briefing is disconnected and excessively long | Actual fixture screenshot puts six long findings before a second summary, repeats Analyze, then shows completed calculations beside unavailable decision-evidence domains without sufficient explanation. |
| P1 | Thin synthesis and weak missing-data guards | Summary covers three financial measures, drawdown and classifier output, but omits compatible balance-sheet facts, observed-price ratios, marked exposure and held-position co-movement. Model-ready fields are formatted without independently guarding malformed values. |
| P2 | Home explains destinations but offers little inspectable process | Case study exists; Home has a search and five passive descriptions. It does not connect the research process and implementation evidence strongly enough for a first-time technical visitor. |
| P2 | Historical outage copy contradicts recovered service | The same unresolved Render-era warning appears in a working MFA-verified session displaying recent SIP history. It is not a current service-status measurement. |

## Baseline verification

- Live anonymous Vercel health 200; direct private state 403; same-origin Pages health 200; signed-out session returns `signed_in: false`. No owner credentials used for these checks.
- Production HTML matches the local recovery output after newline normalization.
- 226 packaged library files compared: 225 match repository source; the remaining difference is an empty `tools/__init__.py` marker.
- 433 JavaScript tests pass. Baseline Python has 634 passes and two privacy-preflight failures noted above.
- 219 rendered baseline component checks pass across 390px, 1440px and a 720 CSS-pixel / 2x-density reflow case. This is not native browser zoom and not evidence of analytical usefulness.
- A real owner session was subsequently observed read-only: MFA-verified mode and entitled SIP history were visible. No notes, trades, funding, credentials or authentication settings were changed. Fresh MFA and candidate persistence were not performed.

## Feature-purpose classification

| Capability | Classification | Credible scope / limitation |
|---|---|---|
| SEC ingestion, annual normalization and lineage | Analytical data engineering | Reported observations and accession/date provenance; no full quarterly/TTM or original-filing archive inferred. |
| Growth, margins, cash-flow proxy, liquidity | Analytical and descriptive | Ratios require eligible inputs and compatible periods/accessions. They do not establish causality or solvency. |
| Five-session logistic model | Experimental analytical model | Chronological matured labels, held-out windows, Brier, baseline and conservative withholding. Synthetic Public inputs do not demonstrate market predictive skill. |
| Historical volatility, drawdown, VaR/ES | Descriptive risk analysis | Dated samples and dependence-aware sample sensitivity; not calibrated future losses. Crypto calendar defect requires repair. |
| DCF and projected cash flow | Assumption-driven | Auditable cash-flow-proxy scenarios. No complete FCFF/enterprise/equity/per-share valuation bridge. |
| Optimization and walk-forward | Analytical experiments | Constraint/fee/date tests and later evaluation; no guarantee of lower future risk or profitable implementation. |
| Portfolio marks and contribution accounting | Analytical bookkeeping | Marked value and capital-versus-gain separation work. Hosted realized/unrealized breakdown is incomplete at baseline. |
| Research synthesis | Partially integrated | Deterministic explanations exist but do not yet reconcile all available domains or present a concise, traceable assessment. |
| News/NLP | Archived experimental implementation | Retained source/tests, retired from the current product for limited demonstrated decision value. Do not advertise it as an active investment signal. |
| Fund analysis | Incomplete | Price/risk research possible; fund holdings, fees and look-through exposure are not supplied by issuer SEC ratios. |

## Public and Private goals at baseline

Public has credible technical depth and a working five-section product, but cannot be called a finished career demonstration solely from its test count. The first-use narrative, source-controlled recovery, excessive briefing depth and current architecture documentation need work. The strongest demonstration is a reproducible SEC case study followed by Models Evaluation and Methods Engineering, not an advertised stock-picking accuracy.

Private reduces some calculation work but does not yet provide a consistently integrated assessment. Valuation completeness, financial freshness, model disagreement and actual portfolio overlap must remain explicit. Legacy basis and fund look-through cannot be manufactured. A coherent conclusion may legitimately be withheld.

The governing November 9 specification was read; subsequent approved retirement of routine news/NLP is preserved. After the initial audit and implementation, both original UX recordings were found in Downloads: Video Project 5.mp4 (95.7 seconds) and Video Project 5 (1).mp4 (187.03 seconds). Chronological frames were visually sampled every four seconds and inspected as contact sheets. This is visual sampling, not full playback or an audio transcript. They confirm the historical restrictive picker, sparse model/method exhibits, cramped portfolio controls and GitHub error destinations. The sampled frames do not establish that every historical defect, including an intermittent object-string error, was reproduced. Current error rendering is covered by regression fixtures. Original recordings/contact sheets stay outside Git and the review gallery because they contain private-session information.
