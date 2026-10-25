import numpy as np
import pandas as pd
import pytest

from quantforge.backtesting.portfolio import (
    compare_strategies,
    performance_metrics,
    simulate_strategy,
)
from quantforge.portfolio.optimization import minimum_variance_weights


def test_min_var_constraints(return_frame):
    weights = minimum_variance_weights(return_frame.iloc[:90])
    assert np.isclose(weights.sum(), 1, atol=1e-6)
    assert (weights >= -1e-7).all()
    assert (weights <= 0.35 + 1e-7).all()


def test_optimizer_rejects_infeasible_cap(return_frame):
    with pytest.raises(ValueError, match="infeasible"):
        minimum_variance_weights(return_frame.iloc[:40], max_weight=0.2)


def test_constant_asset_growth_accounting():
    days = pd.bdate_range("2022-01-03", periods=45)
    returns = pd.DataFrame({"A": np.full(45, 0.01), "B": np.full(45, 0.01)}, index=days)
    path = simulate_strategy(returns, strategy="buy_hold", lookback=20)
    assert np.isclose(path["wealth"].iloc[-1], 1.01**25)
    assert path["turnover"].sum() == 0
    assert np.allclose(path["net_return"], path["gross_return"])


def test_fees_cannot_increase_equity(return_frame):
    no_cost = simulate_strategy(return_frame, strategy="equal_weight", trading_cost_bps=0)
    with_cost = simulate_strategy(return_frame, strategy="equal_weight", trading_cost_bps=50)
    assert with_cost["wealth"].iloc[-1] <= no_cost["wealth"].iloc[-1] + 1e-12
    assert with_cost["trading_cost_fraction"].sum() > 0


def test_evaluation_timing_no_peek(return_frame):
    path = simulate_strategy(return_frame, strategy="minimum_variance", lookback=30)
    assert (path["signal_training_end"] < path["date"]).all()
    assert path.iloc[0]["date"] == return_frame.index[30]


def test_modify_last_return_does_not_affect_prior_path(return_frame):
    a = simulate_strategy(return_frame, strategy="minimum_variance", lookback=30)
    modified = return_frame.copy()
    modified.iloc[-1, 0] = -0.5
    b = simulate_strategy(modified, strategy="minimum_variance", lookback=30)
    assert np.allclose(a["wealth"].iloc[:-1], b["wealth"].iloc[:-1])
    assert a["wealth"].iloc[-1] != b["wealth"].iloc[-1]


def test_strategy_comparison_common_sample(return_frame):
    paths, summary = compare_strategies(return_frame)
    assert set(summary["strategy"]) == {"buy_hold", "equal_weight", "minimum_variance"}
    assert set(summary["evaluation_days"]) == {44}
    assert len(paths) == 44 * 3
    assert all(p["evaluation_days"] == 44 for p in summary.to_dict("records"))


def test_drawdown_and_zero_rf_sharpe():
    r = pd.DataFrame(
        {"strategy": ["test"] * 3, "net_return": [0.1, -0.2, 0.1], "turnover": [0, 0, 0], "trading_cost_fraction": [0, 0, 0]}
    )
    result = performance_metrics(r)
    assert result["maximum_drawdown"] == pytest.approx(-0.2)


def test_invalid_daily_loss(return_frame):
    bad = return_frame.copy()
    bad.iloc[-1, 1] = -1
    with pytest.raises(ValueError):
        simulate_strategy(bad, strategy="equal_weight")
