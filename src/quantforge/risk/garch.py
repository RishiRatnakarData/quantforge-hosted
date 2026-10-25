"""Causal Gaussian GARCH(1,1) variance forecasting with scipy.

All fitted parameters use past observed returns; the daily conditional variance
filters subsequent observed innovations until the next scheduled refit.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import norm


@dataclass(frozen=True)
class GarchFit:
    mean_fraction: float
    omega_pct2: float
    alpha: float
    beta: float
    training_size: int
    optimizer_success: bool

    def forecast_variance(self, observed: np.ndarray) -> float:
        """One-day-ahead variance in decimal-return-squared units."""
        past = np.asarray(observed, dtype=float).reshape(-1)
        if len(past) < 2 or not np.isfinite(past).all():
            raise ValueError("Finite historical returns required")
        innovation = 100 * (past - self.mean_fraction)
        variance = self.omega_pct2 / (1 - self.alpha - self.beta)
        for residual in innovation:
            variance = self.omega_pct2 + self.alpha * residual**2 + self.beta * variance
        return float(variance / 10000)


def _unpack(values: np.ndarray) -> tuple[float, float, float]:
    omega = float(np.exp(values[0]))
    persistence = 0.999 * float(expit(values[1]))
    alpha = persistence * float(expit(values[2]))
    beta = persistence - alpha
    return omega, alpha, beta


def fit_garch(past: np.ndarray | pd.Series) -> GarchFit:
    """Estimate stationary zero-mean-residual Gaussian GARCH(1,1).

    Scale data by 100 for conditioning, estimate a constant return mean from
    the historical window, and initialize conditional variance from the sample.
    """
    r = np.asarray(past, dtype=float).reshape(-1)
    if len(r) < 60 or not np.isfinite(r).all() or (r <= -1).any():
        raise ValueError("GARCH requires >=60 finite plausible daily returns")
    mean = float(r.mean())
    innovation = 100 * (r - mean)
    sample_variance = float(np.var(innovation, ddof=1))
    if sample_variance < 1e-10:
        raise ValueError("GARCH cannot fit a constant-return series")

    def objective(parameters: np.ndarray) -> float:
        omega, alpha, beta = _unpack(parameters)
        v = sample_variance
        likelihood = 0.0
        for x in innovation:
            if not np.isfinite(v) or v <= 0:
                return 1e15
            # Conditional likelihood must use variance known BEFORE observing x_t.
            likelihood += np.log(v) + x * x / v
            v = omega + alpha * x * x + beta * v
        return float(0.5 * likelihood)

    initial = np.array([np.log(max(sample_variance * 0.05, 1e-8)), 2.94, -2.94])
    result = minimize(
        objective, initial, method="L-BFGS-B",
        bounds=[(-18, 12), (-8, 6), (-8, 8)],
        options={"maxiter": 350, "ftol": 1e-9},
    )
    if not result.success or not np.isfinite(result.fun):
        raise RuntimeError(f"GARCH optimization did not converge: {result.message}")
    omega, alpha, beta = _unpack(result.x)
    return GarchFit(mean, omega, alpha, beta, len(r), True)


def rolling_garch_forecasts(
    returns: pd.Series,
    *,
    lookback: int = 252,
    refit_every: int = 63,
    confidence: float = 0.95,
) -> pd.DataFrame:
    """Daily lagged forecasts, refitting on a trailing window every N days.

    Date t always receives a forecast constructed with observations <= t-1.
    """
    if not 0.5 < confidence < 1 or lookback < 60 or refit_every < 1:
        raise ValueError("Invalid rolling GARCH configuration")
    if len(returns) <= lookback or not returns.index.is_monotonic_increasing:
        raise ValueError("Insufficient chronological history")
    if returns.index.has_duplicates:
        raise ValueError("Return dates must be unique")
    x = returns.to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("Nonfinite returns")
    rows = []
    fit = None
    fit_end = None
    fit_start = None
    z = float(norm.ppf(confidence))
    for pos in range(lookback, len(x)):
        if fit is None or (pos - lookback) % refit_every == 0:
            fit = fit_garch(x[pos - lookback:pos])
            fit_end = returns.index[pos - 1]
            fit_start = pos - lookback
        # Filter all past observations since the last model fit's window start.
        # No data from position pos or later is used.
        variance = fit.forecast_variance(x[fit_start:pos])
        var = max(0.0, z * np.sqrt(variance) - fit.mean_fraction)
        es = max(0.0, norm.pdf(z) * np.sqrt(variance) / (1 - confidence)
                 - fit.mean_fraction)
        rows.append({
            "date": returns.index[pos],
            "garch_normal_var": float(var),
            "garch_normal_es": float(es),
            "garch_volatility": float(np.sqrt(variance)),
            "garch_fit_end": fit_end,
            "garch_training_end": returns.index[pos - 1],
            "garch_alpha": fit.alpha,
            "garch_beta": fit.beta,
        })
    return pd.DataFrame(rows)
