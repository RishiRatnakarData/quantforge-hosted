"""V6.2 authenticated SEC issuer selection and independent note deletion."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cloud import api as service
from cloud import sec_fundamentals as sec


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("QF_PROXY_SECRET", "local-proxy")
    monkeypatch.setenv("PUBLIC_SITE_ORIGIN", "https://quantforge.example")
    return TestClient(service.app)


def headers(post=False):
    info = {"x-qf-proxy-secret": "local-proxy"}
    if post:
        info.update({"origin": "https://quantforge.example", "x-qf-action": "1"})
    return info


def _fact(value):
    return {"units": {"USD": [{"val": value, "start": "2025-01-01", "end": "2025-12-31",
                              "form": "10-K", "fp": "FY", "filed": "2026-02-02",
                              "accn": "0000000000-26-000001", "fy": 2025}]}}


def test_sec_endpoint_requires_proxy_and_owner_mfa(client):
    assert client.get("/api/private/sec/company?symbol=JPM").status_code == 403
    assert client.get("/api/private/sec/company?symbol=JPM", headers=headers()).status_code == 401


def test_sec_endpoint_returns_actual_filing_structure_without_keys(client, monkeypatch):
    monkeypatch.setattr(service, "owner", lambda *_: ("owner", "JWT"))
    monkeypatch.setattr(sec, "_DIRECTORY", (float("inf"), {"ZZZT": (987654, "Test Issuer")}))
    monkeypatch.setattr(sec, "_COMPANIES", {})
    called = []

    def fake_fetch(url):
        called.append(url)
        return {"cik": 987654, "facts": {"us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": _fact(1_000),
            "OperatingIncomeLoss": _fact(250),
            "NetCashProvidedByUsedInOperatingActivities": _fact(300),
            "PaymentsToAcquirePropertyPlantAndEquipment": _fact(40),
        }}}

    monkeypatch.setattr(sec, "_fetch_json", fake_fetch)
    r = client.get("/api/private/sec/company?symbol=ZZZT", headers=headers())
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["symbol"] == "ZZZT" and data["cik"] == 987654
    assert data["annual"][0]["metrics"]["free_cash_flow_usd"] == 260
    assert data["annual"][0]["metrics"]["revenue_usd"] == 1000
    assert data["annual"][0]["sources"]["revenue_usd"]["filed"] == "2026-02-02"
    assert len(called) == 1 and called[0].endswith("CIK0000987654.json")
    assert "ALPACA_API_SECRET_KEY" not in r.text and "SEC_USER_AGENT" not in r.text


def test_existing_snapshot_works_without_live_sec_config(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    def no_network(*_):
        raise AssertionError("Expected the bundled historical SEC snapshot")
    monkeypatch.setattr(sec, "_fetch_json", no_network)
    data = sec.get_company("MSFT")
    assert data["symbol"] == "MSFT" and data["annual"]
    assert "archived public snapshot" in data["source"]


def test_invalid_and_unlisted_issuers_have_no_fabricated_fundamentals(monkeypatch):
    monkeypatch.setattr(sec, "_DIRECTORY", (float("inf"), {"JPM": (19617, "JPMorgan")}))
    with pytest.raises(sec.SECFundamentalsError):
        sec.get_company("BTC/USD")
    with pytest.raises(sec.SECFundamentalsError, match="No matching SEC issuer"):
        sec.get_company("VOO")
    with pytest.raises(sec.SECFundamentalsError, match="No matching SEC issuer"):
        sec.get_company("ZZZZ")


def test_delete_one_note_preserves_holdings_and_others(client, monkeypatch):
    monkeypatch.setattr(service, "owner", lambda *_: ("owner", "JWT"))
    before = {**service.default_state(), "cash": 320.0, "holdings": {"JPM": 4},
              "trades": [{"side": "buy"}], "notes": [
                  {"text": "first", "at": "2026-10-20", "symbol": "JPM"},
                  {"text": "delete", "at": "2026-10-21", "symbol": ""},
                  {"text": "last", "at": "2026-10-22", "symbol": "MSFT"},
              ]}
    monkeypatch.setattr(service, "read_state", lambda *_: (before, 3))
    writes = []
    monkeypatch.setattr(service, "save_state", lambda *args: writes.append(args))
    payload = {"expected_version": 3, "watchlist": [],
               "notes": [before["notes"][0], before["notes"][2]]}
    response = client.post("/api/private/notes", headers=headers(True), json=payload)
    assert response.status_code == 200, response.text
    new = response.json()["portfolio"]
    assert [note["text"] for note in new["notes"]] == ["first", "last"]
    assert new["holdings"] == {"JPM": 4}
    assert new["trades"] == [{"side": "buy"}]
    assert new["cash"] == 320.0
    assert len(writes) == 1 and writes[0][3] == 3


def test_stale_notes_version_cannot_delete_anything(client, monkeypatch):
    monkeypatch.setattr(service, "owner", lambda *_: ("owner", "JWT"))
    monkeypatch.setattr(service, "read_state", lambda *_: (service.default_state(), 7))
    monkeypatch.setattr(service, "save_state", lambda *_: (_ for _ in ()).throw(
        AssertionError("stale note deletion must not save")))
    response = client.post("/api/private/notes", headers=headers(True), json={
        "expected_version": 6, "notes": [], "watchlist": []})
    assert response.status_code == 409


def test_private_selector_and_individual_note_delete_are_in_source():
    root = Path(__file__).resolve().parents[1]
    js = (root / "web/site/private.js").read_text(encoding="utf-8")
    builder = (root / "tools/build_unified_site.py").read_text(encoding="utf-8")
    assert "openAssetBrowser('valuation')" in js
    assert "data-note-delete" in js
    assert "window.confirm('Delete this saved research note?" in js
    assert "private/sec/company?symbol=" in js
    assert 'id="private-browse-valuation"' in builder
    assert 'id="private-valuation-selected"' in builder
    assert "ALPACA_API_SECRET_KEY" not in js
