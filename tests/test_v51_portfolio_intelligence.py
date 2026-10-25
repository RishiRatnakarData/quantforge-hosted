"""V5.1 ETF constituent evidence, overlap, read-only rebalancing, local HTTP APIs."""

from __future__ import annotations

import json
import threading
from decimal import Decimal
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from quantforge.desk.engine import DeskError, PaperLedger, portfolio_report
from quantforge.desk.market import DemoDeskMarket
from quantforge.desk.portfolio_intelligence import (
    HoldingsStore,
    lookthrough,
    parse_holdings_csv,
    rebalance_plan,
)
from quantforge.desk.server import make_handler


def _portfolio(tmp_path):
    market = DemoDeskMarket()
    ledger = PaperLedger(tmp_path / "paper.sqlite3")
    ledger.trade(side="buy", symbol="VOO", amount="4000", quote=market.quote("VOO"))
    ledger.trade(side="buy", symbol="QQQ", amount="2000", quote=market.quote("QQQ"))
    ledger.trade(side="buy", symbol="MSFT", amount="1000", quote=market.quote("MSFT"))
    snapshot = ledger.snapshot()
    return ledger, market, portfolio_report(snapshot, {p["symbol"]: market.quote(p["symbol"])
                                                     for p in snapshot["positions"]})


def test_parse_issuer_headers_and_percent_units():
    text = 'Fund holdings as of 2026-10-21\nTicker,Name,Weight (%)\nMSFT,Microsoft,6.45\nAAPL,Apple,5.12\n'
    assert parse_holdings_csv(text) == [("AAPL", Decimal("5.12")), ("MSFT", Decimal("6.45"))]
    # A provider report may include a partial file; never scale partial weight to 100%.
    assert parse_holdings_csv("symbol,weight_pct\nMSFT,1.2\n") == [("MSFT", Decimal("1.2"))]
    with pytest.raises(DeskError, match="exceed"):
        parse_holdings_csv("Ticker,Weight (%)\nMSFT,60\nAAPL,50\n")
    with pytest.raises(DeskError, match="percentage"):
        parse_holdings_csv("Ticker,Weight (%)\nMSFT,-3\n")
    with pytest.raises(DeskError, match="Ticker"):
        parse_holdings_csv("Name,Percentage\nMicrosoft,20\n")


def test_private_holdings_roundtrip_and_inspection(tmp_path):
    ledger, _, portfolio = _portfolio(tmp_path)
    store = HoldingsStore(ledger.path)
    original_cash = ledger.snapshot()["cash"]
    voo = store.save(etf="VOO", as_of="2026-10-20", source="Issuer file, example.test/voo",
                     raw="Ticker,Weight (%)\nMSFT,6\nAAPL,5\n")
    store.save(etf="QQQ", as_of="2026-10-20", source="Issuer file, example.test/qqq",
               raw="symbol,weight_pct\nMSFT,9\nNVDA,8\n")
    assert voo["identified_pct"] == 11
    result = lookthrough(portfolio, HoldingsStore(ledger.path).all())
    direct = next(p for p in portfolio["positions"] if p["symbol"] == "MSFT")["value"]
    etf1 = next(p for p in portfolio["positions"] if p["symbol"] == "VOO")["value"]
    etf2 = next(p for p in portfolio["positions"] if p["symbol"] == "QQQ")["value"]
    expected = direct + .06 * etf1 + .09 * etf2
    assert next(x for x in result["exposures"] if x["ticker"] == "MSFT")["value_usd"] == pytest.approx(expected, abs=.02)
    assert result["etf_pairs"][0]["known_min_weight_overlap_pct"] == 6
    assert result["unknown_etf_value_usd"] == pytest.approx(.89 * etf1 + .83 * etf2, abs=.02)
    assert ledger.snapshot()["cash"] == original_cash
    with pytest.raises(DeskError, match="future"):
        store.save(etf="VOO", as_of="2090-01-01", source="issuer source", raw="Ticker,Weight (%)\nMSFT,6")
    with pytest.raises(DeskError, match="source"):
        store.save(etf="VOO", as_of="2026-10-20", source="", raw="Ticker,Weight (%)\nMSFT,6")


