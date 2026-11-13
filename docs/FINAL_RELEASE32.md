# Final product and reliability release

Baseline: 9261bdedb8254d700d6bf30a2f666c0713f3513e. This document describes implementation; deployment and true owner/cold-start acceptance are recorded separately.

## Reliability

Render Free sleeps after inactivity and documents about a minute to resume, potentially serving an HTML startup page. Reported November 12 shutdown/startup and recovery without redeployment support a hosting availability failure; they do not establish an authentication failure. The existing proxy already converts non-JSON interstitials into unavailable responses. It cannot remove a persistent provider challenge.

This release bounds upstream health probes at eight seconds; the client checks readiness before sending credentials. It polls only the idempotent health read, with a two-minute deadline and cancellation on auth-epoch changes. Session checks use ten-second request timeouts and retain the existing outage recovery. Login is submitted once after readiness and is never automatically replayed after an uncertain response. MFA, enrollment and virtual-account writes retain their single-attempt behavior. A real JSON 401/403/429 is not treated as an invitation to retry authentication. Existing owner identity, AAL2, secure cookies, refresh handling and sign-out guards remain.

Tests distinguish simulated 100-second startup, persistent outage exhaustion, uncertain login, cancellation during wake, invalid credentials, session expiry, password-only MFA gating and logout races. Simulated tests do not establish a real production cold-start pass. No keepalive service or paid infrastructure was added.

## Product changes

Home has no chart or financial exhibit: one headline, one paragraph, direct company suggestions and a compact five-section overview. It uses the same eligible picker as Explore/Compare; selecting a suggestion immediately sets the shared company context. Exact name/ticker submissions open the matching company. Recent selections are deduplicated, and known saved-watchlist matches receive priority in empty-query private results. Suggestions remain listing metadata, not proof of financial coverage or market entitlement.

Private Company briefing now assembles an Investment research summary automatically from the selected company's actual covered figures, entitled historical risk, existing chronological predictive evaluation and current virtual-holding context. It separates favorable evidence, cautions, baseline/Brier comparison, next questions and thesis invalidation questions. Optional horizon and drawdown-review prompts remain tab-local and clear on sign-out; they are not durable personal profiles or suitability assessments. No universal score or automatic trade verdict is generated. Public mode removes the private summary contents.

The original legacy note-add route now refuses at the 100-record limit instead of truncating prior records. The existing append-only thesis and current shared note interfaces remain unchanged. No real owner data was modified.

## Preserved scope and limits

All five research sections, statistical/ML/risk/valuation/optimization/backtest engines, mathematical exhibits, SEC lineage, case study and source-aware missingness remain. No framework, paid API, schema or provider integration was added. Public market experiments remain synthetic; private failed market reads do not substitute simulated observations. The classifier predicts five-session direction, not a future share price or expected profit; weak signals remain withheld.

A wholesale SEC refresh, quarterly/TTM reconstruction, complete debt/share-value bridge, additional forecasting algorithms, durable personal preferences, broader watchlist management and a new durable transaction ledger are deferred. Existing dated coverage and bounded-history limitations remain visible; no new data freshness is claimed. A true after-idle production login needs observed hosting startup and owner-controlled MFA, without manual Render visits or restarts.

## Validation and rollback

Run full pytest/Node, Ruff, privacy/CSP/deterministic build, existing browser CI and tools/smoke_final_release32.py. Inspect Home and fixture-only private summary screenshots across five widths and three browsers. The new final suite covers simulated cold starts and private-content isolation; existing lifecycle tests preserve MFA and sign-out assurance.

Known-good rollback source is 9261bdedb8254d700d6bf30a2f666c0713f3513e. No migration or owner write is required for rollout or rollback. The FastAPI/backend source is unchanged from 9261bde; the release is frontend/proxy-only and can retain that compatible backend. Render Auto Deploy is disabled; if a backend rollout is performed, explicitly deploy and verify its revision. Final deployment IDs and CI links belong in the external release record after actual verification.
