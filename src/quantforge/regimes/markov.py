"""Two-state Gaussian Markov-switching model with past-only predictive filtering.

EM uses smoothed probabilities ONLY within its historical fitting window.
The real-time prediction uses a forward-filtered state and next-state transition.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq
from scipy.special import logsumexp, ndtr


@dataclass(frozen=True)
class GaussianMarkovModel:
    initial: np.ndarray
    transition: np.ndarray
    means: np.ndarray
    variances: np.ndarray
    log_likelihood: float


def _validate(returns: np.ndarray, minimum: int = 40) -> np.ndarray:
    x = np.asarray(returns, dtype=float).reshape(-1)
    if len(x) < minimum or not np.all(np.isfinite(x)):
        raise ValueError("Requires sufficient finite daily returns")
    if x.std() < 1e-9:
        raise ValueError("Cannot identify regimes from near-constant returns")
    return x


def _log_emission(x: np.ndarray, means: np.ndarray, variances: np.ndarray) -> np.ndarray:
    return -0.5 * (np.log(2 * np.pi * variances)[None, :]
                   + (x[:, None] - means[None, :]) ** 2 / variances[None, :])


def _forward_backward(x: np.ndarray, initial: np.ndarray, transition: np.ndarray,
                      means: np.ndarray, variances: np.ndarray) -> tuple:
    emiss = _log_emission(x, means, variances)
    ln_transition = np.log(transition)
    n = len(x)
    alpha = np.zeros((n, 2))
    scales = np.zeros(n)
    alpha[0] = np.log(initial) + emiss[0]
    scales[0] = logsumexp(alpha[0])
    alpha[0] -= scales[0]
    for t in range(1, n):
        alpha[t] = emiss[t] + logsumexp(alpha[t - 1, :, None] + ln_transition, axis=0)
        scales[t] = logsumexp(alpha[t])
        alpha[t] -= scales[t]
    beta = np.zeros((n, 2))
    for t in range(n - 2, -1, -1):
        beta[t] = logsumexp(ln_transition + emiss[t + 1][None, :]
                                + beta[t + 1][None, :], axis=1) - scales[t + 1]
    loggamma = alpha + beta
    gamma = np.exp(loggamma - logsumexp(loggamma, axis=1, keepdims=True))
    joint = np.zeros((2, 2))
    for t in range(n - 1):
        logxi = (alpha[t, :, None] + ln_transition + emiss[t + 1][None, :]
                 + beta[t + 1][None, :])
        joint += np.exp(logxi - logsumexp(logxi))
    return gamma, joint, float(scales.sum())


def fit_gaussian_markov(returns: np.ndarray, iterations: int = 15) -> GaussianMarkovModel:
    """Estimate a two-state Gaussian HMM using historical-window Baum-Welch EM.

    Variances are ordered low to high at the end. No external latent-state labels.
    A single deterministic start makes this an exploratory regime model, not a
    globally optimized model-selection procedure.
    """
    x = _validate(returns)
    if iterations < 1:
        raise ValueError("iterations must be positive")
    scale = max(float(x.std()) ** 2, 1e-8)
    means = np.array([float(np.median(x)), float(np.mean(x))])
    variances = np.array([max(scale * 0.45, 1e-9), max(scale * 2.8, 1e-9)])
    initial = np.array([0.8, 0.2])
    transition = np.array([[0.97, 0.03], [0.08, 0.92]])
    for _ in range(iterations):
        gamma, joint, _ = _forward_backward(x, initial, transition, means, variances)
        weights = np.maximum(gamma.sum(axis=0), 1e-8)
        next_means = (gamma * x[:, None]).sum(axis=0) / weights
        next_vars = (gamma * (x[:, None] - next_means) ** 2).sum(axis=0) / weights
        means = next_means
        variances = np.maximum(next_vars, scale * 0.025)
        transition = (joint + 0.4) / (joint.sum(axis=1, keepdims=True) + 0.8)
        initial = (gamma[0] + 0.1) / 1.2
    order = np.argsort(variances)
    initial = initial[order]
    transition = transition[np.ix_(order, order)]
    means = means[order]
    variances = variances[order]
    _, _, ll = _forward_backward(x, initial, transition, means, variances)
    return GaussianMarkovModel(initial, transition, means, variances, ll)


def filtered_state(model: GaussianMarkovModel, observed: np.ndarray) -> np.ndarray:
    """End-of-window FILTERED state: never use backward smoothing for forecasting."""
    x = _validate(observed, minimum=1)
    emission = _log_emission(x, model.means, model.variances)
    state = model.initial * np.exp(emission[0] - emission[0].max())
    state /= state.sum()
    for t in range(1, len(x)):
        prior = state @ model.transition
        like = np.exp(emission[t] - emission[t].max())
        state = prior * like
        state /= state.sum()
    return state


def filter_update(model: GaussianMarkovModel, posterior: np.ndarray, realized: float) -> np.ndarray:
    """Filter one newly observed return, never a return from the forecast date."""
    emiss = _log_emission(np.array([realized]), model.means, model.variances)[0]
    prior = np.asarray(posterior, dtype=float) @ model.transition
    state = prior * np.exp(emiss - emiss.max())
    return state / state.sum()


def forecast_from_filtered(model: GaussianMarkovModel, posterior: np.ndarray,
                           confidence: float = 0.95) -> dict:
    """One-step-ahead mixture forecast from latest historical posterior."""
    if not 0.5 < confidence < 1:
        raise ValueError("Invalid confidence")
    probabilities = np.asarray(posterior, dtype=float) @ model.transition
    means, sigma = model.means, np.sqrt(model.variances)

    def mixture_cdf(value: float) -> float:
        return float(np.sum(probabilities * ndtr((value - means) / sigma)))

    low = float(np.min(means - 12 * sigma))
    high = float(np.max(means + 12 * sigma))
    cutoff = brentq(lambda z: mixture_cdf(z) - (1 - confidence), low, high)
    second_moment = float(np.sum(probabilities * (model.variances + means**2)))
    return {"high_volatility_probability": float(probabilities[1]),
            "forecast_variance": second_moment,
            "mixture_var_95": max(0.0, -float(cutoff)),
            "next_state_probabilities": probabilities.copy()}


def next_day_forecast(model: GaussianMarkovModel, observed: np.ndarray,
                      confidence: float = 0.95) -> dict:
    """Convenience next-day forecast using historical observations through t-1."""
    return forecast_from_filtered(model, filtered_state(model, observed), confidence)


def rolling_regime_forecasts(returns, *, start_at: int = 252, fit_window: int = 504,
                             refit_every: int = 126):
    """Sequentially refit and filter Gaussian states without future observations."""
    import pandas as pd

    if (len(returns) <= start_at or start_at < 100 or fit_window < 100 or refit_every < 1
            or not isinstance(returns.index, pd.DatetimeIndex)
            or returns.index.has_duplicates or not returns.index.is_monotonic_increasing):
        raise ValueError("Invalid chronology or training length")
    values = np.asarray(returns, dtype=float)
    rows = []
    model = None
    posterior = None
    last_fit = -1
    for pos in range(start_at, len(values)):
        if model is None or pos - last_fit >= refit_every:
            sample = values[max(0, pos - fit_window):pos]
            model = fit_gaussian_markov(sample)
            posterior = filtered_state(model, sample)
            last_fit = pos
        elif posterior is not None:
            posterior = filter_update(model, posterior, values[pos - 1])
        assert posterior is not None
        prediction = forecast_from_filtered(model, posterior)
        rows.append({"date": returns.index[pos], "model_fit_end": returns.index[last_fit - 1],
                     "filter_training_end": returns.index[pos - 1],
                     "realized_return": values[pos],
                     "regime_high_probability": prediction["high_volatility_probability"],
                     "regime_second_moment": prediction["forecast_variance"],
                     "regime_mixture_var_95": prediction["mixture_var_95"],
                     "regime_low_state_sigma": float(np.sqrt(model.variances[0])),
                     "regime_high_state_sigma": float(np.sqrt(model.variances[1]))})
    return pd.DataFrame(rows)
