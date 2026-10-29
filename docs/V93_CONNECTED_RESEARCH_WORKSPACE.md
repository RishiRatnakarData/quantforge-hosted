# QuantForge V9.3 — Connected research workflow and decision briefing

**Baseline:** Verified GitHub V9.2 `d862868114619ddc144958824c8791d9f8146381`.

## Why this release is deliberately larger

The private workspace had a correct automated research flow, but its older manual Decision Center and V7.9 Research Guide produced separate, competing summaries. V9.3 consolidates the interaction layer without throwing away existing models or adding an outside LLM.

### What changes

1. **Research Hub** is the front door. Its existing V9.1 orchestrator, V9.0 decision policy and V9.2 evidence review remain the only source for a new *linked* research briefing.
2. The visible **Previously completed research review (manual)** accordion is removed. Legacy calculation elements remain hidden for existing compatibility and event hooks; nothing is marketed as a second decision center.
3. A session-scoped **research ribbon** appears throughout the protected workspace: last linked candidate, model coverage, current or invalidated status, and direct routes to Research Hub and the briefing.
4. **Advanced Research Lab** displays eligible, completed, failed, or unavailable research methods **from the same orchestration run**, with direct links to the underlying specialist tools. It does not falsely claim all methods were completed.
5. **Research Briefing & Notes** presents the original action and reasons, supporting and opposing evidence, conflicting findings, mandatory model failures, observed-price comparison, evidence provenance, method execution audit and meaningful follow-up actions. Each evidence/method entry links to its specialist page. The preexisting V7.9 session guide is retained as a clearly labeled **optional session overview** rather than a competing investment recommendation.
6. A pure `QFPrivateResearchBriefV93` transformer creates a **bounded, account-balance-free report** from the validated V9.1 result and V9.2 post-policy review. Exports carry only research scope, observed historical percentage comparisons, source tags, assumptions, coverage, and statements—not raw price arrays, holdings, cash amounts, credentials, or broker order information.
7. Changing the selection, history, session, main policy settings or walk-forward assumptions invalidates the linked research briefing. Opening a new tab does **not** recompute the models or invent fresh observations.
8. Mobile-friendly responsive grids and report sections were added without changing public-site navigation, private routes, MFA, or hashed CSP script count.

## Distinction between automated, optional and manual research

The Research Hub executes eligible calculations and generates the linked report; laboratory tools can still be run independently. Independent recalculations must not silently overwrite the published session briefing—the user must run Research Hub again to reconcile the latest eligible data and constraints. A link to a model does not certify a model result, and an ineligible model is displayed as such.

## Boundaries and remaining limitations

- A single **focus company** receives a detailed SEC/valuation/portfolio analysis. The other 2–5 selected securities are compared on matched historical price observations; this is not comprehensive multi-issuer financial statement scoring or a defensible stock ranking.
- Policy thresholds are still user-selected research assumptions, not empirically calibrated expected returns, suitability recommendations, confidence probabilities, or validated predictions.
- Factor analysis requires the user's independent factor import. V9.3 does not invent factor inputs or offer an automatic real trading facility.
- This is a linked *in-memory research report*, not a durable audit database or cross-device saved research history.
- Authenticated provider, account, live MFA, and Cloudflare acceptance still require manual browser verification after publishing. GitHub CI success alone does not prove a live user workflow.

## Acceptance goals

- Clear five-section navigation with Research Hub and Research Briefing names, not multiple decision centers.
- Old manual summary accordion cannot be seen, though compatibility anchors still exist in hidden markup.
- In an authenticated session, complete a 2–5-investment analysis with one candidate, then open the linked briefing and each specialist method without rerunning models.
- Inspect the Lab statuses and verify they match the executed V9.1 ledger, including optional failures and ineligible factors.
- Change candidate or settings to ensure the ribbon/brief are invalidated and export is disabled until another completed assessment.
- Confirm no new network paths, automatic brokerage orders, credential exposure, or hosting fees.
- Verify full Python, JavaScript, Ruff, SEC, CSP, privacy and exact-source inventory checks locally before a publication push.
