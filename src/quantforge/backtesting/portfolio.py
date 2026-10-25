"""Daily portfolio accounting with strictly lagged rebalance signals."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from quantforge.portfolio.optimization import minimum_variance_weights


def simulate_strategy(
    returns: pd.DataFrame,
    *,
    strategy: str,
    lookback: int = 126,
    rebalance_every: int = 21,
    max_weight: float = 0.35,
    trading_cost_bps: float = 5,
) -> pd.DataFrame:
    """Invest at prior close based only on known returns, realize next close return.

    First position is funded at evaluation inception. Thereafter, rebalance costs
    are recognized at the next evaluated return. Turnover is half-L1 absolute
    weight change (one-way traded notional) to avoid counting both buys and sells.
    """
    if strategy not in {"equal_weight", "buy_hold", "minimum_variance"}:
        raise ValueError("Unknown strategy")
    if not (20 <= lookback < len(returns)) or rebalance_every <= 0 or trading_cost_bps < 0:
        raise ValueError("Invalid backtest parameters")
    if returns.isna().any().any() or not np.isfinite(returns.to_numpy(dtype=float)).all():
        raise ValueError("Returns must be complete and finite")
    if (returns <= -1).any().any():
        raise ValueError("Daily returns must be above -100%")
    if not returns.index.is_monotonic_increasing or returns.index.has_duplicates:
        raise ValueError("Dates must be unique and sorted")
    n = returns.shape[1]
    if n < 2:
        raise ValueError("At least two assets required")
    starting = returns.iloc[:lookback]
    if strategy == "minimum_variance":
        weights = minimum_variance_weights(starting, max_weight=max_weight)
    else:
        weights = np.full(n, 1 / n)
    rows = []
    wealth = 1.0
    for i in range(lookback, len(returns)):
        cost = 0.0
        turnover = 0.0
        # Rebalance before the current day's return; training ends at t-1.
        if i > lookback and (i - lookback) % rebalance_every == 0 and strategy != "buy_hold":
            if strategy == "minimum_variance":
                target = minimum_variance_weights(
                    returns.iloc[i - lookback : i], max_weight=max_weight
                )
            else:
                target = np.full(n, 1 / n)
            turnover = float(np.abs(target - weights).sum() / 2)
            cost = turnover * trading_cost_bps / 10_000
            weights = target
        daily = returns.iloc[i].to_numpy(dtype=float)
        gross = float(weights @ daily)
        net = (1 - cost) * (1 + gross) - 1
        wealth *= 1 + net
        if wealth <= 0 or not math.isfinite(wealth):
            raise ArithmeticError("Non-positive or non-finite portfolio wealth")
        weights = weights * (1 + daily) / (1 + gross)
        rows.append(
            {
                "date": returns.index[i],
                "strategy": strategy,
                "gross_return": gross,
                "net_return": net,
                "turnover": turnover,
                "trading_cost_fraction": cost,
                "wealth": wealth,
                "signal_training_end": returns.index[i - 1],
            }
        )
    return pd.DataFrame(rows)


def performance_metrics(path: pd.DataFrame) -> dict:
    values = path["net_return"].to_numpy(dtype=float)
    if not len(values):
        raise ValueError("Empty performance series")
    equity = np.r_[1.0, np.cumprod(1 + values)]
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1
    volatility = float(values.std(ddof=1) * np.sqrt(252)) if len(values) > 1 else 0.0
    annual_return = float(equity[-1] ** (252 / len(values)) - 1)
    sharpe_zero_rf = float(values.mean() / values.std(ddof=1) * np.sqrt(252)) if values.std(ddof=1) > 0 else None
    return {
        "strategy": str(path["strategy"].iloc[0]),
        "evaluation_days": len(values),
        "ending_wealth": float(equity[-1]),
        "annualized_return": annual_return,
        "annualized_volatility": volatility,
        "sharpe_zero_rf": sharpe_zero_rf,
        "maximum_drawdown": float(drawdown.min()),
        "total_turnover": float(path["turnover"].sum()),
        "total_cost_fraction": float(path["trading_cost_fraction"].sum()),
    }


def compare_strategies(returns: pd.DataFrame, **kwargs) -> tuple[pd.DataFrame, pd.DataFrame]:
    paths = [
        simulate_strategy(returns, strategy=name, **kwargs)
        for name in ("buy_hold", "equal_weight", "minimum_variance")
    ]
    result = pd.concat(paths, ignore_index=True)
    summary = pd.DataFrame(performance_metrics(path) for path in paths)
    return result, summary
