"""Strict daily market-data contracts and simple-return calculations.

No missing values are filled, inferred, or projected into trading dates.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class DataContractError(ValueError):
    """A dataset failed a required contract."""


PRICE_BASES = frozenset({
    "total_return_index",
    "dividend_adjusted_close",
    "split_adjusted_close",
    "unadjusted_close",
})
PRICE_COLUMNS = ("date", "symbol", "adjusted_close")


def validate_basis(price_basis: str) -> str:
    """Validate declared basis; this does not independently verify a vendor's claims."""
    if not isinstance(price_basis, str) or price_basis not in PRICE_BASES:
        raise DataContractError(f"Unknown price basis: {price_basis!r}")
    return price_basis


def validate_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Return canonical sorted, daily long-form price observations.

    Strictly enforces one finite positive price per (date, symbol). Does not
    silently turn an intraday/tz-aware feed into a daily closing-price feed.
    """
    if not isinstance(prices, pd.DataFrame):
        raise DataContractError("Prices must be a pandas DataFrame")
    missing = set(PRICE_COLUMNS) - set(prices.columns)
    if missing:
        raise DataContractError(f"Missing required price columns: {sorted(missing)}")
    if prices.empty:
        raise DataContractError("Price data cannot be empty")
    frame = prices.loc[:, list(PRICE_COLUMNS)].copy()
    if frame["date"].isna().any():
        raise DataContractError("Missing price dates")
    try:
        parsed_dates = pd.to_datetime(frame["date"], errors="raise")
    except (ValueError, TypeError, OverflowError) as exc:
        raise DataContractError("Unparseable price dates") from exc
    if not isinstance(parsed_dates.dtype, pd.DatetimeTZDtype):
        frame["date"] = parsed_dates
    else:
        raise DataContractError("Timezone-aware timestamps require a documented daily normalization")
    if frame["date"].isna().any() or (frame["date"] != frame["date"].dt.normalize()).any():
        raise DataContractError("Price dates must be daily midnight observations")
    if frame["symbol"].isna().any():
        raise DataContractError("Missing symbols")
    frame["symbol"] = frame["symbol"].astype(str)
    if (frame["symbol"].str.strip() != frame["symbol"]).any() or (frame["symbol"] == "").any():
        raise DataContractError("Symbols cannot be empty or padded with whitespace")
    try:
        frame["adjusted_close"] = pd.to_numeric(frame["adjusted_close"], errors="raise")
    except (ValueError, TypeError) as exc:
        raise DataContractError("Prices must be numeric") from exc
    data = frame["adjusted_close"].to_numpy(dtype=float)
    if not np.isfinite(data).all() or (data <= 0).any():
        raise DataContractError("Prices must be positive and finite")
    if frame.duplicated(subset=["date", "symbol"]).any():
        raise DataContractError("Duplicate date-symbol observations")
    return frame.sort_values(["date", "symbol"]).reset_index(drop=True)


def make_complete_panel(prices: pd.DataFrame) -> pd.DataFrame:
    """Pivot observations to a complete cross-section without filling any gaps."""
    clean = validate_prices(prices)
    panel = clean.pivot(index="date", columns="symbol", values="adjusted_close")
    panel = panel.sort_index().sort_index(axis=1)
    panel.columns.name = "symbol"
    if panel.isna().any().any():
        raise DataContractError("Panel has missing symbol-date observations; no filling is permitted")
    if len(panel) < 2:
        raise DataContractError("At least two price dates are required")
    return panel.astype(float)


def simple_returns(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute P[t]/P[t-1]-1; do not forward-fill missing prices."""
    if not isinstance(panel, pd.DataFrame) or len(panel) < 2:
        raise DataContractError("At least two daily price observations are required")
    if not panel.index.is_monotonic_increasing or panel.index.has_duplicates:
        raise DataContractError("Panel dates must be ascending and unique")
    if panel.isna().any().any():
        raise DataContractError("Panel contains missing prices")
    arr = panel.to_numpy(dtype=float)
    if not np.isfinite(arr).all() or (arr <= 0).any():
        raise DataContractError("Panel contains invalid prices")
    returns = panel.iloc[1:].divide(panel.shift(1).iloc[1:]) - 1
    if not np.isfinite(returns.to_numpy(dtype=float)).all():
        raise DataContractError("Calculated returns are not finite")
    return returns
