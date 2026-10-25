"""Deterministic synthetic weekday price data; NEVER real investment evidence."""

from __future__ import annotations

import numpy as np
import pandas as pd


def simulated_market(rows: int = 330, seed: int = 20261022) -> pd.DataFrame:
    """Construct four positive artificial price paths with an artificial regime shift."""
    if rows < 2 or rows > 100_000:
        raise ValueError("Demo requires 2 to 100,000 simulated weekdays")
    dates = pd.bdate_range("2022-01-03", periods=rows)
    rng = np.random.default_rng(seed)
    tickers = ["SIM_ALPHA", "SIM_BETA", "SIM_GAMMA", "SIM_DELTA"]
    # Correlation and variance shift are entirely specified by the generator.
    common = rng.standard_normal(rows - 1)
    noise = rng.standard_normal((rows - 1, len(tickers)))
    regime = np.where(np.arange(rows - 1) < (rows - 1) // 2, 0.006, 0.014)
    log_returns = (
        np.array([0.00030, 0.00018, 0.00014, 0.00008])
        + regime[:, None] * (0.55 * common[:, None] + 0.65 * noise)
    )
    levels = np.vstack([np.full(len(tickers), 100.0), 100.0 * np.exp(np.cumsum(log_returns, axis=0))])
    return (
        pd.DataFrame(levels, index=dates, columns=tickers)
        .rename_axis("date")
        .stack()
        .rename("adjusted_close")
        .rename_axis(index=["date", "symbol"])
        .reset_index()
        .sort_values(["date", "symbol"])
        .reset_index(drop=True)
    )
