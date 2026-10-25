"""V5.2 five-year FCFF accounting, sensitivity, SEC provenance and HTTP routing."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import pytest

from quantforge.desk.company_models import calculate_company_dcf, compare_fundamentals
from quantforge.desk.engine import DeskError, PaperLedger
from quantforge.desk.market import DemoDeskMarket
from quantforge.desk.sec_research import SECResearch
from quantforge.desk.server import make_handler

END = "2025-12-31"
START = "2025-01-01"


def fact(value, *, annual=False):
    record = {"form": "10-K", "filed": "2026-02-15", "end": END,
              "accn": "0001234-26-000001", "val": value}
    if annual:
        record["start"] = START
    return record


def sec_fixture(*, omit=()):
    raw = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": (125_000_000, True),
        "OperatingIncomeLoss": (25_000_000, True),
        "DepreciationDepletionAndAmortization": (5_000_000, True),
        "PaymentsToAcquirePropertyPlantAndEquipment": (8_000_000, True),
        "CashAndCashEquivalentsAtCarryingValue": (20_000_000, False),
        "LongTermDebtCurrent": (3_000_000, False),
        "LongTermDebtNoncurrent": (12_000_000, False),
        "ShortTermInvestments": (2_000_000, False),
        "NetCashProvidedByUsedInOperatingActivities": (30_000_000, True),
        "NetIncomeLoss": (22_000_000, True),
        "Assets": (220_000_000, False),
    }
    facts = {k: {"units": {"USD": [fact(v, annual=a)]}}
             for k, (v, a) in raw.items() if k not in omit}
    facts["WeightedAverageNumberOfDilutedSharesOutstanding"] = {"units": {
        "shares": [fact(10_000_000, annual=True)]}}
    return {"cik": 789019, "entityName": "Example Software", "facts": {"us-gaap": facts}}


def test_dcf_accounting_identity_and_sensitivity():
    result = calculate_company_dcf(sec_fixture(), ticker="MSFT", cik=789019,
                                   assumptions={"growth_pct": 0, "margin_pct": 20,
                                                "wacc_pct": 10, "terminal_growth_pct": 2,
                                                "tax_pct": 20, "nwc_pct": 0})
    assert len(result["forecast"]) == 5
    assert all(x["fcff_usd"] == 17_000_000 for x in result["forecast"])
    assert result["observed"]["net_debt_usd"] == -7_000_000
    base = result["base"]
    assert base["equity_usd"] == pytest.approx(base["enterprise_usd"] + 7_000_000, abs=1)
    assert base["price_usd"] == pytest.approx(base["equity_usd"] / 10_000_000, abs=.01)
    assert result["sensitivity"][1]["values"][1]["price_usd"] == base["price_usd"]
    # Holding all else constant, higher WACC lowers enterprise value.
    assert result["sensitivity"][0]["values"][1]["price_usd"] < base["price_usd"]
    # Raising terminal growth increases enterprise value.
    assert result["sensitivity"][1]["values"][0]["price_usd"] < base["price_usd"]
    assert "WeightedAverageNumberOfDilutedSharesOutstanding" in result["provenance"]["shares"]["tag"]
    assert "NOT a buy signal" in result["limitations"]


def test_dcf_blocks_missing_sec_inputs_and_bad_assumptions():
    with pytest.raises(DeskError, match="D&A was not available"):
        calculate_company_dcf(sec_fixture(omit=["DepreciationDepletionAndAmortization"]),
                              ticker="MSFT", cik=789019)
    with pytest.raises(DeskError, match="identifier"):
        calculate_company_dcf(sec_fixture(), ticker="AAPL", cik=1)
    with pytest.raises(DeskError, match="WACC"):
        calculate_company_dcf(sec_fixture(), ticker="MSFT", cik=789019,
                              assumptions={"wacc_pct": 3, "terminal_growth_pct": 3})
    with pytest.raises(DeskError, match="growth_pct"):
        calculate_company_dcf(sec_fixture(), ticker="MSFT", cik=789019,
                              assumptions={"growth_pct": float('nan')})


def test_dcf_valid_annual_depreciation_tags_and_explicit_assumption():
    for tag in ("DepreciationAndAmortization", "DepreciationAmortizationAndAccretionNet"):
        payload = sec_fixture(omit=["DepreciationDepletionAndAmortization"])
        payload["facts"]["us-gaap"][tag] = {"units": {"USD": [fact(5_000_000, annual=True)]}}
        result = calculate_company_dcf(payload, ticker="MSFT", cik=789019)
        assert result["provenance"]["da"]["tag"] == tag
        assert result["observed"]["da_is_assumed"] is False
    payload = sec_fixture(omit=["DepreciationDepletionAndAmortization"])
    res = calculate_company_dcf(payload, ticker="MSFT", cik=789019,
                                assumptions={"da_pct": "4"})
    assert res["observed"]["da_is_assumed"] is True
    assert res["observed"]["da_to_sales_pct"] == 4.0
    assert "da" not in res["provenance"]
    assert res["forecast"][0]["da_usd"] > 0
    assert "NOT a reported SEC number" in res["limitations"]
    # Explicit user scenario beats a tagged amount and remains visibly assumed.
    explicit = calculate_company_dcf(sec_fixture(), ticker="MSFT", cik=789019,
                                     assumptions={"da_pct": 1})
    assert explicit["observed"]["da_is_assumed"] is True
    assert explicit["observed"]["da_to_sales_pct"] == 1.0
    for bad in (-1, 50.1, float("nan"), "not-a-number"):
        with pytest.raises(DeskError, match="da_pct"):
            calculate_company_dcf(payload, ticker="MSFT", cik=789019,
                                  assumptions={"da_pct": bad})



def test_missing_short_term_investments_disclosed():
    result = calculate_company_dcf(sec_fixture(omit=["ShortTermInvestments"]),
                                   ticker="MSFT", cik=789019)
    assert not result["observed"]["short_term_investments_included"]
    assert "net debt excludes them" in result["limitations"]


class Response:
    def __init__(self, p):
        self.data = p

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class Session:
    def get(self, url, *, headers, timeout):
        if "company_tickers.json" in url:
            return Response({"0": {"ticker": "MSFT", "cik_str": 789019},
                             "1": {"ticker": "AAPL", "cik_str": 789019}})
        return Response(sec_fixture())


def test_dcf_and_comparables_local_api(tmp_path):
    sec = SECResearch(user_agent="Personal dev@myresearch.test", session=Session())
    comparisons = compare_fundamentals(sec, ["MSFT", "AAPL"])
    assert len(comparisons["companies"]) == 2
    assert comparisons["companies"][0]["data"]["operating_margin_pct"] == 20
    ledger = PaperLedger(tmp_path / "paper.sqlite3")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ledger, DemoDeskMarket(), demo=True, sec_research=sec))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        path = "/api/company-dcf?" + urlencode({"symbol": "MSFT", "growth_pct": "0",
                                                  "margin_pct": "20", "wacc_pct": "10",
                                                  "terminal_growth_pct": "2"})
        with urlopen(root + path) as response:
            assert json.load(response)["ticker"] == "MSFT"
        with urlopen(root + "/api/company-comparables?symbols=MSFT,AAPL") as response:
            assert len(json.load(response)["companies"]) == 2
        with pytest.raises(HTTPError) as exc:
            urlopen(root + "/api/company-dcf?symbol=MSFT&wacc_pct=3&terminal_growth_pct=6")
        assert exc.value.code == 422
        with urlopen(root + "/") as response:
            html = response.read().decode()
        for marker in ('id="dcfSymbol"', 'id="dcfSensitivity"', 'id="fundCompare1"', 'id="dcfDa"'):
            assert marker in html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_dcf_http_supports_manual_da_when_sec_tag_missing(tmp_path):
    class MissingDaSession(Session):
        def get(self, url, *, headers, timeout):
            if "companyfacts" in url:
                return Response(sec_fixture(omit=["DepreciationDepletionAndAmortization"]))
            return super().get(url, headers=headers, timeout=timeout)

    sec = SECResearch(user_agent="Personal dev@myresearch.test", session=MissingDaSession())
    ledger = PaperLedger(tmp_path / "paper.sqlite3")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(
        ledger, DemoDeskMarket(), demo=True, sec_research=sec))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with pytest.raises(HTTPError) as exc:
            urlopen(root + "/api/company-dcf?symbol=MSFT")
        assert exc.value.code == 422
        path = "/api/company-dcf?" + urlencode({"symbol": "MSFT", "da_pct": "4"})
        with urlopen(root + path) as response:
            result = json.load(response)
        assert result["observed"]["da_is_assumed"] is True
        assert result["assumptions_pct"]["da_of_revenue"] == 4.0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
