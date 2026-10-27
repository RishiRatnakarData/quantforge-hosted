"""Owner-only historical feed fallback: require uniform provenance and fail closed."""
import datetime as dt

import pytest
from fastapi.testclient import TestClient

from cloud import api as service
from quantforge.live.provider import AlpacaClient, MarketDataError


def dates():
    start = dt.date(2026, 8, 3)
    return [(start + dt.timedelta(days=i)).isoformat() for i in range(45)
            if (start + dt.timedelta(days=i)).weekday() < 5]


def records(symbol):
    return [{"date": day, "symbol": symbol, "open": 100 + index, "close": 101 + index}
            for index, day in enumerate(dates())]


class StubAlpaca:
    def __init__(self, *, blocked=True):
        self.calls = []
        self.blocked = blocked

    def history(self, symbol, start, end, *, feed="sip"):
        self.calls.append((symbol, feed))
        if feed == "sip" and symbol == "META" and self.blocked:
            raise MarketDataError("Alpaca market-data request failed (HTTP 403): feed or endpoint access denied; try IEX.")
        return records(symbol)


def _request(monkeypatch, fake, symbols="AMZN,META"):
    monkeypatch.setattr(service, "owner", lambda *_: ("owner-id", "token"))
    monkeypatch.setenv("QF_PROXY_SECRET", "offline-fixture-proxy")
    monkeypatch.setattr(service.AlpacaClient, "from_environment", lambda: fake)
    return TestClient(service.app).get(
        "/api/private/history",
        params={"symbols": symbols, "days": 90},
        headers={"x-qf-proxy-secret": "offline-fixture-proxy"},
    )


def test_denied_sip_retries_all_equities_on_iex(monkeypatch):
    fake = StubAlpaca()
    result = _request(monkeypatch, fake)
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["symbols"] == ["AMZN", "META"]
    assert data["equity_feed"] == "iex"
    assert "IEX-only" in data["source"]
    assert "not consolidated" in data["coverage"]
    assert fake.calls == [("AMZN", "sip"), ("META", "sip"), ("AMZN", "iex"), ("META", "iex")]
    assert len(data["dates"]) >= 15


def test_successful_sip_is_not_downgraded(monkeypatch):
    fake = StubAlpaca(blocked=False)
    result = _request(monkeypatch, fake)
    assert result.status_code == 200, result.text
    assert result.json()["equity_feed"] == "sip"
    assert "SIP" in result.json()["source"]
    assert all(feed == "sip" for _, feed in fake.calls)


def test_unrelated_provider_errors_are_not_retried(monkeypatch):
    fake = StubAlpaca(blocked=False)

    def denied(symbol, start, end, *, feed="sip"):
        fake.calls.append((symbol, feed))
        raise MarketDataError("Alpaca market-data request failed (HTTP 401): authentication failed")

    fake.history = denied
    result = _request(monkeypatch, fake)
    assert result.status_code == 422
    assert fake.calls == [("AMZN", "sip")]


def test_provider_history_rejects_unknown_feeds():
    provider = AlpacaClient("fake-key", "fake-secret")
    with pytest.raises(MarketDataError, match="SIP or IEX"):
        provider.history("AMZN", "2026-01-02", "2026-01-08", feed="unknown")


def test_provider_history_uses_explicit_iex_without_leaking_credentials():
    class Session:
        def __init__(self):
            self.params = []
        def get(self, url, *, headers, params, timeout):
            self.params.append(params)
            class Response:
                def raise_for_status(self):
                    return None
                def json(self):
                    return {"bars": [{"t": "2026-01-02T00:00:00Z", "o": 90, "c": 100}], "next_page_token": None}
            return Response()
    session = Session()
    provider = AlpacaClient("fake-key", "fake-secret", session=session)
    values = provider.history("AMZN", "2026-01-02", "2026-01-08", feed="iex")
    assert values[0]["close"] == 100
    assert session.params[0]["feed"] == "iex"
    assert "fake-secret" not in str(values)


def test_iex_denial_still_fails_closed(monkeypatch):
    fake = StubAlpaca()

    def blocked(symbol, start, end, *, feed="sip"):
        fake.calls.append((symbol, feed))
        raise MarketDataError(
            "Alpaca market-data request failed (HTTP 403): feed or endpoint access denied; try IEX."
        )

    fake.history = blocked
    response = _request(monkeypatch, fake)
    assert response.status_code == 422
    assert fake.calls == [("AMZN", "sip"), ("AMZN", "iex")]


def test_mixed_assets_fallback_does_not_change_crypto_source(monkeypatch):
    fake = StubAlpaca()
    monkeypatch.setattr(service.crypto_history, "history", lambda symbol, start, end: records(symbol))
    response = _request(monkeypatch, fake, symbols="AMZN,META,BTC/USD")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["equity_feed"] == "iex"
    assert data["asset_classes"]["BTC/USD"] == "crypto"
    assert data["asset_classes"]["META"] == "us_equity"
    assert "US crypto" in data["source"]
    assert len(data["closes"]["BTC/USD"]) == len(data["dates"])
