"""Source-faithful official ECB reference FX observations. No ETF/Tiingo dependency."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import numpy as np
import pandas as pd
import requests

CURRENCIES = ("USD", "GBP", "JPY", "CHF")
API = "https://data-api.ecb.europa.eu/service/data/EXR/"
REUSE_POLICY = (
    "https://www.ecb.europa.eu/stats/ecb_statistics/"
    "governance_and_quality_framework/html/usage_policy.en.html"
)


def build_api_url(start: str, end: str) -> str:
    """Construct a narrowly scoped ECB daily reference-rate data request."""
    dates = (pd.Timestamp(start), pd.Timestamp(end))
    if dates[0] >= dates[1] or dates[1] > pd.Timestamp.today().normalize():
        raise ValueError("The ECB date range must be valid and end no later than today")
    return (f"{API}D.{'+'.join(CURRENCIES)}.EUR.SP00.A"
            f"?startPeriod={dates[0].date()}&endPeriod={dates[1].date()}&format=csvdata")


def decode_ecb_csv(raw: bytes, *, min_common_days: int = 300) -> pd.DataFrame:
    """Parse official CSV as observed, rejecting conflicting or incomplete records.

    Quotes are units of each listed currency per one euro, not tradable prices.
    No filling, interpolation, forward filling, or fabricated weekend observations.
    """
    if not raw or len(raw) > 20_000_000:
        raise ValueError("ECB CSV is empty or exceeds the maximum expected payload")
    try:
        frame = pd.read_csv(io.BytesIO(raw), dtype={"CURRENCY": str})
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Unable to parse ECB SDMX CSV") from exc
    required = {"TIME_PERIOD", "OBS_VALUE", "CURRENCY"}
    if frame.empty or not required.issubset(frame.columns):
        raise ValueError("Missing required ECB SDMX columns")
    checks = {"FREQ": "D", "CURRENCY_DENOM": "EUR", "EXR_TYPE": "SP00", "EXR_SUFFIX": "A"}
    for column, expected in checks.items():
        if column in frame and not frame[column].eq(expected).all():
            raise ValueError(f"Unexpected ECB series dimension: {column}")
    if set(frame["CURRENCY"].astype(str)) != set(CURRENCIES):
        raise ValueError("ECB response must contain exactly the configured four currencies")
    frame["date"] = pd.to_datetime(frame["TIME_PERIOD"], errors="coerce")
    frame["quote"] = pd.to_numeric(frame["OBS_VALUE"], errors="coerce")
    if frame["date"].isna().any() or frame["quote"].isna().any():
        raise ValueError("Invalid date or missing ECB reference quote")
    if not np.isfinite(frame["quote"].to_numpy()).all() or (frame["quote"] <= 0).any():
        raise ValueError("ECB reference quotes must be strictly positive and finite")
    if frame.duplicated(["date", "CURRENCY"]).any():
        raise ValueError("Duplicate ECB observation date/currency")
    if (frame["date"].dt.dayofweek >= 5).any():
        raise ValueError("Unexpected weekend reference-rate observations")
    panel = frame.pivot(index="date", columns="CURRENCY", values="quote")
    panel = panel.reindex(columns=CURRENCIES).dropna(how="any").sort_index()
    if len(panel) < min_common_days:
        raise ValueError("Insufficient common observed ECB business days")
    if panel.index.has_duplicates or not panel.index.is_monotonic_increasing:
        raise ValueError("ECB dates are not uniquely ordered")
    return panel.rename_axis(None, axis=1)


def fetch_ecb(start: str, end: str, *, session=None) -> tuple[pd.DataFrame, bytes, str]:
    """Download once with timeout; verify HTTPS host and CSV contract."""
    url = build_api_url(start, end)
    client = session or requests.Session()
    response = client.get(url, headers={"Accept": "text/csv", "User-Agent":
                          "QuantForge public statistical portfolio study"}, timeout=(12, 60))
    response.raise_for_status()
    if not response.url.startswith(API):
        raise ValueError("ECB request redirected away from the official data API")
    panel = decode_ecb_csv(response.content)
    return panel, response.content, response.url


def raw_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def save_raw_ecb(raw: bytes, output: Path) -> str:
    """Retain original ECB statistics unchanged, rather than republishing edits as source."""
    output.mkdir(parents=True, exist_ok=True)
    location = output / "ecb_original_source.csv"
    location.write_bytes(raw)
    return raw_sha256(raw)
