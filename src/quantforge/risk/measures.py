"""Daily one-period downside risk in units of portfolio return."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm


def _vector(returns: pd.Series | np.ndarray) -> np.ndarray:
    array = np.asarray(returns, dtype=float).reshape(-1)
    if len(array) < 2 or not np.isfinite(array).all():
        raise ValueError("At least two finite observations are required")
    return array


def _confidence(confidence: float) -> None:
    if not 0.5 < confidence < 1:
        raise ValueError("Confidence must be strictly between .5 and 1")


def historical_var(returns: pd.Series | np.ndarray, confidence: float = 0.95) -> float:
    _confidence(confidence)
    losses = -_vector(returns)
    return max(0.0, float(np.quantile(losses, confidence)))


def historical_es(returns: pd.Series | np.ndarray, confidence: float = 0.95) -> float:
    """Expected shortfall estimated from the empirical worst 1-alpha fraction.

    Uses fractional interpolation of the boundary order statistic, rather than
    an unstable inclusive-tie rule. Losses may be negative for all-gain samples;
    ES (like VaR) is floored at zero for the loss-budget convention.
    """
    _confidence(confidence)
    losses = np.sort(-_vector(returns))[::-1]
    count = (1 - confidence) * len(losses)
    whole = int(math.floor(count))
    fraction = count - whole
    numerator = losses[:whole].sum()
    if fraction > 1e-12:
        numerator += fraction * losses[whole]
    if count <= 0:
        raise ValueError("Tail count must be positive")
    return max(0.0, float(numerator / count))


def parametric_var(returns: pd.Series | np.ndarray, confidence: float = 0.95) -> float:
    """Normal-model daily VaR: z_alpha * sample_sigma - sample_mean."""
    _confidence(confidence)
    vector = _vector(returns)
    return max(0.0, float(norm.ppf(confidence) * vector.std(ddof=1) - vector.mean()))


def ewma_variance(returns: pd.Series | np.ndarray, decay: float = 0.94) -> float:
    """Exponentially weighted second moment, newest observation highest weight.

    Assumes daily mean approximately zero; it is a variance proxy rather than
    demeaned sample variance. Weights are normalized over the finite window.
    """
    if not 0 < decay < 1:
        raise ValueError("Decay must be between 0 and 1")
    vector = _vector(returns)
    weights = decay ** np.arange(len(vector) - 1, -1, -1)
    return float(np.dot(weights, vector**2) / weights.sum())


def rolling_risk_forecasts(
    returns: pd.Series,
    *,
    lookback: int = 126,
    confidence: float = 0.95,
) -> pd.DataFrame:
    """Predict each day's loss using data ending the PRIOR observation."""
    if lookback < 20 or len(returns) <= lookback:
        raise ValueError("Need >=20 training days and a nonempty evaluation window")
    if not returns.index.is_monotonic_increasing or returns.index.has_duplicates:
        raise ValueError("Dates must be unique and ascending")
    values = _vector(returns)
    forecasts = []
    for pos in range(lookback, len(values)):
        past = values[pos - lookback : pos]
        forecasts.append(
            {
                "date": returns.index[pos],
                "realized_return": float(values[pos]),
                "historical_var": historical_var(past, confidence),
                "historical_es": historical_es(past, confidence),
                "normal_var": parametric_var(past, confidence),
                "normal_variance": float(np.var(past, ddof=1)),
                "ewma_normal_var": max(0.0, float(norm.ppf(confidence) * math.sqrt(ewma_variance(past)))),
                "ewma_variance": ewma_variance(past),
                "training_end": returns.index[pos - 1],
            }
        )
    return pd.DataFrame(forecasts)


def _bern_log_likelihood(successes: int, total: int, probability: float) -> float:
    """Binomial log likelihood, including boundary probability cases."""
    failures = total - successes
    if probability == 0:
        return 0.0 if successes == 0 else -math.inf
    if probability == 1:
        return 0.0 if failures == 0 else -math.inf
    return successes * math.log(probability) + failures * math.log1p(-probability)


def kupiec_coverage(exceptions: pd.Series | np.ndarray, confidence: float = 0.95) -> dict:
    """Kupiec POF likelihood-ratio test of exception frequency (not independence)."""
    _confidence(confidence)
    flags = np.asarray(exceptions, dtype=bool).reshape(-1)
    if len(flags) == 0:
        raise ValueError("No forecast observations")
    n = len(flags)
    x = int(flags.sum())
    p0 = 1 - confidence
    ll_null = _bern_log_likelihood(x, n, p0)
    ll_hat = _bern_log_likelihood(x, n, x / n)
    statistic = max(0.0, float(-2 * (ll_null - ll_hat)))
    return {
        "observations": n,
        "exceptions": x,
        "exception_rate": x / n,
        "expected_exception_rate": p0,
        "kupiec_lr": statistic,
        "kupiec_pvalue": float(chi2.sf(statistic, df=1)),
    }


def coverage_table(forecasts: pd.DataFrame, confidence: float = 0.95) -> pd.DataFrame:
    rows = []
    for key in ("historical_var", "normal_var", "ewma_normal_var"):
        flags = -forecasts["realized_return"].to_numpy() > forecasts[key].to_numpy()
        values = kupiec_coverage(flags, confidence)
        values["model"] = key
        rows.append(values)
    return pd.DataFrame(rows)[
        ["model", "observations", "exceptions", "exception_rate", "expected_exception_rate", "kupiec_lr", "kupiec_pvalue"]
    ]
