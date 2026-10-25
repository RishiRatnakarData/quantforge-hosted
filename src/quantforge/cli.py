"""Windows-friendly local command line entry point."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

import pandas as pd
import requests

from quantforge.backtesting.portfolio import compare_strategies
from quantforge.data.contracts import make_complete_panel, simple_returns
from quantforge.data.simulation import simulated_market
from quantforge.data.sources import fred_vintage, read_market_csv
from quantforge.data.storage import sha256_file, write_analytics, write_json
from quantforge.data.tiingo import DEFAULT_ETFS, load_tiingo_history
from quantforge.desk.server import run_investment_desk
from quantforge.factors.french import (
    descriptive_factor_regression,
    read_french_five_factor_daily_archive,
)
from quantforge.financials.annual import download_companyfacts
from quantforge.financials.demo import synthetic_companyfacts
from quantforge.integration.v4 import run_v4_integration
from quantforge.live.local_app import serve_personal_desk
from quantforge.public.analytics import evaluate_fx
from quantforge.public.ecb import fetch_ecb, save_raw_ecb
from quantforge.public.site import build_public_site
from quantforge.reporting.dashboard import write_demo_dashboard
from quantforge.research.study import run_v1_study
from quantforge.research.v2 import run_v2_study
from quantforge.research.v3 import run_v3_study
from quantforge.risk.measures import coverage_table, rolling_risk_forecasts
from quantforge.simulator.marketdata import (
    create_replay_data,
    kaggle_archive_bars,
    synthetic_bars,
    validate_bars,
)
from quantforge.simulator.website import build_stock_site


def run_research(
    prices: pd.DataFrame,
    *,
    output: Path,
    source: str,
    vendor: str,
    price_basis: str,
    input_sha256: str | None = None,
    lookback: int = 126,
    source_details: dict | None = None,
) -> dict:
    """Run the first baselines and record all data and experiment assumptions."""
    panel = make_complete_panel(prices)
    returns = simple_returns(panel)
    if len(returns) <= lookback:
        raise ValueError("Input history is shorter than the evaluation/lookback requirement")
    output.mkdir(parents=True, exist_ok=True)
    tidy_returns = returns.rename_axis("date").stack().rename("simple_return").reset_index()
    storage = write_analytics(output, prices, tidy_returns)
    # This frictionless daily equal-weight proxy is for forecasting coverage ONLY;
    # the investable accounting strategies below include drift/rebalance costs.
    proxy = returns.mean(axis=1)
    forecasts = rolling_risk_forecasts(proxy, lookback=lookback)
    coverage = coverage_table(forecasts)
    paths, comparisons = compare_strategies(returns, lookback=lookback)
    for file, frame in (
        ("risk_forecasts.csv", forecasts),
        ("risk_coverage.csv", coverage),
        ("portfolio_paths.csv", paths),
        ("portfolio_comparison.csv", comparisons),
    ):
        frame.to_csv(output / file, index=False, float_format="%.12g")
    label = "SIMULATED DEMO — NO HISTORICAL CLAIMS" if source == "simulation" else f"EXTERNAL DATA — {vendor}"
    write_demo_dashboard(forecasts, paths, output / "research_dashboard.html", label=label)
    summary = {
        "dataset_type": source,
        "source": vendor,
        "price_basis": price_basis,
        "model_status": "V1 preliminary baselines; NOT advanced model research",
        "assets": list(panel.columns),
        "price_observations": len(prices),
        "return_dates": len(returns),
        "evaluation_dates": len(forecasts),
        "date_min": panel.index.min().date().isoformat(),
        "date_max": panel.index.max().date().isoformat(),
        "coverage": coverage.to_dict(orient="records"),
        "portfolio_comparison": comparisons.astype(object).where(pd.notna(comparisons), None).to_dict(orient="records"),
        "disclaimer": (
            "Deterministic simulated prices, with intentionally specified variance shift; "
            "never represent these results as investment evidence."
            if source == "simulation"
            else "External source provided by researcher; verify licensing, survivorship, total-return adjustments and publication timing before interpreting findings."
        ),
    }
    manifest = {
        "project": "QuantForge",
        "release": "0.2.0",
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
        "data_origin": source,
        "vendor": vendor,
        "original_input_sha256": input_sha256,
        "price_basis": price_basis,
        "lookback_trading_days": lookback,
        "risk_confidence": 0.95,
        "ewma_decay": 0.94,
        "rebalance_trading_days": 21,
        "trading_cost_bps_one_way": 5,
        "market_calendar": ("XNYS verified against exchange_calendars" if source == "external_tiingo"
                            else "Observed input trading dates; simulation uses weekdays only"),
        "currency": "Input provider's units; demo is arbitrary index levels",
        "storage": storage,
        "no_interpolation": True,
        "universe_construction": "Fixed research symbols / complete panel; not survivorship corrected",
    }
    if source_details is not None:
        write_json(output / "source_manifest.json", source_details)
        manifest["source_manifest"] = "source_manifest.json"
    write_json(output / "summary.json", summary)
    write_json(output / "manifest.json", manifest)
    return {"summary": summary, "manifest": manifest}


def write_factor_report(output: Path, prices: pd.DataFrame, archive: Path) -> dict:
    """Ex-post daily risk-factor exposures; cannot be traded as same-day signals."""
    factors = read_french_five_factor_daily_archive(archive)
    returns = simple_returns(make_complete_panel(prices))
    exposures = {}
    for symbol in returns.columns:
        exposures[str(symbol)] = descriptive_factor_regression(returns[symbol], factors)
    factors.to_csv(output / "daily_factors_ex_post.csv", index=False, float_format="%.12g")
    result = {
        "source": "Kenneth French Data Library 5 factors daily",
        "archive_sha256": sha256_file(archive),
        "data_status": "ex_post_descriptive_only_not_point_in_time_signals",
        "assets": exposures,
    }
    write_json(output / "factor_exposures.json", result)
    return result


def parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser(description="QuantForge reproducible research tooling")
    command = main.add_subparsers(dest="command", required=True)
    demo = command.add_parser("demo", help="Deterministic, clearly SIMULATED offline validation")
    demo.add_argument("--rows", type=int, default=330)
    demo.add_argument("--seed", type=int, default=20261022)
    demo.add_argument("--output", type=Path, default=Path("outputs/demo"))
    demo.add_argument("--lookback", type=int, default=126)
    csv = command.add_parser("ingest-csv", help="Run baselines on your licensed daily price CSV")
    csv.add_argument("--path", type=Path, required=True)
    csv.add_argument("--vendor", required=True, help="Actual provider/source")
    csv.add_argument(
        "--basis", required=True,
        choices=["total_return_index", "dividend_adjusted_close", "split_adjusted_close", "unadjusted_close"],
    )
    csv.add_argument("--output", type=Path, default=Path("outputs/market"))
    csv.add_argument("--lookback", type=int, default=126)
    real = command.add_parser("tiingo", help="Private real-data research with Tiingo EOD")
    real.add_argument("--symbols", nargs="+", default=list(DEFAULT_ETFS))
    real.add_argument("--start", default="2010-01-01")
    real.add_argument("--end", default="2025-12-31")
    real.add_argument("--cache-dir", type=Path, default=Path("data/private/tiingo"))
    real.add_argument("--output", type=Path, default=Path("outputs/real_etfs"))
    real.add_argument("--lookback", type=int, default=126)
    real.add_argument("--offline", action="store_true", help="Use immutable cached snapshots only")
    real.add_argument("--refresh", action="store_true", help="Replace snapshots from provider")
    real.add_argument("--french-archive", type=Path, help="Downloaded official daily five-factor ZIP")
    macro = command.add_parser("fred-vintage", help="Retrieve one as-of ALFRED vintage")
    macro.add_argument("--series", required=True)
    macro.add_argument("--as-of", required=True)
    macro.add_argument("--start", required=True)
    macro.add_argument("--output", type=Path, default=Path("outputs/fred_vintage"))
    v1 = command.add_parser(
        "v1-risk", help="Private risk study using existing V0.2 development prices"
    )
    v1.add_argument("--input-prices", type=Path, required=True,
                    help="V0.2 outputs/real_etfs/prices.csv (NOT full provider prices)")
    v1.add_argument("--source-manifest", type=Path, required=True,
                    help="V0.2 outputs/real_etfs/source_manifest.json")
    v1.add_argument("--output", type=Path, default=Path("outputs/v1_risk"))
    v1.add_argument("--risk-window", type=int, default=252)
    v1.add_argument("--garch-refit", type=int, default=63)
    v1.add_argument("--french-archive", type=Path,
                    help="Optional official daily 5-factor ZIP for descriptive ETF factor regression")
    v1_demo = command.add_parser("v1-demo", help="Offline simulated V1 smoke test")
    v1_demo.add_argument("--rows", type=int, default=520)
    v1_demo.add_argument("--seed", type=int, default=20261022)
    v1_demo.add_argument("--output", type=Path, default=Path("outputs/v1_demo"))
    v2 = command.add_parser("v2-analysis", help="V2 private forecast/option study from existing V1 outputs")
    v2.add_argument("--v1-dir", type=Path, required=True)
    v2.add_argument("--output", type=Path, default=Path("outputs/v2_real"))
    v2_demo = command.add_parser("v2-demo", help="V1 and V2 integrated offline simulated study")
    v2_demo.add_argument("--rows", type=int, default=520)
    v2_demo.add_argument("--seed", type=int, default=20261022)
    v2_demo.add_argument("--output", type=Path, default=Path("outputs/v2_demo"))
    v3demo = command.add_parser("v3-demo", help="SYNTHETIC Microsoft-shaped statement / DCF test")
    v3demo.add_argument("--output", type=Path, default=Path("outputs/v3_demo"))
    v3demo.add_argument("--as-of", default="2026-10-22")
    v3demo.add_argument("--config", type=Path, default=Path("configs/valuation_assumptions.json"))
    v3sec = command.add_parser("v3-sec", help="Microsoft SEC Company Facts as-of fundamental valuation")
    v3sec.add_argument("--as-of", default="2026-10-22")
    v3sec.add_argument("--snapshot", type=Path, help="Existing SEC Company Facts JSON (offline replay)")
    v3sec.add_argument("--cache-dir", type=Path, default=Path("data/private/sec"))
    v3sec.add_argument("--config", type=Path, default=Path("configs/valuation_assumptions.json"))
    v3sec.add_argument("--output", type=Path, default=Path("outputs/v3_sec_msft"))
    publicdemo = command.add_parser("public-demo", help="Build a fully labeled offline synthetic recruiter site")
    publicdemo.add_argument("--rows", type=int, default=620)
    publicdemo.add_argument("--seed", type=int, default=41)
    publicdemo.add_argument("--output", type=Path, default=Path("outputs/public_demo"))
    ecb = command.add_parser("public-ecb", help="Retrieve official ECB FX and run auditable risk research")
    ecb.add_argument("--start", default="2015-01-01")
    ecb.add_argument("--end", default="2025-12-31")
    ecb.add_argument("--output", type=Path, default=Path("outputs/public_ecb"))
    ecb.add_argument("--no-advanced", action="store_true", help="Skip GARCH/ML/regime for fast preliminary analysis")
    website = command.add_parser("public-site", help="Build the recruiter website from an existing ECB or synthetic run")
    website.add_argument("--fx-dir", type=Path, required=True)
    website.add_argument("--sec-dir", type=Path, help="Existing real v3-sec output; synthetic accounting is refused")
    website.add_argument("--output", type=Path, default=Path("site"))
    stocks_demo = command.add_parser("stock-demo", help="Interactive historical stock simulator with SYNTHETIC prices")
    stocks_demo.add_argument("--sessions", type=int, default=650)
    stocks_demo.add_argument("--seed", type=int, default=42042)
    stocks_demo.add_argument("--output", type=Path, default=Path("outputs/stock_demo"))
    stocks_cc0 = command.add_parser("stock-kaggle", help="Import the historical CC0-labeled 2017 stock archive")
    stocks_cc0.add_argument("--archive", type=Path, required=True)
    stocks_cc0.add_argument("--output", type=Path, default=Path("outputs/stock_cc0"))
    stocks_cc0.add_argument("--start", default="2014-01-02")
    stocks_cc0.add_argument("--end", default="2017-11-10")
    stocks_cc0.add_argument("--accept-dataset-license", action="store_true")
    stocks_local = command.add_parser("stock-import-local", help="Private, user-supplied daily stock CSV")
    stocks_local.add_argument("--csv", type=Path, required=True)
    stocks_local.add_argument("--output", type=Path, default=Path("outputs/stock_local"))
    stock_site = command.add_parser("stock-site", help="Build the stock-first investor and recruiter website")
    stock_site.add_argument("--stock-dir", type=Path, required=True)
    stock_site.add_argument("--sec-dir", type=Path, help="Previously verified real SEC V3 valuation output")
    stock_site.add_argument("--output", type=Path, default=Path("site"))
    stock_site.add_argument("--local-only", action="store_true", help="Never upload this private site")
    current = command.add_parser("investment-desk", help="Current-day stock/ETF/crypto research and forward-only PAPER portfolio")
    current.add_argument("--demo", action="store_true", help="Fictional quotes for offline testing; no API keys")
    current.add_argument("--db", type=Path, default=Path.home() / ".quantforge" / "investment_desk.sqlite3")
    current.add_argument("--starting-cash", default="10000")
    current.add_argument("--port", type=int, default=8765)
    current.add_argument("--sec-dir", type=Path, help="Existing verified Microsoft V3 SEC output")
    personal = command.add_parser("personal-desk", help="LOCAL ONLY: Alpaca IEX quotes and private stock replay")
    personal.add_argument("--symbols", nargs="+", default=["MSFT", "AAPL", "NVDA", "AMZN", "SPY"])
    personal.add_argument("--start", default="2020-01-02")
    personal.add_argument("--end", default=dt.date.today().isoformat())
    personal.add_argument("--sec-dir", type=Path, help="Verified FY2026 Microsoft SEC study folder")
    personal.add_argument("--port", type=int, default=8765)
    v4demo = command.add_parser("v4-demo", help="Offline V4 integrated, SYNTHETIC research and DCF")
    v4demo.add_argument("--rows", type=int, default=520)
    v4demo.add_argument("--seed", type=int, default=20261022)
    v4demo.add_argument("--output", type=Path, default=Path("outputs/v4_demo"))
    v4 = command.add_parser("v4-integrate", help="Integrate verified synthetic market and SEC accounting outputs")
    v4.add_argument("--v1-dir", required=True, type=Path)
    v4.add_argument("--v2-dir", required=True, type=Path)
    v4.add_argument("--v3-dir", required=True, type=Path)
    v4.add_argument("--output", required=True, type=Path)
    return main


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "investment-desk":
            run_investment_desk(db=args.db, demo=args.demo, port=args.port,
                                starting_cash=args.starting_cash, sec_dir=args.sec_dir)
            return 0
        if args.command == "personal-desk":
            serve_personal_desk(symbols=args.symbols, start=args.start, end=args.end,
                                sec_dir=args.sec_dir, port=args.port)
            return 0
        if args.command == "stock-demo":
            bars = synthetic_bars(sessions=args.sessions, seed=args.seed)
            create_replay_data(output=args.output, frame=bars, origin="synthetic")
            site = build_stock_site(stock_dir=args.output, output=args.output / "site")
            print(f"SYNTHETIC stock simulator ready: {site['url']}")
            print("FICTIONAL PRICES ONLY. NO ACTUAL MARKET PERFORMANCE CLAIMS.")
            return 0
        if args.command == "stock-kaggle":
            frame = kaggle_archive_bars(args.archive, start=args.start, end=args.end)
            create_replay_data(output=args.output, frame=frame, origin="cc0_kaggle_2017",
                               source_path=args.archive,
                               approved_redistribution=args.accept_dataset_license)
            site = build_stock_site(stock_dir=args.output, output=args.output / "site")
            print(f"Historical CC0-labeled stock website ready: {site['url']}")
            print("DATA ENDS 2017-11-10. Retrospective selection and adjusted-pricing caveats apply.")
            return 0
        if args.command == "stock-import-local":
            frame = validate_bars(pd.read_csv(args.csv))
            create_replay_data(output=args.output, frame=frame,
                               origin="user_supplied_local", source_path=args.csv)
            site = build_stock_site(stock_dir=args.output, output=args.output / "site",
                                    local_only=True)
            print(f"PRIVATE stock simulation ready: {site['url']}")
            print("Do not publish this generated site or its embedded source prices.")
            return 0
        if args.command == "stock-site":
            site = build_stock_site(stock_dir=args.stock_dir, sec_dir=args.sec_dir,
                                    output=args.output, local_only=args.local_only)
            print(f"Stock-first website ready: {site['url']}")
            print(f"Source: {site['market_origin']} | SEC included: {site['sec_included']}")
            return 0
        if args.command == "public-site":
            result = build_public_site(fx_dir=args.fx_dir, sec_dir=args.sec_dir,
                                       output=args.output)
            print(f"Recruiter site ready: {result['site']}")
            print(f"Evidence origin: {result['origin']} | SEC integrated: {result['sec_integrated']}")
            return 0
        if args.command == "public-ecb":
            panel, original_csv, url = fetch_ecb(args.start, args.end)
            sha = save_raw_ecb(original_csv, args.output)
            result = evaluate_fx(panel, output=args.output, origin="ecb_reference_fx",
                                 source_url=url, source_sha=sha,
                                 advanced=not args.no_advanced)
            site = build_public_site(fx_dir=args.output, output=args.output / "site")
            print(f"ECB study complete: {result['observed_quote_days']} actual quote dates")
            print(f"Recruiter website: {site['site']}")
            print("Source: ECB statistics. No Tiingo request or ETF holdout analysis.")
            return 0
        if args.command == "public-demo":
            if args.rows < 350:
                raise ValueError("Synthetic demo needs at least 350 observations")
            import numpy as np

            from quantforge.public.ecb import CURRENCIES
            rng = np.random.default_rng(args.seed)
            dates = pd.bdate_range("2022-01-03", periods=args.rows)
            rates = pd.DataFrame(index=dates)
            for currency, opening, sigma in (("USD", 1.12, .006), ("GBP", .83, .003),
                                             ("JPY", 132.0, .008), ("CHF", 1.05, .004)):
                shocks = rng.normal(.00008, sigma, size=args.rows)
                shocks[args.rows//2:] *= 1.45
                rates[currency] = opening * np.exp(np.cumsum(shocks))
            rates = rates.reindex(columns=CURRENCIES)
            evaluate_fx(rates, output=args.output, origin="synthetic_fx_fixture",
                        source_url="quantforge:generated_offline_fixture", source_sha=None)
            site = build_public_site(fx_dir=args.output, output=args.output / "site")
            print(f"SYNTHETIC recruiter demonstration complete: {site['site']}")
            print("No market observations and no real valuation claims in this demo.")
            return 0
        if args.command == "v4-integrate":
            result = run_v4_integration(v1_dir=args.v1_dir, v2_dir=args.v2_dir,
                                        v3_dir=args.v3_dir, output=args.output)
            print(f"V4 integrated research: {result['output']}")
            print(f"Origins: {', '.join(result['data_origins'])}; FINAL HOLDOUT NOT ACCESSED")
            return 0
        if args.command == "v4-demo":
            prices = simulated_market(rows=args.rows, seed=args.seed)
            prices["symbol"] = prices["symbol"].replace({
                "SIM_ALPHA": "SPY", "SIM_BETA": "IWM",
                "SIM_GAMMA": "GLD", "SIM_DELTA": "TLT",
            })
            v1dir = args.output / "v1_synthetic"
            v2dir = args.output / "v2_synthetic"
            v3dir = args.output / "v3_synthetic"
            run_v1_study(prices, output=v1dir, dataset="simulation")
            run_v2_study(v1_dir=v1dir, output=v2dir)
            v3dir.mkdir(parents=True, exist_ok=True)
            snapshot = v3dir / "SYNTHETIC_companyfacts.json"
            snapshot.write_text(json.dumps(synthetic_companyfacts(), sort_keys=True), encoding="utf-8")
            run_v3_study(snapshot, as_of="2026-10-22", output=v3dir,
                         config_path=Path("configs/valuation_assumptions.json"),
                         origin="synthetic_demo")
            result = run_v4_integration(v1_dir=v1dir, v2_dir=v2dir,
                                        v3_dir=v3dir, output=args.output / "integrated")
            print(f"V4 SYNTHETIC demonstration complete: {result['output']}")
            print("All market metrics simulated; all accounting data fictional; no licensed prices used.")
            return 0
        if args.command == "v3-demo":
            args.output.mkdir(parents=True, exist_ok=True)
            snapshot = args.output / "SYNTHETIC_NOT_SEC_companyfacts.json"
            snapshot.write_text(json.dumps(synthetic_companyfacts(), sort_keys=True), encoding="utf-8")
            result = run_v3_study(snapshot, as_of=args.as_of, output=args.output,
                                  config_path=args.config, origin="synthetic_demo")
            print(f"V3 SYNTHETIC valuation demo complete: {result['output']}")
            print("FICTIONAL FINANCIALS. NO REAL MICROSOFT VALUATION CLAIMS.")
            return 0
        if args.command == "v3-sec":
            if args.snapshot is not None:
                snapshot = args.snapshot
                if not snapshot.is_file():
                    raise ValueError(f"SEC snapshot missing: {snapshot}")
            else:
                user_agent = os.environ.get("SEC_USER_AGENT", "")
                snapshot = download_companyfacts(
                    user_agent=user_agent,
                    target=args.cache_dir / "CIK0000789019_companyfacts.json",
                )
            result = run_v3_study(snapshot, as_of=args.as_of, output=args.output,
                                  config_path=args.config, origin="sec_companyfacts")
            print(f"V3 SEC valuation study complete: {result['output']}")
            print(f"Latest eligible fiscal year: {result['fiscal_year']}; "
                  f"DCF scenarios: {result['scenarios']}")
            print("Valuation assumptions are hypothetical; see filing audit, disclosure limitations, and memo.")
            return 0
        if args.command == "v2-analysis":
            origin = json.loads((args.v1_dir / "manifest_v1.json").read_text(encoding="utf-8"))
            if origin.get("dataset") == "external_tiingo":
                raise ValueError("V4 disables persistent Tiingo-derived analysis on Starter accounts. "
                                 "Use v4-demo for publication-safe research.")
            study = run_v2_study(v1_dir=args.v1_dir, output=args.output)
            print(f"V2 research complete: {study['output']}")
            print(f"Evaluation dates: {study['evaluation_dates']} | compared models: {study['models']}")
            print("DEVELOPMENT ONLY: Keep empirical outputs private; 2019-2025 holdout excluded.")
            return 0
        if args.command == "v2-demo":
            prices = simulated_market(rows=args.rows, seed=args.seed)
            prices["symbol"] = prices["symbol"].replace({
                "SIM_ALPHA": "SPY", "SIM_BETA": "IWM",
                "SIM_GAMMA": "GLD", "SIM_DELTA": "TLT",
            })
            prior = args.output / "v1_synthetic_baseline"
            run_v1_study(prices, output=prior, dataset="simulation")
            study = run_v2_study(v1_dir=prior, output=args.output / "v2_results")
            print(f"V2 simulated demonstration complete: {study['output']}")
            print("SIMULATED DATA ONLY, NOT EMPIRICAL FINANCIAL EVIDENCE")
            return 0
        if args.command == "v1-risk":
            raise ValueError("V4 disables persisted Tiingo Starter datasets and derived results. "
                             "Use the synthetic demonstration and review provider data rights.")
            prices = read_market_csv(
                args.input_prices, vendor="Tiingo EOD (V0.2 audited)",
                price_basis="dividend_adjusted_close",
            )
            study = run_v1_study(
                prices, output=args.output, dataset="external_tiingo",
                price_input=args.input_prices, source_manifest=args.source_manifest,
                risk_window=args.risk_window, garch_refit=args.garch_refit,
            )
            if args.french_archive is not None:
                write_factor_report(args.output, prices, args.french_archive)
            print(f"V1 private financial risk study complete: {study['output']}")
            print(f"Risk evaluation: {study['risk_days']} dates, "
                  f"{study['models']} risk models and "
                  f"{study['strategies']} portfolio strategies")
            print("IMPORTANT: Development-only data. KEEP ALL MARKET RESULTS PRIVATE.")
            return 0
        if args.command == "v1-demo":
            prices = simulated_market(rows=args.rows, seed=args.seed)
            prices["symbol"] = prices["symbol"].replace({
                "SIM_ALPHA": "SPY", "SIM_BETA": "IWM",
                "SIM_GAMMA": "GLD", "SIM_DELTA": "TLT",
            })
            study = run_v1_study(prices, output=args.output, dataset="simulation")
            print(f"V1 simulated demonstration complete: {study['output']}")
            print(f"Risk evaluation: {study['risk_days']} dates; "
                  "SIMULATION ONLY, NOT EMPIRICAL EVIDENCE")
            return 0
        if args.command == "fred-vintage":
            frame = fred_vintage(args.series, as_of=args.as_of, observation_start=args.start)
            args.output.mkdir(parents=True, exist_ok=True)
            frame.to_csv(args.output / "fred_observations.csv", index=False)
            write_json(args.output / "vintage_manifest.json", {
                "provider": "FRED/ALFRED", "series": args.series,
                "as_of_date": args.as_of, "observation_start": args.start,
                "rows": len(frame),
                "limitations": "Date-level vintage does not establish intraday public release timing",
            })
            print(f"Saved FRED/ALFRED vintage: {len(frame)} observations at {args.output.resolve()}")
            return 0
        if args.command == "demo":
            prices = simulated_market(rows=args.rows, seed=args.seed)
            result = run_research(
                prices,
                output=args.output,
                source="simulation",
                vendor="quantforge_internal_simulation",
                price_basis="synthetic_index_levels",
                lookback=args.lookback,
            )
        elif args.command == "tiingo":
            raise ValueError("Tiingo Starter terms (updated October 2026) prohibit durable storage "
                             "of provider data and derived outputs. V4 disables this prior "
                             "persisting workflow. No API request was made.")
            prices, provenance = load_tiingo_history(
                symbols=args.symbols,
                start=args.start,
                end=args.end,
                cache_dir=args.cache_dir,
                offline=args.offline,
                refresh=args.refresh,
            )
            # Restrict exploratory risk/portfolio reporting to the prespecified
            # development period. In particular, do NOT inspect 2019-2025
            # holdout performance just because the vendor returned those dates.
            developer_cutoff = pd.Timestamp("2018-12-31")
            development_prices = prices.loc[prices["date"] <= developer_cutoff].copy()
            if development_prices.empty:
                raise ValueError(
                    "No observations in the prespecified 2010-2018 development window; "
                    "do not redefine the 2019-2025 holdout without revising the protocol"
                )
            provenance["development_cutoff"] = developer_cutoff.date().isoformat()
            provenance["holdout_policy"] = (
                "2019-2025 provider records stored privately; not scored or plotted "
                "during preliminary V0 baseline evaluation"
            )
            args.output.mkdir(parents=True, exist_ok=True)
            prices.to_csv(
                args.output / "private_full_provider_prices.csv", index=False,
                float_format="%.12g",
            )
            provenance["private_full_provider_prices"] = "private_full_provider_prices.csv"
            result = run_research(
                development_prices,
                output=args.output,
                source="external_tiingo",
                vendor="Tiingo EOD (development window only)",
                price_basis="dividend_adjusted_close",
                lookback=args.lookback,
                source_details=provenance,
            )
            if args.french_archive is not None:
                write_factor_report(args.output, development_prices, args.french_archive)
        elif args.command == "ingest-csv":
            prices = read_market_csv(args.path, vendor=args.vendor, price_basis=args.basis)
            result = run_research(
                prices,
                output=args.output,
                source="external_csv",
                vendor=args.vendor,
                price_basis=args.basis,
                input_sha256=sha256_file(args.path),
                lookback=args.lookback,
            )
        else:
            raise ValueError("Unknown command")
    except (ValueError, RuntimeError, OSError, ArithmeticError, requests.RequestException) as exc:
        print(f"QuantForge error: {exc}", file=sys.stderr)
        return 2
    summary = result["summary"]
    print(f"Completed: {args.output.resolve()}")
    print(f"Dataset: {summary['dataset_type']}; assets: {len(summary['assets'])}")
    print(f"Evaluation days: {summary['evaluation_dates']}; input days: {summary['return_dates']+1}")
    print(f"Storage: {result['manifest']['storage']['storage_engine']}")
    if summary["dataset_type"] == "simulation":
        print("IMPORTANT: SIMULATED DEMO, NOT EMPIRICAL MARKET RESULTS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
