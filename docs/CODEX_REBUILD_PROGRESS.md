# QuantForge rebuild progress — November 10, 2026

Review branch: `codex/quantforge-product-rebuild`.
Base commit: `53dcc960c6f0c036beb00435173b33fa49574b1a` (Release D).
Implementation is isolated on this review branch. The final local review commit is available through `git log -1`; the base SHA above remains the reference for the full diff. No push, merge or deployment.
The local implementation and feature integration are complete. **Production acceptance remains separate**: no push, merge or deployment has occurred.

## Authority and inspected evidence

The current user request controls execution. The November 9 master specification supplies the approved five-section product requirements. Historical handoff instructions to run installers, commit/push automatically, preserve nine primary routes, or restart Release A are superseded. No installer was run.

Read the complete current handoff, first-message document, master specification, November 9 complete handover, video audit, release/failure history, parity/acceptance checklist, historical source audit and actual Release C notes. FULL ZIP was extracted into the chat workspace, not over the source repository. Reviewed all six supplied contact sheets covering both recordings, extracted frames every two seconds from both original MP4s, and inspected detailed private-price/news and portfolio frames. This was frame-based visual inspection, not continuous audiovisual playback.

Recorded negative acceptance cases: raw object-string login error; restricted picker; private/public ambiguity; inaccessible contextual notes/trades; sparse model/method views; plain-text math; cramped mobile weights; GitHub 404s. The observed 251 Alpaca SIP closes and 50 headlines remain historical video evidence, not current entitlement proof.

## Verified baseline and deployment

| Check | Observed evidence |
| --- | --- |
| Local source | Clean `main`, exact HEAD above, remote `RishiRatnakarData/quantforge-hosted`; separate review branch created before source edits |
| Environment | Explicit repository `.venv/Scripts/python.exe`; FastAPI, pytest and Ruff import successfully |
| Baseline regression | 571 Python tests, 390 Node tests; Ruff, CSP and privacy audits passed |
| Exact SHA CI | Run `42857843161` failed in browser build: `ModuleNotFoundError: requests`; local fix adds the build dependency to that job |
| Cloudflare before edits | HTTP 200, byte-identical to baseline `public/index.html`; SHA-256 `20ab1cd8c88e6c663959d12dfd0c0aaddcd940c52be4798a5d1fa2afcf1740fc` |
| Live API/Render | Pages `/api/health` and signed-out `/api/private/state` returned 429/challenge responses. Neither API revision nor signed-out origin denial verified live |
| GitHub links | Authenticated metadata reports `isPrivate: true`; anonymous repository request returns 404. Do not change visibility without owner direction |
| Live owner services | No credentials used; MFA, provider entitlements, saved-note persistence and actual virtual-account acceptance remain owner-only |

## Implemented changes

**Authentication/error presentation.** New `research_errors_v24.js` maps response status to safe, actionable messages shared by original private API calls and the shared app adapter. Structured FastAPI validation arrays/objects and provider details cannot become `[object Object]` or leak echoed inputs. Handles 400/401/403/409/422/429/unavailable/network cases. Existing API owner/MFA checks remain unchanged.

**Private discovery and research.** Explore now debounces authenticated provider name searches through the existing `/api/private/assets?category=all` route. Provider-listed US equities outside the 94-issuer SEC snapshot can load entitled history; SEC statements remain unavailable rather than invented. Virtual transactions use the same provider directory instead of the snapshot-plus-four-ETF list. No new provider or order endpoint. Missing feed metadata is labeled unknown rather than inferred as crypto.

**Mode isolation and persistence.** Global visible public/private status and return toggle across all five sections. Mode changes invalidate calculations, clear private DOM content, and remove private-only assets from the public comparison basket. Notes and dated briefs live in Explore; current saved virtual holdings, transaction form and ledger live in Portfolio. Existing versioned bridge writers and archive codec are reused. Old `QF96` saved assessments render as historical records beside company notes. Account modal contains account/logout actions, not the primary note/trade workflow.

