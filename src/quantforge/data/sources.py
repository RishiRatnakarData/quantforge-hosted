"""External provider adapters with explicit attribution and as-of conventions."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests

from quantforge.data.contracts import validate_basis, validate_prices


class ProviderError(RuntimeError):
    """A data source cannot be called or returned invalid provider content."""


def read_market_csv(path: str | Path, *, vendor: str, price_basis: str) -> pd.DataFrame:
    """Read a user-provided, authorized market-data file; retain metadata separately."""
    if not isinstance(vendor, str) or not vendor.strip():
        raise ValueError("A nonempty vendor attribution is mandatory")
    validate_basis(price_basis)
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as exc:
        raise ProviderError(f"Cannot read market CSV: {path}") from exc
    return validate_prices(frame)


def fred_vintage(
    series_id: str,
    *,
    as_of: str,
    observation_start: str,
    api_key: str | None = None,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Request FRED observations with a fixed same-day real-time vintage.

    Date-level historical availability is NOT intraday release-time proof.
    """
    key = api_key or os.environ.get("FRED_API_KEY")
    if not key:
        raise ProviderError("FRED_API_KEY is required to retrieve FRED/ALFRED vintages")
    if not series_id or not str(series_id).strip():
        raise ProviderError("FRED series ID is required")
    as_of_date = pd.Timestamp(as_of).date().isoformat()
    start_date = pd.Timestamp(observation_start).date().isoformat()
    if start_date > as_of_date:
        raise ProviderError("FRED observation start is after the as-of date")
    http = session if session is not None else requests.Session()
    try:
        result = http.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id": str(series_id).strip(),
                "api_key": key,
                "file_type": "json",
                "observation_start": start_date,
                "observation_end": as_of_date,
                "realtime_start": as_of_date,
                "realtime_end": as_of_date,
            },
            timeout=30,
        )
        result.raise_for_status()
        payload = result.json()
    except (requests.RequestException, ValueError) as exc:
        raise ProviderError(f"FRED request failed for {series_id}") from exc
    if not isinstance(payload, dict) or "observations" not in payload:
        raise ProviderError("FRED response lacks observations")
    frame = pd.DataFrame(payload["observations"])
    if frame.empty:
        return pd.DataFrame(columns=["date", "value", "realtime_start", "realtime_end"])
    required = {"date", "value", "realtime_start", "realtime_end"}
    if not required.issubset(frame.columns):
        raise ProviderError("FRED observations missing dated vintage fields")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"].replace(".", pd.NA), errors="coerce")
    frame["realtime_start"] = pd.to_datetime(frame["realtime_start"], errors="coerce")
    frame["realtime_end"] = pd.to_datetime(frame["realtime_end"], errors="coerce")
    if frame[["date", "realtime_start", "realtime_end"]].isna().any().any():
        raise ProviderError("Malformed FRED vintage dates")
    if (frame["date"] > pd.Timestamp(as_of_date)).any():
        raise ProviderError("FRED response contains future observation dates")
    return frame.sort_values("date").reset_index(drop=True)


def sec_companyfacts(
    cik: int | str,
    *,
    user_agent: str | None = None,
    session: requests.Session | None = None,
) -> dict:
    """Download SEC Company Facts; filings must subsequently be filtered by filed date."""
    agent = user_agent or os.environ.get("SEC_USER_AGENT")
    if not agent or "@" not in agent or not agent.strip():
        raise ProviderError("SEC_USER_AGENT must identify a real contact for SEC requests")
    try:
        cik_number = int(cik)
    except (TypeError, ValueError) as exc:
        raise ProviderError("CIK must be numeric") from exc
    if not 0 < cik_number <= 9_999_999_999:
        raise ProviderError("Invalid SEC CIK")
    http = session if session is not None else requests.Session()
    try:
        response = http.get(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_number:010d}.json",
            headers={"User-Agent": agent, "Accept-Encoding": "gzip, deflate"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ProviderError(f"SEC Company Facts request failed for CIK {cik_number}") from exc
    if not isinstance(payload, dict) or "facts" not in payload or "cik" not in payload:
        raise ProviderError("Unexpected SEC Company Facts response")
    return payload
