# QuantForge V8.1.1 — Public research navigation and reviewer experience

## Rationale
The homepage label **Start here** sounded like onboarding, and two accordion sections hid supporting public pages while Financials and Dashboard remained visible. The public homepage also sent its third primary action to MFA-only personal research instead of a reviewer-accessible portfolio asset.

## Exact changes
1. Rename public sidebar entry **Start here** to **Overview**. The topbar reflects **Research overview**.
2. Display all nine public sections in one consistent always-visible grouped sidebar: **Financial research** (Overview, Company financials, Analysis dashboard), **Interactive models** (Portfolio simulator, Risk & allocation, DCF scenarios, Peer comparison), and **Methods & engineering** (Research methods, Data & engineering). Groups are labels, not inconsistent expandable accordions.
3. On small screens, present the same grouped buttons in responsive grids. No public route is hidden behind a group accordion.
4. Replace the homepage's third main action (private MFA-only tool) with a direct entry to **Research methods**. Keep **Private workspace** as a separate clearly labeled, MFA-protected navigation destination when the unified site is built.
5. Add a direct homepage GitHub source-and-tests link using safe `rel="noopener noreferrer"` behavior. No third-party script or hosted chart dependency was introduced.
6. Update the V8.0/V8.1 navigation regression checks to assert the new intended structure and preserve all their other requirements. Add four Python and three Node checks covering navigation, recruiter paths, provenance and MFA boundaries.

## Explicitly unchanged
- 94-company historical SEC Company Facts snapshot, source attribution, fiscal-year logic, missing data and data-provider rights boundary.
- All company financial charts, fiscal-year values, revenues, scenario projection limits and export behavior.
- Simulated public optimization and strategy illustrations and their labeling as hypothetical.
- Nine private workspace task views, MFA, private positions, research guide, market data retrieval and backend security.
- Three-protected-script CSP structure and security headers.

## Validation
This release is designed to run full repository Ruff, Pytest, Node, public build, source integrity, CSP and privacy checks before staging or pushing. GitHub CI is watched for the exact commit. After GitHub CI, check that Cloudflare Pages **Production** deployed the same commit; CI success alone is not proof of deployed production.

## Production acceptance
- Open production Overview: direct SEC, Dashboard and Research methods links all work.
- Public sidebar shows all nine routes under three headings; no folded sections.
- Confirm company search and reported data render for Microsoft, AMD, Adobe, and another sector.
- Change SEC metric between operating margin, net income, and free cash flow; inspect historical chart and values.
- Run a one-, three-, or five-year hypothetical revenue scenario; chart and table must distinguish SEC baseline from assumed future values.
- Confirm comparisons and CSV export; years, missing values and citation/provenance remain intact.
- Confirm portfolio optimization and walk-forward are labeled illustrative/simulated.
- Verify Research methods links to working source and test pages.
- Verify MFA on Private workspace and after sign-in: Overview, Virtual trades and Research guide & notes.
- On 1440px desktop, 800px tablet and ~390px phone, confirm navigation/buttons, charts and tables remain usable; inspect horizontal overflow and font readability.

## Career positioning
V8.1.1 is a credible public *research engineering portfolio* spanning financial data ingestion, SEC parsing, exploratory and comparative analysis, optimization/model diagnostics, and tested website deployment. It is **not** a Bloomberg/Robinhood/Fidelity substitute: historical company filings do not imply licensed real-time stock prices, predictive stock performance, a brokerage execution service, or financial advice.
