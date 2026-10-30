# QuantForge — Company comparison and beginner-first research

## Public company comparison

- Uses the published, dated SEC Company Facts snapshot and per-metric filing accessions. Does not replace missing figures with zeros or generate pseudo-SEC filings.
- Compares each peer on the **same** available ratios: annual revenue growth, operating margin, net margin and free-cash-flow proxy margin. It prefers four ratios; a three-ratio comparison is labeled partial; a two-ratio comparison is labeled limited. A valid comparable peer group must include at least three issuers including the selected issuer.
- Uses broad, **editorially assigned** industry group names as a filter. They are not presented as an official SEC sector field. Falls back to an explicitly labeled broader search when too few peers qualify in one group.
- All standardized distances describe financial-statement similarity, **not** future returns, price targets, performance, risk-adjusted quality or machine-learned investment probability. Unavailable firms are directed to Company Financials.
- Both a bar visualization and numeric comparison remain available; fiscal-year comparability, date cutoffs and partial financial coverage are explained.

## Authenticated beginner-first research

- The primary Research page offers one shared company selection (two to five), one **Run complete research** action, and a single compact results page. Users can remove a selection directly. Portfolio, Saved Reports, and Advanced Research are separate, concise destinations.
- The orchestrator loads shared history, optimization, backtesting, walk-forward and robustness inputs once where eligible. It evaluates each selected company's SEC fundamentals, dated provider quote, risk and portfolio evidence separately; it does not reuse another company's dossier or report a model as executed when it was not.
- Candidate-specific optional factor checks not reexecuted in the comparative pass are labeled incomplete. Missing data and violated hard risk limits cannot be colored positive. A descriptive screen is **not** a predictive machine-learning stock model or an instruction to trade.
- Main results use a short explanation, screening constraints, available supporting/contradictory findings and historical maximum drawdown; detailed assumptions, diagnostics and method traces remain in Advanced Research.
- The research action is **not** a brokerage order and adds no generative-AI API or recurring subscription requirement. Company information is available only within the authenticated workspace.

## Validation and remaining manual sign-off

- Deterministic public site build and strict three-script Content Security Policy, full Python/JavaScript regression suites and publication/privacy audits.
- Browser smoke checks use local content and seeded test fixtures. They **do not** verify live MFA, Alpaca quote accuracy, account synchronization, saved-note persistence, private archive import, device accessibility, or the mathematical reliability of future forecasts.
- Manual acceptance must validate private authentication, each selected company's data source, market-history reuse, ineligible-model handling, portfolio effects, save/delete/report, mobile navigation, and sign-out.
