"""VaR exception inference (Kupiec POF and Christoffersen independence/CC).

These likelihood ratio tests rely on asymptotic approximations and can have low
power for short samples or extreme tail confidence levels.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import binomtest, chi2

from quantforge.risk.measures import kupiec_coverage


def _bernoulli_ll(ones: int, trials: int, probability: float) -> float:
    zeros = trials - ones
    if not 0 <= ones <= trials or not 0 <= probability <= 1:
        raise ValueError("Invalid Bernoulli likelihood arguments")
    if probability == 0:
        return 0.0 if ones == 0 else -math.inf
    if probability == 1:
        return 0.0 if zeros == 0 else -math.inf
    return ones * math.log(probability) + zeros * math.log1p(-probability)


def independence_test(flags: np.ndarray | pd.Series) -> dict:
    """Christoffersen LR independence test with consecutive transitions.

    Missing days are never silently filled. An all-zero or all-one sample has
    inadequate variation to estimate conditional independence; return null.
    """
    x = np.asarray(flags).reshape(-1)
    if x.dtype.kind not in "biu" or not np.isin(x, [0, 1]).all():
        raise ValueError("Exception flags must be boolean or 0/1")
    if len(x) < 3:
        raise ValueError("At least three observed exceptions are required")
    x = x.astype(bool)
    n00 = int(np.sum(~x[:-1] & ~x[1:]))
    n01 = int(np.sum(~x[:-1] & x[1:]))
    n10 = int(np.sum(x[:-1] & ~x[1:]))
    n11 = int(np.sum(x[:-1] & x[1:]))
    counts = {"n00": n00, "n01": n01, "n10": n10, "n11": n11}
    if x.sum() == 0 or x.sum() == len(x):
        return {**counts, "lr_ind": None, "pvalue_ind": None,
                "identifiable": False}
    d0, d1 = n00 + n01, n10 + n11
    # If a source state was not observed, the alternative collapses onto the
    # unconditional model and a chi-square(1) reference is not informative.
    if d0 == 0 or d1 == 0:
        return {**counts, "lr_ind": None, "pvalue_ind": None,
                "identifiable": False}
    probability = (n01 + n11) / (len(x) - 1)
    ll_null = _bernoulli_ll(n01 + n11, len(x) - 1, probability)
    ll_alt = (_bernoulli_ll(n01, d0, n01 / d0)
              + _bernoulli_ll(n11, d1, n11 / d1))
    statistic = max(0.0, 2 * (ll_alt - ll_null))
    return {**counts, "lr_ind": float(statistic),
            "pvalue_ind": float(chi2.sf(statistic, 1)), "identifiable": True}


def diagnostics_table(
    forecasts: pd.DataFrame,
    *,
    confidence: float = 0.95,
    var_columns: tuple[str, ...] = (
        "historical_var", "normal_var", "ewma_normal_var", "garch_normal_var"
    ),
) -> pd.DataFrame:
    """Backtest one-day loss thresholds against strictly aligned realized returns."""
    if not 0.5 < confidence < 1:
        raise ValueError("Confidence must lie in (.5, 1)")
    if forecasts.empty or "realized_return" not in forecasts.columns:
        raise ValueError("Realized returns are required")
    if "date" not in forecasts or pd.to_datetime(forecasts["date"]).duplicated().any():
        raise ValueError("Each forecast requires a unique target date")
    if not pd.to_datetime(forecasts["date"]).is_monotonic_increasing:
        raise ValueError("Forecast targets must be chronological")
    actual = forecasts["realized_return"].to_numpy(dtype=float)
    if not np.isfinite(actual).all():
        raise ValueError("Realized returns must be finite")
    rows = []
    for key in var_columns:
        if key not in forecasts:
            continue
        var = forecasts[key].to_numpy(dtype=float)
        if not np.isfinite(var).all() or (var < 0).any():
            raise ValueError(f"Invalid one-day VaR series: {key}")
        exceed = -actual > var  # Strict >, as documented
        uc = kupiec_coverage(exceed, confidence)
        ind = independence_test(exceed)
        row = {"model": key, **uc, **ind}
        row["binomial_exact_pvalue"] = float(
            binomtest(int(exceed.sum()), len(exceed), 1 - confidence).pvalue
        )
        if ind["identifiable"]:
            lr_cc = uc["kupiec_lr"] + ind["lr_ind"]
            row["lr_conditional_coverage"] = lr_cc
            row["pvalue_conditional_coverage"] = float(chi2.sf(lr_cc, 2))
        else:
            row["lr_conditional_coverage"] = None
            row["pvalue_conditional_coverage"] = None
        row["mean_exception_loss"] = (float((-actual[exceed]).mean())
                                      if exceed.any() else None)
        row["warnings"] = (
            "Approximate LR asymptotics; low expected exceptions"
            if len(exceed) * (1 - confidence) < 20 else "Approximate LR asymptotics"
        )
        rows.append(row)
    if not rows:
        raise ValueError("No specified forecast model columns found")
    return pd.DataFrame(rows)
