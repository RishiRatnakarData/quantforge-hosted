"""Owner-only SEC company facts, cached with filing provenance and missing-data honesty.

Alpaca's asset catalog supplies the selection UI; SEC EDGAR supplies fundamentals.
No market-data credentials or financial statements are sent to public visitors.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import threading
import time
from typing import Any

import requests

from tools.build_public_sec_snapshot import TAGS, _observations

_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")
_LOCK = threading.Lock()
_DIRECTORY: tuple[float, dict[str, tuple[int, str]]] | None = None
_COMPANIES: dict[int, tuple[float, dict]] = {}
_CACHE_SECONDS = 6 * 3600
_DIRECTORY_SECONDS = 24 * 3600
_LAST_SEC_REQUEST = 0.0


class SECFundamentalsError(ValueError):
    """Safe user-facing error; no SEC response body or network details."""


def _agent() -> str:
    agent = os.getenv("SEC_USER_AGENT", "").strip()
    if ("@" not in agent or len(agent) < 12 or len(agent) > 200
            or "example.com" in agent or "\n" in agent or "\r" in agent):
        raise SECFundamentalsError(
            "To load new SEC companies, add SEC_USER_AGENT to the Render environment "
            "with your project name and a real contact email. Existing public SEC data is still available."
        )
    return agent


def _fetch_json(url: str) -> Any:
    # Global serial lock prevents our own instance from rapidly requesting SEC data.
    # Rate limiting is not globally coordinated across independent Render processes.
    global _LAST_SEC_REQUEST
    with _LOCK:
        remaining = 0.55 - (time.monotonic() - _LAST_SEC_REQUEST)
        if remaining > 0:
            time.sleep(remaining)
        _LAST_SEC_REQUEST = time.monotonic()
        try:
            response = requests.get(
                url, headers={"User-Agent": _agent(), "Accept": "application/json"}, timeout=25
            )
            response.raise_for_status()
            if len(response.content) > 18_000_000:
                raise SECFundamentalsError("SEC response exceeds the allowed size.")
            return response.json()
        except (requests.RequestException, json.JSONDecodeError) as exc:
            raise SECFundamentalsError(
                "SEC EDGAR is unavailable or declined this request. Try again later."
            ) from exc


def _ticker_directory() -> dict[str, tuple[int, str]]:
    global _DIRECTORY
    now = time.monotonic()
    with _LOCK:
        if _DIRECTORY and _DIRECTORY[0] > now:
            return _DIRECTORY[1]
    raw = _fetch_json("https://www.sec.gov/files/company_tickers.json")
    if not isinstance(raw, dict) or len(raw) > 100_000:
        raise SECFundamentalsError("SEC issuer directory is unavailable.")
    directory: dict[str, tuple[int, str]] = {}
    for row in raw.values():
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("ticker", "")).upper().strip().replace("-", ".")
        try:
            cik = int(row.get("cik_str", -1))
        except (TypeError, ValueError):
            continue
        if _TICKER_RE.fullmatch(symbol) and 0 < cik < 10**10:
            directory[symbol] = (cik, str(row.get("title", symbol))[:140])
    with _LOCK:
        _DIRECTORY = (time.monotonic() + _DIRECTORY_SECONDS, directory)
    return directory


def _transform(raw: dict, symbol: str, cik: int, name: str, as_of: dt.date) -> dict:
    try:
        returned_cik = int(raw.get("cik", -1)) if isinstance(raw, dict) else -1
    except (TypeError, ValueError):
        returned_cik = -1
    if returned_cik != cik:
        raise SECFundamentalsError("SEC company identity could not be verified.")
    facts = raw.get("facts")
    gaap = facts.get("us-gaap") if isinstance(facts, dict) else None
    if not isinstance(gaap, dict):
        raise SECFundamentalsError("No comparable SEC US-GAAP company facts are available.")
    series = {field: _observations(gaap, tags, as_of) for field, tags in TAGS.items()}
    ends = sorted(series["revenue_usd"], reverse=True)[:3]
    if not ends:
        raise SECFundamentalsError("This issuer has no eligible annual SEC revenue disclosure.")
    annual = []
    for end in ends:
        row: dict = {"fiscal_end": end, "metrics": {}, "sources": {}}
        for field, tags in TAGS.items():
            fact = series[field].get(end)
            row["metrics"][field] = fact["val"] if fact else None
            if fact:
                row["sources"][field] = {
                    "filed": fact.get("filed", ""),
                    "accession": fact.get("accn", ""),
                    "tag": next((tag for tag in tags
                                 if fact in gaap.get(tag, {}).get("units", {}).get("USD", [])), ""),
                }
        ocf = row["metrics"]["operating_cash_flow_usd"]
        capex = row["metrics"]["capex_usd"]
        row["metrics"]["free_cash_flow_usd"] = (
            ocf - capex if ocf is not None and capex is not None else None
        )
        annual.append(row)
    return {"symbol": symbol, "name": name, "cik": cik,
            "source_url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
            "annual": annual, "as_of": as_of.isoformat(), "source": "SEC EDGAR companyfacts"}


def get_company(symbol: str) -> dict:
    symbol = symbol.strip().upper()
    if not _TICKER_RE.fullmatch(symbol):
        raise SECFundamentalsError("Select a valid listed stock from Browse investments.")
    # Bundled public snapshot remains usable without live SEC access; do not rewrite or refresh it.
    from pathlib import Path

    file = Path(__file__).resolve().parents[1] / "web/site/sec_snapshot.json"
    if file.is_file():
        try:
            snapshot = json.loads(file.read_text(encoding="utf-8"))
            for company in snapshot.get("companies", []):
                if company.get("symbol") == symbol:
                    return {**company, "as_of": snapshot.get("as_of", ""),
                            "source": "SEC EDGAR archived public snapshot"}
        except (ValueError, OSError, TypeError):
            pass
    issuer = _ticker_directory().get(symbol)
    if issuer is None:
        raise SECFundamentalsError(
            "No matching SEC issuer was found. ETFs, some foreign listings, and "
            "companies without US-GAAP filings cannot use this valuation scenario."
        )
    cik, name = issuer
    now = time.monotonic()
    with _LOCK:
        cached = _COMPANIES.get(cik)
        if cached and cached[0] > now:
            return cached[1]
    raw = _fetch_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    output = _transform(raw, symbol, cik, name, dt.date.today())
    with _LOCK:
        if len(_COMPANIES) >= 24:
            _COMPANIES.pop(next(iter(_COMPANIES)))
        _COMPANIES[cik] = (time.monotonic() + _CACHE_SECONDS, output)
    return output
