"""Constrained, fully invested long-only minimum-variance allocation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def minimum_variance_weights(
    training_returns: pd.DataFrame,
    *,
    max_weight: float = 0.35,
) -> np.ndarray:
    """Optimize only on the supplied historical training window."""
    values = training_returns.to_numpy(dtype=float)
    if values.ndim != 2 or values.shape[0] < 20 or values.shape[1] < 2:
        raise ValueError("Need >=20 days of >=2 assets")
    if not np.isfinite(values).all():
        raise ValueError("Non-finite training returns")
    n = values.shape[1]
    if not 1 / n <= max_weight <= 1:
        raise ValueError("Max weight infeasible for the asset count")
    covariance = np.cov(values, rowvar=False, ddof=1)
    trace = float(np.trace(covariance)) / n
    # Numerical regularization only, not a fitted shrinkage model.
    covariance = covariance + np.eye(n) * max(trace * 1e-7, 1e-12)
    initial = np.full(n, 1 / n)
    result = minimize(
        lambda weights: float(weights @ covariance @ weights) * 1e4,
        initial,
        method="SLSQP",
        bounds=[(0, max_weight)] * n,
        constraints=[{"type": "eq", "fun": lambda weights: weights.sum() - 1}],
        options={"ftol": 1e-11, "maxiter": 300},
    )
    if not result.success:
        raise RuntimeError(f"Minimum-variance optimizer failed: {result.message}")
    if abs(result.x.sum() - 1) > 1e-6 or (result.x < -1e-7).any() or (result.x > max_weight + 1e-7).any():
        raise RuntimeError("Optimization constraints violated")
    return result.x
