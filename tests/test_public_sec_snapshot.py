"""Regression tests: public market-data boundary and SEC annual facts extraction."""
import datetime as dt
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("public_sec", ROOT / "tools/build_public_sec_snapshot.py")
sec = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(sec)


def fixture(cik=789019):
    def annual(vals):
        return {"units": {"USD": [dict(form="10-K", fp="FY", start=f"{year-1}-07-01",
                                       end=f"{year}-06-30", filed=f"{year}-07-31",
                                       accn=f"0000-{year}-01", val=val)
                                  for year, val in vals]}}
    return {"cik": cik, "facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": annual([(2024, 100), (2025, 125), (2026, 150)]),
        "OperatingIncomeLoss": annual([(2024, 20), (2025, 30), (2026, 45)]),
        "NetCashProvidedByUsedInOperatingActivities": annual([(2024, 11), (2025, 12), (2026, 13)]),
        "PaymentsToAcquirePropertyPlantAndEquipment": annual([(2024, 4), (2025, 5), (2026, 6)]),
    }}}


def test_asof_blocks_future_filings():
    msft = sec.transform(fixture(), "MSFT", dt.date(2025, 8, 1))
    assert [x["fiscal_end"] for x in msft["annual"]] == ["2025-06-30", "2024-06-30"]
    assert msft["annual"][0]["metrics"]["revenue_usd"] == 125
    assert msft["annual"][0]["metrics"]["free_cash_flow_usd"] == 7


def test_missing_annual_metrics_are_not_invented():
    data = fixture()
    del data["facts"]["us-gaap"]["OperatingIncomeLoss"]
    latest = sec.transform(data, "MSFT", dt.date(2026, 9, 1))["annual"][0]
    assert latest["metrics"]["operating_income_usd"] is None


def test_cik_mismatch_fails_closed():
    with pytest.raises(ValueError, match="CIK mismatch"):
        sec.transform(fixture(), "AAPL", dt.date(2026, 9, 1))


def test_fake_or_stale_annual_facts_rejected():
    data = fixture()
    facts = data["facts"]["us-gaap"]["RevenueFromContractWithCustomerExcludingAssessedTax"]["units"]["USD"]
    facts[0]["form"] = "10-Q"
    with pytest.raises(ValueError, match="fewer than 2"):
        sec.transform(data, "MSFT", dt.date(2025, 8, 1))


def test_no_secrets_or_market_data_in_public_snapshot():
    data = fixture()
    result = sec.transform(data, "MSFT", dt.date(2026, 9, 1))
    text = json.dumps(result).lower()
    for disallowed in ("alpaca", "token", "api_key", "stock_prices", "private_portfolio", "user_agent"):
        assert disallowed not in text


def test_public_site_and_builder_have_distinct_data_origin():
    template = (ROOT / "web/site/site.template.html").read_text(encoding="utf-8")
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    assert 'id="page-sec"' in template
    assert 'id="sec-company"' in template
    assert "/* QF_SEC_DATA */" in (ROOT / "web/site/app.js").read_text(encoding="utf-8")
    assert 'sec_snapshot.json' in builder
    assert 'RESEARCH OVERVIEW' in template
    assert 'Simulated holdings and prices' in template


def test_public_universe_is_twelve_named_distinct_issuers():
    assert len(sec.ISSUERS) == 12
    assert len({cik for cik, _ in sec.ISSUERS.values()}) == 12
    assert set(sec.SECTORS) == set(sec.ISSUERS)
    assert {"MSFT", "AAPL", "NVDA", "GOOGL", "AMZN", "META", "COST", "WMT", "KO", "JNJ", "XOM", "CAT"} == set(sec.ISSUERS)


def test_public_sec_selector_generated_from_dataset():
    js = (ROOT / "web/site/app.js").read_text(encoding="utf-8")
    assert "$('sec-company').innerHTML=SEC_DATA.companies.map" in js
    assert "SEC_DATA.companies.map(c=>" in js
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    # Duplicates and missing original issuers must still be rejected.
    assert "len(symbols) != len(set(symbols))" in builder
    assert "not set(ISSUERS).issubset(symbols)" in builder
    # Additional issuers are allowed, but core CIK and SEC lineage must be checked.
    assert "c['symbol'] in ISSUERS and c['cik'] != ISSUERS[c['symbol']][0]" in builder
    assert "source_url" in builder
    assert "len(c['annual']) < 2" in builder


def test_sector_is_explicitly_editorial_not_gaap():
    result = sec.transform(fixture(), "MSFT", dt.date(2026, 9, 1))
    assert result["sector"] == "Technology"
    assert "sector" not in result["annual"][0]["metrics"]


def test_snapshot_requests_each_public_issuer_with_identifiable_header(monkeypatch):
    class FakeResponse:
        def __init__(self, cik):
            self.cik = cik

        def raise_for_status(self):
            return None

        def json(self):
            return fixture(self.cik)

    calls = []
    agent = "QuantForge Research " + "someone" + chr(64) + "domain.test"

    def fake_get(url, headers, timeout):
        assert timeout == 35
        assert headers['User-Agent'] == agent
        assert headers['Accept'] == 'application/json'
        cik = int(url.split('CIK')[1].split('.json')[0])
        calls.append(cik)
        return FakeResponse(cik)

    monkeypatch.setattr(sec.time, 'sleep', lambda *_args: None)
    dataset = sec.build_snapshot(dt.date(2026, 9, 1), agent, get=fake_get)
    assert len(calls) == len(sec.ISSUERS) == len(dataset['companies']) == 12
    assert len(set(calls)) == 12
    assert {c['symbol'] for c in dataset['companies']} == set(sec.ISSUERS)
    assert all(len(c['annual']) == 3 for c in dataset['companies'])
