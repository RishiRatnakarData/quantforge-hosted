"""Alpaca Basic personal-use market data. Never redistribute private feed content.

Public site uses provider-hosted third-party charts. User credentials stay in local
Python process, not HTML, JavaScript, a static site or git. Quotes are IEX-only.
Older historical bars are SIP aggregates with `split` adjustment, *not* adjusted
for cash dividends; simulated returns are explicitly price-only.
"""

from __future__ import annotations

import datetime as dt
import math
import os
import re
import threading
import time
from dataclasses import dataclass
from typing import Any

import requests

API_ROOT = "https://data.alpaca.markets"
SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")


class MarketDataError(ValueError):
    """Invalid market inputs, missing authorization or unavailable provider data."""


def valid_symbol(raw: str) -> str:
    symbol = raw.upper().strip()
    if not SYMBOL_PATTERN.fullmatch(symbol):
        raise MarketDataError("Enter a U.S. ticker such as MSFT, AAPL, NVDA or SPY.")
    return symbol


def positive_number(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MarketDataError(f"The provider sent invalid {name}.") from exc
    if not math.isfinite(number) or number <= 0:
        raise MarketDataError(f"The provider sent invalid {name}.")
    return number


@dataclass(frozen=True)
class CacheEntry:
    value: dict[str, Any]
    expires: float


class AlpacaClient:
    """Lightweight API access restricted to a private local user session."""

    def __init__(self, api_key: str, secret_key: str, *, session: requests.Session | None = None,
                 clock: Any = time.monotonic) -> None:
        if not api_key.strip() or not secret_key.strip():
            raise MarketDataError("Set both ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY locally.")
        self._headers = {"APCA-API-KEY-ID": api_key.strip(),
                         "APCA-API-SECRET-KEY": secret_key.strip()}
        self._session = session or requests.Session()
        self._clock = clock
        self._lock = threading.Lock()
        self._cache: dict[tuple[str, str], CacheEntry] = {}

    @classmethod
    def from_environment(cls) -> AlpacaClient:
        return cls(os.getenv("ALPACA_API_KEY_ID", ""), os.getenv("ALPACA_API_SECRET_KEY", ""))

    def _get(self, endpoint: str, params: dict, *, ttl: int = 60) -> dict:
        # Explicit read-only endpoint, no trading, no retries or background polling.
        cache_key = (endpoint, str(sorted(params.items())))
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached and cached.expires > self._clock():
                return dict(cached.value)
        try:
            res = self._session.get(API_ROOT + endpoint, headers=self._headers,
                                    params=params, timeout=25)
            res.raise_for_status()
            value = res.json()
        except requests.HTTPError as exc:
            # Only expose status, never provider bodies, request headers or URL (which
            # could contain private account details on other endpoints).
            response = exc.response
            code = response.status_code if response is not None else None
            problem = {
                400: "invalid request parameters",
                401: "authentication failed; check the local API keys",
                403: "feed or endpoint access denied; try IEX",
                404: "requested market-data endpoint not found",
                422: "request or feed not permitted",
                429: "rate limit reached; try again later",
            }.get(code, "provider or network error")
            if code is not None and 500 <= code <= 599:
                problem = "Alpaca service error; retry later"
            status = f" (HTTP {code})" if code is not None else ""
            raise MarketDataError(f"Alpaca market-data request failed{status}: {problem}.") from exc
        except requests.RequestException as exc:
            raise MarketDataError("Alpaca network request failed; check your connection and retry.") from exc
        except ValueError as exc:
            raise MarketDataError("Alpaca returned invalid JSON.") from exc
        if not isinstance(value, dict) or "message" in value and "bars" not in value:
            raise MarketDataError("Alpaca rejected the request or returned an unexpected result.")
        with self._lock:
            self._cache[cache_key] = CacheEntry(value, self._clock() + ttl)
        return value

    def quote(self, ticker: str) -> dict:
        """Latest available IEX trade. Never claim it represents full-market NBBO."""
        symbol = valid_symbol(ticker)
        raw = self._get(f"/v2/stocks/{symbol}/trades/latest", {"feed": "iex"}, ttl=30)
        trade = raw.get("trade")
        if not isinstance(trade, dict):
            raise MarketDataError("No IEX trade is available for this ticker.")
        price = positive_number(trade.get("p"), "trade price")
        timestamp = str(trade.get("t") or "unknown")
        return {"symbol": symbol, "price": price, "timestamp": timestamp,
                "venue": "IEX", "coverage": "IEX only; not consolidated US market",
                "source": "Alpaca personal API", "quote_type": "latest_traded_price"}

    def history(self, ticker: str, start: str, end: str) -> list[dict]:
        """Split-adjusted historical SIP 1-day bars; basic plan excludes last 15 minutes."""
        symbol = valid_symbol(ticker)
        try:
            first, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
        except ValueError as exc:
            raise MarketDataError("Dates must be YYYY-MM-DD.") from exc
        if first > last or first < dt.date(2016, 1, 1) or last > dt.date.today():
            raise MarketDataError("Use a valid historical date range from 2016 through today.")
        results: list[dict] = []
        seen_dates: set[str] = set()
        pages: set[str] = set()
        token: str | None = None
        for _ in range(50):
            params = {"timeframe": "1Day", "start": start, "end": end,
                      "feed": "sip", "adjustment": "split", "limit": 10000,
                      "sort": "asc"}
            if token:
                params["page_token"] = token
            raw = self._get(f"/v2/stocks/{symbol}/bars", params, ttl=600)
            bars = raw.get("bars")
            if not isinstance(bars, list):
                raise MarketDataError("Historical bar response is unavailable or malformed.")
            for bar in bars:
                if not isinstance(bar, dict):
                    raise MarketDataError("Malformed historical OHLC row.")
                day = str(bar.get("t", ""))[:10]
                try:
                    dt.date.fromisoformat(day)
                except ValueError as exc:
                    raise MarketDataError("Malformed historical OHLC date.") from exc
                if day in seen_dates:
                    raise MarketDataError("Duplicate date in provider's stock history.")
                seen_dates.add(day)
                results.append({"date": day, "symbol": symbol,
                                "open": positive_number(bar.get("o"), "open"),
                                "close": positive_number(bar.get("c"), "close")})
            token = raw.get("next_page_token")
            if not token:
                break
            if not isinstance(token, str) or token in pages:
                raise MarketDataError("Invalid or repeated history pagination token.")
            pages.add(token)
        else:
            raise MarketDataError("Historical response exceeded safety pagination limit.")
        if not results:
            raise MarketDataError(f"No daily historical bars found for {symbol}.")
        results.sort(key=lambda record: record["date"])
        return results
