"""Portfolio accounting, executed signal lag, allocation and stress validations."""

import numpy as np
import pandas as pd
import pytest

from quantforge.portfolio.advanced import (
    allocation_weights,
    backtest_allocations,
    regularized_covariance,
)
from quantforge.risk.stress import stress_table


def synthetic_returns(days=180, seed=2026):
    random = np.random.default_rng(seed)
    symbols = ["SPY", "IWM", "EFA", "EEM", "IEF", "TLT", "GLD", "LQD"]
    matrix = random.normal(0.0002, 0.009, (days, len(symbols)))
    return pd.DataFrame(matrix, columns=symbols,
                        index=pd.bdate_range("2014-01-01", periods=days))


def test_covariance_shrinkage_recovers_diagonal():
    returns = synthetic_returns()
    diagonal = regularized_covariance(returns, shrinkage=1)
    assert np.allclose(diagonal - np.diag(np.diag(diagonal)), 0)
    assert np.linalg.eigvalsh(diagonal).min() > 0


def test_constrained_allocations_are_long_only_and_fully_invested():
    returns = synthetic_returns()
    for name in ("minimum_variance", "shrunk_minimum_variance",
                 "regularized_mean_variance"):
        weights = allocation_weights(returns, strategy=name)
        assert weights.sum() == pytest.approx(1, abs=1e-6)
        assert weights.min() > -1e-7
        assert weights.max() < 0.3500001


def test_all_strategies_charge_initial_purchases_and_reconcile_wealth():
    returns = synthetic_returns()
    paths, metrics, positions = backtest_allocations(
        returns, lookback=40, rebalance_every=20, trading_cost_bps=10
    )
    assert len(metrics) == 5
    assert set(metrics["strategy"]) == {
        "spy_buy_hold", "equal_weight", "minimum_variance",
        "shrunk_minimum_variance", "regularized_mean_variance"
    }
    for name, group in paths.groupby("strategy"):
        assert group.iloc[0]["turnover"] == pytest.approx(1)
        assert group.iloc[0]["trading_cost_fraction"] == pytest.approx(0.001)
        assert group["wealth"].iloc[-1] == pytest.approx(np.prod(1 + group["net_return"]))
        assert (group["signal_training_end"] < group["execution_close_date"]).all()
        assert (group["execution_close_date"] < group["date"]).all()
        if name == "spy_buy_hold":
            assert group["turnover"].iloc[1:].sum() == 0
    latest = positions[positions["position_type"] == "ending_mark_to_market"]
    assert len(latest) == len(returns.columns) * 5
    for _, group in latest.groupby("strategy"):
        assert group["weight"].sum() == pytest.approx(1)
    scenarios = stress_table(latest)
    assert len(scenarios) == 5 * 4
    assert np.isfinite(scenarios["hypothetical_loss"]).all()


def test_portfolio_no_future_signals_even_one_day_before_execution():
    returns = synthetic_returns(days=100)
    before, _, _ = backtest_allocations(returns, lookback=30, rebalance_every=10)
    altered = returns.copy()
    altered.iloc[31:] += 0.05
    after, _, _ = backtest_allocations(altered, lookback=30, rebalance_every=10)
    # Return at t=31 does not affect the initial weights chosen using <= t-2.
    initial = before[before["date"] == returns.index[31]].sort_values("strategy")
    revised = after[after["date"] == returns.index[31]].sort_values("strategy")
    np.testing.assert_allclose(initial["turnover"], revised["turnover"])
    np.testing.assert_allclose(initial["trading_cost_fraction"],
                               revised["trading_cost_fraction"])


def test_scenario_rejects_missing_symbols():
    partial = pd.DataFrame({"strategy": ["x", "x"], "symbol": ["SPY", "NOPE"],
                            "weight": [0.5, 0.5]})
    with pytest.raises(ValueError, match="required symbol"):
        stress_table(partial)
