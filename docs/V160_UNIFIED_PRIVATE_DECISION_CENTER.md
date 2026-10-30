# V16.0 — Unified Private Decision Center

## Product organization

V16.0 is a **private-workspace-only** usability and evidence-interpretation release, building on the published V15.0 research engine. The existing public website and all specialist analysis modules remain available. The primary nav is now:

1. **Decision Center** — a single actionable research dashboard, one-click current analysis, a company selector and explicit risk-constraint settings.
2. **Discover & Compare** — company screening, individual-company financial and factor studies.
3. **Advanced Research** — historical market data, valuation/scenarios, portfolio optimization, backtesting, walk-forward methods, filing-lineage and audit details.
4. **Portfolio & Reports** — virtual positions, scenario trades, linked research briefing, and saved research notes.

Historical diagnostics and the optional archive file picker are moved into **Advanced Research**, behind expandable details. The standard Decision Center uses the application's existing SEC snapshot and the authenticated market-data provider, and its existing orchestration already loads aligned prices for the chosen universe. No local file upload is required for this **standard assessment**.

### Why the historical archive is still optional

The user's `data/sec_filing_revisions_v98.json` exists on their Windows machine and was intentionally excluded from publicly deployed files. A static website cannot automatically read that private local file after sign-in. V16.0 therefore does not claim that the full original-versus-amended SEC archive is automatically available remotely. The deep point-in-time revision study remains an **optional advanced-only** research tool; historical coverage and robustness methods must continue to report missing evidence when the archive is absent. Fully automated private historical archive ingestion would require an explicitly authenticated server-side data pipeline and associated security review.

## Explanation of the visual score

The new **Observed evidence alignment** number is a deterministic rule-based *screening rubric*, not a calibrated statistical prediction or stock rating. It uses only the existing completed assessment's directional conclusions:

| Domain | Weight | Source |
|---|---:|---|
| Business health | 25 | SEC-derived annual growth/profitability/cash-generation measures |
| Valuation context | 25 | Matched observed-price financial ratios |
| Downside risk | 20 | Historical drawdown and loss-tail screening |
| Portfolio fit | 20 | Current virtual exposure and user-selected limits |
| Strategy resilience | 10 | Historical whole-universe walk-forward performance |

Each domain's existing result is mapped to `supports` = 1.0, `mixed` = 0.5, `cautions` = 0.0. `available` indicates measurement without directional support and **does not** count as supportive. `unavailable` is excluded from the directional denominator; missing **required** history/fundamentals/downside/portfolio evidence or a mandatory model block withholds the score entirely. Fewer than 40 eligible directional weight-points also withholds it. Scores are rounded percentages of weighted eligible directional-screen alignment. The separate **Method coverage %** is completed methods divided by total methods, not accuracy or source completeness.

Color is a compact research cue, **not a broker instruction**:

- **Green**: all five categories provide directional evidence, no required block, alignment ≥70. Extended historical integrity can still be limited and is separately labeled.
- **Amber**: mixed findings, incomplete optional studies, insufficient directional categories for green, or moderate alignment.
- **Red**: required evidence is missing/blocked or documented downside screens are unfavorable enough to place alignment below 35.

The existing research engine's text decision and rationale are displayed verbatim as the primary qualitative assessment, including its constraints and objections. V16.0 does not invent new price targets or execute orders. Comparison visuals show **observed historical drawdowns and price-only changes**, not a cross-company stock-buy ranking.

## Invalidation and privacy

The dashboard is derived from the *current* linked research briefing, V13 integrity audit and V14 workflow state. A changed investment universe, risk setting, history, logout, or invalidated assessment clears the prior score. Raw price arrays, holdings, account identifiers, credentials, notes and SEC source accessions are omitted from V16.0's sanitized export. All new scoring logic is pure JavaScript without network I/O or storage. The current MFA/provider and saved-note browser flows remain unchanged and require manual owner sign-off.

## Quality gates and sign-off

- Node regression suite and full Python regression (Windows runtime) must pass.
- Ruff, CSP bundle and secret/privacy checks must pass.
- Generated `public/index.html` and `public/_headers` must be deterministic.
- Exactly the approved release-source and generated files may be staged.
- GitHub CI must pass and production HTML must match locally generated content after publishing.
- **Still not automatically verified**: real MFA login, authenticated Alpaca history, optional archive browser import, saved-note persistence and logout. Do not mark them passed until manually exercised.

## V16.0 FIX1: legacy contract migration

The navigation intentionally changes from five named groups to four consolidated groups.
Five earlier Python UI regression modules previously enforced the retired five-group
names/count; they now assert the four-group structure while keeping all their
original MFA, provider, research-route, CSP, and output integrity checks.
The private view query selector is rewritten with equivalent CSS selector syntax
to avoid a spurious substring match in generated-HTML uniqueness checks.
This is an assertion migration, not a relaxation of authentication or finance checks.
