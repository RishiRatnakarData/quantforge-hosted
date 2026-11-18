# QuantForge 4.5 — Your Investment Decision Companion

A redesign built around the first-time investor's question: **"What am I considering, what could go wrong, and how will it affect my money?"**

**NEW**
- Calm editorial-style, responsive interface in place of the rectangular trading dashboard; no external UI framework, third-party images, or paywalls
- Private goal/time-horizon/loss-comfort preferences and a virtual cash-reserve choice
- One-page what-if decision analysis with precise portfolio exposure, reserve flags, dollar-denominated stress losses, quote attribution, timestamps, and per-asset explanations
- Saved watchlist and research journal stored locally in SQLite
- Guided action flow: purpose → research → portfolio impact → virtual trade → review the reasoning
- Existing paper-only ledger, SEC-based Microsoft DCF, risk simulation and quant research modules preserved
- Offline fictional demo requires no Alpaca account and makes no real-market claims

**NOT PRESENTED AS CURRENT CAPABILITIES**
- No personalized investment recommendations, actual broker orders, market-wide realtime consolidated quotes, automatic crypto due diligence, actual ETF constituents, calibrated ML stock forecasts, or complete historical return statistics
- Older forecasting and advanced portfolio math remain available as separate research modules, not interactive buy/sell signals
- Public GitHub demo must exclude private licensed market data, user database, and API keys

**VERIFICATION:** Run Python `pytest`, Ruff and the interactive demo locally after installation. Live authenticated Alpaca IEX and venue-specific crypto retrieval require user's own credentials and have not been tested with their account.
