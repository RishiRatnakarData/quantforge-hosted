"""Quantitative model invariants and causal forecast regression tests."""

import numpy as np
import pandas as pd
import pytest

from quantforge.risk.conditional_coverage import diagnostics_table, independence_test
from quantforge.risk.garch import fit_garch, rolling_garch_forecasts


def test_independence_transition_counts_and_degenerate_case():
    result = independence_test(np.array([0, 0, 1, 1, 0, 1], dtype=bool))
    assert (result["n00"], result["n01"], result["n10"], result["n11"]) == (1, 2, 1, 1)
    assert result["identifiable"]
    assert 0 <= result["pvalue_ind"] <= 1
    flat = independence_test(np.zeros(100, dtype=bool))
    assert flat["lr_ind"] is None
    assert not flat["identifiable"]


def test_independence_rejects_nonbinary_values():
    with pytest.raises(ValueError):
        independence_test(np.array([0, 1, 2, 0]))


def test_coverage_diagnostics_known_exceptions():
    frames = pd.DataFrame({
        "date": pd.bdate_range("2020-01-01", periods=5),
        "realized_return": [0.01, -0.02, -0.01, 0.005, -0.07],
        "garch_normal_var": [0.03] * 5,
    })
    result = diagnostics_table(frames, var_columns=("garch_normal_var",))
    assert result.loc[0, "exceptions"] == 1
    assert result.loc[0, "exception_rate"] == pytest.approx(0.2)
    assert result.loc[0, "n00"] + result.loc[0, "n01"] + result.loc[0, "n10"] + result.loc[0, "n11"] == 4
    assert result.loc[0, "binomial_exact_pvalue"] > 0


def test_garch_filter_matches_hand_calculation():
    rng = np.random.default_rng(200)
    history = rng.normal(0, .01, 105)
    fit = fit_garch(history)
    assert fit.alpha >= 0 and fit.beta >= 0 and fit.alpha + fit.beta < 1
    variance = fit.omega_pct2 / (1 - fit.alpha - fit.beta)
    for r in history:
        variance = fit.omega_pct2 + fit.alpha * (100 * (r - fit.mean_fraction))**2 + fit.beta * variance
    assert fit.forecast_variance(history) == pytest.approx(variance / 10000, rel=1e-11)


def test_garch_rolling_forecasts_causal_with_future_mutation():
    rng = np.random.default_rng(11)
    index = pd.bdate_range("2017-01-01", periods=120)
    r = pd.Series(rng.normal(0, .011, len(index)), index=index)
    original = rolling_garch_forecasts(r, lookback=65, refit_every=25)
    changed = r.copy()
    changed.iloc[-10:] = changed.iloc[-10:] * 5
    altered = rolling_garch_forecasts(changed, lookback=65, refit_every=25)
    # All targets before the edited dates are identical, even across refits.
    pd.testing.assert_frame_equal(original.iloc[:-10], altered.iloc[:-10])
    assert (pd.to_datetime(original["garch_fit_end"]) < original["date"]).all()


def test_garch_constant_series_rejected():
    with pytest.raises(ValueError, match="constant"):
        fit_garch(np.full(80, 0.002))
