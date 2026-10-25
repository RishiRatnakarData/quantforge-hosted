"""V2: model-comparison and mathematical finance using V1 research evidence."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
from plotly import graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm

from quantforge.data.storage import sha256_file, write_json
from quantforge.derivatives.black_scholes import monte_carlo_european, price_and_greeks
from quantforge.forecasting.advanced import rolling_ml_forecast
from quantforge.regimes.markov import rolling_regime_forecasts
from quantforge.risk.conditional_coverage import diagnostics_table
from quantforge.simulation.portfolio_mc import portfolio_monte_carlo

DEV_CUTOFF = pd.Timestamp("2018-12-31")
FORECAST_KEYS = (
    "historical_var", "normal_var", "ewma_normal_var", "garch_normal_var",
    "ridge_normal_var", "boost_normal_var", "regime_mixture_var_95",
)
VARIANCE_KEYS = (
    "normal_variance", "ewma_variance", "garch_volatility",
    "ridge_variance", "gradient_boosting_variance", "regime_second_moment",
)


def _load_v1(v1_dir: Path) -> tuple[pd.Series, pd.DataFrame, dict, dict]:
    root = Path(v1_dir)
    paths_file = root / "portfolio_paths.csv"
    forecast_file = root / "risk_forecasts.csv"
    manifest_file = root / "manifest_v1.json"
    audit_file = root / "data_audit.json"
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        audit = json.loads(audit_file.read_text(encoding="utf-8"))
        paths = pd.read_csv(paths_file, parse_dates=["date"])
        baseline = pd.read_csv(forecast_file, parse_dates=["date", "training_end", "garch_training_end"])
    except (OSError, ValueError, KeyError) as exc:
        raise ValueError("Complete V1 research directory is required") from exc
    if manifest.get("dataset") not in {"simulation", "external_tiingo"}:
        raise ValueError("Unknown V1 data origin")
    if (manifest.get("holdout_2019_to_2025") != "excluded_unread"
            or manifest.get("research_window") not in {
                "development_through_2018_only", "synthetic_non_empirical"}):
        raise ValueError("V1 manifest does not attest holdout exclusion")
    if manifest.get("risk_target") != "equal_weight_investable_net_return_after_costs":
        raise ValueError("V1 risk target does not match research protocol")
    if (audit.get("missing_prices") != 0 or audit.get("duplicate_price_rows") != 0):
        raise ValueError("Underlying V1 data audit not clean")
    equal = paths.loc[paths["strategy"] == "equal_weight", ["date", "net_return"]]
    if (equal.empty or equal["date"].duplicated().any()
            or not equal["date"].is_monotonic_increasing or equal["net_return"].isna().any()):
        raise ValueError("Invalid V1 equal-weight daily net-return series")
    series = equal.set_index("date")["net_return"].astype(float)
    if (len(series) < 350 or not np.isfinite(series).all()
            or (series <= -1).any()):
        raise ValueError("V1 return series incomplete")
    if (manifest["dataset"] == "external_tiingo"
            and (series.index.min() < pd.Timestamp("2010-01-01")
                 or series.index.max() > DEV_CUTOFF
                 or pd.to_datetime(audit["last_date"]) > DEV_CUTOFF)):
        raise ValueError("Refusing to inspect 2019-2025 holdout in V2")
    required = {"realized_return", "historical_var", "normal_var", "ewma_normal_var",
                "garch_normal_var", "normal_variance", "ewma_variance", "garch_volatility"}
    if not required.issubset(baseline.columns) or baseline["date"].duplicated().any():
        raise ValueError("V1 risk forecasts missing fields or duplicate dates")
    if not (baseline["training_end"] < baseline["date"]).all():
        raise ValueError("V1 risk model training-time leakage")
    if not (baseline["garch_training_end"] < baseline["date"]).all():
        raise ValueError("V1 GARCH training-time leakage")
    matched = series.reindex(baseline["date"])
    if (matched.isna().any() or not np.allclose(matched.to_numpy(float),
                                                baseline["realized_return"].to_numpy(float),
                                                atol=1e-9, rtol=1e-8)):
        raise ValueError("V1 realized returns do not reconcile with portfolio paths")
    source = {"v1_manifest_sha256": sha256_file(manifest_file),
              "v1_portfolio_paths_sha256": sha256_file(paths_file),
              "v1_risk_forecasts_sha256": sha256_file(forecast_file),
              "dataset": manifest["dataset"],
              "source_price_sha256": manifest.get("input_file_sha256")}
    return series, baseline, manifest, source


def _model_frame(returns: pd.Series, baseline: pd.DataFrame) -> pd.DataFrame:
    ml = rolling_ml_forecast(returns, start_at=252, refit_every=63)
    regimes = rolling_regime_forecasts(returns, start_at=252, refit_every=126)
    fields = ["date", "ridge_variance", "gradient_boosting_variance",
              "model_fit_end", "feature_training_end"]
    ml = ml.loc[:, fields].rename(columns={"model_fit_end": "ml_fit_end"})
    regimes = regimes.drop(columns=["realized_return"])
    combined = baseline.merge(ml, on="date", validate="one_to_one", how="inner")
    combined = combined.merge(regimes, on="date", validate="one_to_one", how="inner")
    if len(combined) != len(baseline):
        raise ValueError("Advanced models not aligned to V1 evaluation dates")
    for name in ("ml_fit_end", "feature_training_end", "model_fit_end", "filter_training_end"):
        if not (combined[name] < combined["date"]).all():
            raise ValueError(f"Future information leaked into {name}")
    confidence = norm.ppf(0.95)
    combined["ridge_normal_var"] = confidence * np.sqrt(combined["ridge_variance"])
    combined["boost_normal_var"] = confidence * np.sqrt(combined["gradient_boosting_variance"])
    return combined


def _scores(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    results = []
    realized = frame["realized_return"].to_numpy(float)
    squared = realized**2
    mapping = {"normal_var": "normal_variance", "ewma_normal_var": "ewma_variance",
               "garch_normal_var": "garch_volatility", "ridge_normal_var": "ridge_variance",
               "boost_normal_var": "gradient_boosting_variance",
               "regime_mixture_var_95": "regime_second_moment"}
    for name, column in mapping.items():
        raw = frame[column].to_numpy(float)
        variance = raw**2 if column == "garch_volatility" else raw
        variance = np.clip(variance, 1e-10, None)
        loss = -realized
        threshold = frame[name].to_numpy(float)
        # Pinball/check loss for 0.95 loss quantile.
        check = np.where(loss >= threshold, 0.95, -0.05) * (loss - threshold)
        results.append({"model": name, "mean_qlike": float(np.mean(np.log(variance)
                                                            + squared / variance)),
                        "mean_squared_variance_error": float(np.mean((variance - squared)**2)),
                        "mean_pinball_loss": float(check.mean()),
                        "observations": len(frame)})
    # Historical VaR has a quantile but no associated volatility forecast.
    historical_losses = -realized
    hthreshold = frame["historical_var"].to_numpy(float)
    check = np.where(historical_losses >= hthreshold, 0.95, -0.05) * (historical_losses - hthreshold)
    results.append({"model": "historical_var", "mean_qlike": np.nan,
                    "mean_squared_variance_error": np.nan,
                    "mean_pinball_loss": float(check.mean()), "observations": len(frame)})
    scores = pd.DataFrame(results)
    diagnostics = diagnostics_table(frame, confidence=0.95, var_columns=FORECAST_KEYS)
    return scores, diagnostics


def _option_research() -> tuple[pd.DataFrame, dict]:
    # Generic hypothetical option; no claim of observed derivative prices.
    assumptions = {"spot": 100.0, "strike": 100.0, "time_years": 1.0,
                   "rate": 0.03, "volatility": 0.20, "dividend_yield": 0.01}
    call = price_and_greeks(kind="call", **assumptions)
    put = price_and_greeks(kind="put", **assumptions)
    mc = monte_carlo_european(kind="call", **assumptions, paths=20000, seed=42)
    records = []
    for v in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
        for tenor in (0.25, 0.5, 1.0, 2.0):
            values = price_and_greeks(kind="call", **{**assumptions,
                                                   "volatility": v,
                                                   "time_years": tenor})
            records.append({"annual_volatility": v, "time_years": tenor, **values})
    output = {"assumptions": assumptions, "call": call, "put": put,
              "monte_carlo_call": mc, "interpretation": "hypothetical_model_only"}
    return pd.DataFrame(records), output


def _dashboard(df: pd.DataFrame, out: Path, dataset: str) -> None:
    chart = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                          subplot_titles=["One-day annualized volatility forecasts",
                                          "High-volatility regime probability (predictive)",
                                          "95% forecast loss thresholds and actual losses"],
                          row_heights=[0.34, 0.26, 0.40])
    colors = {"garch_volatility": "#8759B7", "ridge_variance": "#3066BE",
              "gradient_boosting_variance": "#D47A28", "regime_second_moment": "#157F78"}
    for name, color in colors.items():
        variance = df[name]**2 if name == "garch_volatility" else df[name]
        chart.add_trace(go.Scatter(x=df["date"], y=np.sqrt(variance) * np.sqrt(252),
                                   name=name, line={"color": color, "width": 1.3}),
                        row=1, col=1)
    chart.add_trace(go.Scatter(x=df["date"], y=df["regime_high_probability"],
                               name="High-vol regime probability", line={"color": "#9B4F76"}),
                    row=2, col=1)
    chart.add_trace(go.Scatter(x=df["date"], y=-df["realized_return"],
                               name="Realized loss", line={"color": "#989898", "width": 0.7}),
                    row=3, col=1)
    for name, color in (("ewma_normal_var", "#157F78"),
                        ("garch_normal_var", "#8759B7"),
                        ("boost_normal_var", "#D47A28"),
                        ("regime_mixture_var_95", "#3066BE")):
        chart.add_trace(go.Scatter(x=df["date"], y=df[name], name=name,
                                   line={"color": color, "width": 1.2}), row=3, col=1)
    chart.update_layout(height=1120, title=f"QuantForge V2 — DEVELOPMENT RESEARCH ({dataset})",
                        legend={"orientation": "h", "y": -0.12},
                        paper_bgcolor="#F8FAFC", plot_bgcolor="white",
                        font={"family": "Arial", "color": "#1E3149"})
    chart.update_yaxes(title_text="Annualized vol", tickformat=".0%", row=1, col=1)
    chart.update_yaxes(title_text="Probability", tickformat=".0%", row=2, col=1)
    chart.update_yaxes(title_text="Daily loss", tickformat=".1%", row=3, col=1)
    chart.write_html(out, include_plotlyjs=True, full_html=True)


def run_v2_study(*, v1_dir: Path, output: Path, mc_paths: int = 20000) -> dict:
    """Evaluate advanced model predictions; only read an already-validated V1 directory."""
    returns, baseline, v1_manifest, provenance = _load_v1(v1_dir)
    output = Path(output)
    if output.resolve() == Path(v1_dir).resolve():
        raise ValueError("V2 output must be separate from V1 evidence")
    aligned = _model_frame(returns, baseline)
    scores, diagnostics = _scores(aligned)
    scenarios = [portfolio_monte_carlo(returns.iloc[-252:].to_numpy(float),
                                       paths=mc_paths, drift=drift)
                 for drift in ("zero", "sample")]
    option_surface, options = _option_research()
    output.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(output / "advanced_forecasts.csv", index=False, float_format="%.12g")
    scores.to_csv(output / "forecast_model_scores.csv", index=False, float_format="%.12g")
    # Stability audit reports near-zero forecasts rather than hiding them.
    stability_rows = []
    for key in ("ridge_variance", "gradient_boosting_variance"):
        values = aligned[key].to_numpy(float)
        stability_rows.append({
            "model": key, "observations": len(values),
            "minimum_forecast_variance": float(values.min()),
            "median_forecast_variance": float(np.median(values)),
            "near_1e_minus_10_guard_count": int(np.count_nonzero(values <= 1.01e-10)),
        })
    pd.DataFrame(stability_rows).to_csv(
        output / "variance_forecast_stability.csv", index=False, float_format="%.12g"
    )
    diagnostics.to_csv(output / "var_coverage_comparison.csv", index=False, float_format="%.12g")
    option_surface.to_csv(output / "option_sensitivity.csv", index=False, float_format="%.12g")
    write_json(output / "option_model_validation.json", options)
    write_json(output / "portfolio_monte_carlo.json", {"scenarios": scenarios})
    manifest = {"release": "2.0.1-development-research", "created_utc": dt.datetime.now(dt.UTC).isoformat(),
                **provenance, "holdout_2019_to_2025": "excluded_unread",
                "v1_research_window": v1_manifest["research_window"],
                "analysis_window": [str(aligned["date"].min().date()),
                                    str(aligned["date"].max().date())],
                "evaluation_dates": len(aligned),
                "predictor_history": "All predictors use returns through t-1",
                "ml_model_parameters": "Fixed ridge alpha 12, gradient boosting 60 iter, 7 leaves",
                "ml_refit_every_sessions": 63, "regime_states": 2,
                "regime_em_iterations": 15, "regime_refit_every_sessions": 126,
                "regime_window_sessions": 504,
                "mc_market_assumption": "hypothetical iid Gaussian scenarios, not historical claims",
                "options_assumption": "hypothetical Black-Scholes inputs, not actual options quotes",
                "provider_rights": "KEEP ALL EMPIRICAL OUTPUTS PRIVATE pending licensing review"}
    write_json(output / "manifest_v2.json", manifest)
    _dashboard(aligned, output / "advanced_dashboard.html", provenance["dataset"])
    merged = diagnostics.merge(scores, on="model", how="left").sort_values("model")
    lines = ["| Model | Exceptions | Exception rate | Kupiec p-value | Mean pinball loss | Mean QLIKE |",
             "|---|---:|---:|---:|---:|---:|"]
    for _, row in merged.iterrows():
        qlike = (f"{row['mean_qlike']:.5f}" if pd.notna(row["mean_qlike"]) else "n/a")
        lines.append(f"| {row['model']} | {int(row['exceptions'])} | "
                     f"{row['exception_rate']:.2%} | {row['kupiec_pvalue']:.4f} | "
                     f"{row['mean_pinball_loss']:.6f} | {qlike} |")
    report = ("# QuantForge V2 — Development Research (not final holdout)\n\n"
              f"Dataset origin: `{provenance['dataset']}`; evaluated {len(aligned)} common dates. "
              "**Do not claim 2019–2025 holdout validation.**\n\n"
              "## Same-date volatility and 95% VaR comparison\n\n"
              + "\n".join(lines) + "\n\n"
              "**Research status:** The simplest baselines remain required comparators. "
              "An apparently lower error does not establish significance or investment value. "
              "QLIKE uses noisy squared daily returns; quantile loss is a different objective. "
              "Kupiec coverage does not by itself establish VaR independence or ES calibration.\n\n"
              "**Chronology:** Model fitting, feature creation, regime filtering, and predictions "
              "use only observations dated before each prediction. Hidden-state backward smoothing "
              "is permitted inside historical EM calibration, never for an earlier prediction. "
              "Parameters, state count and refit cadence are fixed development choices.\n\n"
              "## Mathematical-finance components\n\n"
              "`option_model_validation.json` records hypothetical Black–Scholes call/put, "
              "Greeks, and independent antithetic Monte Carlo estimates. "
              "`option_sensitivity.csv` varies maturity and volatility. "
              "`portfolio_monte_carlo.json` contains **assumption-driven** 21-session "
              "portfolio scenario distributions under zero and sample drift; these are not "
              "a calibrated historical crisis forecast.\n\n"
              "## Remaining limitations\n\n"
              "- Present-day reconstructed adjusted prices are not point-in-time corporate-action data.\n"
              "- Retrospective ETF universe and limited development sample.\n"
              "- Gaussian regimes may be sensitive to local EM maxima, state labels, and re-estimation.\n"
              "- Daily squared returns are noisy targets and Gaussian VaR can miss fat tails.\n"
              "- Ridge uses a positive log-link with a 1e-8 proxy stabilizer; log-scale "
              "forecasts are not guaranteed unbiased for conditional expected variance.\n"
              "- No significance-adjusted multiple-model superiority claims.\n"
              "- Option inputs are assumed, with no observed derivatives market data.\n"
              "- Market-data licensing needs review before any public empirical chart/report.\n")
    (output / "V2_RESEARCH_REPORT.md").write_text(report, encoding="utf-8")
    return {"output": str(output.resolve()), "models": len(scores),
            "evaluation_dates": len(aligned), "dataset": provenance["dataset"]}
