"""Current stock, ETF and crypto observations for the private investment desk."""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any

from quantforge.desk.catalog import BY_SYMBOL, display_name
from quantforge.desk.engine import DeskError, asset_type
from quantforge.live.provider import AlpacaClient, positive_number

CRYPTO_ROOT = "/v1beta3/crypto/us/latest/trades"


class AlpacaDeskMarket:
    """Read-only Alpaca market observations; no brokerage endpoint or order routing."""

    def __init__(self, client: AlpacaClient | None = None) -> None:
        self.client = client or AlpacaClient.from_environment()

    def quote(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.strip().upper()
        kind = asset_type(symbol)
        if kind != "crypto":
            return {**self.client.quote(symbol), "asset_class": kind, "name": display_name(symbol),
                    "synthetic": False}
        raw = self.client._get(CRYPTO_ROOT, {"symbols": symbol}, ttl=30)
        trade = (raw.get("trades") or {}).get(symbol)
        if not isinstance(trade, dict):
            raise DeskError("Crypto exchange returned no matching recent trade.")
        return {"symbol": symbol, "asset_class": "crypto",
                "price": positive_number(trade.get("p"), "crypto price"),
                "timestamp": str(trade.get("t") or ""),
                "venue": "Alpaca US crypto", "source": "Alpaca private market data",
                "name": display_name(symbol),
                "coverage": "Alpaca venue only, not global crypto market", "quote_type": "latest_traded_price",
                "synthetic": False}


class DemoDeskMarket:
    """Deterministic, fictional prices only for offline QA and UI exploration."""

    PRICES = {"MSFT": 400.0, "AAPL": 220.0, "NVDA": 130.0, "AMZN": 195.0,
              "SPY": 565.0, "VOO": 518.0, "VTI": 280.0, "QQQ": 475.0,
              "BTC/USD": 69000.0, "ETH/USD": 3600.0, "SOL/USD": 140.0}

    @staticmethod
    def _fictional_catalog_price(symbol: str, kind: str) -> float:
        """Stable invented demo quote, never a live, historical or estimated price."""
        n = int.from_bytes(hashlib.sha256(symbol.encode("ascii")).digest()[:4], "big")
        if kind == "crypto":
            return round(2 + n % 90000 / 10, 2)
        return round((20 if kind == "etf" else 8) + n % 70000 / 100, 2)

    def quote(self, symbol: str) -> dict:
        symbol = symbol.strip().upper()
        kind = asset_type(symbol)
        if symbol not in self.PRICES and symbol not in BY_SYMBOL:
            raise DeskError("Choose a listed company or use the Browse directory in demo mode.")
        price = self.PRICES.get(symbol)
        if price is None:
            price = self._fictional_catalog_price(symbol, kind)
        return {"symbol": symbol, "asset_class": kind, "price": price,
                "name": display_name(symbol),
                "timestamp": dt.datetime.now(dt.UTC).isoformat(),
                "venue": "FICTIONAL DEMO", "source": "synthetic constants, not market data",
                "coverage": "SIMULATED — NO REAL INVESTMENT PRICES", "synthetic": True,
                "quote_type": "fictional_test_price"}
