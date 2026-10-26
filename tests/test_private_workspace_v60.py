"""V6.0 owner-only historical research and virtual-capital controls."""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from cloud import api as service


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("QF_PROXY_SECRET", "mock-proxy")
    monkeypatch.setenv("PUBLIC_SITE_ORIGIN", "https://quantforge.example")
    return TestClient(service.app)


def headers(post=False):
    h = {"x-qf-proxy-secret": "mock-proxy"}
    if post:
        h.update({"origin": "https://quantforge.example", "x-qf-action": "1"})
    return h


def test_history_and_virtual_cash_require_authenticated_owner(client):
    assert (
        client.get("/api/private/history?symbols=MSFT,AAPL&days=365", headers=headers()).status_code
        == 401
    )
    assert (
        client.post(
            "/api/private/capital",
            headers=headers(True),
            json={"action": "deposit", "amount": "10", "expected_version": 0},
        ).status_code
        == 401
    )
    assert client.get("/api/private/history?symbols=MSFT,AAPL&days=365").status_code == 403


def test_historical_research_does_not_expose_keys_and_aligns_dates(client, monkeypatch):
    monkeypatch.setattr(service, "owner", lambda *_: ("owner", "jwt"))
    calls = []

    class Provider:
        def history(self, symbol, start, end):
            calls.append((symbol, start, end))
            records = [
                {"date": (dt.date(2026, 1, 1) + dt.timedelta(days=i)).isoformat(), "close": 100 + i}
                for i in range(20)
            ]
            if symbol == "AAPL":
                records = records[1:] + [{"date": "2026-02-01", "close": 130}]
            return records

    monkeypatch.setattr(service.AlpacaClient, "from_environment", lambda: Provider())
    r = client.get("/api/private/history?symbols=MSFT,AAPL&days=365", headers=headers())
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["dates"]) == 19
    assert len(data["closes"]["MSFT"]) == len(data["closes"]["AAPL"]) == 19
    assert "ALPACA_API_SECRET_KEY" not in r.text and data["licensed_private"] is True
    assert len(calls) == 2 and all(s == "MSFT" or s == "AAPL" for s, *_ in calls)


@pytest.mark.parametrize(
    "symbols,days",
    [
        ("MSFT", 365),
        ("BTC/USD,AAPL", 365),
        ("MSFT,AAPL", 999),
        ("MSFT,MSFT", 365),
        ("MSFT,AAPL,VOO,QQQ,NVDA,CAT", 365),
    ],
)
def test_invalid_history_request_never_contacts_provider(client, monkeypatch, symbols, days):
    monkeypatch.setattr(service, "owner", lambda *_: ("owner", "jwt"))
    monkeypatch.setattr(
        service.AlpacaClient,
        "from_environment",
        lambda: (_ for _ in ()).throw(AssertionError("called provider")),
    )
    r = client.get(
        "/api/private/history", params={"symbols": symbols, "days": days}, headers=headers()
    )
    assert r.status_code == 422


def test_virtual_capital_adds_cash_without_touching_holdings(client, monkeypatch):
    monkeypatch.setattr(service, "owner", lambda *_: ("owner", "jwt"))
    initial = {**service.default_state(), "cash": 500.0, "holdings": {"MSFT": 2.0}}
    monkeypatch.setattr(service, "read_state", lambda *_: (initial, 3))
    writes = []
    monkeypatch.setattr(service, "save_state", lambda *a: writes.append(a))
    r = client.post(
        "/api/private/capital",
        headers=headers(True),
        json={"action": "deposit", "amount": "250", "expected_version": 3},
    )
    assert r.status_code == 200, r.text
    assert r.json()["portfolio"]["cash"] == 750.0
    assert r.json()["portfolio"]["holdings"] == {"MSFT": 2.0}
    assert r.json()["portfolio"]["capital_events"][0]["action"] == "deposit"
    assert len(writes) == 1 and writes[0][3] == 3


def test_reset_requires_explicit_confirmation_and_preserves_notes(client, monkeypatch):
    monkeypatch.setattr(service, "owner", lambda *_: ("owner", "jwt"))
    initial = {
        **service.default_state(),
        "holdings": {"MSFT": 3.0},
        "notes": [{"text": "keep"}],
        "trades": [{"side": "buy"}],
    }
    monkeypatch.setattr(service, "read_state", lambda *_: (initial, 1))
    writes = []
    monkeypatch.setattr(service, "save_state", lambda *a: writes.append(a))
    payload = {"action": "reset", "amount": "25000", "expected_version": 1}
    denied = client.post("/api/private/capital", headers=headers(True), json=payload)
    assert denied.status_code == 422 and not writes
    allowed = client.post(
        "/api/private/capital", headers=headers(True), json={**payload, "confirmation": "RESET"}
    )
    assert allowed.status_code == 200, allowed.text
    s = allowed.json()["portfolio"]
    assert s["holdings"] == {} and s["trades"] == [] and s["cash"] == 25000.0
    assert s["notes"] == [{"text": "keep"}]


def test_withdraw_cannot_exceed_virtual_cash(client, monkeypatch):
    monkeypatch.setattr(service, "owner", lambda *_: ("owner", "jwt"))
    monkeypatch.setattr(service, "read_state", lambda *_: (service.default_state(), 7))
    result = client.post(
        "/api/private/capital",
        headers=headers(True),
        json={"action": "withdraw", "amount": "12000", "expected_version": 7},
    )
    assert result.status_code == 422


def test_public_copy_and_private_views_are_source_separated():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    template = (root / "web/site/site.template.html").read_text(encoding="utf-8")
    builder = (root / "tools/build_unified_site.py").read_text(encoding="utf-8")
    private = (root / "web/site/private.js").read_text(encoding="utf-8")
    assert "quantforge.</div>" not in template
    assert "Three short stops" not in template
    for tab in ("home", "trade", "research", "backtest", "valuation", "settings"):
        assert f'data-private-view="{tab}"' in builder
    assert "private/history?" in private
    assert "private/capital" in private
    assert "ALPACA_API_SECRET_KEY" not in private
