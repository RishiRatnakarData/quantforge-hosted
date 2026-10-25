"""Paper-only investing: finance invariants, chronology, crypto and local security."""

from __future__ import annotations

import datetime as dt
import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from quantforge.desk.engine import (
    DeskError,
    PaperLedger,
    asset_type,
    portfolio_report,
    position_capacity,
    valid_quote,
)
from quantforge.desk.market import AlpacaDeskMarket, DemoDeskMarket
from quantforge.desk.server import make_handler
from quantforge.live.provider import AlpacaClient


def test_stocks_index_etfs_crypto_and_validation():
    assert asset_type(" MSFT ") == "stock"
    assert asset_type("voo") == "etf"
    assert asset_type("btc/usd") == "crypto"
    with pytest.raises(DeskError):
        asset_type("../../etc")
    with pytest.raises(DeskError):
        asset_type("BTC/NOTVALID")


def test_virtual_ledger_no_overspending_and_cash_identity(tmp_path):
    path = tmp_path / "ledger.sqlite3"
    ledger = PaperLedger(path)
    q = DemoDeskMarket().quote("MSFT")
    with pytest.raises(DeskError, match="Insufficient"):
        ledger.trade(side="buy", symbol="MSFT", amount="999999", quote=q)
    assert ledger.snapshot()["cash"] == 10000
    trade = ledger.trade(side="buy", symbol="MSFT", amount="1000", quote=q)
    assert 0 < trade["quantity"] < 2.5
    assert trade["fee"] == 0.5
    assert trade["cash_after"] == 9000
    state = ledger.snapshot()
    assert len(state["positions"]) == 1
    assert state["positions"][0]["quantity"] == trade["quantity"]
    report = portfolio_report(state, {"MSFT": q})
    assert report["equity"] < 10000  # entry fee
    assert report["hypothetical_risk"]["es_95_usd"] >= report["hypothetical_risk"]["var_95_usd"]
    assert report["concentration_hhi"] > 0
    assert portfolio_report(state, {"MSFT": q})["hypothetical_risk"] == report["hypothetical_risk"]
    assert PaperLedger(path).snapshot()["cash"] == 9000  # persistent user-owned ledger


def test_sell_cost_basis_and_no_short_sales(tmp_path):
    m = DemoDeskMarket()
    ledger = PaperLedger(tmp_path / "paper.db")
    ledger.trade(side="buy", symbol="BTC/USD", amount="3000", quote=m.quote("BTC/USD"))
    q = ledger.snapshot()["positions"][0]["quantity"]
    with pytest.raises(DeskError, match="Cannot sell"):
        ledger.trade(side="sell", symbol="BTC/USD", amount=str(q + 1), quote=m.quote("BTC/USD"))
    result = ledger.trade(side="sell", symbol="BTC/USD", amount=str(q), quote=m.quote("BTC/USD"))
    assert result["realized_pnl"] < 0  # entry+exit fictional fees at unchanged prices
    assert not ledger.snapshot()["positions"]
    assert ledger.snapshot()["cash"] < 10000


def test_invalid_stale_and_future_quote_block_orders(tmp_path):
    market = DemoDeskMarket()
    ledger = PaperLedger(tmp_path / "paper.db")
    now = dt.datetime(2026, 10, 23, 18, 30, tzinfo=dt.UTC)
    old = market.quote("SPY")
    old["timestamp"] = "2026-10-23T17:00:00+00:00"
    with pytest.raises(DeskError, match="stale"):
        ledger.trade(side="buy", symbol="SPY", amount="100", quote=old, now=now)
    future = {**old, "timestamp": "2026-10-23T19:00:00+00:00"}
    with pytest.raises(DeskError, match="future"):
        valid_quote(future, now=now, require_fresh=True)
    with pytest.raises(DeskError, match="does not match"):
        ledger.trade(side="buy", symbol="MSFT", amount="100", quote=market.quote("SPY"))
    assert ledger.snapshot()["cash"] == 10000


