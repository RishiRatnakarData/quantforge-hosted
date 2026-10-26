"""Read-only Alpaca US crypto daily bars for the single-owner QuantForge workspace.

Only a small USD pair allowlist used by the existing virtual ledger is queried.
Never return authentication headers, HTTP bodies, or raw exception URLs.
"""

from __future__ import annotations

import datetime as dt
import os
import threading
import time
from typing import Any

import requests

SUPPORTED = frozenset({'BTC/USD', 'ETH/USD', 'SOL/USD', 'LTC/USD', 'AVAX/USD', 'DOGE/USD', 'LINK/USD'})
ENDPOINT = 'https://data.alpaca.markets/v1beta3/crypto/us/bars'
_LOCK = threading.Lock()
_CACHE: dict[tuple[str, str, str], tuple[float, list[dict[str, Any]]]] = {}


class CryptoHistoryError(ValueError):
    """Invalid or unavailable crypto history, safe to display without credentials."""


def _positive(value: Any) -> float:
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise CryptoHistoryError('Alpaca provided an invalid historical crypto close.') from exc
    if not 0 < result < float('inf'):
        raise CryptoHistoryError('Alpaca provided an invalid historical crypto close.')
    return result


def _fetch(symbol: str, first: str, last: str) -> list[dict[str, Any]]:
    key = os.getenv('ALPACA_API_KEY_ID', '').strip()
    secret = os.getenv('ALPACA_API_SECRET_KEY', '').strip()
    if not key or not secret:
        raise CryptoHistoryError('Alpaca paper API credentials are not configured.')
    prices: dict[str, float] = {}
    page: str | None = None
    tokens: set[str] = set()
    for _ in range(8):
        params = {'symbols': symbol, 'timeframe': '1Day', 'start': first,
                  'end': last, 'limit': 10000, 'sort': 'asc'}
        if page:
            params['page_token'] = page
        try:
            response = requests.get(
                ENDPOINT,
                headers={'APCA-API-KEY-ID': key, 'APCA-API-SECRET-KEY': secret},
                params=params,
                timeout=25,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            label = {
                400: 'invalid historical request', 401: 'invalid Alpaca credentials',
                403: 'crypto history is not available to this account',
                429: 'rate limit reached; try later',
            }.get(status, 'provider request failed')
            raise CryptoHistoryError(f'Alpaca crypto history unavailable ({label}).') from exc
        except (requests.RequestException, ValueError) as exc:
            raise CryptoHistoryError('Alpaca crypto history is temporarily unavailable.') from exc
        if not isinstance(payload, dict) or not isinstance(payload.get('bars'), dict):
            raise CryptoHistoryError('Alpaca returned malformed crypto history.')
        bars = payload['bars'].get(symbol, [])
        if not isinstance(bars, list):
            raise CryptoHistoryError('Alpaca returned malformed crypto daily bars.')
        for bar in bars:
            if not isinstance(bar, dict):
                raise CryptoHistoryError('Alpaca returned malformed crypto daily bars.')
            raw = str(bar.get('t') or '')
            # The US crypto 1Day candle is an UTC calendar-day observation.
            if len(raw) < 10 or not (raw.endswith('Z') or '+00:00' in raw):
                raise CryptoHistoryError('Alpaca returned a crypto timestamp without UTC.')
            day = raw[:10]
            try:
                observed = dt.date.fromisoformat(day)
            except ValueError as exc:
                raise CryptoHistoryError('Alpaca returned a malformed crypto date.') from exc
            if not first <= day <= last or observed > dt.datetime.now(dt.UTC).date():
                raise CryptoHistoryError('Crypto bar falls outside the requested UTC period.')
            if day in prices:
                raise CryptoHistoryError('Duplicate crypto daily bar from Alpaca.')
            prices[day] = _positive(bar.get('c'))
        page = payload.get('next_page_token')
        if not page:
            break
        if not isinstance(page, str) or len(page) > 1000 or page in tokens:
            raise CryptoHistoryError('Alpaca returned invalid crypto pagination.')
        tokens.add(page)
    else:
        raise CryptoHistoryError('Crypto history exceeded the page safety limit.')
    if not prices:
        raise CryptoHistoryError(f'No historical crypto observations available for {symbol}.')
    return [{'date': day, 'symbol': symbol, 'close': prices[day]} for day in sorted(prices)]


def history(symbol: str, start: str, end: str) -> list[dict[str, Any]]:
    if symbol not in SUPPORTED:
        raise CryptoHistoryError('Select a supported USD cryptocurrency pair.')
    try:
        first = dt.date.fromisoformat(start)
        last = dt.date.fromisoformat(end)
    except ValueError as exc:
        raise CryptoHistoryError('Dates must be YYYY-MM-DD.') from exc
    if first > last or last > dt.datetime.now(dt.UTC).date() or (last - first).days > 750:
        raise CryptoHistoryError('Select a supported crypto history period.')
    entry = (symbol, start, end)
    now = time.monotonic()
    with _LOCK:
        cached = _CACHE.get(entry)
        if cached and cached[0] > now:
            return [dict(row) for row in cached[1]]
    rows = _fetch(symbol, start, end)
    with _LOCK:
        # Bounded short-lived private cache to reduce free-tier provider requests.
        if len(_CACHE) > 32:
            _CACHE.clear()
        _CACHE[entry] = (time.monotonic() + 600, rows)
    return [dict(row) for row in rows]
