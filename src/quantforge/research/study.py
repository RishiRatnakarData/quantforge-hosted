"""QuantForge V1 development-period portfolio and market-risk research."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
from plotly import graph_objects as go
from plotly.subplots import make_subplots

from quantforge.data.contracts import make_complete_panel, simple_returns, validate_prices
from quantforge.data.storage import sha256_file, write_json
from quantforge.portfolio.advanced import backtest_allocations, regularized_covariance
from quantforge.risk.conditional_coverage import diagnostics_table
from quantforge.risk.garch import rolling_garch_forecasts
from quantforge.risk.measures import rolling_risk_forecasts
from quantforge.risk.stress import stress_table

DEV_CUTOFF = pd.Timestamp("2018-12-31")
PRESET_UNIVERSE = {"SPY", "IWM", "EFA", "EEM", "IEF", "TLT", "GLD", "LQD"}


def _read_v02_manifest(source_manifest: Path | None, dataset: str) -> dict:
    if dataset == "simulation":
        return {"provider": "QuantForge deterministic simulation", "price_basis": "synthetic"}
    if source_manifest is None:
        raise ValueError("Real-data risk study requires --source-manifest from V0.2")
    try:
        manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Could not read V0.2 source manifest") from exc
    if (manifest.get("provider") != "Tiingo EOD"
            or manifest.get("price_basis") != "dividend_adjusted_close"
            or manifest.get("calendar_audit", {}).get("pass") is not True):
        raise ValueError("V0.2 source manifest must attest Tiingo adjusted closes and XNYS audit")
    if set(manifest.get("symbol_universe", [])) != PRESET_UNIVERSE:
        raise ValueError("Different instrument universe: research design must be versioned")
    if len(manifest.get("snapshots", [])) != 8:
        raise ValueError("Missing source snapshots in source manifest")
    return manifest


def _audit(prices: pd.DataFrame, dataset: str) -> tuple[pd.DataFrame, dict]:
    clean = validate_prices(prices)
    panel = make_complete_panel(clean)
    if panel.index.max() > DEV_CUTOFF and dataset != "simulation":
        raise ValueError("2019–2025 holdout data prohibited in V1 development study")
    if dataset == "external_tiingo":
        if set(panel.columns) != PRESET_UNIVERSE:
            raise ValueError("Research universe must match predeclared ETF list")
        if panel.index.min() < pd.Timestamp("2010-01-01"):
            raise ValueError("External research price series starts before agreed window")
        if len(panel) < 500:
            raise ValueError("Insufficient ETF daily history for V1 evaluation")
    returns = simple_returns(panel)
    # Flag large changes, not automatically discard them: splits/corporate actions
    # require an independent review before interpreting economic findings.
    extremes = (returns.abs() > 0.20).sum().to_dict()
    stale = (returns == 0).sum().to_dict()
    audit = {
        "observations": len(panel),
        "return_observations": len(returns),
        "symbols": list(panel.columns),
        "first_date": str(panel.index.min().date()),
        "last_date": str(panel.index.max().date()),
        "missing_prices": int(panel.isna().sum().sum()),
        "duplicate_price_rows": int(clean.duplicated(["date", "symbol"]).sum()),
        "abs_daily_return_over_20pct_counts": {k: int(v) for k, v in extremes.items()},
        "zero_return_counts": {k: int(v) for k, v in stale.items()},
        "holdout_excluded": bool(dataset == "external_tiingo"),
        "status": "automatic_contract_pass; adjustment_spot_checks_not_independently_verified",
    }
    return returns, audit


def _scoring(forecasts: pd.DataFrame, confidence: float) -> pd.DataFrame:
    realized = forecasts["realized_return"].to_numpy(float)
    loss = -realized
    results = []
    for var in ("historical_var", "normal_var", "ewma_normal_var", "garch_normal_var"):
        threshold = forecasts[var].to_numpy(float)
        # Proper quantile/pinball loss for the alpha quantile of daily LOSS.
        score = np.where(loss >= threshold, confidence, confidence - 1) * (loss - threshold)
        results.append({"model": var, "mean_pinball_loss": float(score.mean()),
                        "evaluation_days": len(score)})
    for vol_key, name in (("normal_variance", "normal_var"),
                          ("ewma_variance", "ewma_normal_var"),
                          ("garch_volatility", "garch_normal_var")):
        v = forecasts[vol_key].to_numpy(float)
        if vol_key == "garch_volatility":
            v = v**2
        # Proper QLIKE loss for latent variance, using daily squared return as
        # a noisy realized-variance proxy; daily drift is ignored.
        v = np.maximum(v, 1e-12)
        qlike = float(np.mean(np.log(v) + realized**2 / v))
        for row in results:
            if row["model"] == name:
                row["mean_qlike"] = qlike
                break
    return pd.DataFrame(results)


def _latest_positions(weights: pd.DataFrame) -> pd.DataFrame:
    return weights.loc[weights["position_type"] == "ending_mark_to_market"].copy()


def _make_dashboard(
    paths: pd.DataFrame,
    forecasts: pd.DataFrame,
    diagnostics: pd.DataFrame,
    comparisons: pd.DataFrame,
    output: Path,
    dataset: str,
) -> None:
    figure = make_subplots(
        rows=3, cols=1, shared_xaxes=False,
        subplot_titles=("Growth of $1 — net transaction costs",
                        "One-day 95% portfolio loss forecast and observed losses",
                        "Rolling one-day conditional volatility (EWMA vs GARCH)"),
        vertical_spacing=0.095,
        row_heights=[0.40, 0.35, 0.25],
    )
    palette = ["#2D5EA8", "#E37D30", "#0C8F7B", "#9A56A7", "#4D7592"]
    for (strategy, group), color in zip(paths.groupby("strategy", sort=False), palette, strict=True):
        figure.add_trace(go.Scatter(x=group["date"], y=group["wealth"], name=strategy,
                                    mode="lines", line={"color": color, "width": 1.8}),
                         row=1, col=1)
    figure.add_trace(go.Scatter(x=forecasts["date"], y=-forecasts["realized_return"],
                                name="Observed daily loss", mode="lines",
                                line={"color": "#8D929D", "width": 0.65}), row=2, col=1)
    for name, color in (("historical_var", "#E37D30"),
                        ("ewma_normal_var", "#0C8F7B"),
                        ("garch_normal_var", "#9A56A7")):
        figure.add_trace(go.Scatter(x=forecasts["date"], y=forecasts[name],
                                    name=name, mode="lines",
                                    line={"color": color, "width": 1.45}), row=2, col=1)
    for name, color in (("ewma_variance", "#0C8F7B"),
                        ("garch_volatility", "#9A56A7")):
        y = (np.sqrt(forecasts[name]) if name == "ewma_variance"
             else forecasts[name]) * np.sqrt(252)
        figure.add_trace(go.Scatter(x=forecasts["date"], y=y, name=name,
                                    mode="lines", line={"color": color, "width": 1.6}),
                         row=3, col=1)
    figure.update_layout(height=1170, margin={"l": 80, "r": 35, "t": 75, "b": 45},
                         paper_bgcolor="#FBFCFE", plot_bgcolor="#FFFFFF",
                         font={"family": "Arial, sans-serif", "color": "#172C42"},
                         legend={"orientation": "h", "y": -0.055},
                         hovermode="x unified", title={
                             "text": "QuantForge V1 — Portfolio Risk Research | DEVELOPMENT ONLY",
                             "font": {"size": 20}})
    figure.update_yaxes(title_text="Net wealth", row=1, col=1)
    figure.update_yaxes(title_text="Daily loss fraction", row=2, col=1)
    figure.update_yaxes(title_text="Annualized vol", tickformat=".0%", row=3, col=1)
    figure.update_xaxes(showgrid=True, gridcolor="#E8EDF2")
    figure.write_html(output, include_plotlyjs=True, full_html=True)


def _research_report(
    output: Path, dataset: str, audit: dict, comparisons: pd.DataFrame,
    diagnostics: pd.DataFrame, scoring: pd.DataFrame, input_hash: str,
) -> None:
    # Avoid optional tabulate dependency; all distributions have CSV evidence.
    comp_lines = ["| Strategy | Net ending wealth | Annualized volatility | Maximum drawdown |",
                  "|---|---:|---:|---:|"]
    for _, r in comparisons.iterrows():
        comp_lines.append(f"| {r['strategy']} | {r['ending_wealth']:.4f} | "
                          f"{r['annualized_volatility']:.2%} | {r['maximum_drawdown']:.2%} |")
    risk_lines = ["| Forecast | Exceptions | Exception rate | Kupiec p | Independence p | Pinball loss |",
                  "|---|---:|---:|---:|---:|---:|"]
    merged = diagnostics.merge(scoring, on="model", how="left")
    for _, r in merged.iterrows():
        p_ind = r["pvalue_ind"]
        p_ind_str = f"{p_ind:.4f}" if pd.notna(p_ind) else "not estimable"
        risk_lines.append(f"| {r['model']} | {int(r['exceptions'])} | "
                          f"{r['exception_rate']:.2%} | {r['kupiec_pvalue']:.4f} | "
                          f"{p_ind_str} | {r['mean_pinball_loss']:.6f} |")
    document = (
        "# QuantForge V1 — Development-period Risk Research Summary\n\n"
        f"**Dataset:** {dataset}; **date range:** {audit['first_date']} – {audit['last_date']}; "
        f"**price-file SHA-256:** `{input_hash}`.\n\n"
        "**Research status:** diagnostic development results, not a preregistered "
        "out-of-sample final test. The 2019–2025 holdout has not been evaluated. "
        "Do not represent exploratory differences as statistically proven investment alpha.\n\n"
        "## Net-of-cost portfolio comparison\n\n"
        + "\n".join(comp_lines) + "\n\n"
        "Fully invested comparison uses past-only trailing 126-day weight estimation "
        "with a one-session execution delay; "
        "a 35% max weight for diversified strategies, monthly (21-session) rebalances, "
        "and 5 bp on all traded notional (purchases plus sales, including initial purchases). "
        "These are stylized closing-price implementation assumptions. Sharpe is a "
        "zero-cash-rate proxy. A SPY buy-and-hold benchmark has no concentration cap.\n\n"
        "## VaR backtesting — one-day 95% loss budget\n\n"
        + "\n".join(risk_lines) + "\n\n"
        "VaR models target the same realized daily net return of the investable "
        "equal-weight portfolio. Risk forecasts are formed only after a 252-observation "
        "training window. GARCH(1,1) is Gaussian, stationary, refitted every 63 sessions; "
        "its conditional variance is filtered daily. A forecast for date t uses returns "
        "through t-1. Coverage and independence likelihood ratio p-values are asymptotic "
        "and may have limited power; tail-severity ES verification remains future work.\n\n"
        "## Important limitations\n\n"
        "- The eight ETF symbols were chosen retrospectively. The universe is not "
        "survivorship-corrected.\n"
        "- Tiingo adjusted-close history is a present-day reconstructed history, not "
        "a historical point-in-time adjusted tape. Corporate-action spot checks remain.\n"
        "- The pre-2019 period includes model development; results here are **not** "
        "a confirmation of the central research hypothesis.\n"
        "- Daily squared returns are a noisy volatility forecast target. The report "
        "does not test ES calibration or optimize model hyperparameters.\n"
        "- Closing-price execution, taxes, financing rates, bid–ask impact, and "
        "liquidity constraints are not modeled.\n"
        "- Provider licensing may prohibit redistribution of empirical output; "
        "keep these outputs private pending rights review.\n\n"
        "## Supporting evidence\n\n"
        "`data_audit.json`, `manifest_v1.json`, `portfolio_metrics.csv`, "
        "`portfolio_paths.csv`, `portfolio_weights.csv`, `risk_forecasts.csv`, "
        "`risk_diagnostics.csv`, `forecast_scoring.csv`, `stress_scenarios.csv`, "
        "`covariance.csv`, `correlation.csv`, `cost_rebalance_sensitivity.csv` "
        "and `risk_dashboard.html`.\n"
    )
    (output / "RESEARCH_SUMMARY.md").write_text(document, encoding="utf-8")


def run_v1_study(
    prices: pd.DataFrame,
    *,
    output: Path,
    dataset: str,
    price_input: Path | None = None,
    source_manifest: Path | None = None,
    risk_window: int = 252,
    garch_refit: int = 63,
    confidence: float = 0.95,
) -> dict:
    """Write development-only results with independent experimental provenance."""
    if dataset not in {"simulation", "external_tiingo"}:
        raise ValueError("Unknown dataset type")
    if confidence != 0.95:
        raise ValueError("V1 research protocol is fixed at 95% confidence")
    source = _read_v02_manifest(source_manifest, dataset)
    returns, audit = _audit(prices, dataset)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths, comparisons, weights = backtest_allocations(returns, lookback=126)
    investable = (paths.loc[paths["strategy"] == "equal_weight", ["date", "net_return"]]
                  .set_index("date")["net_return"].sort_index())
    if len(investable) <= risk_window:
        raise ValueError("Need more price history to evaluate 252-session risk models")
    risk = rolling_risk_forecasts(investable, lookback=risk_window,
                                  confidence=confidence)
    garch = rolling_garch_forecasts(investable, lookback=risk_window,
                                    refit_every=garch_refit, confidence=confidence)
    forecasts = risk.merge(garch, on="date", how="inner", validate="one_to_one")
    if len(forecasts) != len(risk) or len(forecasts) != len(garch):
        raise RuntimeError("Risk models failed same-date alignment")
    if not (pd.to_datetime(forecasts["training_end"]) < forecasts["date"]).all():
        raise RuntimeError("Forecast chronology violation")
    if not (pd.to_datetime(forecasts["garch_training_end"]) < forecasts["date"]).all():
        raise RuntimeError("GARCH forecast chronology violation")
    diagnostics = diagnostics_table(forecasts, confidence=confidence)
    scoring = _scoring(forecasts, confidence)
    stress = stress_table(_latest_positions(weights)) if dataset == "external_tiingo" else None
    # Prespecified sensitivity grid. Never choose strategy based on these
    # development-period outcomes and then claim confirmation on the holdout.
    sensitivity = []
    for cost_bps, interval in ((0, 21), (5, 21), (15, 21), (5, 63)):
        if cost_bps == 5 and interval == 21:
            metrics = comparisons
        else:
            _, metrics, _ = backtest_allocations(
                returns, lookback=126, rebalance_every=interval,
                trading_cost_bps=cost_bps,
            )
        for _, r in metrics.iterrows():
            sensitivity.append({"trading_cost_bps": cost_bps,
                                "rebalance_sessions": interval,
                                "strategy": r["strategy"],
                                "ending_wealth": r["ending_wealth"],
                                "annualized_volatility": r["annualized_volatility"],
                                "maximum_drawdown": r["maximum_drawdown"],
                                "total_turnover": r["total_turnover"]})
    sensitivity_table = pd.DataFrame(sensitivity)
    covariance = regularized_covariance(returns.iloc[-252:])
    covariance_frame = pd.DataFrame(covariance, index=returns.columns, columns=returns.columns)
    correlation = returns.iloc[-252:].corr()

    for filename, df in (
        ("portfolio_paths.csv", paths), ("portfolio_metrics.csv", comparisons),
        ("portfolio_weights.csv", weights), ("risk_forecasts.csv", forecasts),
        ("risk_diagnostics.csv", diagnostics), ("forecast_scoring.csv", scoring),
        ("covariance.csv", covariance_frame), ("correlation.csv", correlation),
        ("cost_rebalance_sensitivity.csv", sensitivity_table),
    ):
        df.to_csv(output / filename, index=filename in {"covariance.csv", "correlation.csv"},
                  float_format="%.12g")
    if stress is not None:
        stress.to_csv(output / "stress_scenarios.csv", index=False, float_format="%.12g")
    hash_value = (sha256_file(price_input) if price_input is not None
                  else "deterministic-in-memory-simulation")
    write_json(output / "data_audit.json", audit)
    write_json(output / "manifest_v1.json", {
        "release": "1.0.0-research-core", "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
        "dataset": dataset, "input_file_sha256": hash_value,
        "source_manifest_sha256": (sha256_file(source_manifest)
                                   if source_manifest else None),
        "price_provider": source["provider"], "price_basis": source["price_basis"],
        "research_window": "development_through_2018_only" if dataset != "simulation"
                           else "synthetic_non_empirical",
        "holdout_2019_to_2025": "excluded_unread",
        "portfolio_training": 126, "portfolio_rebalance": 21,
        "rebalance_signal_lag": "prior-prior close signal; execution at prior close",
        "portfolio_max_weight": 0.35, "trading_cost_bps_all_traded_notional": 5,
        "risk_lookback": risk_window, "garch_refit_every": garch_refit,
        "confidence": confidence, "evaluation_days": len(forecasts),
        "risk_target": "equal_weight_investable_net_return_after_costs",
        "stress_is_hypothetical": True,
        "rights_note": "Keep empirical outputs private; raw Tiingo prices not redistributed",
    })
    _make_dashboard(paths, forecasts, diagnostics, comparisons,
                    output / "risk_dashboard.html", dataset)
    _research_report(output, dataset, audit, comparisons, diagnostics, scoring, hash_value)
    return {"portfolio_days": len(paths) // len(comparisons),
            "risk_days": len(forecasts), "strategies": len(comparisons),
            "models": len(diagnostics), "output": str(output.resolve())}
