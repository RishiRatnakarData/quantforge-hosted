"""V4: auditable, publication-safe integration of independently run research branches.

Intentionally REFUSES persisted Tiingo Starter results, including derived results.
The integrated report is explicitly labelled by its individual data origins.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from plotly import graph_objects as go
from plotly.subplots import make_subplots

from quantforge.data.storage import sha256_file, write_json


class EvidenceError(ValueError):
    """An invalid, irreconcilable or unlicensed evidence bundle."""


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EvidenceError(f"Missing or unreadable evidence: {path.name}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"Expected JSON object: {path.name}")
    return value


def _read_csv(path: Path, required: set[str]) -> pd.DataFrame:
    try:
        frame = pd.read_csv(path)
    except (OSError, ValueError) as exc:
        raise EvidenceError(f"Missing or unreadable table: {path.name}") from exc
    if frame.empty or not required.issubset(frame.columns):
        raise EvidenceError(f"Incomplete table: {path.name}")
    return frame


def _verify_math(v1: Path, v2: Path, v3: Path) -> dict:
    """Validate lineage, arithmetic and chronology before any aggregation."""
    m1 = _read_json(v1 / "manifest_v1.json")
    m2 = _read_json(v2 / "manifest_v2.json")
    m3 = _read_json(v3 / "manifest_v3.json")
    audit1 = _read_json(v1 / "data_audit.json")
    audit3 = _read_json(v3 / "financial_statement_audit.json")
    if m1.get("dataset") != "simulation" or m2.get("dataset") != "simulation":
        raise EvidenceError(
            "V4 packaging refuses Tiingo-based persistent data and derived outputs. "
            "The current Starter terms prohibit retention. Use synthetic V1/V2 outputs "
            "or separately licensed data after adapting the data provenance policy."
        )
    if m2.get("v1_manifest_sha256") != sha256_file(v1 / "manifest_v1.json"):
        raise EvidenceError("V2 is not derived from the supplied V1 manifest")
    if m2.get("v1_portfolio_paths_sha256") != sha256_file(v1 / "portfolio_paths.csv"):
        raise EvidenceError("V2/V1 portfolio path hashes do not match")
    if m2.get("v1_risk_forecasts_sha256") != sha256_file(v1 / "risk_forecasts.csv"):
        raise EvidenceError("V2/V1 risk forecast hashes do not match")
    if m1.get("holdout_2019_to_2025") != "excluded_unread":
        raise EvidenceError("V1 holdout exclusion attestation missing")
    if m2.get("holdout_2019_to_2025") != "excluded_unread":
        raise EvidenceError("V2 holdout exclusion attestation missing")
    if m3.get("portfolio_2019_2025_holdout_accessed") is not False:
        raise EvidenceError("V3 holdout exclusion attestation missing")
    if m3.get("data_origin") not in {"synthetic_demo", "sec_companyfacts"}:
        raise EvidenceError("Unknown or insufficiently attributed accounting data origin")
    if audit1.get("missing_prices") != 0 or audit1.get("duplicate_price_rows") != 0:
        raise EvidenceError("V1 data contract was not clean")
    if audit3.get("status") != "latest_year_complete_and_balance_reconciled":
        raise EvidenceError("Financial statements did not pass their balance audit")
    scenarios = _read_csv(v3 / "dcf_scenarios.csv", {
        "scenario", "wacc", "terminal_growth", "enterprise_value_usd_millions",
        "equity_value_usd_millions", "net_debt_usd_millions",
        "diluted_shares_millions_proxy", "intrinsic_value_per_share_usd",
        "pv_explicit_fcf_usd_millions", "pv_terminal_usd_millions",
    })
    if set(scenarios["scenario"]) != {"bear", "base", "bull"}:
        raise EvidenceError("V3 requires exactly bear, base and bull scenario entries")
    for _, row in scenarios.iterrows():
        ev = float(row["pv_explicit_fcf_usd_millions"]) + float(row["pv_terminal_usd_millions"])
        equity = ev - float(row["net_debt_usd_millions"])
        per_share = equity / float(row["diluted_shares_millions_proxy"])
        if (not np.isfinite(per_share) or float(row["wacc"]) <= float(row["terminal_growth"])
                or not np.isclose(ev, float(row["enterprise_value_usd_millions"]), rtol=1e-8)
                or not np.isclose(equity, float(row["equity_value_usd_millions"]), rtol=1e-8)
                or not np.isclose(per_share, float(row["intrinsic_value_per_share_usd"]), rtol=1e-8)):
            raise EvidenceError("DCF identity mismatch, nonfinite value or WACC <= terminal growth")
    forecasts = _read_csv(v2 / "advanced_forecasts.csv", {
        "date", "realized_return", "ewma_normal_var", "historical_var", "garch_normal_var",
        "ml_fit_end", "feature_training_end", "model_fit_end", "filter_training_end",
    })
    dates = pd.to_datetime(forecasts["date"], errors="raise")
    if dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise EvidenceError("Duplicate or unsorted advanced risk forecast dates")
    for col in ("ml_fit_end", "feature_training_end", "model_fit_end", "filter_training_end"):
        if not (pd.to_datetime(forecasts[col], errors="raise") < dates).all():
            raise EvidenceError(f"Timing leakage in {col}")
    if len(forecasts) != int(m2.get("evaluation_dates", -1)):
        raise EvidenceError("V2 evaluation-date count disagrees with manifest")
    vals = forecasts["realized_return"].to_numpy(float)
    if not np.isfinite(vals).all():
        raise EvidenceError("Nonfinite realized returns")
    scores = _read_csv(v2 / "forecast_model_scores.csv", {
        "model", "mean_pinball_loss", "mean_qlike"})
    coverage = _read_csv(v2 / "var_coverage_comparison.csv", {
        "model", "observations", "exceptions", "exception_rate", "kupiec_pvalue"})
    metric = _read_csv(v1 / "portfolio_metrics.csv", {
        "strategy", "ending_wealth", "annualized_volatility", "maximum_drawdown"})
    drivers = _read_csv(v3 / "forecast_drivers.csv", {
        "scenario", "forecast_year", "revenue", "ebit", "tax_on_ebit",
        "depreciation_amortization", "capex", "delta_nwc", "unlevered_fcf"})
    for _, r in drivers.iterrows():
        derived = (r["ebit"] - r["tax_on_ebit"] + r["depreciation_amortization"]
                   - r["capex"] - r["delta_nwc"])
        if not np.isclose(derived, r["unlevered_fcf"], rtol=1e-8, atol=1e-6):
            raise EvidenceError("FCFF identity mismatch")
    return {"v1_manifest": m1, "v2_manifest": m2, "v3_manifest": m3,
            "v1_audit": audit1, "v3_audit": audit3,
            "scenarios": scenarios, "drivers": drivers, "forecasts": forecasts,
            "scores": scores, "coverage": coverage, "portfolio": metric}


def _sustained_capex(drivers: pd.DataFrame, scenarios: pd.DataFrame,
                      fraction: float = 0.35) -> dict:
    """Reprice original BASE case under a constant 35% of revenue cash-CapEx ratio.

    Terminal FCFF is recomputed from the stressed fifth-year FCFF; all other
    forecast drivers, growth, WACC, cash/debt and share count remain constant.
    """
    base = scenarios.set_index("scenario").loc["base"]
    rows = drivers.loc[drivers["scenario"] == "base"].sort_values("forecast_year")
    if len(rows) != 5 or list(rows["forecast_year"].astype(int)) != [1, 2, 3, 4, 5]:
        raise EvidenceError("Five sequential base forecast years are required")
    wacc = float(base["wacc"])
    growth = float(base["terminal_growth"])
    if wacc <= growth:
        raise EvidenceError("WACC must exceed perpetuity growth")
    stressed = rows.copy()
    stressed["capex"] = stressed["revenue"] * fraction
    stressed["unlevered_fcf"] = (stressed["ebit"] - stressed["tax_on_ebit"]
                                + stressed["depreciation_amortization"]
                                - stressed["capex"] - stressed["delta_nwc"])
    fcfs = stressed["unlevered_fcf"].to_numpy(float)
    pv_explicit = float(sum(fcf / (1 + wacc)**year for year, fcf in enumerate(fcfs, start=1)))
    tv = float(fcfs[-1] * (1 + growth) / (wacc - growth))
    pv_tv = tv / (1 + wacc)**5
    enterprise = pv_explicit + pv_tv
    equity = enterprise - float(base["net_debt_usd_millions"])
    per_share = equity / float(base["diluted_shares_millions_proxy"])
    return {"capex_to_sales_assumption": fraction, "wacc": wacc,
            "terminal_growth": growth, "pv_explicit_fcf_usd_millions": pv_explicit,
            "pv_terminal_usd_millions": pv_tv, "enterprise_value_usd_millions": enterprise,
            "intrinsic_value_per_share_usd": per_share,
            "original_base_value_per_share_usd": float(base["intrinsic_value_per_share_usd"]),
            "pct_change_from_base": per_share / float(base["intrinsic_value_per_share_usd"]) - 1,
            "scope": "Illustrative one-variable CapEx stress, not a recommendation or forecast"}


def _bootstrap_uncertainty(forecasts: pd.DataFrame, *, seed: int = 20261023,
                           replicates: int = 400, block: int = 21) -> pd.DataFrame:
    """Paired block-bootstrap mean pinball differences against FIXED EWMA benchmark.

    Development-period descriptive inference only. No alpha/significance claim.
    """
    realized = -forecasts["realized_return"].to_numpy(float)
    models = ("historical_var", "normal_var", "ewma_normal_var", "garch_normal_var",
              "ridge_normal_var", "boost_normal_var", "regime_mixture_var_95")
    available = [name for name in models if name in forecasts]
    if "ewma_normal_var" not in available:
        raise EvidenceError("Required fixed EWMA reference forecast missing")

    def loss(name: str) -> np.ndarray:
        q = forecasts[name].to_numpy(float)
        if not np.isfinite(q).all():
            raise EvidenceError(f"Nonfinite VaR forecast for {name}")
        return np.where(realized >= q, .95, -.05) * (realized - q)

    ref = loss("ewma_normal_var")
    n = len(ref)
    if n < 50:
        raise EvidenceError("Insufficient common observations for robustness check")
    rng = np.random.default_rng(seed)
    block = max(1, min(block, n))
    indices = np.empty((replicates, n), dtype=np.int32)
    for b in range(replicates):
        pos = 0
        while pos < n:
            start = rng.integers(0, n)
            take = min(n - pos, block)
            indices[b, pos:pos + take] = (start + np.arange(take)) % n
            pos += take
    records = []
    for name in available:
        delta = loss(name) - ref
        means = delta[indices].mean(axis=1)
        records.append({"model": name, "reference": "ewma_normal_var",
                        "mean_pinball_delta": float(delta.mean()),
                        "bootstrap_ci_low": float(np.quantile(means, .025)),
                        "bootstrap_ci_high": float(np.quantile(means, .975)),
                        "observations": n, "block_sessions": block,
                        "replicates": replicates, "seed": seed,
                        "status": "exploratory_dependence_aware_not_final_holdout"})
    return pd.DataFrame(records)


def _create_dashboard(tables: dict, stress: dict, output: Path, *, synthetic: bool) -> None:
    p = tables["portfolio"].sort_values("ending_wealth", ascending=False)
    c = tables["coverage"].sort_values("model")
    s = tables["scenarios"].sort_values("intrinsic_value_per_share_usd")
    figures = make_subplots(rows=2, cols=2, vertical_spacing=.20, horizontal_spacing=.15,
                            subplot_titles=("Portfolio ending wealth", "95% VaR exception rates",
                                            "DCF value per share", "CapEx stress: base comparison"))
    figures.add_trace(go.Bar(x=p["strategy"], y=p["ending_wealth"], name="Wealth",
                             marker_color="#2864a8"), row=1, col=1)
    figures.add_trace(go.Bar(x=c["model"], y=c["exception_rate"] * 100, name="VaR exceedances",
                             marker_color="#5d778e"), row=1, col=2)
    figures.add_hline(y=5, line_dash="dash", line_color="#af4f4f", row=1, col=2)
    figures.add_trace(go.Bar(x=s["scenario"], y=s["intrinsic_value_per_share_usd"],
                             name="Value/share", marker_color="#307d72"), row=2, col=1)
    figures.add_trace(go.Bar(x=["Original base", "35% CapEx"],
                             y=[stress["original_base_value_per_share_usd"],
                                stress["intrinsic_value_per_share_usd"]],
                             name="Sensitivity", marker_color="#c08b50"), row=2, col=2)
    figures.update_layout(height=950, template="plotly_white", showlegend=False,
                          margin=dict(t=105, b=150, l=75, r=65))
    for row in (1, 2):
        for col in (1, 2):
            figures.update_xaxes(tickangle=-35, row=row, col=col)
    subtitle = ("SYNTHETIC RISK + SYNTHETIC FINANCIALS — demonstration only" if synthetic else
                "SYNTHETIC RISK + REAL SEC FINANCIAL STATEMENTS — separate data origins")
    plot = figures.to_html(full_html=False, include_plotlyjs=True, config={"displaylogo": False})
    title = "QuantForge | Research and Valuation Intelligence"
    content = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta
name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title>
<style>body{{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f4f6f8;color:#172433}}
main{{max-width:1300px;margin:auto;padding:28px}}header{{background:#112638;color:white;padding:30px;border-radius:12px}}
h1{{margin:0 0 12px}}.qual{{color:#f8dda7;font-weight:bold}}section{{background:white;padding:18px;border-radius:12px;margin-top:16px}}
small{{color:#566879}}code{{background:#eef2f5;padding:3px}}a{{color:#125c91}}</style></head><body>
<main><header><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p>
<p class='qual'>RESEARCH DEMONSTRATION — NOT INVESTMENT ADVICE — NOT A FINAL HOLDOUT STUDY</p></header>
<section><h2>Research workstreams</h2><p>The panels below are bundled offline and each retains
its original data-origin designation.</p>
<p><a href='views/portfolio_risk.html'>Portfolio risk and strategy dashboard</a> &nbsp; | &nbsp;
<a href='views/advanced_models.html'>Advanced volatility/regime dashboard</a> &nbsp; | &nbsp;
<a href='views/company_valuation.html'>Corporate financial analysis and DCF</a></p></section>
<section><h2>Comparative analytics</h2>{plot}</section>
<section><h2>Methods and limitations</h2><p>Risk results are generated from a deterministic synthetic
series, not historical ETF data. The valuation branch uses {"a synthetic Company Facts fixture" if synthetic else "public SEC Company Facts"}
with hypothetical operating and discount-rate assumptions. Charts do not imply model superiority,
tradable returns, or an investment recommendation.</p>
<p>Only a separate, expressly licensed data source and a documented rights review can justify publication
of real-market research. Current Tiingo Starter terms prohibit persistent storage of provider and derived data.</p>
<p>See the evidence manifest, portfolio case study, and investment memorandum in the same folder.</p></section>
<footer><small>QuantForge | Research prototype with auditable lineage and data-origin labels.</small></footer></main></body></html>"""
    output.write_text(content, encoding="utf-8")


