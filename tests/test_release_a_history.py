"""Release A owner-only single stock flow; preserve existing multi-stock semantics."""

import datetime as dt

import pytest
from fastapi import HTTPException, Response

from cloud import api as service


def request():
    from fastapi import Request

    return Request({"type": "http", "headers": []})


def test_owner_gate_precedes_validation_and_market_calls(monkeypatch):
    def deny(_req, _response):
        raise HTTPException(403, "MFA required")

    monkeypatch.setattr(service, "owner", deny)
    with pytest.raises(HTTPException, match="MFA required"):
        service.private_history_single(request(), Response(), "AAPL")


def test_single_history_feeds_and_format(monkeypatch):
    monkeypatch.setattr(service, "owner", lambda _a, _b: ("owner", "token"))
    end = dt.datetime.now(dt.UTC).date() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=30)
    rows = [{"date": (start + dt.timedelta(days=i)).isoformat(), "close": 100 + i}
            for i in range(20)]
    calls = []

    class Client:
        def history(self, symbol, start_date, end_date, *, feed="sip"):
            calls.append((symbol, start_date, end_date, feed))
            return rows

    monkeypatch.setattr(service.AlpacaClient, "from_environment", lambda: Client())
    answer = service.private_history_single(request(), Response(), "aapl", 90)
    assert answer["symbol"] == "AAPL"
    assert answer["observations"] == rows
    assert answer["equity_feed"] == "sip"
    assert answer["ohlcv_available"] is False
    assert answer["licensed_private"] is True
    assert len(calls) == 1
    assert calls[0][0] == "AAPL"
    assert "dividends" in answer["coverage"]


def test_single_history_fallback_to_iex_only_on_denied_sip(monkeypatch):
    monkeypatch.setattr(service, "owner", lambda _a, _b: ("owner", "token"))
    calls = []

    class Client:
        def history(self, symbol, first, last, *, feed="sip"):
            calls.append(feed)
            if feed == "sip":
                raise service.MarketDataError("HTTP 403 feed or endpoint access denied")
            return [{"date": f"2026-09-{i:02d}", "close": 100.0 + i} for i in range(1, 20)]

    monkeypatch.setattr(service.AlpacaClient, "from_environment", lambda: Client())
    result = service.private_history_single(request(), Response(), "MSFT")
    assert calls == ["sip", "iex"]
    assert result["equity_feed"] == "iex"
    assert "single venue" in result["coverage"]


def test_single_history_rejects_bad_symbol_period_data(monkeypatch):
    monkeypatch.setattr(service, "owner", lambda _a, _b: ("owner", "token"))
    for symbol, days in [("AAPL,MSFT", 365), ("AAPL", 5), ("=CMD", 90)]:
        with pytest.raises(HTTPException) as exc:
            service.private_history_single(request(), Response(), symbol, days)
        assert exc.value.status_code == 422
    class Client:
        def history(self, *_args, **_kwargs):
            return [{"date": "2026-10-01", "close": 1.0}] * 20
    monkeypatch.setattr(service.AlpacaClient, "from_environment", lambda: Client())
    with pytest.raises(HTTPException, match="duplicate"):
        service.private_history_single(request(), Response(), "AAPL")
