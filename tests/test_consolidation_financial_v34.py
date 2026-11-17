"""Publication-stage financial compatibility and owner-only universe regressions."""
import datetime as dt

from fastapi.testclient import TestClient

from cloud import api, research_universe
from cloud.valuation_market_v73 import extract


def fact(value, *, accession="0000789019-26-000001", start=None, unit="USD"):
    row = {"val": value, "end": "2026-06-30", "filed": "2026-08-01", "form": "10-K", "accn": accession}
    if start:
        row["start"] = start
    return {"units": {unit: [row]}}


def raw():
    return {"cik": 789019, "facts": {"us-gaap": {
        "CashAndCashEquivalentsAtCarryingValue": fact(30e9),
        "LongTermDebtCurrent": fact(6e9), "LongTermDebtNoncurrent": fact(41e9),
        "WeightedAverageNumberOfDilutedSharesOutstanding": fact(7.6e9, start="2025-07-01", unit="shares"),
    }}}


def test_balance_facts_need_same_filing_not_only_same_date():
    data = raw()
    valid = extract(data, symbol="MSFT", cik=789019, as_of=dt.date(2026, 11, 17))
    assert valid["debtCashSameFiling"] is True
    assert valid["reportedDebtComponentsTotal"] == 47e9
    assert valid["cash"]["accession"] == "0000789019-26-000001"
    data["facts"]["us-gaap"]["LongTermDebtNoncurrent"] = fact(44e9, accession="0000789019-26-000002")
    mixed = extract(data, symbol="MSFT", cik=789019, as_of=dt.date(2026, 11, 17))
    assert mixed["debtCashSamePeriod"] is True
    assert mixed["debtCashSameFiling"] is False
    assert mixed["reportedDebtComponentsTotal"] is None


def test_missing_filing_provenance_and_duration_shares_are_not_instant_capital():
    data = raw()
    del data["facts"]["us-gaap"]["LongTermDebtCurrent"]["units"]["USD"][0]["accn"]
    output = extract(data, symbol="MSFT", cik=789019, as_of=dt.date(2026, 11, 17))
    assert output["debtCashSameFiling"] is False
    assert output["shares"] is None
    assert output["annualDilutedShares"]["value"] == 7.6e9
    assert output["annualDilutedShares"]["start"] == "2025-07-01"
    assert "not current fully diluted" in output["shareBasisDisclosure"]


def test_future_and_quarterly_diluted_denominators_are_withheld():
    data = raw()
    row = data["facts"]["us-gaap"]["WeightedAverageNumberOfDilutedSharesOutstanding"]["units"]["shares"][0]
    row["start"] = "2026-04-01"
    assert extract(data, symbol="MSFT", cik=789019, as_of=dt.date(2026, 11, 17))["annualDilutedShares"] is None
    row["start"] = "2025-07-01"
    row["filed"] = "2026-12-01"
    assert extract(data, symbol="MSFT", cik=789019, as_of=dt.date(2026, 11, 17))["annualDilutedShares"] is None


def test_exact_eligible_sec_intersection_has_no_implicit_market_or_fund_coverage():
    snapshot = {"as_of": "2026-10-25", "companies": [{"symbol": "MSFT", "name": "Microsoft"}, {"symbol": "AAPL", "name": "Apple"}]}
    assets = [{"symbol": "MSFT", "asset_class": "us_equity", "tradable": True},
              {"symbol": "AAPL", "asset_class": "us_equity", "tradable": False},
              {"symbol": "SPY", "asset_class": "us_equity", "tradable": True}]
    result = research_universe.intersect(snapshot, assets)
    assert [row["symbol"] for row in result["items"]] == ["MSFT"]
    assert result["catalog_count"] == 2 and result["excluded_count"] == 1
    assert "whole market" in result["limitations"]


def test_universe_requires_existing_proxy_owner_and_mfa_boundary(monkeypatch):
    monkeypatch.setenv("QF_PROXY_SECRET", "fixture-proxy")
    monkeypatch.setenv("PUBLIC_SITE_ORIGIN", "https://quantforge.example")
    monkeypatch.setenv("OWNER_USER_ID", "fixture-owner")
    monkeypatch.setenv("SUPABASE_URL", "https://unit-test.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "fixture-public-key")
    calls = []
    monkeypatch.setattr(research_universe, "get_universe", lambda: calls.append(True) or {"eligible_count": 1})
    client = TestClient(api.app)
    assert client.get("/api/private/research-universe").status_code == 403
    assert not calls
    monkeypatch.setattr(api, "owner", lambda *_: ("fixture-owner", "fixture-token"))
    assert client.get("/api/private/research-universe", headers={"x-qf-proxy-secret": "fixture-proxy"}).json()["eligible_count"] == 1
    assert len(calls) == 1
