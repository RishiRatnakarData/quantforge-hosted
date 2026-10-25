"""Dividend-yield Black-Scholes-Merton European pricing and risk sensitivities."""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm


def price_and_greeks(*, spot: float, strike: float, time_years: float,
                     rate: float, volatility: float, dividend_yield: float = 0.0,
                     kind: str = "call") -> dict:
    """Continuously compounded r and q; vega/rho are per 1.0 unit change.

    Theta is per calendar YEAR, holding model inputs fixed.
    At expiry, or zero volatility, derivatives may be undefined and are NaN.
    """
    if (not all(math.isfinite(v) for v in (spot, strike, time_years, rate,
                                           volatility, dividend_yield))
            or spot <= 0 or strike <= 0 or time_years < 0 or volatility < 0
            or kind not in {"call", "put"}):
        raise ValueError("Invalid option inputs")
    t, r, q, sigma = time_years, rate, dividend_yield, volatility
    forward_pv = spot * math.exp(-q * t)
    strike_pv = strike * math.exp(-r * t)
    if t == 0 or sigma == 0:
        intrinsic = max(0.0, forward_pv - strike_pv) if kind == "call" else max(
            0.0, strike_pv - forward_pv)
        return {"price": intrinsic, "delta": math.nan, "gamma": math.nan,
                "vega": math.nan, "theta": math.nan, "rho": math.nan}
    sqrt_t = math.sqrt(t)
    d1 = (math.log(spot / strike) + (r - q + 0.5 * sigma**2) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    phi = norm.pdf(d1)
    common = -spot * math.exp(-q * t) * phi * sigma / (2 * sqrt_t)
    gamma = math.exp(-q * t) * phi / (spot * sigma * sqrt_t)
    vega = spot * math.exp(-q * t) * phi * sqrt_t
    if kind == "call":
        price = forward_pv * norm.cdf(d1) - strike_pv * norm.cdf(d2)
        delta = math.exp(-q * t) * norm.cdf(d1)
        theta = common - r * strike_pv * norm.cdf(d2) + q * forward_pv * norm.cdf(d1)
        rho = t * strike_pv * norm.cdf(d2)
    else:
        price = strike_pv * norm.cdf(-d2) - forward_pv * norm.cdf(-d1)
        delta = math.exp(-q * t) * (norm.cdf(d1) - 1)
        theta = common + r * strike_pv * norm.cdf(-d2) - q * forward_pv * norm.cdf(-d1)
        rho = -t * strike_pv * norm.cdf(-d2)
    return {"price": float(price), "delta": float(delta), "gamma": float(gamma),
            "vega": float(vega), "theta": float(theta), "rho": float(rho)}


def monte_carlo_european(*, spot: float, strike: float, time_years: float,
                         rate: float, volatility: float, dividend_yield: float = 0.0,
                         kind: str = "call", paths: int = 20000,
                         seed: int = 1123) -> dict:
    """Risk-neutral antithetic terminal-price Monte Carlo with approximate 95% CI."""
    price_and_greeks(spot=spot, strike=strike, time_years=time_years, rate=rate,
                     volatility=volatility, dividend_yield=dividend_yield, kind=kind)
    if paths < 100 or paths % 2:
        raise ValueError("Require an even path count of at least 100")
    rng = np.random.default_rng(seed)
    half = rng.standard_normal(paths // 2)
    shocks = np.column_stack([half, -half])
    terminal = spot * np.exp((rate - dividend_yield - 0.5 * volatility**2) * time_years
                             + volatility * math.sqrt(time_years) * shocks)
    payoff = np.maximum(terminal - strike, 0) if kind == "call" else np.maximum(
        strike - terminal, 0)
    # Pair-averaged payoff is the independent sampling unit under antithetics.
    pairs = math.exp(-rate * time_years) * payoff.mean(axis=1)
    value = float(pairs.mean())
    standard_error = float(pairs.std(ddof=1) / math.sqrt(len(pairs)))
    return {"mc_price": value, "mc_standard_error": standard_error,
            "ci95_lower": value - 1.96 * standard_error,
            "ci95_upper": value + 1.96 * standard_error, "paths": paths}
