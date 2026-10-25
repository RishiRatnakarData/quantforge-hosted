"""Create the recruiter-facing stock site from audited public or locally supplied data."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quantforge.data.storage import sha256_file
from quantforge.public.site import _company_evidence

from .marketdata import BENCHMARK, validate_bars


def build_stock_site(*, stock_dir: Path, output: Path,
                     sec_dir: Path | None = None, local_only: bool = False) -> dict:
    stock_dir, output = Path(stock_dir), Path(output)
    manifest = json.loads((stock_dir / "stock_manifest.json").read_text(encoding="utf-8"))
    bars_path = stock_dir / "stock_bars.csv"
    if sha256_file(bars_path) != manifest["data_sha256"]:
        raise ValueError("Stock observations do not match provenance fingerprint")
    if manifest["data_origin"] not in {"synthetic", "cc0_kaggle_2017", "user_supplied_local", "alpaca_personal_private"}:
        raise ValueError("Unrecognized data origin")
    if not manifest["publication_allowed"] and not local_only:
        raise ValueError("Source license has not cleared public redistribution. Use --local-only.")
    if manifest["data_origin"] in {"user_supplied_local", "alpaca_personal_private"} and not local_only:
        raise ValueError("Cannot publish private BYO stock observations")
    bars = validate_bars(pd.read_csv(bars_path), min_sessions=10)
    if int(bars["date"].nunique()) != manifest["sessions"]:
        raise ValueError("Session count mismatch")
    if list(sorted(bars["symbol"].unique())) != manifest["tickers"]:
        raise ValueError("Ticker set mismatch")
    company = _company_evidence(sec_dir) if sec_dir else None
    dates = [str(pd.Timestamp(x).date()) for x in sorted(bars["date"].unique())]
    open_panel = bars.pivot(index="date", columns="symbol", values="open")
    close_panel = bars.pivot(index="date", columns="symbol", values="close")
    prices = {"dates": dates, "symbols": sorted(set(bars["symbol"]) - {BENCHMARK}),
              "benchmark": BENCHMARK,
              "open": {s: [round(float(v), 6) for v in open_panel[s]] for s in manifest["tickers"]},
              "close": {s: [round(float(v), 6) for v in close_panel[s]] for s in manifest["tickers"]}}
    data = {"prices": prices, "manifest": manifest, "valuation": company,
            "local_only": bool(local_only)}
    template = Path(__file__).with_name("stock_template.html").read_text(encoding="utf-8")
    html = template.replace("__APP_DATA__", json.dumps(data, separators=(",", ":"),
                                                     allow_nan=False).replace("<", "\\u003c"))
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(html, encoding="utf-8")
    source = {
        "release": "4.3.0", "purpose": "interactive historical stock replay + current-stock explorer",
        "dataset_origin": manifest["data_origin"],
        "market_data_sha256": manifest["data_sha256"],
        "publication_allowed": bool(manifest["publication_allowed"] and not local_only),
        "trading_model": "Decision at close; execution at following observed open; 5bp per-side turnover default",
        "price_warning": "Back-adjusted prices are not point-in-time executable quote levels",
        "latest_market_widget": "TradingView (independent third-party embed; quotes may be delayed)",
        "sec_included": bool(company),
        "limitations": manifest["limitations"],
    }
    (output / "evidence.json").write_text(json.dumps(source, indent=2), encoding="utf-8")
    (output / "CASE_STUDY.md").write_text(
        "# QuantForge — Stock Simulator & Financial Research\n\n"
        "The main artifact is the interactive `index.html`, not a research PDF.\n\n"
        "The historical replay queues decisions at the close and fills on the following "
        "session's adjusted open; it charges 5bp per side by default and compares a "
        "buy-and-hold SPY benchmark. Other analytics include drawdown and volatility.\n\n"
        f"Data origin: **{manifest['data_origin']}**. "
        "See `evidence.json` and `stock_manifest.json`. Current charts use an independent "
        "TradingView widget and are not the backtest feed.\n\n"
        "Important limitations: a retrospectively chosen universe is survivorship-biased; "
        "dividend-adjusted historical price bars are total-return proxies, not executable "
        "point-in-time opening prices. No borrowing, tax, or market-impact model. "
        "A game is not proof of out-of-sample alpha or an investment recommendation.\n",
        encoding="utf-8",
    )
    (output / "stock_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"url": str((output / "index.html").resolve()),
            "market_origin": manifest["data_origin"],
            "observations": len(dates), "sec_included": bool(company)}
