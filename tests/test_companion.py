"""User-centered investment decision support, data integrity and privacy tests."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from quantforge.desk.companion import CompanionStore, decision_brief
from quantforge.desk.engine import DeskError, PaperLedger, portfolio_report
from quantforge.desk.market import DemoDeskMarket
from quantforge.desk.server import make_handler


def test_profile_persistence_and_reject_invalid(tmp_path):
    db = tmp_path / "paper.sqlite3"
    saved = CompanionStore(db)
    assert saved.profile()["goal"] == "explore"
    assert saved.save_profile({"horizon": "under_one", "comfort": "cautious", "cash_buffer_pct": 40})["horizon"] == "under_one"
    assert CompanionStore(db).profile()["cash_buffer_pct"] == 40
    with pytest.raises(DeskError):
        saved.save_profile({"comfort": "random"})
    with pytest.raises(DeskError):
        saved.save_profile({"cash_buffer_pct": True})
    with pytest.raises(DeskError):
        saved.save_profile({"cash_buffer_pct": 110})


def test_paper_impact_math_with_existing_stock_and_no_lookahead(tmp_path):
    ledger = PaperLedger(tmp_path / "paper.sqlite3")
    m = DemoDeskMarket()
    ledger.trade(side="buy", symbol="MSFT", amount="1000", quote=m.quote("MSFT"))
    report = portfolio_report(ledger.snapshot(), {"MSFT": m.quote("MSFT")})
    p = CompanionStore(ledger.path).profile()
    d = decision_brief(m.quote("MSFT"), report, p, 500)
    assert d["position_weight_before_pct"] > 9
    assert d["position_weight_after_pct"] > d["position_weight_before_pct"]
    assert d["scenario_loss_added_usd"] == pytest.approx((500 - d["approx_fee_usd"]) * .30)
    assert d["scenario_loss_usd"] > d["scenario_loss_added_usd"]
    assert d["post_cash_usd"] == pytest.approx(8500)
    assert d["scenario_loss_of_portfolio_pct"] > 1
    assert "forecast" in d["guidance"]
    with pytest.raises(DeskError):
        decision_brief(m.quote("MSFT"), report, p, 999999)
    with pytest.raises(DeskError):
        decision_brief(m.quote("MSFT"), report, p, float("nan"))


def test_goal_and_asset_class_cautions_are_truthfully_different(tmp_path):
    ledger = PaperLedger(tmp_path / "paper.sqlite3")
    portfolio = portfolio_report(ledger.snapshot(), {})
    m = DemoDeskMarket()
    p = CompanionStore(ledger.path).save_profile({"horizon": "under_one", "comfort": "cautious"})
    crypto = decision_brief(m.quote("BTC/USD"), portfolio, p, 1000)
    etf = decision_brief(m.quote("VOO"), portfolio, p, 1000)
    assert crypto["scenario_loss_usd"] > etf["scenario_loss_usd"]
    assert any("crypto" in f.lower() for f in crypto["flags"])
    assert any("short time horizon" in f for f in crypto["flags"])
    assert not any("short time horizon" in f for f in etf["flags"])
    assert "holdings and fees" in etf["asset_explainer"]
    assert crypto["fresh_for_paper"]


def test_notes_and_watchlist_are_private_and_validated(tmp_path):
    s = CompanionStore(tmp_path / "journal.sqlite3")
    quote = DemoDeskMarket().quote("VOO")
    s.watch("VOO")
    s.watch("VOO")
    assert len(s.watchlist()) == 1
    with pytest.raises(DeskError):
        s.add_note(symbol="VOO", note="no", budget=50, quote=quote)
    with pytest.raises(DeskError):
        s.add_note(symbol="MSFT", note="I want to understand the balance sheet", budget=50, quote=quote)
    s.add_note(symbol="VOO", note="I want broad exposure, but first I will check the fees.", budget=100, quote=quote)
    assert len(CompanionStore(s.path).notes()) == 1
    assert s.notes()[0]["quote_source"] == "synthetic constants, not market data"
    assert s.watch("VOO", remove=True) == []


def test_companion_local_http_flow(tmp_path):
    ledger = PaperLedger(tmp_path / "app.sqlite3")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ledger, DemoDeskMarket(), demo=True))
    runner = threading.Thread(target=server.serve_forever, daemon=True)
    runner.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    def get(path):
        with urlopen(base + path) as response:
            return json.load(response)

    def post(path, payload):
        req = Request(base + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urlopen(req) as response:
            return json.load(response)

    try:
        assert get("/api/profile")["goal"] == "explore"
        post("/api/profile", {"comfort": "cautious", "horizon": "under_one"})
        assert get("/api/profile")["horizon"] == "under_one"
        query = urlencode({"symbol": "BTC/USD", "budget": 600})
        assert get("/api/decision?" + query)["flags"]
        post("/api/watchlist", {"symbol": "VOO"})
        assert get("/api/watchlist")["watchlist"][0]["symbol"] == "VOO"
        post("/api/notes", {"symbol": "MSFT", "note": "Check long term cash flow before acting", "budget": 500})
        assert len(get("/api/notes")["notes"]) == 1
        with pytest.raises(HTTPError) as exc:
            post("/api/profile", {"cash_buffer_pct": 120})
        assert exc.value.code == 422
        with urlopen(base) as response:
            page = response.read().decode()
        assert "Investment desk" in page
        assert "Preferences" in page
        assert "Investment desk" in page and 'id="quickResearch"' in page
    finally:
        server.shutdown()
        runner.join(timeout=4)
        server.server_close()
