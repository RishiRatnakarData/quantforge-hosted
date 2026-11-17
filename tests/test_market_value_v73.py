"""V7.3 SEC share/debt selection, auth boundary and accuracy regression tests."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from cloud.sec_fundamentals import SECFundamentalsError
from cloud.valuation_market_v73 import _fact, extract

TODAY = dt.date(2026, 10, 27)


def make_raw(shares=7_500_000_000):
    def row(value, end, form="10-K", filed="2026-08-01", start=None):
        data = {"val": value, "end": end, "form": form, "filed": filed, "accn": "0000789019-26-000001"}
        if start:
            data["start"] = start
        return data
    return {"cik": 789019, "facts": {
        "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
            row(shares, "2026-07-31"), row(100, "2024-01-01", filed="2024-02-01"),
            row(1_000, "2026-08-31", filed="2026-11-01"),
        ]}}},
        "us-gaap": {
            "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [row(30e9,"2026-06-30")]}},
            "LongTermDebtCurrent": {"units": {"USD": [row(6e9,"2026-06-30")]}},
            "LongTermDebtNoncurrent": {"units": {"USD": [row(41e9,"2026-06-30")]}},
        },
    }}


def test_selects_point_in_time_shares_and_same_period_balance_sheet():
    out=extract(make_raw(), symbol="MSFT", cik=789019, as_of=TODAY)
    assert out["shares"]["value"] == 7_500_000_000
    assert out["reportedDebtComponentsTotal"] == 47e9
    assert out["debtCashSamePeriod"] is True
    assert out["cash"]["value"] == 30e9


def test_never_mix_debt_from_different_balance_sheet_dates():
    raw = make_raw()
    raw["facts"]["us-gaap"]["LongTermDebtNoncurrent"]["units"]["USD"][0]["end"]="2026-03-31"
    out=extract(raw,symbol="MSFT",cik=789019,as_of=TODAY)
    assert out["noncurrentLongTermDebt"] is None
    assert out["reportedDebtComponentsTotal"] is None


def test_missing_shares_never_become_zero():
    raw = make_raw()
    raw["facts"]["dei"] = {}
    out=extract(raw,symbol="MSFT",cik=789019,as_of=TODAY)
    assert out["shares"] is None


def test_duration_share_facts_not_accepted_as_instant_shares():
    raw = make_raw()
    raw["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"] = [
        {"val":7000000000,"start":"2025-07-01","end":"2026-06-30","filed":"2026-08-01","form":"10-K"}]
    assert extract(raw,symbol="MSFT",cik=789019,as_of=TODAY)["shares"] is None


def test_company_cik_mismatch_rejected():
    with pytest.raises(SECFundamentalsError):
        extract(make_raw(), symbol="MSFT", cik=1, as_of=TODAY)


def test_future_date_and_nonfinite_values_rejected():
    x={"us-gaap":{"CashAndCashEquivalentsAtCarryingValue":{"units":{"USD":[
        {"val":float("nan"),"end":"2026-06-30","filed":"2026-08-01","form":"10-K"},
        {"val":99,"end":"2026-06-30","filed":"2026-11-01","form":"10-K"},
    ]}}}}
    assert _fact(x,"us-gaap","CashAndCashEquivalentsAtCarryingValue","USD",as_of=TODAY) is None


def test_private_route_is_guarded_in_source():
    # Use AST-independent textual audit: route invokes existing MFA owner check.
    source=(Path(__file__).resolve().parents[1]/"cloud/api.py").read_text(encoding="utf-8")
    assert '@app.get("/api/private/valuation-capital")' in source
    route=source.split('@app.get("/api/private/valuation-capital")',1)[1].split('@app.',1)[0]
    assert 'owner(request, response)' in route
    assert 'valuation_market_v73.get_capital(symbol)' in route
