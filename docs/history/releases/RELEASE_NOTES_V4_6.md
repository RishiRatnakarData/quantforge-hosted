# QuantForge V4.6 — My Investment Desk

V4.6 replaces the general-consumer-style homepage with a restrained, single-user research workstation. **It is not a public investing service or financial adviser.** The portfolio, risk and DCF engines are inherited from V4.5; this is a product/experience refinement, not a claim of new model performance.

## What's changed

- Sidebar navigation and readable, compact layout; independent mobile layout.
- Home view centered on the private paper portfolio, fast ticker research, saved watchlist and core workspaces.
- Investment rules in a collapsible editor instead of an onboarding questionnaire.
- Company/research pages use neutral financial language and optional technical definitions, not a finance course.
- Standalone fully fictional interactive preview, no credentials needed.
- Local-only backend, IEX quote limitations and safe private-data boundary unchanged.
- Existing algorithmic implementations and finance models remain available with their tests.

## Not included

No public deployment of personal holdings or market data, no real brokerage orders, no invented historical return series, no completed live Alpaca integration, no research paper, no claim of professional advice.

## Run

From the inner project folder (the one with `pyproject.toml`):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m quantforge investment-desk --demo --db .private\demo.sqlite3
```

Open `http://127.0.0.1:8765/` while the server is running. All prices in `--demo` are fictional. For private current-market use, follow the Alpaca credential instructions in README; never upload or paste secrets.
