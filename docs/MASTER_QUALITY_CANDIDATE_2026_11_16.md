# Master quality candidate — November 16, 2026

Status: locally implemented and validated; not published. The recovered production remains separate from this candidate. Initial audit: [priorities and baseline](MASTER_QUALITY_INITIAL_AUDIT_2026_11_16.md). Infrastructure: [deployment and rollback](VERCEL_RECOVERY_DEPLOYMENT.md). Career review: [evidence and interview route](CAREER_EVIDENCE_2026_11_16.md).

## Concrete improvements

The recovery is now maintainable source: exact reviewed proxy origins, shared FastAPI runtime, isolated reproducible Vercel packaging, source manifest and no local provider caches in Git. This preserves the already-working Pages → Vercel Hobby → Supabase route; it does not revive the superseded Render User-Agent experiment.

Home now leads directly into a business-to-evidence research journey, with five usable destinations and a reproducible case study. Explore presents an assessment before supporting evidence, using keyboard-accessible tabs instead of a long duplicated report. The main Analyze action remains in the research toolbar. Compare labels use a separate legend so coincident observations do not produce overlapping text. Models retain Results/Evaluation/Method and native MathML. Portfolio retains its three workflows and now separates recorded basis-dependent gains from contribution accounting. Methods keeps source/test exhibits and accurately describes the recovered infrastructure.

Private synthesis combines eligible annual financial evidence, matching observed-price valuation, historical downside, existing held-out model evaluation and actual marked holding context. A company study can include up to three actual held names alongside the candidate and benchmark. Results are invalidated on company revision, owner-state version or authentication changes. Public cannot inherit owner findings.

## Analytical policy and boundaries

The assessment is a deterministic interpretation of evidence, not a trained investment adviser or arbitrary weighted score. It distinguishes strengths, cautions, disagreements, unavailable domains and follow-up questions. There is no buy/sell verdict or calibrated chance of success. Completed calculations do not imply sufficient current decision evidence.

Annual financial evidence older than 550 days and market observations older than seven days trigger disclosed review policies; these are research heuristics, not regulatory deadlines. Same-accession balance inputs are required for eligible ratios. Negative equity is a caution, not a low leverage benefit. Price/FCF comparisons are dated observed multiples; the DCF remains a cash-flow-proxy scenario without a complete enterprise/equity/per-share bridge. Existing model screening requires at least 12 matured test windows, accuracy at least the historical baseline and Brier better than baseline by 0.005. This conservative screening is not proof of predictive skill. Held-name correlation requires at least 60 common returns; 0.80 is a disclosed overlap-review heuristic, not a universal diversification rule. An indicated position shock is hypothetical and does not forecast loss.

Single-asset daily crypto volatility now uses 365 observations per year, including rolling, split-sample and block-resampling calculations; equity uses 252. Crypto daily-gap inputs are rejected. Multi-asset Compare still supports the existing aligned equity scope; mixed-calendar/crypto comparison is not advertised as implemented. Daily tail loss and drawdown are not multiplied by an annualization factor.

## Virtual accounting

`cloud/paper_accounting.py` maintains a versioned, namespaced JSON book in the existing protected state; no database migration or owner record modification was performed. Entry fees enter total basis. On a partial sale, cents of average basis are allocated in proportion to units; a final sale consumes the entire remaining basis. Exit fees reduce proceeds before realized P&L. Unrealized P&L requires a quote and verified basis for that marked position. Cumulative account gain still equals marked value less net contributions; deposits are not profits.

The previously unused legacy cost_basis field is not treated as evidence. Legacy unknown basis remains unknown; tracked realized gain may cover only later activity. Closing an unknown position and subsequently buying establishes basis for the new position, not a reconstructed historical return. This is virtual bookkeeping, not tax reporting. Existing expected-version checks and request-id reconciliation remain; a replay does not apply accounting twice.

Stale-quote preview refusals now disclose only whitelisted observation timestamp, age, source and freshness limit. The stock/fund limit remains 900 seconds and crypto 300 seconds. Closed markets do not make an old trade fresh. Authentication errors do not reveal provider observation context; raw error objects never become user-facing strings. No real order route exists.

## Verification evidence

| Check | Result and scope |
| --- | --- |
| Python | 646 passed, seven pre-existing deprecation warnings; security, numerical, state, fee/basis, idempotency, packaging and revision guards |
| JavaScript | 445 passed; retained engines plus nine contrasting assessment cases, basis and safe stale-context fixtures |
| Ruff / public CSP / prepublish | Passed; strict script hashes and privacy/source/document-link checks |
| Rendered components | 444 checks at 320/390/768/1024/1440 CSS px and 720 CSS px at 2x density; no recorded overflow/control clipping/chart-text/console failures |
| Cross-browser journeys | 15 journeys across Chromium/Firefox/WebKit and five widths |
| Focused new workflows | Six Chromium/Firefox/WebKit journeys at 390/1440; matched valuation, held correlation, summary order, accessible tabs, stale refusal, no transaction POST, Public isolation |

Reproducible commands: `python -m pytest -q`; `node --test` with all `web/tests/*.test.cjs`; `python -m ruff check .`; `python tools/build_unified_site.py`; `python tools/audit_public_bundle.py`; `python tools/prepublish_check.py`; `python tools/smoke_final24_layout.py`; `python tools/smoke_final_release32.py`; `python tools/smoke_master_quality_v33.py`. Python checks used the existing installed Python 3.12 environment from the original checkout; this recovery checkout has no separate .venv. Browser owner state and financial examples are isolated fixtures, not exported records.

The original UX recordings were visually sampled after the initial audit; see the audit for exact scope. Screenshots cover the actual candidate artifact, with controlled data. Layout density emulation is not native browser zoom. Native zoom and a full assistive-technology audit remain unverified.

## Live baseline versus candidate acceptance

Anonymous direct API health and proxied health returned 200; direct unauthenticated private state returned 403, signed-out session returned false. Production Public HTML matched the preserved recovery baseline hash. In the normal signed-in Chrome production session, a read-only company analysis completed and MFA remained verified. No notes, holdings, funding, transactions or authentication settings were changed. This verifies the recovery baseline, not the unpublished candidate.

Vercel dashboard showed Hobby and Ready for existing deployment 4Wg5T2A4j7XBYB8ByqsusdTJiPqo. Its CLI deployment reports revision not-reported; do not claim it runs this candidate commit. Standard Protection and one masked automation bypass entry were observed. No bypass was read, used or revoked. Computer Use stopped because it could not establish the current Windows browser URL confidently; native zoom and bypass removal remain pending. Render support packets remain unsent.

## Release gate

No push, merge or deployment in this assignment. Publication requires approval for the exact candidate, one appropriate CI run, preservation of current Pages/API rollback deployment identifiers, free-plan verification, then API-first release and Pages acceptance. Verify the expected health revision, anonymous denial, owner-controlled MFA and candidate read-only analysis. Any owner persistence/trade acceptance must be separately controlled; mocks do not prove live persistence. Rollback returns to the existing recovered artifacts, not Render-only routing, with no Supabase reset. See the deployment guide.
