"""Mathematical finance identities and reproducibility tests."""

import math

import numpy as np
import pandas as pd
import pytest

from quantforge.derivatives.black_scholes import monte_carlo_european, price_and_greeks
from quantforge.forecasting.advanced import lagged_volatility_features, rolling_ml_forecast
from quantforge.regimes.markov import (
    filter_update,
    filtered_state,
    fit_gaussian_markov,
    next_day_forecast,
    rolling_regime_forecasts,
)
from quantforge.simulation.portfolio_mc import portfolio_monte_carlo

PARAMS = {"spot": 100.0, "strike": 102.0, "time_years": 0.75,
          "rate": 0.04, "volatility": 0.23, "dividend_yield": 0.015}


def series(n=380):
    rng = np.random.default_rng(10)
    return pd.Series(rng.normal(0, 0.009, n),
                     index=pd.bdate_range("2015-01-01", periods=n))


def test_put_call_parity_and_no_arbitrage():
    call = price_and_greeks(kind="call", **PARAMS)
    put = price_and_greeks(kind="put", **PARAMS)
    t = PARAMS["time_years"]
    parity = (PARAMS["spot"] * math.exp(-PARAMS["dividend_yield"] * t)
              - PARAMS["strike"] * math.exp(-PARAMS["rate"] * t))
    assert call["price"] - put["price"] == pytest.approx(parity, abs=1e-10)
    assert call["price"] > 0 and put["price"] > 0
    assert call["gamma"] == pytest.approx(put["gamma"])
    assert call["vega"] == pytest.approx(put["vega"])
    assert call["delta"] - put["delta"] == pytest.approx(math.exp(-PARAMS["dividend_yield"] * t))


def test_analytic_greeks_match_finite_differences():
    center = price_and_greeks(kind="call", **PARAMS)
    delta = (price_and_greeks(kind="call", **(PARAMS | {"spot": PARAMS["spot"] + 0.01}))["price"]
             - price_and_greeks(kind="call", **(PARAMS | {"spot": PARAMS["spot"] - 0.01}))["price"]) / 0.02
    vega = (price_and_greeks(kind="call", **(PARAMS | {"volatility": PARAMS["volatility"] + 0.0001}))["price"]
            - price_and_greeks(kind="call", **(PARAMS | {"volatility": PARAMS["volatility"] - 0.0001}))["price"]) / 0.0002
    assert delta == pytest.approx(center["delta"], abs=1e-6)
    assert vega == pytest.approx(center["vega"], abs=1e-5)


def test_mc_price_matches_closed_form_within_uncertainty():
    analytic = price_and_greeks(kind="call", **PARAMS)["price"]
    mc = monte_carlo_european(kind="call", paths=40000, seed=42, **PARAMS)
    assert abs(analytic - mc["mc_price"]) < 4 * mc["mc_standard_error"] + 0.01
    assert mc == monte_carlo_european(kind="call", paths=40000, seed=42, **PARAMS)


def test_at_expiry_and_invalid_option_parameters():
    expired = price_and_greeks(spot=110, strike=100, time_years=0, rate=0.02,
                              volatility=0.2)
    assert expired["price"] == 10.0
    assert math.isnan(expired["delta"])
    with pytest.raises(ValueError):
        price_and_greeks(**(PARAMS | {"spot": -5}))
    with pytest.raises(ValueError):
        monte_carlo_european(kind="call", paths=99, **PARAMS)


def test_portfolio_monte_carlo_is_deterministic_and_tail_consistent():
    returns = np.random.default_rng(42).normal(0, 0.01, 252)
    first = portfolio_monte_carlo(returns, paths=2000, seed=7)
    assert first == portfolio_monte_carlo(returns, paths=2000, seed=7)
    assert first["loss_expected_shortfall_95"] >= first["loss_var_95"]
    assert 0 < first["probability_of_loss"] < 1
    with pytest.raises(ValueError):
        portfolio_monte_carlo(np.ones(300) * np.nan)


def test_features_never_use_target_day():
    x = series()
    original = lagged_volatility_features(x)
    modified = x.copy()
    modified.iloc[180] = -0.9
    updated = lagged_volatility_features(modified)
    pd.testing.assert_series_equal(original.iloc[180], updated.iloc[180])
    assert original.iloc[181]["lag_squared_return"] != updated.iloc[181]["lag_squared_return"]


def test_ml_predictions_invariant_to_future_returns():
    x = series(320)
    baseline = rolling_ml_forecast(x, start_at=252, refit_every=40)
    changed = x.copy()
    changed.iloc[-1] = -0.85
    rerun = rolling_ml_forecast(changed, start_at=252, refit_every=40)
    pd.testing.assert_frame_equal(baseline.drop(columns="realized_return"),
                                  rerun.drop(columns="realized_return"), check_exact=True,
                                  obj="Past-only training and current-target exclusion")
    assert (pd.to_datetime(baseline["feature_training_end"]) < baseline["date"]).all()
    assert (pd.to_datetime(baseline["model_fit_end"]) < baseline["date"]).all()


def test_markov_filtered_state_and_predictive_probability():
    x = series(340).to_numpy(float)
    model = fit_gaussian_markov(x[:250], iterations=8)
    assert model.variances[0] <= model.variances[1]
    assert np.allclose(model.transition.sum(axis=1), 1)
    filtered = filtered_state(model, x[:249])
    updated = filter_update(model, filtered, x[249])
    np.testing.assert_allclose(updated, filtered_state(model, x[:250]), atol=1e-10)
    forecast = next_day_forecast(model, x[:250])
    assert 0 <= forecast["high_volatility_probability"] <= 1
    assert forecast["forecast_variance"] > 0
    assert forecast["mixture_var_95"] >= 0


def test_markov_future_shock_does_not_change_earlier_predictions():
    x = series(305)
    prior = rolling_regime_forecasts(x, start_at=252, refit_every=100)
    changed = x.copy()
    changed.iloc[-1] *= 9
    rerun = rolling_regime_forecasts(changed, start_at=252, refit_every=100)
    pd.testing.assert_frame_equal(prior.drop(columns="realized_return"),
                                  rerun.drop(columns="realized_return"), check_exact=True)
    assert (prior["filter_training_end"] < prior["date"]).all()
    assert (prior["model_fit_end"] < prior["date"]).all()


def test_ridge_log_link_does_not_collapse_to_arbitrary_variance_floor():
    """Near-constant returns must not map a negative Ridge forecast to 1e-10."""
    rng = np.random.default_rng(311)
    values = rng.normal(0, 0.0007, 360)
    # Extremely calm observations can produce extrapolations in the previous
    # log1p target; the log-link must remain strictly positive and finite.
    values[150:205] *= 0.05
    sample = pd.Series(values, index=pd.bdate_range("2015-01-01", periods=len(values)))
    forecasts = rolling_ml_forecast(sample, start_at=252, refit_every=30)
    assert np.isfinite(forecasts["ridge_variance"]).all()
    assert (forecasts["ridge_variance"] > 1e-10).all()
    assert (forecasts["ridge_variance"] < 0.05).all()
    loss = np.log(forecasts["ridge_variance"]) + (
        forecasts["realized_return"] ** 2 / forecasts["ridge_variance"]
    )
    assert np.isfinite(loss).all()
    assert abs(loss.mean()) < 100.0