def test_position_limits_with_crypto_and_cash(tmp_path):
    m = DemoDeskMarket()
    ledger = PaperLedger(tmp_path / "p.db")
    ledger.trade(side="buy", symbol="BTC/USD", amount="1000", quote=m.quote("BTC/USD"))
    snap = ledger.snapshot()
    report = portfolio_report(snap, {"BTC/USD": m.quote("BTC/USD")})
    capacity = position_capacity(snap, report, "ETH/USD")
    assert capacity["maximum_buy_budget_usd"] <= 501
    assert position_capacity(snap, report, "BTC/USD")["maximum_buy_budget_usd"] <= 501
    assert position_capacity(snap, report, "MSFT")["maximum_buy_budget_usd"] > 2000
    assert report["stress"]["stocks_etfs_down_20_crypto_down_40_usd"] > 0


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class StubSession:
    def __init__(self, value):
        self.value = value
        self.calls = []

    def get(self, url, *, headers, params, timeout):
        assert headers["APCA-API-SECRET-KEY"] == "private-value"
        self.calls.append((url, params))
        return Response(self.value)


def test_crypto_provider_endpoint_does_not_disclose_credentials():
    session = StubSession({"trades": {"BTC/USD": {"p": 102345.4, "t": "2026-10-23T14:00:00Z"}}})
    market = AlpacaDeskMarket(AlpacaClient("my-key", "private-value", session=session))
    q = market.quote("BTC/USD")
    assert q["price"] == 102345.4
    assert q["venue"] == "Alpaca US crypto"
    assert session.calls[0][0].endswith("/v1beta3/crypto/us/latest/trades")
    assert session.calls[0][1] == {"symbols": "BTC/USD"}
    assert "private-value" not in json.dumps(q)


def test_private_server_endpoints_and_paper_order(tmp_path):
    ledger = PaperLedger(tmp_path / "user.sqlite3")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ledger, DemoDeskMarket(), demo=True))
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        root = f"http://127.0.0.1:{port}"
        with urlopen(root + "/") as f:
            html = f.read().decode()
        assert "Investment desk" in html
        assert "Investment analysis" in html
        with urlopen(root + "/api/health") as f:
            assert json.load(f)["mode"] == "synthetic_demo"
        request = Request(root + "/api/paper-order", data=json.dumps(
            {"symbol": "MSFT", "side": "buy", "amount": "1000", "expected_price": 400}).encode(),
            headers={"Content-Type": "application/json"})
        with urlopen(request) as f:
            result = json.load(f)
        assert result["portfolio"]["positions"][0]["symbol"] == "MSFT"
        assert result["portfolio"]["cash"] == 9000
        other = Request(root + "/api/paper-order", data=b"{}",
                        headers={"Content-Type": "application/json", "Origin": "https://bad.example"})
        with pytest.raises(HTTPError) as error:
            urlopen(other)
        assert error.value.code == 403
    finally:
        server.shutdown()
        t.join(timeout=4)
        server.server_close()


def test_real_sec_valuation_can_be_read_and_reconciled(tmp_path):
    from quantforge.desk.valuation import load_sec_valuation

    (tmp_path / "manifest_v3.json").write_text(json.dumps({
        "data_origin": "sec_companyfacts", "as_of": "2026-10-22"}))
    (tmp_path / "financial_statement_audit.json").write_text(json.dumps({
        "latest_fiscal_year": 2026,
        "status": "latest_year_complete_and_balance_reconciled",
        "cross_filing_review": "still_required"}))
    lines = ["scenario,wacc,terminal_growth,pv_explicit_fcf_usd_millions,"
             "pv_terminal_usd_millions,enterprise_value_usd_millions,"
             "net_debt_usd_millions,equity_value_usd_millions,"
             "diluted_shares_millions_proxy,intrinsic_value_per_share_usd"]
    for name in ("bear", "base", "bull"):
        lines.append(name + ",0.10,0.03,400,600,1000,-100,1100,10,110")
    (tmp_path / "dcf_scenarios.csv").write_text("\n".join(lines) + "\n")
    result = load_sec_valuation(tmp_path)
    assert result["status"] == "verified_calculation_not_investment_recommendation"
    assert len(result["scenarios"]) == 3
    assert result["fiscal_year"] == 2026
    lines[-1] = lines[-1].replace(",1100,10,110", ",1000,10,110")
    (tmp_path / "dcf_scenarios.csv").write_text("\n".join(lines) + "\n")
    with pytest.raises(DeskError, match="reconciliation"):
        load_sec_valuation(tmp_path)
    (tmp_path / "manifest_v3.json").write_text(json.dumps({"data_origin": "synthetic_demo"}))
    with pytest.raises(DeskError, match="real, SEC"):
        load_sec_valuation(tmp_path)
