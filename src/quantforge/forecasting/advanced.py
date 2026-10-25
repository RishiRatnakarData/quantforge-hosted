"""Leakage-controlled one-day realized-square-return volatility predictors.

Fixed-model parameters avoid tuning against the reserved 2019-2025 period.
Models are re-estimated using strictly prior observations on a fixed cadence.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from quantforge.risk.measures import ewma_variance

FEATURES = (
    "lag_abs_return", "lag_squared_return", "rv5", "rv21", "rv63",
    "mean_abs21", "ewma21", "downside21",
)


def lagged_volatility_features(returns: pd.Series) -> pd.DataFrame:
    """Row dated t contains returns through t-1 exclusively."""
    if (not isinstance(returns.index, pd.DatetimeIndex)
            or not returns.index.is_monotonic_increasing or returns.index.has_duplicates):
        raise ValueError("Requires unique chronological DatetimeIndex")
    if not np.isfinite(returns.to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite returns")
    x = returns.shift(1)
    sq = x**2
    frame = pd.DataFrame(index=returns.index)
    frame["lag_abs_return"] = x.abs()
    frame["lag_squared_return"] = sq
    for days in (5, 21, 63):
        frame[f"rv{days}"] = sq.rolling(days).mean()
    frame["mean_abs21"] = x.abs().rolling(21).mean()
    frame["ewma21"] = sq.ewm(alpha=0.06, adjust=False, min_periods=21).mean()
    frame["downside21"] = x.clip(upper=0).pow(2).rolling(21).mean()
    return frame.loc[:, FEATURES]


def rolling_ml_forecast(returns: pd.Series, *, start_at: int = 252,
                        refit_every: int = 63, training_window: int = 756) -> pd.DataFrame:
    """Chronological expanding-to-capped-window fit; at t uses labels through t-1.

    The output represents proxy conditional variance, *not* implied volatility.
    Fixed Ridge and gradient-boosting hyperparameters; no holdout-based tuning.
    """
    if start_at < 130 or refit_every < 1 or training_window < 130:
        raise ValueError("Insufficient fitting window")
    if len(returns) <= start_at:
        raise ValueError("No evaluation dates")
    data = lagged_volatility_features(returns)
    # Boosting predicts log1p-scaled squared returns; its inverse is nonnegative.
    target = pd.Series(np.log1p(1e4 * returns.astype(float).pow(2)), index=returns.index)
    # Ridge uses a *log-link*, ensuring strictly positive variance on inversion.
    # Prior V2 applied max(prediction, 0) to the log1p target, mapping negative
    # Ridge extrapolations to 1e-10 variance and destabilizing QLIKE.
    ridge_target = pd.Series(
        np.log(returns.astype(float).pow(2) + 1e-8), index=returns.index
    )
    rows = []
    models = {}
    latest_fit = -1
    for pos in range(start_at, len(returns)):
        # Train feature/label rows only from indices strictly before pos.
        if not models or pos - latest_fit >= refit_every:
            first = max(0, pos - training_window)
            x_train = data.iloc[first:pos]
            y_train = target.iloc[first:pos]
            ridge_y_train = ridge_target.iloc[first:pos]
            valid = x_train.notna().all(axis=1) & y_train.notna() & ridge_y_train.notna()
            if valid.sum() < 60:
                raise ValueError("Insufficient historical model samples")
            models = {
                "ridge": make_pipeline(StandardScaler(), Ridge(alpha=12.0)),
                "gradient_boosting": HistGradientBoostingRegressor(
                    max_iter=60, max_leaf_nodes=7, min_samples_leaf=20,
                    learning_rate=0.05, l2_regularization=3.0, random_state=11,
                ),
            }
            models["ridge"].fit(x_train.loc[valid], ridge_y_train.loc[valid])
            models["gradient_boosting"].fit(x_train.loc[valid], y_train.loc[valid])
            latest_fit = pos
        x_predict = data.iloc[[pos]]
        if x_predict.isna().any().any():
            raise ValueError("Forecast feature incomplete")
        ridge_log_variance = float(models["ridge"].predict(x_predict)[0])
        ridge_variance = float(np.exp(np.clip(ridge_log_variance, -30.0, 0.0)))
        boost_prediction = float(models["gradient_boosting"].predict(x_predict)[0])
        boost_variance = float(np.expm1(max(boost_prediction, 0.0)) / 1e4)
        forecasts = {
            "ridge_variance": float(np.clip(ridge_variance, 1e-10, 0.05)),
            "gradient_boosting_variance": float(np.clip(boost_variance, 1e-10, 0.05)),
        }
        past = returns.iloc[max(0, pos - 252):pos].to_numpy(float)
        rows.append({"date": returns.index[pos],
                     "feature_training_end": returns.index[pos - 1],
                     "model_fit_end": returns.index[latest_fit - 1],
                     "realized_return": float(returns.iloc[pos]),
                     "ridge_variance": forecasts["ridge_variance"],
                     "gradient_boosting_variance": forecasts["gradient_boosting_variance"],
                     "rv21_variance": float(np.mean(past[-21:]**2)),
                     "ewma_variance_proxy": ewma_variance(past)})
    return pd.DataFrame(rows)
