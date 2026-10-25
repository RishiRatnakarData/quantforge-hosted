"""Parse an official Kenneth French *daily* five-factor CSV ZIP archive.

Use for ex-post factor analysis. Daily factor values are not automatically known
at the same day's close for a trading strategy; publication lags are separate.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from quantforge.data.contracts import DataContractError

FACTOR_COLUMNS = ("market_excess", "SMB", "HML", "RMW", "CMA", "RF")


def read_french_five_factor_daily_archive(path: str | Path) -> pd.DataFrame:
    """Parse the first contiguous YYYYMMDD data block; convert percent to fractions."""
    with zipfile.ZipFile(path) as archive:
        candidates = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(candidates) != 1:
            raise DataContractError("Expected exactly one CSV file in the factor archive")
        raw = archive.read(candidates[0]).decode("utf-8-sig", errors="replace")
    lines = raw.splitlines()
    start = None
    for index, line in enumerate(lines):
        header = [value.strip().lower().replace(" ", "") for value in next(csv.reader([line]))]
        if header == ["", "mkt-rf", "smb", "hml", "rmw", "cma", "rf"]:
            start = index + 1
            break
    if start is None:
        raise DataContractError("Five-factor header not found in archive")
    daily = []
    for line in lines[start:]:
        if re.match(r"^\s*\d{8}\s*,", line):
            daily.append(line)
        elif daily:
            break
    if not daily:
        raise DataContractError("No daily eight-digit dates found")
    frame = pd.read_csv(
        io.StringIO("\n".join(daily)),
        header=None,
        names=["date", *FACTOR_COLUMNS],
        dtype={"date": str},
    )
    frame["date"] = pd.to_datetime(frame["date"], format="%Y%m%d", errors="coerce")
    if frame["date"].isna().any() or frame["date"].duplicated().any():
        raise DataContractError("Invalid or duplicate factor dates")
    if not frame["date"].is_monotonic_increasing:
        raise DataContractError("Factor dates must increase")
    for name in FACTOR_COLUMNS:
        frame[name] = pd.to_numeric(frame[name], errors="coerce") / 100.0
    factor_matrix = frame[list(FACTOR_COLUMNS)].to_numpy(dtype=float)
    if not np.isfinite(factor_matrix).all() or (np.abs(factor_matrix) >= 0.999).any():
        raise DataContractError("Bad factor values or missing-value sentinels")
    return frame


def descriptive_factor_regression(
    asset_returns: pd.Series,
    daily_factors: pd.DataFrame,
    *,
    min_overlap: int = 30,
) -> dict:
    """Five-factor ordinary least squares, descriptive NOT executable signal.

    No future sample is used to *trade*, but factor publication lags make this
    regression unsuitable as same-day point-in-time features without revisions.
    """
    if min_overlap < 30:
        raise ValueError("Minimum overlap threshold must be >=30")
    if not asset_returns.index.is_monotonic_increasing or asset_returns.index.has_duplicates:
        raise DataContractError("Asset return dates must increase uniquely")
    required = {"date", *FACTOR_COLUMNS}
    if not required.issubset(daily_factors.columns):
        raise DataContractError("Missing five-factor table fields")
    factors = daily_factors.set_index("date").sort_index()
    if factors.index.has_duplicates:
        raise DataContractError("Duplicate factor dates")
    aligned = pd.DataFrame({"return": asset_returns}).join(factors, how="inner").dropna()
    if len(aligned) < min_overlap:
        raise DataContractError("Insufficient nonmissing factor-date overlap")
    regressors = aligned[["market_excess", "SMB", "HML", "RMW", "CMA"]].to_numpy(dtype=float)
    dependent = aligned["return"].to_numpy(dtype=float) - aligned["RF"].to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(aligned)), regressors])
    coefs, _, rank, singular_values = np.linalg.lstsq(design, dependent, rcond=None)
    if rank != design.shape[1]:
        raise DataContractError("Factor design is singular")
    fitted = design @ coefs
    total_ss = ((dependent - dependent.mean()) ** 2).sum()
    r2 = 1 - float(((dependent - fitted) ** 2).sum() / total_ss) if total_ss > 0 else None
    return {
        "observations": len(aligned),
        "alpha_daily": float(coefs[0]),
        "beta_market": float(coefs[1]),
        "beta_SMB": float(coefs[2]),
        "beta_HML": float(coefs[3]),
        "beta_RMW": float(coefs[4]),
        "beta_CMA": float(coefs[5]),
        "r_squared": r2,
        "condition_number": float(singular_values.max() / singular_values.min()),
        "interpretation": "ex_post_descriptive_factor_exposure_not_trading_signal",
    }
