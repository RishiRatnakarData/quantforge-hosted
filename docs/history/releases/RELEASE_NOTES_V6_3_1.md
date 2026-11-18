# QuantForge V6.3.1 — Risk–Return Chart Legibility

**Scope:** private historical optimizer display only. No change to historical calculations, portfolio weights, authentication, market data, credentials, SEC filings, database or virtual transactions.

## Correction

- Handle repeated or near-identical annualized volatility in constrained portfolio scenarios by giving the chart an explicit minimum horizontal and vertical domain.
- Place ticks with percentage labels on both axes instead of silently falling back to an arbitrary scaling denominator.
- Deduplicate identical scenario points; overlay distinctive equal-weight and selected-optimized markers.
- Explain when weight caps and the selected investment set generate near-identical volatility rather than displaying a confusing line pinned to the chart edge.
- Reject nonfinite comparison inputs with a clear unavailable-data message.

The marks are **in-sample portfolio candidates**, not a forecast or a statistically established efficient frontier. Optimized historical volatility may improve while maximum drawdown or other downside metrics worsen.

## Validation

Run the Python suite, Ruff, Node tests (including `web/tests/private_optimizer_chart.test.cjs`), unified site build and prepublication check before publishing. The code has no new API dependencies.
