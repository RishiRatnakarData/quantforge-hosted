"""Curated company discovery, classification, and fictional offline demo safety."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

import pytest

from quantforge.desk.catalog import BY_SYMBOL, CATALOG, directory_data, display_name
from quantforge.desk.engine import DeskError, PaperLedger, asset_type
from quantforge.desk.market import DemoDeskMarket
from quantforge.desk.server import make_handler


def test_catalog_unique_names_and_broad_categories():
    assert len(CATALOG) >= 250
    assert len(BY_SYMBOL) == len(CATALOG)
    assert all(a["symbol"] and a["name"] for a in CATALOG)
    assert len({a["category"] for a in CATALOG}) >= 9
    for symbol, expected_name in {"AAPL": "Apple", "MSFT": "Microsoft", "VOO": "Vanguard S&P 500 ETF", "BTC/USD": "Bitcoin"}.items():
        assert display_name(symbol) == expected_name
    assert directory_data()["complete_market_listing"] is False
    assert display_name("UNLISTED") == "UNLISTED"


def test_all_listed_tickers_are_valid_and_demo_supported():
    market = DemoDeskMarket()
    for asset in CATALOG:
        quote = market.quote(asset["symbol"])
        assert quote["symbol"] == asset["symbol"]
        assert quote["asset_class"] == asset["asset_class"]
        assert asset_type(asset["symbol"]) == asset["asset_class"]
        assert quote["price"] > 0
        assert quote["synthetic"] is True
        assert "FICTIONAL" in quote["venue"]
        assert quote["price"] == market.quote(asset["symbol"])["price"]
    with pytest.raises(DeskError):
        market.quote("NONEXIST")


def test_directory_endpoint_read_only_and_not_prices(tmp_path):
    ledger = PaperLedger(tmp_path / "demo.sqlite3")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ledger, DemoDeskMarket(), demo=True))
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        root = f"http://127.0.0.1:{server.server_address[1]}"
        with urlopen(root + "/api/directory") as response:
            data = json.load(response)
        assert data["total"] == len(CATALOG)
        assert any(e["name"] == "Apple" for e in data["entries"])
        assert all("price" not in e for e in data["entries"])
        with urlopen(root + "/api/decision?symbol=SCHB&budget=500") as response:
            decision = json.load(response)
        assert decision["asset_class"] == "etf"
        assert decision["symbol"] == "SCHB"
        assert decision["fresh_for_paper"] is True
    finally:
        server.shutdown()
        server.server_close()
        t.join(timeout=2)