def run_v4_integration(*, v1_dir: Path, v2_dir: Path, v3_dir: Path,
                       output: Path) -> dict:
    """Prepare integrated evidence and publications; NEVER copy underlying market data."""
    v1, v2, v3, output = map(Path, (v1_dir, v2_dir, v3_dir, output))
    for origin in (v1, v2, v3):
        if not origin.is_dir():
            raise EvidenceError(f"Evidence directory missing: {origin}")
    if any(output.resolve() == path.resolve() for path in (v1, v2, v3)):
        raise EvidenceError("V4 output must not overwrite source evidence")
    tables = _verify_math(v1, v2, v3)
    stress = _sustained_capex(tables["drivers"], tables["scenarios"])
    uncertainty = _bootstrap_uncertainty(tables["forecasts"])
    synthetic = tables["v3_manifest"]["data_origin"] == "synthetic_demo"
    output.mkdir(parents=True, exist_ok=True)
    # Version manifest is deliberately informational, not a rights clearance token.
    names = {"v1": (v1, ("manifest_v1.json", "portfolio_metrics.csv", "risk_forecasts.csv")),
             "v2": (v2, ("manifest_v2.json", "advanced_forecasts.csv", "forecast_model_scores.csv")),
             "v3": (v3, ("manifest_v3.json", "dcf_scenarios.csv", "forecast_drivers.csv"))}
    upstream = {branch: {name: sha256_file(folder / name) for name in files}
                for branch, (folder, files) in names.items()}
    warning = "SYNTHETIC MARKET RESEARCH; NOT EMPIRICAL PERFORMANCE"
    memo = (v3 / "INVESTMENT_MEMO.md").read_text(encoding="utf-8")
    memo_prefix = ("**V4 INTEGRATION NOTICE:** The market-risk branch is SIMULATED. "
                   f"The valuation branch is {'SYNTHETIC' if synthetic else 'PUBLIC SEC FACTS'}; "
                   "DCF operating drivers and WACC are assumptions. Independent valuation audit remains open.\n\n")
    (output / "INVESTMENT_MEMO.md").write_text(memo_prefix + memo, encoding="utf-8")
    uncertainty.to_csv(output / "model_uncertainty.csv", index=False, float_format="%.12g")
    tables["coverage"].to_csv(output / "model_comparison.csv", index=False, float_format="%.12g")
    tables["scenarios"].to_csv(output / "valuation_scenarios.csv", index=False, float_format="%.12g")
    write_json(output / "capex_stress.json", stress)
    manifest = {"project": "QuantForge", "release": "4.1.0", "created_utc": dt.datetime.now(dt.UTC).isoformat(),
                "market_data_origin": "simulation", "valuation_data_origin": tables["v3_manifest"]["data_origin"],
                "publication_status": "DEMONSTRATION_ONLY_NOT_EMPIRICAL_PUBLICATION",
                "license_policy": "No persisted Tiingo Starter source or derived data permitted",
                "holdout_2019_2025": "not_accessed", "market_coverage_dates": len(tables["forecasts"]),
                "v3_as_of": tables["v3_manifest"]["as_of"], "upstream_sha256": upstream,
                "audit": {"v1": "passed_source_contract", "v2": "passed_lineage_and_chronology",
                          "v3": "passed_arithmetic_automatic_only_original_filings_need_independent_review"},
                "mandatory_qualifications": [warning, "No data licensing approval implied",
                                             "No post-2018 historical ETF holdout tested",
                                             "SEC valuation assumptions are hypothetical",
                                             "Multiple comparisons are exploratory"]}
    write_json(output / "evidence_manifest.json", manifest)
    # Workstream dashboards have been validated as synthetic or SEC-origin before copying.
    views = output / "views"
    views.mkdir(parents=True, exist_ok=True)
    for src, dest in (
        (v1 / "risk_dashboard.html", views / "portfolio_risk.html"),
        (v2 / "advanced_dashboard.html", views / "advanced_models.html"),
        (v3 / "valuation_dashboard.html", views / "company_valuation.html"),
    ):
        if not src.is_file() or src.stat().st_size < 100:
            raise EvidenceError(f"Required offline workstream dashboard missing: {src.name}")
        shutil.copyfile(src, dest)
    _create_dashboard(tables, stress, output / "integrated_dashboard.html", synthetic=synthetic)
    return {"output": str(output.resolve()), "model_count": len(tables["coverage"]),
            "scenarios": len(tables["scenarios"]), "evaluation_dates": len(tables["forecasts"]),
            "data_origins": ["simulation", tables["v3_manifest"]["data_origin"]]}