def test_lookthrough_missing_holdings_not_zero(tmp_path):
    _, _, p = _portfolio(tmp_path)
    d = lookthrough(p, {})
    assert len(d["funds"]) == 2
    assert all(x["identified_weight_pct"] == 0 for x in d["funds"])
    assert d["unknown_etf_value_usd"] > 5000
    assert {x["ticker"] for x in d["exposures"]} == {"MSFT"}
    assert not d["etf_pairs"]


def test_rebalance_conserves_cash_and_never_executes(tmp_path):
    ledger, _, p = _portfolio(tmp_path)
    before = ledger.snapshot()
    # Shift holdings to a smaller ETF allocation, more MSFT, and 10% cash.
    target = {"VOO": 30, "QQQ": 20, "MSFT": 40, "CASH": 10}
    result = rebalance_plan(p, target)
    assert result["executed"] is False
    assert any(t["side"] == "sell" for t in result["trades"])
    assert any(t["side"] == "buy" for t in result["trades"])
    assert all(t["quantity"] > 0 and t["value_usd"] > 0 for t in result["trades"])
    assert result["estimated_fees_usd"] > 0
    assert result["cash_after_usd"] >= 0
    assert result["largest_target_drift_pct_points"] < .1
    assert ledger.snapshot() == before
    assert result == rebalance_plan(p, target)  # deterministic
    with pytest.raises(DeskError, match="total 100"):
        rebalance_plan(p, {**target, "CASH": 11})
    with pytest.raises(DeskError, match="every held"):
        rebalance_plan(p, {"MSFT": 50, "CASH": 50})


def test_all_cash_and_zero_holdings(tmp_path):
    market = DemoDeskMarket()
    ledger = PaperLedger(tmp_path / "empty.sqlite3")
    p = portfolio_report(ledger.snapshot(), {})
    plan = rebalance_plan(p, {"CASH": 100})
    assert plan["trades"] == []
    assert plan["cash_after_usd"] == 10000
    assert lookthrough(p, {})["exposures"] == []
    ledger.trade(side="buy", symbol="VOO", amount="4000", quote=market.quote("VOO"))
    state = ledger.snapshot()
    p = portfolio_report(state, {"VOO": market.quote("VOO")})
    plan = rebalance_plan(p, {"VOO": 0, "CASH": 100})
    assert len(plan["trades"]) == 1
    assert plan["trades"][0]["side"] == "sell"
    assert plan["cash_after_usd"] > 9990


def _request(base, path, payload):
    return urlopen(Request(base + path, data=json.dumps(payload).encode(),
                           headers={"Content-Type": "application/json"}, method="POST"))


def test_local_api_import_lookthrough_and_read_only_rebalance(tmp_path):
    ledger, market, _ = _portfolio(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ledger, market, demo=True))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        snapshot = ledger.snapshot()
        with _request(base, "/api/holdings-imports", {"etf": "VOO", "as_of": "2026-10-21",
            "source": "Example issuer CSV test", "csv": "Ticker,Weight (%)\nMSFT,6\nAAPL,5\n"}) as response:
            assert json.load(response)["holdings"] == 2
        with urlopen(base + "/api/holdings-lookthrough") as response:
            look = json.load(response)
            assert any(x["ticker"] == "MSFT" for x in look["exposures"])
            assert look["unknown_etf_value_usd"] > 0
        with urlopen(base + "/api/holdings-imports") as response:
            assert json.load(response)["funds"][0]["etf"] == "VOO"
        with _request(base, "/api/rebalance-plan", {"targets": {"VOO": 30, "QQQ": 20,
            "MSFT": 30, "CASH": 20}}) as response:
            assert json.load(response)["executed"] is False
        assert ledger.snapshot() == snapshot
        with pytest.raises(HTTPError) as error:
            _request(base, "/api/rebalance-plan", {"targets": {"CASH": 100}})
        assert error.value.code == 422
        with urlopen(base + "/") as response:
            ui = response.read().decode()
            assert "ETF holdings overlap" in ui
            assert "Rebalance plan" in ui
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
