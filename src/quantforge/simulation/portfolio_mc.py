"""Illustrative, parametric portfolio Monte Carlo; not a trading backtest."""

from __future__ import annotations

import numpy as np


def portfolio_monte_carlo(returns: np.ndarray, *, horizon: int = 21,
                          paths: int = 20000, seed: int = 20261022,
                          drift: str = "zero") -> dict:
    """IID normal daily returns; scenarios use fixed normal innovation seed.

    Net investable portfolio history is used to estimate volatility, but this
    simulation does NOT reproduce holdings drift, rebalancing, or market crises.
    """
    x = np.asarray(returns, dtype=float).reshape(-1)
    if (len(x) < 30 or not np.isfinite(x).all() or horizon < 1 or paths < 100
            or np.any(x <= -1) or drift not in {"zero", "sample"}):
        raise ValueError("Invalid Monte Carlo configuration")
    sigma = float(x.std(ddof=1))
    mean = 0.0 if drift == "zero" else float(x.mean())
    rng = np.random.default_rng(seed)
    generated = rng.normal(mean, sigma, size=(paths, horizon))
    terminal = np.prod(1.0 + np.clip(generated, -0.999, None), axis=1)
    losses = 1 - terminal
    var95 = float(np.quantile(losses, 0.95))
    return {"horizon_trading_days": horizon, "paths": paths, "seed": seed,
            "daily_drift_assumption": mean, "daily_volatility_estimate": sigma,
            "ending_wealth_mean": float(terminal.mean()),
            "ending_wealth_median": float(np.median(terminal)),
            "probability_of_loss": float((terminal < 1).mean()),
            "loss_var_95": var95,
            "loss_expected_shortfall_95": float(losses[losses >= var95].mean()),
            "model": "iid_normal_fixed_parameters_hypothetical"}
