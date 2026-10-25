"""Private market-data adapter and no-redistribution checks (mocked; no API key needed)."""

from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pytest
import requests

from quantforge.live.local_app import prepare_private_site
from quantforge.live.provider import AlpacaClient, MarketDataError, valid_symbol
from quantforge.simulator.website import build_stock_site


class StubResponse:
    def __init__(self, payload: dict, status: int = 200):
        self.payload = payload
        self.status = status

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError("Service rejected request")

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payloads):
        self.payloads = iter(payloads)
        self.requests = []

    def get(self, url, *, headers, params, timeout):
        assert url.startswith("https://data.alpaca.markets/v2/stocks/")
        assert headers["APCA-API-KEY-ID"] == "demo-key"
        self.requests.append((url, params))
        return StubResponse(next(self.payloads))


def test_credentials_are_required():
    with pytest.raises(MarketDataError, match="ALPACA"):
        AlpacaClient("", "")


def test_symbol_input_is_validated():
    assert valid_symbol(" aapl ") == "AAPL"
    with pytest.raises(MarketDataError):
        valid_symbol("../hidden")


def test_quote_is_iex_only_and_timestamped():
    session = FakeSession([{"trade": {"p": 251.50, "t": "2026-10-23T16:15:02Z"}}])
    client = AlpacaClient("demo-key", "demo-secret", session=session)
    quote = client.quote("MSFT")
    assert quote["price"] == 251.5
    assert quote["venue"] == "IEX"
    assert quote["timestamp"].startswith("2026-10")
    assert session.requests[0][1]["feed"] == "iex"
    assert "demo-secret" not in json.dumps(quote)


def test_historical_pagination_split_adjustment_and_price_only():
    session = FakeSession([
        {"bars": [{"t": "2020-01-02T05:00:00Z", "o": 101, "c": 105}],
         "next_page_token": "next"},
        {"bars": [{"t": "2020-01-03T05:00:00Z", "o": 106, "c": 108}],
         "next_page_token": None},
    ])
    client = AlpacaClient("demo-key", "demo-secret", session=session)
    results = client.history("AAPL", "2020-01-02", "2020-01-05")
    assert [r["date"] for r in results] == ["2020-01-02", "2020-01-03"]
    assert session.requests[0][1]["feed"] == "sip"
    assert session.requests[0][1]["adjustment"] == "split"
    assert session.requests[1][1]["page_token"] == "next"


def test_malformed_and_duplicate_history_block():
    payload = {"bars": [{"t": "2020-01-02T00:00:00Z", "o": 1, "c": 2},
                        {"t": "2020-01-02T00:00:00Z", "o": 2, "c": 3}]}
    with pytest.raises(MarketDataError, match="Duplicate"):
        AlpacaClient("demo-key", "demo-secret", session=FakeSession([payload])).history(
            "SPY", "2020-01-02", "2020-01-05")


class FakeClient:
    def history(self, symbol, start, end):
        assert start == "2020-01-01"
        assert end == "2020-03-31"
        dates = [d.date().isoformat() for d in __import__("pandas").bdate_range(
            dt.date(2020, 1, 1), periods=50)]
        return [{"date": d, "symbol": symbol, "open": 100 + i,
                 "close": 100 + i + float(np.sin(i) * .1)} for i, d in enumerate(dates)]


def test_private_site_remains_local_and_refuses_public_output(tmp_path):
    result = prepare_private_site(client=FakeClient(), root=tmp_path,
                                  symbols=["MSFT", "SPY"], start="2020-01-01",
                                  end="2020-03-31")
    assert result["observations"] == 50
    html = (result["site"] / "index.html").read_text()
    assert "Get latest IEX trade" in html
    assert "demo-secret" not in html
    source = json.loads((result["site"] / "evidence.json").read_text())
    assert not source["publication_allowed"]
    with pytest.raises(ValueError, match="public redistribution|source license|Source license"):
        build_stock_site(stock_dir=tmp_path / "private-market-data",
                         output=tmp_path / "public")


def test_provider_http_error_reports_status_without_secret():
    class DeniedResponse:
        status_code = 403

    class DeniedSession:
        def get(self, url, *, headers, params, timeout):
            raise requests.HTTPError("sensitive-key-should-not-appear", response=DeniedResponse())

    client = AlpacaClient("demo-key", "demo-secret", session=DeniedSession())
    with pytest.raises(MarketDataError, match=r"HTTP 403.*try IEX") as exc:
        client._get("/v2/stocks/MSFT/bars", {"feed": "sip"})
    assert "demo-secret" not in str(exc.value)
    assert "sensitive-key" not in str(exc.value)


def test_provider_connection_error_never_echoes_sensitive_detail():
    class OfflineSession:
        def get(self, url, *, headers, params, timeout):
            raise requests.ConnectionError("secret network diagnostics")

    client = AlpacaClient("demo-key", "demo-secret", session=OfflineSession())
    with pytest.raises(MarketDataError, match="network request failed") as exc:
        client._get("/v2/stocks/MSFT/bars", {"feed": "iex"})
    assert "secret" not in str(exc.value)
