"""Scenario arithmetic on portfolio exposures; scenarios are hypothetical, not forecasts."""

from __future__ import annotations

import numpy as np
import pandas as pd

# Fractional one-session price shocks. Hypothetical stress scenarios only.
SCENARIOS = {
    "equity_selloff": {"SPY": -0.10, "IWM": -0.14, "EFA": -0.11, "EEM": -0.16,
                       "IEF": 0.02, "TLT": 0.05, "GLD": 0.04, "LQD": -0.03},
    "rates_up": {"SPY": -0.03, "IWM": -0.05, "EFA": -0.03, "EEM": -0.04,
                 "IEF": -0.04, "TLT": -0.10, "GLD": -0.02, "LQD": -0.05},
    "credit_stress": {"SPY": -0.07, "IWM": -0.11, "EFA": -0.08, "EEM": -0.10,
                      "IEF": 0.01, "TLT": 0.04, "GLD": 0.02, "LQD": -0.09},
    "commodity_spike": {"SPY": -0.02, "IWM": -0.04, "EFA": -0.03, "EEM": 0.00,
                        "IEF": -0.01, "TLT": -0.03, "GLD": 0.12, "LQD": -0.02},
}


def stress_table(latest_weights: pd.DataFrame) -> pd.DataFrame:
    """Linear instantaneous revaluation, excluding fees and nonlinear effects."""
    if latest_weights.empty or not {"strategy", "symbol", "weight"}.issubset(latest_weights):
        raise ValueError("Weight table must include strategy, symbol, weight")
    rows = []
    for strategy, group in latest_weights.groupby("strategy", sort=False):
        symbols = group["symbol"].tolist()
        weights = group["weight"].to_numpy(dtype=float)
        if not np.isfinite(weights).all() or (weights < 0).any() or not np.isclose(weights.sum(), 1):
            raise ValueError("Stress allocation must be fully invested, long only")
        for label, shocks in SCENARIOS.items():
            if not set(symbols).issubset(shocks):
                raise ValueError("Scenario lacks required symbol")
            change = sum(float(w) * shocks[s] for w, s in zip(weights, symbols, strict=True))
            rows.append({"strategy": strategy, "scenario": label,
                         "hypothetical_return": float(change),
                         "hypothetical_loss": float(-change),
                         "assumption": "instantaneous_linear_no_rebalance_no_costs"})
    return pd.DataFrame(rows)
