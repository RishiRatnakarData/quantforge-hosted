"""Chronological long-only portfolio comparison with explicit two-sided trading costs."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from quantforge.backtesting.portfolio import performance_metrics

STRATEGIES = (
    "spy_buy_hold",
    "equal_weight",
    "minimum_variance",
    "shrunk_minimum_variance",
    "regularized_mean_variance",
)


def regularized_covariance(
    training_returns: pd.DataFrame,
    *,
    shrinkage: float = 0.25,
) -> np.ndarray:
    """Shrink sample covariance towards diagonal; fixed shrinkage is NOT Ledoit-Wolf."""
    x = training_returns.to_numpy(dtype=float)
    if x.ndim != 2 or len(x) < 20 or x.shape[1] < 2 or not np.isfinite(x).all():
        raise ValueError("Requires 20+ daily observations of 2+ assets")
    if not 0 <= shrinkage <= 1:
        raise ValueError("Shrinkage must be in [0,1]")
    covariance = np.cov(x, rowvar=False, ddof=1)
    diagonal = np.diag(np.diag(covariance))
    result = (1 - shrinkage) * covariance + shrinkage * diagonal
    return result + np.eye(x.shape[1]) * max(float(np.trace(result)) / x.shape[1] * 1e-7,
                                            1e-12)


def allocation_weights(
    training_returns: pd.DataFrame,
    *,
    strategy: str,
    max_weight: float = 0.35,
    shrinkage: float = 0.25,
    risk_aversion: float = 5.0,
) -> np.ndarray:
    x = training_returns.to_numpy(dtype=float)
    n = training_returns.shape[1]
    if n < 2 or len(x) < 20 or not np.isfinite(x).all():
        raise ValueError("Invalid training returns")
    if not 1 / n - 1e-12 <= max_weight <= 1:
        raise ValueError("Concentration cap is infeasible")
    if strategy == "equal_weight":
        return np.full(n, 1 / n)
    if strategy == "spy_buy_hold":
        if "SPY" not in training_returns.columns:
            raise ValueError("SPY is required for the market benchmark")
        return np.array([float(symbol == "SPY") for symbol in training_returns.columns])
    if strategy not in STRATEGIES:
        raise ValueError("Unknown portfolio allocation strategy")
    # Annualization affects both mean/variance in the same units.
    covariance = regularized_covariance(
        training_returns, shrinkage=0 if strategy == "minimum_variance" else shrinkage
    ) * 252
    expected = np.clip(x.mean(axis=0) * 252, -0.25, 0.25)
    if risk_aversion <= 0:
        raise ValueError("Risk aversion must be positive")

    def objective(weights: np.ndarray) -> float:
        variance = 0.5 * float(weights @ covariance @ weights) * risk_aversion
        if strategy == "regularized_mean_variance":
            return variance - float(expected @ weights)
        return variance

    fit = minimize(
        objective, np.full(n, 1 / n), method="SLSQP",
        constraints=[{"type": "eq", "fun": lambda weights: float(weights.sum() - 1)}],
        bounds=[(0, max_weight)] * n,
        options={"maxiter": 300, "ftol": 1e-11},
    )
    if not fit.success or (fit.x < -1e-7).any() or (
        fit.x > max_weight + 1e-7
    ).any() or abs(fit.x.sum() - 1) > 1e-6:
        raise RuntimeError(f"Portfolio optimization failed for {strategy}: {fit.message}")
    return fit.x


def backtest_allocations(
    returns: pd.DataFrame,
    *,
    lookback: int = 126,
    rebalance_every: int = 21,
    trading_cost_bps: float = 5.0,
    max_weight: float = 0.35,
    shrinkage: float = 0.25,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Trade at previous close, realize current close-to-close return next.

    Cost = bps * SUM of absolute traded notional, counting buys AND sells.
    No borrowing, shorting, slippage model or market impact is represented.
    Initial purchases from cash incur one side of costs. Rebalancing trades
    are computed against weights after previous close-to-close drift.
    """
    if not 20 <= lookback < len(returns) or rebalance_every < 1:
        raise ValueError("Invalid evaluation configuration")
    if not 0 <= trading_cost_bps <= 1000:
        raise ValueError("Trading cost bps must lie in [0,1000]")
    if returns.index.has_duplicates or not returns.index.is_monotonic_increasing:
        raise ValueError("Returns dates must be strictly chronological")
    if returns.columns.has_duplicates:
        raise ValueError("Asset symbols must be unique")
    x = returns.to_numpy(dtype=float)
    if not np.isfinite(x).all() or (x <= -1).any():
        raise ValueError("Return values must be finite and exceed -100%")
    if "SPY" not in returns.columns:
        raise ValueError("SPY required for market benchmark")
    all_paths = []
    all_positions = []
    for name in STRATEGIES:
        weight = None
        gross_wealth = 1.0
        net_wealth = 1.0
        rows = []
        # One-session execution delay: signal uses returns through t-2,
        # order executes at t-1 close, earns t-1 -> t return.
        first = lookback + 1
        for t in range(first, len(returns)):
            rebalance = t == first or (
                name != "spy_buy_hold" and (t - first) % rebalance_every == 0
            )
            cost = 0.0
            turnover = 0.0
            if rebalance:
                target = allocation_weights(
                    returns.iloc[t - lookback - 1:t - 1], strategy=name,
                    max_weight=max_weight,
                    shrinkage=shrinkage,
                )
                if weight is None:
                    traded = float(np.abs(target).sum())  # enter from all cash
                else:
                    traded = float(np.abs(target - weight).sum())  # both legs
                turnover = traded
                cost = traded * trading_cost_bps / 10_000
                weight = target.copy()
                all_positions.extend({
                    "strategy": name, "execution_date": returns.index[t - 1],
                    "training_end": returns.index[t - 2],
                    "symbol": symbol, "weight": float(target[j]),
                    "position_type": "target",
                } for j, symbol in enumerate(returns.columns))
            market = x[t]
            gross = float(weight @ market)
            net = (1 - cost) * (1 + gross) - 1
            gross_wealth *= 1 + gross
            net_wealth *= 1 + net
            if net_wealth <= 0 or not math.isfinite(net_wealth):
                raise ArithmeticError("Impossible portfolio wealth")
            weight = weight * (1 + market) / (1 + gross)
            if t == len(returns) - 1:
                all_positions.extend({
                    "strategy": name, "execution_date": returns.index[t],
                    "training_end": returns.index[t - 2],
                    "symbol": symbol, "weight": float(weight[j]),
                    "position_type": "ending_mark_to_market",
                } for j, symbol in enumerate(returns.columns))
            rows.append({
                "date": returns.index[t], "strategy": name,
                "gross_return": gross, "net_return": net,
                "turnover": turnover, "trading_cost_fraction": cost,
                "gross_wealth": gross_wealth, "wealth": net_wealth,
                "signal_training_end": returns.index[t - 2],
                "execution_close_date": returns.index[t - 1],
            })
        all_paths.append(pd.DataFrame(rows))
    paths = pd.concat(all_paths, ignore_index=True)
    comparisons = pd.DataFrame(performance_metrics(group)
                               for _, group in paths.groupby("strategy", sort=False))
    return paths, comparisons, pd.DataFrame(all_positions)