**Research depth.** Compare adds actual SEC operating-margin bars and company-by-company financial explanations. Models adds held-out model/baseline accuracy, calibration, dated drawdown samples, discounted cash-flow contributions, guarded interactive DCF assumptions and recomputed fee sensitivity. The retained rolling `private_walkforward_v65.js` and `private_optimizer.js` now run from Strategy Testing with Compare selection, aligned observations, 126-close training / 21-session testing, 60% caps, cost-aware equal-weight benchmark and explicit window/weight evidence. No numerical engine was replaced. A misleading claim that accuracy always improved was corrected to match the unchanged `>= baseline` gate.

**Methods and presentation.** Native accessible MathML, six worked-method exhibits, selected-company SEC lineage/chart, public/private architecture and security explanations. Private repository references appear as code paths with access requirements instead of dead public hyperlinks. Grayscale shell, readable text, purposeful chart space, full-width mobile weights, responsive primary-chart coordinates and honest synthetic index table units. No external math renderer, React rewrite, paid service or production runtime dependency.

## Completed feature parity and guarded availability

“Integrated” means reachable in the new five-section interface. “Preserved” alone does not imply migrated or owner-accepted. All owner acceptance is open unless stated otherwise.

| Existing engine / capability | Approved destination | Current integration | Automated evidence | Owner acceptance |
| --- | --- | --- | --- | --- |
| SEC snapshot, analytics, filing dates/accessions | Explore / Compare / Methods Data | Integrated, unchanged dataset and missingness | Existing SEC Python/Node tests; browser financial/missingness cases | Open |
| Single-company entitled daily closes | Explore | Integrated; source/feed/date explicit; no private synthetic fallback | A/C/new browser, API suite | Live entitlement open |
| Authenticated provider asset directory | Explore / Portfolio | Integrated US-equity name search; history vs SEC coverage distinct | Existing directory/API tests; new non-SEC browser case | Open |
| 2–5 exact-date comparisons, histogram, scatter, correlation, CSV | Compare | Integrated; new financial contrast/prose | B/new browser; `research_compare_portfolio_v21.test.cjs` | Open |
| L2 five-session classifier | Models Prediction | Integrated with baseline, calibration, gating, formula and examples | `private_predictive_ml_v180.test.cjs`, C/new browser | Real-data assessment open |
| Historical volatility, VaR/ES, drawdown, block sensitivity | Models Risk | Integrated, unchanged definitions; extra dated drawdown exhibit | `research_models_core_v22.test.cjs`, C/new browser | Open |
| SEC cash-flow-proxy DCF | Models Valuation | Integrated, interactive bounded assumptions and terminal decomposition | Existing DCF tests and new browser rendering | No FCFF/equity bridge claimed |
| Fixed lagged price filter / costs | Models Strategy | Integrated with fee sensitivity | Existing chronology/cost tests; C/new browser | Open |
| Constrained covariance minimum variance | Portfolio What If? | Integrated; same cash/weight constraints | B/new browser; existing numerical tests | Open |
| `private_walkforward_v65.js` / `private_optimizer.js` | Models Strategy | Restored in shared UI with explicit rolling train/test windows | Existing optimizer/walk-forward tests; new public/private browser runs | Open |
| Supabase versioned notes and virtual transactions | Explore / Portfolio | Integrated with contextual controls and ledger | Hosted API, D/new browser; isolated mock writes only | Real persistence open |
| Existing `QF96` saved assessment codec | Explore saved research | Restored readable historical summaries and deletion indexes | Existing v96 tests; new archive browser fixture | Open |
| TF-IDF topics / negation-aware lexical news | Explore / Methods | Existing endpoint/UI retained; math and worked explanation added | `test_news_intelligence_v180.py`; independent outage browsers | Actual headlines open |
| `sec_peer_model.js` standardized financial similarity | Compare | Integrated in Compare with same-feature distances, eligible/excluded counts and editorial industry controls | Existing peer suite retained | Local source and browser integration verified; owner acceptance open |
| Forecast distributions / Monte Carlo / robustness engines | Models / Portfolio Analysis | Integrated SEC financial scenarios, covariance Monte Carlo and equal-date walk-forward robustness in Models / Portfolio | Existing forecast/optimizer/robustness suites retained | Local source and browser integration verified; owner acceptance open |
| ETF-proxy factors / optional French-factor study | Models Risk / Portfolio Analysis | Integrated independent ETF loadings and optional daily FF3 with chronological holdout in Models Risk | Existing v86/v87 tests retained | Eligible-data path and withholding verified; real input acceptance open |
| SEC filing revision archives / PIT / archive quality | Methods Data / deeper research diagnostics | Integrated replay, coverage, archive quality, historical robustness, attribution and integrity in Methods Data; optional files remain session-only | Existing v97–v120 Python/Node suites retained | Local integration verified; independent evidence remains optional |
| Original orchestration/policy/attribution/integrity modules | One-click research / model evaluation | Integrated candidate dossier, orchestration ledger, conditional research screens, counterfactual sensitivity, comparative and integrity summaries; no arbitrary score or stock ranking displayed | Existing v90–v170 suites retained | Local adapters verified; stale/incomplete inputs remain withheld |
| True saved-account valuation history and cash-flow-adjusted performance path | Portfolio Overview | Integrated server-verified persisted account marks, contribution and value curves, funding controls and P&L-change reconciliation; no invented history or unsupported percentage returns | Existing owner accounting tests; B mock | Genuine history starts at recorded server marks; unknown prior values are intentionally absent |
| Supabase MFA, proxy, RLS, server-side credentials | All private routes | Preserved; additive owner-gated snapshot route and safe health revision metadata; no authorization, SQL or proxy bypass | Full hosted/MFA/proxy suites | Owner MFA/logout open |

