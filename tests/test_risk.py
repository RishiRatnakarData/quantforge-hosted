import numpy as np
import pytest

from quantforge.risk.measures import (
    coverage_table,
    ewma_variance,
    historical_es,
    historical_var,
    kupiec_coverage,
    parametric_var,
    rolling_risk_forecasts,
)


def test_hand_calculated_tail_values():
    returns = np.array([-0.10, -0.05, 0.01, 0.02, 0.03])
    assert historical_var(returns, 0.8) == pytest.approx(0.06)
    assert historical_es(returns, 0.8) == pytest.approx(0.10)


def test_es_at_least_var():
    r = np.linspace(-0.2, 0.1, 200)
    assert historical_es(r) >= historical_var(r)


def test_normal_var_matches_formula():
    returns = np.array([0.01, -0.01, 0.0, 0.02, -0.02])
    assert parametric_var(returns) == pytest.approx(1.6448536269514722 * returns.std(ddof=1))


def test_ewma_weights_recency():
    newer_big_shock = [0.0, 0.0, 0.09]
    older_big_shock = [0.09, 0.0, 0.0]
    assert ewma_variance(newer_big_shock) > ewma_variance(older_big_shock)


@pytest.mark.parametrize("conf", [0, .5, 1.0, 2.0])
def test_confidence_bounds(conf):
    with pytest.raises(ValueError):
        historical_var([0, 0.01], conf)


def test_future_changes_cannot_affect_past_forecasts(return_frame):
    series = return_frame.mean(axis=1)
    a = rolling_risk_forecasts(series, lookback=30)
    altered = series.copy()
    altered.iloc[-1] = -0.7
    b = rolling_risk_forecasts(altered, lookback=30)
    assert np.allclose(a["historical_var"], b["historical_var"])
    assert np.allclose(a["ewma_normal_var"], b["ewma_normal_var"])
    assert a.iloc[-1]["realized_return"] != b.iloc[-1]["realized_return"]
    assert (a["training_end"] < a["date"]).all()


def test_rolling_window_is_lagged(return_frame):
    series = return_frame.mean(axis=1)
    r = rolling_risk_forecasts(series, lookback=25)
    assert r.iloc[0]["historical_var"] == pytest.approx(historical_var(series.iloc[:25]))


def test_coverage_extreme_exception_counts():
    all_miss = kupiec_coverage(np.ones(45, dtype=bool))
    none_miss = kupiec_coverage(np.zeros(45, dtype=bool))
    assert all_miss["exceptions"] == 45
    assert none_miss["exceptions"] == 0
    assert np.isfinite(all_miss["kupiec_lr"])
    assert np.isfinite(none_miss["kupiec_lr"])


def test_coverage_table_rows(return_frame):
    series = return_frame.mean(axis=1)
    f = rolling_risk_forecasts(series, lookback=25)
    coverage = coverage_table(f)
    assert len(coverage) == 3
    assert (coverage["observations"] == len(f)).all()
