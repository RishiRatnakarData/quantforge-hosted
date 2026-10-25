"""Authenticated Tiingo EOD adapter: unshared raw snapshots, strict daily audit.

LEGACY PERSISTENT STORAGE ADAPTER. As of October 2026 Tiingo Starter and
trial plans do NOT permit durable retention of source or derived data.
Only call directly after verifying separate storage rights. The standard V4
CLI disables this workflow. No HTTP call is attempted at import time.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from quantforge.data.contracts import DataContractError, validate_prices
from quantforge.data.sources import ProviderError

DEFAULT_ETFS = ("SPY", "IWM", "EFA", "EEM", "IEF", "TLT", "GLD", "LQD")
_TICKER = re.compile(r"^[A-Z][A-Z0-9.-]{0,15}$")


def _day(value: str) -> str:
    """Only allow exact YYYY-MM-DD dates; never infer ambiguous date formats."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ProviderError("Dates must use YYYY-MM-DD")
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ProviderError("Invalid research date") from exc


def _symbols(symbols: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    value = tuple(symbols)
    if not value or len(value) != len(set(value)) or any(not _TICKER.fullmatch(s) for s in value):
        raise ProviderError("Use distinct, uppercase US ETF symbols")
    return value


def _cache_file(cache_dir: Path, symbol: str, start: str, end: str) -> Path:
    # The exact dated snapshot is cached, never silently expanded or blended.
    return cache_dir / f"tiingo_{symbol}_{start}_{end}.json"


def _parse_records(records: Any, symbol: str, start: str, end: str) -> pd.DataFrame:
    if not isinstance(records, list) or not records:
        raise ProviderError(f"Tiingo provided no daily observations for {symbol}")
    if any(not isinstance(item, dict) for item in records):
        raise ProviderError(f"Invalid Tiingo EOD rows for {symbol}")
    frame = pd.DataFrame(records)
    if not {"date", "adjClose", "close", "divCash", "splitFactor"}.issubset(frame.columns):
        raise ProviderError(f"Missing Tiingo daily fields for {symbol}")
    # Tiingo's midnight-UTC stamp is a daily DATE LABEL, not a real trade timestamp.
    parsed = pd.to_datetime(frame["date"], utc=True, errors="coerce")
    if parsed.isna().any() or (parsed.dt.hour != 0).any() or (parsed.dt.minute != 0).any():
        raise ProviderError(f"Bad daily date labels for {symbol}")
    dates = parsed.dt.tz_localize(None).dt.normalize()
    if ((dates < pd.Timestamp(start)) | (dates > pd.Timestamp(end))).any():
        raise ProviderError(f"Tiingo returned out-of-range dates for {symbol}")
    result = pd.DataFrame({"date": dates, "symbol": symbol, "adjusted_close": frame["adjClose"]})
    try:
        clean = validate_prices(result)
    except DataContractError as exc:
        raise ProviderError(f"Invalid adjusted EOD values for {symbol}: {exc}") from exc
    # Additional checks catch malformed provider values not in the normalized schema.
    for field in ("close", "divCash", "splitFactor"):
        numeric = pd.to_numeric(frame[field], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(numeric).all():
            raise ProviderError(f"Invalid {field} for {symbol}")
        if field != "divCash" and (numeric <= 0).any():
            raise ProviderError(f"Nonpositive {field} for {symbol}")
    return clean


def audit_xnys_calendar(prices: pd.DataFrame) -> dict:
    """Audit true XNYS sessions; no silent filling, smoothing, or date deletion."""
    try:
        import exchange_calendars as xcals
    except ImportError as exc:
        raise ProviderError("exchange-calendars dependency is required for session validation") from exc
    clean = validate_prices(prices)
    actual = pd.DatetimeIndex(clean["date"].unique()).sort_values()
    cal = xcals.get_calendar("XNYS")
    try:
        expected = cal.sessions_in_range(actual.min(), actual.max())
    except (ValueError, IndexError) as exc:
        raise ProviderError("Requested history falls outside the XNYS calendar range") from exc
    outside = actual.difference(expected)
    missing = expected.difference(actual)
    expected_pairs = len(actual) * clean["symbol"].nunique()
    missing_pairs = expected_pairs - len(clean)
    audit = {
        "calendar": "XNYS",
        "session_min": actual.min().date().isoformat(),
        "session_max": actual.max().date().isoformat(),
        "expected_sessions_between_bounds": len(expected),
        "observed_sessions": len(actual),
        "observed_symbols": sorted(clean["symbol"].unique().tolist()),
        "missing_market_sessions": [str(item.date()) for item in missing[:12]],
        "nonmarket_dates": [str(item.date()) for item in outside[:12]],
        "missing_symbol_session_pairs": int(missing_pairs),
        "pass": len(outside) == 0 and len(missing) == 0 and missing_pairs == 0,
    }
    return audit


def load_tiingo_history(
    *,
    symbols: list[str] | tuple[str, ...] = DEFAULT_ETFS,
    start: str = "2010-01-01",
    end: str = "2025-12-31",
    cache_dir: str | Path = "data/private/tiingo",
    token: str | None = None,
    offline: bool = False,
    refresh: bool = False,
    authorized_persistent_storage: bool = False,
    session: requests.Session | None = None,
    calendar_check: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """Get a FIXED research universe with individually hashed private snapshots.

    Uses cache by default, so reruns never silently mix new provider revisions.
    For fresh snapshots use ``refresh=True`` and record the new manifest.
    """
    tickers = _symbols(symbols)
    first, last = _day(start), _day(end)
    if first > last:
        raise ProviderError("Research start date is after end date")
    if offline and refresh:
        raise ProviderError("Cannot refresh in offline mode")
    if not authorized_persistent_storage:
        raise ProviderError(
            "Tiingo Starter/Trial plans prohibit durable data and derived-data storage. "
            "This legacy adapter requires independently verified persistent-storage rights."
        )
    folder = Path(cache_dir)
    auth = token or os.environ.get("TIINGO_API_TOKEN")
    http = session if session is not None else requests.Session()
    frames = []
    files = []
    for symbol in tickers:
        target = _cache_file(folder, symbol, first, last)
        if target.exists() and not refresh:
            try:
                raw = target.read_bytes()
                records = json.loads(raw)
            except (OSError, ValueError) as exc:
                raise ProviderError(f"Corrupted Tiingo cache for {symbol}") from exc
            cache_status = "reused_snapshot"
        else:
            if offline:
                raise ProviderError(f"Missing cached {symbol}; cannot run offline")
            if not auth or not auth.strip():
                raise ProviderError("Set TIINGO_API_TOKEN in PowerShell (do not put it in Git)")
            try:
                response = http.get(
                    f"https://api.tiingo.com/tiingo/daily/{symbol}/prices",
                    headers={"Authorization": f"Token {auth}", "Accept": "application/json"},
                    params={"startDate": first, "endDate": last, "resampleFreq": "daily"},
                    timeout=45,
                )
                response.raise_for_status()
                records = response.json()
            except (requests.RequestException, ValueError) as exc:
                # Do not echo exception content: proxies may include authentication values.
                raise ProviderError(f"Tiingo retrieval failed for {symbol}; check key and access") from exc
            # Validate BEFORE storing response to avoid caching 403/rate-limit JSON.
            _parse_records(records, symbol, first, last)
            raw = json.dumps(records, separators=(",", ":"), allow_nan=False).encode("utf-8")
            folder.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".json.partial")
            temporary.write_bytes(raw)
            # Do not destroy the older raw revision when refreshing a provider snapshot.
            if target.exists():
                old_bytes = target.read_bytes()
                if old_bytes != raw:
                    old_sha = hashlib.sha256(old_bytes).hexdigest()
                    archived = target.with_name(f"{target.stem}_archived_{old_sha}.json")
                    if not archived.exists():
                        archived.write_bytes(old_bytes)
            temporary.replace(target)
            cache_status = "downloaded_snapshot"
        frames.append(_parse_records(records, symbol, first, last))
        files.append({
            "symbol": symbol,
            "snapshot_path": str(target),
            "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "status": cache_status,
            "rows": len(frames[-1]),
        })
    merged = validate_prices(pd.concat(frames, ignore_index=True))
    audit = audit_xnys_calendar(merged) if calendar_check else {"pass": None, "reason": "not_run"}
    if calendar_check and audit["pass"]:
        # Prevent a provider truncating 2010-2025 to 2024-2025 and passing an
        # otherwise internally complete panel. Check requested calendar endpoints.
        import exchange_calendars as xcals

        sessions = xcals.get_calendar("XNYS").sessions_in_range(first, last)
        if len(sessions) == 0:
            raise ProviderError("Requested interval has no XNYS trading sessions")
        if (audit["session_min"] != str(sessions.min().date())
                or audit["session_max"] != str(sessions.max().date())):
            raise ProviderError(
                "Provider history does not cover requested XNYS start/end trading sessions; "
                f"received {audit['session_min']} to {audit['session_max']}"
            )
    if calendar_check and not audit["pass"]:
        raise ProviderError(
            "Daily panel failed XNYS audit; inspect missing sessions/symbols before research: "
            f"missing sessions={audit['missing_market_sessions']}, "
            f"nonmarket={audit['nonmarket_dates']}, missing symbol-session pairs="
            f"{audit['missing_symbol_session_pairs']}"
        )
    manifest = {
        "provider": "Tiingo EOD",
        "source_endpoint": "https://api.tiingo.com/tiingo/daily/{symbol}/prices",
        "symbol_universe": list(tickers),
        "request_start": first,
        "request_end": last,
        "price_basis": "dividend_adjusted_close",
        "provider_field": "adjClose",
        "calendar_audit": audit,
        "private_license": "Tiingo individual/internal-use only; do not commit/share raw files",
        "point_in_time_note": (
            "Snapshot captures provider observations when downloaded; these are NOT archived "
            "point-in-time corporate-action-adjusted historical snapshots."
        ),
        "retrieval_utc": dt.datetime.now(dt.UTC).isoformat(),
        "snapshots": files,
    }
    return merged, manifest
