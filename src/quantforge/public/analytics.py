"""ECB return-risk comparison. Entirely separate from the reserved ETF holdout."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from quantforge.data.storage import sha256_file
from quantforge.forecasting.advanced import rolling_ml_forecast
from quantforge.regimes.markov import rolling_regime_forecasts
from quantforge.risk.conditional_coverage import diagnostics_table
from quantforge.risk.garch import rolling_garch_forecasts
from quantforge.risk.measures import rolling_risk_forecasts

from .ecb import CURRENCIES, REUSE_POLICY

MODELS = ("historical_var", "normal_var", "ewma_normal_var", "garch_normal_var",
          "ridge_normal_var", "boost_normal_var", "regime_mixture_var_95")


def evaluate_fx(panel: pd.DataFrame, *, output: Path, origin: str,
                source_url: str, source_sha: str | None,
                advanced: bool = True, lookback: int = 252) -> dict:
    """Forecast prior-only 95% loss thresholds on ECB EUR-foreign-currency changes.

    This is a return on the unhedged EUR quote, NOT a financed tradable P&L.
    Currency series are NEVER interpreted as dividends/total-return ETFs.
    """
    if origin not in {"ecb_reference_fx", "synthetic_fx_fixture"}:
        raise ValueError("Public research accepts only genuine ECB or synthetic FX origins")
    if list(panel.columns) != list(CURRENCIES) or len(panel) < max(330, lookback + 5):
        raise ValueError("Insufficient aligned observations or unexpected currency universe")
    if (panel <= 0).any().any() or not np.isfinite(panel.to_numpy(float)).all():
        raise ValueError("Invalid FX reference rates")
    if panel.index.has_duplicates or not panel.index.is_monotonic_increasing:
        raise ValueError("Input dates must be unique and chronological")
    output.mkdir(parents=True, exist_ok=True)
    returns = panel.pct_change(fill_method=None).iloc[1:]
    if returns.isna().any().any():
        raise ValueError("Gaps detected in the aligned ECB currency panel")
    base = {}
    all_forecasts = []
    diagnostics = []
    for currency in CURRENCIES:
        fx = returns[currency].rename(currency)
        forecasts = rolling_risk_forecasts(fx, lookback=lookback)
        if not (pd.to_datetime(forecasts["training_end"]) < forecasts["date"]).all():
            raise ValueError("Forward-looking leak in baseline VaR predictions")
        for _, row in diagnostics_table(forecasts).iterrows():
            diagnostics.append({"currency": currency, "model": row["model"],
                                "observations": int(row["observations"]),
                                "exceptions": int(row["exceptions"]),
                                "exception_rate": float(row["exception_rate"]),
                                "kupiec_pvalue": float(row["kupiec_pvalue"]),
                                "pvalue_ind": (float(row["pvalue_ind"])
                                               if pd.notna(row["pvalue_ind"]) else None)})
        base[currency] = {"latest_quote": float(panel[currency].iloc[-1]),
                          "observed_return_days": len(fx),
                          "annualized_volatility": float(fx.std() * np.sqrt(252)),
                          "largest_daily_drop": float(fx.min()),
                          "first_quote": float(panel[currency].iloc[0])}
        shown = forecasts[["date", "realized_return", "historical_var", "normal_var",
                           "ewma_normal_var", "training_end"]].copy()
        shown.insert(0, "currency", currency)
        all_forecasts.append(shown)
    forecast_frames = pd.concat(all_forecasts, ignore_index=True)
    advanced_table = pd.DataFrame()
    if advanced:
        usd = returns["USD"]
        core = rolling_risk_forecasts(usd, lookback=lookback)
        garch = rolling_garch_forecasts(usd, lookback=lookback, refit_every=63)
        ml = rolling_ml_forecast(usd, start_at=max(252, lookback), refit_every=63)
        regime = rolling_regime_forecasts(usd, start_at=max(252, lookback), refit_every=63)
        # Equal target dates, no resampling of observations.
        advanced_table = (core.merge(garch, on="date", validate="one_to_one")
                          .merge(ml.drop(columns=["realized_return"]), on="date",
                                 validate="one_to_one")
                          .merge(regime.drop(columns=["realized_return"]), on="date",
                                 validate="one_to_one"))
        if len(advanced_table) != len(core):
            raise ValueError("Risk models disagree on common evaluation dates")
        for col in ("training_end", "garch_training_end", "ml_fit_end", "model_fit_end",
                    "feature_training_end", "filter_training_end"):
            if col in advanced_table and not (pd.to_datetime(advanced_table[col]) <
                                              advanced_table["date"]).all():
                raise ValueError(f"Future leakage in {col}")
        z = float(norm.ppf(.95))
        advanced_table["ridge_normal_var"] = z * np.sqrt(
            advanced_table["ridge_variance"].to_numpy(float))
        advanced_table["boost_normal_var"] = z * np.sqrt(
            advanced_table["gradient_boosting_variance"].to_numpy(float))
        for _, row in diagnostics_table(advanced_table, var_columns=MODELS).iterrows():
            diagnostics.append({"currency": "USD", "model": row["model"],
                                "observations": int(row["observations"]),
                                "exceptions": int(row["exceptions"]),
                                "exception_rate": float(row["exception_rate"]),
                                "kupiec_pvalue": float(row["kupiec_pvalue"]),
                                "pvalue_ind": (float(row["pvalue_ind"])
                                               if pd.notna(row["pvalue_ind"]) else None),
                                "evaluation": "advanced_common_dates"})
    paths = output / "observed_fx_quotes.csv"
    panel.rename_axis("date").to_csv(paths, float_format="%.10g")
    forecast_frames.to_csv(output / "fx_baseline_forecasts.csv", index=False,
                           float_format="%.12g")
    if advanced:
        advanced_table.to_csv(output / "fx_advanced_usd.csv", index=False,
                              float_format="%.12g")
    rows = pd.DataFrame(diagnostics)
    rows.to_csv(output / "fx_coverage.csv", index=False, float_format="%.12g")
    manifest = {
        "release": "4.1.0", "data_origin": origin,
        "source_url": source_url, "source_sha256": source_sha,
        "reuse_policy_url": REUSE_POLICY if origin == "ecb_reference_fx" else None,
        "series": [f"EXR.D.{cur}.EUR.SP00.A" for cur in CURRENCIES],
        "source_attribution": ("Source: ECB statistics" if origin == "ecb_reference_fx"
                               else "QuantForge deterministic synthetic FX fixture"),
        "quote_convention": "foreign currency units for one EUR; positive change is EUR appreciation",
        "return_definition": "one-period reference-rate percentage change, not investable PnL",
        "missing_day_policy": "intersection_of_observed_daily_quotes_no_interpolation",
        "sample_start": str(panel.index.min().date()),
        "sample_end": str(panel.index.max().date()),
        "observed_quote_days": len(panel),
        "sample_type": "exploratory_historical_model_comparison_not_pure_holdout",
        "historical_etf_holdout_2019_2025": "excluded_not_loaded",
        "lookback_days": lookback,
        "advanced_usd_models": advanced,
        "quote_sha256": sha256_file(paths),
        "latest_summary": base,
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
    }
    (output / "fx_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
