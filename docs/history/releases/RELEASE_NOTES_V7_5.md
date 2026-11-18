# QuantForge V7.5 - Portfolio Model-Risk Clarity

**Scope:** A focused audit-driven correction to the existing private V7.4 allocation what-if. Not a new price feed, trading feature, valuation target, or market recommendation.

The interface and research export now separate cash-inclusive *allocation-bucket concentration* from *invested-only HHI* (HHI normalized across security positions, excluding virtual cash). An all-cash baseline has **undefined** invested-only concentration, not zero. Cash exposure and the largest position relative to invested assets are presented explicitly.

The risk note explains that cash is assigned zero price returns in this historical volatility comparison. Consequently, adding stock exposure can increase market volatility **even as cash-inclusive HHI falls**. The change is not an expected-return forecast or a guarantee of future risk. Equity risk annualization cannot be applied to mixed/crypto holdings; the historical comparison is withheld for those cases.

The JSON schema is backward compatible (`quantforge.allocation-research.v1`): old keys remain, and new descriptive fields distinguish invested-only concentration and historical volatility direction. Research exports continue to omit individual portfolio balances, units, budgets, trade details, and raw licensed observations.

**Unchanged:** Supabase Auth/TOTP, private ownership checks, API endpoints, Alpaca keys, SEC source snapshots, portfolio accounting/trades, prices, notes, virtual ledger.

**Release gate:** Dry-run, Ruff, full pytest, all web JavaScript tests, compiled bundle/CSP audit, prepublication privacy review, clean allowlisted Git diff, CI Python 3.11/3.12, then live verification.
