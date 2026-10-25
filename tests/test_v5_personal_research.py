"""V5 equal-budget alternatives, SEC provenance, missing-data, and local routing."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from urllib.parse import quote
from urllib.request import urlopen

import pytest

from quantforge.desk.comparison import compare_ideas
from quantforge.desk.engine import DeskError, PaperLedger, portfolio_report
from quantforge.desk.market import DemoDeskMarket
from quantforge.desk.sec_research import SECResearch, parse_annual_fundamentals
from quantforge.desk.server import make_handler


def account(tmp_path):
    ledger = PaperLedger(tmp_path / "paper.sqlite3")
    market = DemoDeskMarket()
    snap = ledger.snapshot()
    positions = {p["symbol"]: market.quote(p["symbol"]) for p in snap["positions"]}
    portfolio = portfolio_report(snap, positions)
    return ledger, market, portfolio


def test_compare_alternatives_are_not_additive(tmp_path):
    _, market, portfolio = account(tmp_path)
    profile = {"goal": "explore", "horizon": "five_plus", "comfort": "balanced", "cash_buffer_pct": 20}
    result = compare_ideas(["MSFT", "VOO", "BTC/USD"], "500", market, portfolio, profile)
    assert result["no_orders"]
    assert len(result["rows"]) == 3
    assert result["budget_usd"] == 500
    assert all(r["post_cash_usd"] == 9500 for r in result["rows"])
    assert [r["scenario_decline_pct"] for r in result["rows"]] == [30, 20, 40]
    assert result["rows"][0]["scenario_added_loss_usd"] == pytest.approx(149.925, abs=.01)
    assert all(r["synthetic"] for r in result["rows"])


@pytest.mark.parametrize("symbols", [["MSFT"], ["MSFT", "MSFT"], ["MSFT", "VOO", "SPY", "QQQ", "AAPL"], ["INVALID CRYPTO", "VOO"]])
def test_compare_rejects_bad_symbols(tmp_path, symbols):
    _, market, portfolio = account(tmp_path)
    profile = {"comfort": "balanced", "horizon": "five_plus", "cash_buffer_pct": 20}
    with pytest.raises(DeskError):
        compare_ideas(symbols, 500, market, portfolio, profile)


def test_compare_respects_available_cash(tmp_path):
    _, market, portfolio = account(tmp_path)
    profile = {"comfort": "balanced", "horizon": "five_plus", "cash_buffer_pct": 20}
    with pytest.raises(DeskError, match="virtual cash"):
        compare_ideas(["MSFT", "VOO"], 10001, market, portfolio, profile)


def sec_fact(val, end, *, start=None, form="10-K", filed="2026-08-01", accession="0000"):
    out = {"form": form, "end": end, "val": val, "filed": filed, "accn": accession}
    if start:
        out["start"] = start
    return out


def gaap(*facts):
    return {"units": {"USD": list(facts)}}


def sec_payload():
    return {
        "cik": 789019, "entityName": "Example Software Inc.",
        "facts": {"us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": gaap(
                sec_fact(100_000_000, "2024-12-31", start="2024-01-01", filed="2025-02-01"),
                sec_fact(125_000_000, "2025-12-31", start="2025-01-01", filed="2026-02-01"),
                # Should not take an inappropriate 10-Q YTD fact over the full-year 10-K.
                sec_fact(999_000_000, "2026-03-31", start="2026-01-01", form="10-Q"),
            ),
            "OperatingIncomeLoss": gaap(sec_fact(25_000_000, "2025-12-31", start="2025-01-01")),
            "NetIncomeLoss": gaap(sec_fact(20_000_000, "2025-12-31", start="2025-01-01")),
            "NetCashProvidedByUsedInOperatingActivities": gaap(sec_fact(30_000_000, "2025-12-31", start="2025-01-01")),
            "PaymentsToAcquirePropertyPlantAndEquipment": gaap(sec_fact(8_000_000, "2025-12-31", start="2025-01-01")),
            "Assets": gaap(sec_fact(200_000_000, "2025-12-31")),
        }},
    }


def test_sec_ann_report_provenance_and_missing_fields():
    r = parse_annual_fundamentals(sec_payload(), ticker="MSFT", cik=789019)
    assert r["fiscal_end"] == "2025-12-31"
    assert r["revenue_usd"] == 125_000_000
    assert r["revenue_growth_pct"] == 25
    assert r["operating_margin_pct"] == 20
    assert r["net_margin_pct"] == 16
    assert r["free_cash_flow_usd"] == 22_000_000
    assert r["long_term_debt_usd"] is None
    assert r["revenue_source_tag"] == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert "sec.gov" in r["filings_url"]


def test_sec_rejects_wrong_company_and_insufficient_facts():
    with pytest.raises(DeskError, match="identifier"):
        parse_annual_fundamentals(sec_payload(), ticker="AAPL", cik=320193)
    empty = {"cik": 789019, "facts": {"us-gaap": {}}}
    with pytest.raises(DeskError, match="revenue"):
        parse_annual_fundamentals(empty, ticker="MSFT", cik=789019)


class MockSECResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class MockSECSession:
    def __init__(self):
        self.calls = []

    def get(self, url, *, headers, timeout):
        self.calls.append((url, headers, timeout))
        data = {"0": {"ticker": "MSFT", "cik_str": 789019}} if "company_tickers" in url else sec_payload()
        return MockSECResponse(data)


def test_sec_client_requires_user_agent_and_caches():
    with pytest.raises(DeskError, match="SEC_USER_AGENT"):
        SECResearch(user_agent="").fundamentals("MSFT")
    client = MockSECSession()
    research = SECResearch(user_agent="Personal Research qa@research.test", session=client)
    assert research.fundamentals("MSFT")["symbol"] == "MSFT"
    assert research.fundamentals("MSFT")["symbol"] == "MSFT"
    assert len(client.calls) == 2
    assert all("Personal Research" in c[1]["User-Agent"] for c in client.calls)
    with pytest.raises(DeskError, match="ETFs or crypto"):
        research.fundamentals("BTC/USD")


def test_new_routes_and_front_end(tmp_path):
    ledger, market, _ = account(tmp_path)
    sec = SECResearch(user_agent="Personal qa@research.test", session=MockSECSession())
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ledger, market, demo=True, sec_research=sec))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urlopen(root + "/api/compare?symbols=" + quote("MSFT,VOO") + "&budget=500") as response:
            x = json.load(response)
        assert len(x["rows"]) == 2
        with urlopen(root + "/api/fundamentals?symbol=MSFT") as response:
            f = json.load(response)
        assert f["free_cash_flow_usd"] == 22_000_000
        with urlopen(root + "/") as response:
            html = response.read().decode()
        assert 'id="compareRun"' in html
        assert 'id="fetchFinancials"' in html
        assert 'id="directorySearch"' in html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