## Test and screenshot evidence

Repository environment was used for all Python commands. Browser/video inspection tools (`playwright==1.57.0`, `imageio-ffmpeg`) were installed into the existing local venv with approval; no application dependency was added. Chromium, Firefox and WebKit test desktop/mobile widths. Completion journeys use an isolated HTTPS origin with the actual generated CSP header and no network access to owner services. These are not physical-device acceptance results.

- `python -m pytest -q`: 580 passing; seven existing dependency deprecation warnings.
- `node --test web/tests/*.test.cjs`: 397 passing, including structured-error, retained-engine integration and contribution/P&L tests.
- `python -m ruff check .`, all browser/proxy JS syntax checks, privacy prepublish audit, public bundle audit and whitespace checks pass.
- Deterministic paired HTML/CSP rebuild verified by comparing both SHA-256 values before/after generation; still exactly three protected scripts.
- A/B/C/D browser journeys cover keyboard/Back, common-date comparisons, optimization/weights, owner accounting, structured errors, provider failures, source isolation and contextual notes/trades. C/D assertions were updated to test richer exhibits and contextual replacements; checks were not disabled.
- `tools/smoke_rebuild_browser.py`: desktop 1440×900 and mobile 390×844; public and private offline fixtures; all five routes; four Models categories × three phases; four Methods views; three Portfolio views; home search; structured 422 failure; non-SEC asset; missing feed; rolling study; notes/brief/archive; versioned virtual trade; public mode privacy; logout; no page overflow or uncaught JS errors. All network requests are aborted at the browser boundary; fixtures supply every owner request.
- Screenshots/gallery: `C:/Users/toris/OneDrive/Documents/ChatGPT/career/QuantForge-review/index.html`. Full route/subview matrix and error/saved-research examples. All private captures contain offline fixtures. Reviewed selected desktop/mobile charts, formula rendering and controls; full visual owner sign-off remains open.

## Completion engineering evidence

