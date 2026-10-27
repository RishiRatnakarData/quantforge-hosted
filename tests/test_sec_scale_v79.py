"""V7.9 public SEC Company Facts expansion: genuine filing selection, no invented data."""
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "extend_public_sec_v79.py"
spec = importlib.util.spec_from_file_location("sec_v79", SCRIPT)
sec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sec)


def fact(tag, val, *, start="2023-01-01", end="2023-12-31", filed="2024-02-01"):
    return {"start": start, "end": end, "filed": filed, "form": "10-K", "fp": "FY",
            "accn": "0000000001-24-000001", "val": val}


def company_fixture():
    def item(x, tag):
        result = fact(tag, x)
        prior = fact(tag, x * .8, start="2022-01-01", end="2022-12-31", filed="2023-02-01")
        return {"units": {"USD": [result, prior]}}
    return {"cik": 1234, "entityName": "Fictional test fixture, not a published issuer",
            "facts": {"us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": item(120, "RevenueFromContractWithCustomerExcludingAssessedTax"),
                "OperatingIncomeLoss": item(20, "OperatingIncomeLoss"),
                "NetCashProvidedByUsedInOperatingActivities": item(30, "NetCashProvidedByUsedInOperatingActivities"),
                "PaymentsToAcquirePropertyPlantAndEquipment": item(7, "PaymentsToAcquirePropertyPlantAndEquipment"),
            }}}


def test_valid_annual_facts_have_lineage_and_fcf_proxy():
    row = sec.build_company(company_fixture(), "DEMO", 1234, "2026-10-27")
    assert len(row["annual"]) == 2
    latest = row["annual"][0]
    assert latest["metrics"]["free_cash_flow_usd"] == 23
    assert latest["sources"]["revenue_usd"]["accession"] == "0000000001-24-000001"
    assert latest["metrics"]["net_income_usd"] is None


def test_no_future_filings_or_wrong_issuer():
    assert sec.build_company(company_fixture(), "DEMO", 9999, "2026-10-27") is None
    assert sec.build_company(company_fixture(), "DEMO", 1234, "2022-01-01") is None


def test_too_short_period_and_wrong_form_are_rejected():
    item = fact("Revenues", 10, start="2023-10-01", end="2023-12-31")
    assert sec.annual_observations({"facts": {"us-gaap": {"Revenues": {"units": {"USD": [item]}}}}}, ("Revenues",), "2026-10-27") == []
    item["form"] = "8-K"
    assert sec.annual_observations({"facts": {"us-gaap": {"Revenues": {"units": {"USD": [item]}}}}}, ("Revenues",), "2026-10-27") == []


def test_bad_symbols_rejected():
    for item in ["AAPL,<script>", "XYZ/US", ""]:
        try:
            sec.parse_symbols(item)
        except ValueError:
            pass
        else:
            raise AssertionError("Untrusted symbol unexpectedly accepted")
