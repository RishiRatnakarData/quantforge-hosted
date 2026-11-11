"""Cached, owner-only Alpaca asset discovery for the hosted investment workspace.

Names and listing metadata only. Never fetch or send secret headers to a browser.
The directory is not a quote service and has no trading/order capability.
"""

from __future__ import annotations

import os
import re
import threading
import time
from typing import Any

import requests

TRADING_ROOT = "https://paper-api.alpaca.markets"
_SYMBOL = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")
_SUPPORTED_CRYPTO = {"BTC/USD", "ETH/USD", "SOL/USD", "LTC/USD", "AVAX/USD", "DOGE/USD", "LINK/USD"}
_POPULAR = ("AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "WMT", "COST", "AMD", "NFLX", "KO", "XOM", "V", "SPY", "VOO", "QQQ", "VTI", "IWM", "SCHD", "BND")
_LOCK = threading.Lock()
_CACHE: dict[str, tuple[float, list[dict[str, str]]]] = {}
CACHE_SECONDS = 3600


class AssetDirectoryError(ValueError):
    """Provider unavailable or malformed; safe to display to the authenticated owner."""


def _download(asset_class: str) -> list[dict[str, str]]:
    key = os.getenv("ALPACA_API_KEY_ID", "").strip()
    secret = os.getenv("ALPACA_API_SECRET_KEY", "").strip()
    if not key or not secret:
        raise AssetDirectoryError("Alpaca paper API credentials are not configured.")
    try:
        res = requests.get(
            f"{TRADING_ROOT}/v2/assets",
            headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret},
            params={"status": "active", "asset_class": asset_class},
            timeout=20,
        )
        res.raise_for_status()
        raw: Any = res.json()
    except requests.RequestException as exc:
        raise AssetDirectoryError("Alpaca asset directory is unavailable; try again later.") from exc
    except ValueError as exc:
        raise AssetDirectoryError("Alpaca returned invalid asset directory data.") from exc
    if not isinstance(raw, list) or len(raw) > 100_000:
        raise AssetDirectoryError("Alpaca asset directory returned an unexpected response.")
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in raw:
        if not isinstance(row, dict) or row.get("status") != "active" or row.get("tradable") is not True:
            continue
        symbol = str(row.get("symbol") or "").strip().upper()
        if asset_class == "crypto":
            if symbol not in _SUPPORTED_CRYPTO:
                continue  # Other crypto pairs are not yet supported by the virtual ledger.
        elif not _SYMBOL.fullmatch(symbol):
            continue  # Avoid selecting symbols our read-only quote/history endpoints reject.
        if symbol in seen:
            continue
        name = " ".join(str(row.get("name") or symbol).split())[:120]
        exchange = str(row.get("exchange") or "")[:30]
        items.append({"symbol": symbol, "name": name, "exchange": exchange,
                      "asset_class": "crypto" if asset_class == "crypto" else "us_equity",
                      "instrument_type": "crypto" if asset_class == "crypto" else
                      "ETF / fund" if re.search(r"\b(etf|fund|trust|ultrapro|ultra|direxion|graniteshares|t-rex|2x|3x)\b", name, re.I) else "equity listing",
                      "instrument_type_source": "provider asset class" if asset_class == "crypto" else "name heuristic; subtype not independently verified",
                      "tradable": True, "history_status": "Subject to provider/feed entitlement"})
        seen.add(symbol)
    items.sort(key=lambda x: (x["name"].casefold(), x["symbol"]))
    return items


def _get_assets(asset_class: str) -> list[dict[str, str]]:
    now = time.monotonic()
    with _LOCK:
        cached = _CACHE.get(asset_class)
        if cached and cached[0] > now:
            return cached[1]
        assets = _download(asset_class)
        _CACHE[asset_class] = (time.monotonic() + CACHE_SECONDS, assets)
        return assets


def browse(*, category: str = "popular", letter: str = "", query: str = "", page: int = 0) -> dict:
    """Paginate directory on the server. Browsing by category/letter needs no typing."""
    if category not in ("popular", "all", "crypto") or not 0 <= page <= 1000:
        raise ValueError("Select a valid investment category and page.")
    if letter and (len(letter) != 1 or not letter.isascii() or not letter.isalpha()):
        raise ValueError("Select an A-Z letter.")
    query = query.strip().casefold()
    if len(query) > 60:
        raise ValueError("Search text is too long.")
    assets = _get_assets("crypto" if category == "crypto" else "us_equity")
    if category == "popular":
        order = {symbol: i for i, symbol in enumerate(_POPULAR)}
        assets = sorted((x for x in assets if x["symbol"] in order), key=lambda x: order[x["symbol"]])
    if letter:
        assets = [x for x in assets if x["name"].upper().startswith(letter.upper())]
    if query:
        assets = [x for x in assets if query in x["name"].casefold() or query in x["symbol"].casefold()]
        assets.sort(key=lambda x: (0 if x["symbol"].casefold() == query else 1,
                                 0 if x["name"].casefold().startswith(query) else 1,
                                 1 if x.get("instrument_type") == "ETF / fund" else 0,
                                 x["name"].casefold()))
    limit = 24
    total = len(assets)
    start = page * limit
    return {"items": assets[start:start + limit], "total": total, "page": page,
            "pages": max(1, (total + limit - 1) // limit),
            "has_previous": page > 0, "has_next": start + limit < total,
            "category": category, "licensed_private": True,
            "source": "Alpaca paper trading asset directory (cached up to 1 hour)"}