- `research_deep_v25.js` reuses the original numerical implementations through scoped adapters; it does not rewrite their arithmetic. `research_deep_ui_v25.js` presents their actual outputs in the existing five routes, with source/date context and unavailable states.
- Price/SEC valuation uses the existing owner-gated quotes, on-demand SEC company and capital endpoints. Ratios are independent of historical-price availability; public mode cannot fabricate them. Hypothetical cash-flow assumptions show their reported historical baseline, including negative or missing cash flow.
- Optional revision JSON and independent FF3 CSV are bounded, schema-validated and memory-only. They are never transmitted, stored or made mandatory. Import validation does not authenticate a file as original SEC or factor-library data.
- The additive `POST /api/private/valuation-snapshot` accepts only `expected_version`; owner/MFA checks and the original state-version guard run before complete fresh provider marks are written. It stores at most 365 observations in existing private JSON state; no SQL migration or new service.
- Snapshots retain total value, cash, net contributed capital, P&L and dated quote provenance. Deposits/withdrawals remain capital flows. Old, unrecorded account values are not reconstructed; irregular marks cannot establish time-weighted returns, so those percentages are withheld.
- Existing marked-value displays refresh after successful state writes. Notes support versioned edits and deletion, while legacy saved assessment records remain readable.
- Compare discovery now uses authenticated provider names as well as the selected-company context; public mode resets its universe and list to published SEC coverage.
- `/api/health` now includes contract `shared-research-v25` and a revision only when the supplied revision is exactly a 40-character lowercase hexadecimal SHA. Missing or malformed revision metadata becomes `not-reported`.
- New API tests cover proxy/owner denial, version conflict, stale/invalid/mismatched quotes, account conservation, cash-only deposits, bounded marks and safe revision metadata. Original MFA/security/numerical tests remain intact.
- The legacy B browser journey now logs in through the real private bridge using a mocked verified auth response, rather than toggling only a display flag. Accounting and outage assertions remain.
- `tools/smoke_completion_browser.py` covers deep engines, optional archive/FF3 success, successful observed quote/SEC-share ratios, public withholding, keyboard chart inspection, account snapshots/funding, note edits, provider-backed Compare selection and mode clearing in Chromium/Firefox/WebKit at 1440px and 390px.
- CI now installs the missing `requests` build dependency and all three test browsers, and runs the original A–D journeys plus both complete research journeys.

## Production / owner acceptance gates

| Item | Status and boundary |
| --- | --- |
| Local source and numerical/security regressions | Complete: 580 Python and 397 Node tests, Ruff, syntax, deterministic build, privacy/CSP and whitespace checks |
| Browser implementation | A–D plus full-route Chromium and completed-engine Chromium/Firefox/WebKit journeys; desktop/mobile emulation; no physical-phone claim |
| Independent optional evidence | Fully connected with strict withholding when missing, invalid, unaligned or incomplete; file authenticity and real research conclusions require owner review |
| Account history | Recording and persistence implemented; existing accounts start with no marks until the owner explicitly records them; no automatic real-account writes in tests |
| Live owner services | Manual real MFA, provider/feed/news entitlements, persisted note/edit/reload, funding/virtual trades and logout still require owner acceptance |
| API deployment | No deployment performed. Baseline Cloudflare API checks hit 429; new health contract/revision is available after an approved API release |
| Remote CI and static parity | Local CI fix prepared and tested locally; a new remote run and deployed-byte comparison require approved publication |
| GitHub source access | Repository remains private. In-app explanations stand alone; source references accurately state access requirements |
| Publication | No push, merge, deployment or repository-visibility change. Review code/screenshots and complete owner service checks before publishing |

The remaining items are external acceptance and publication gates, not hidden claims of live-provider or historical-data availability. Preserve the approved product and these tested guards during owner review.

Final frozen-build evidence: all six Chromium/Firefox/WebKit desktop/mobile completion journeys passed with the matching HTML/CSP artifact pair. A test-harness artifact race during an intermediate regeneration was corrected by freezing that pair for each run.
