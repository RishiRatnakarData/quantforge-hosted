import pytest

from quantforge.data.sources import ProviderError
from quantforge.financials.sec_facts import extract_filed_company_fact


@pytest.fixture
def facts():
    rows = [
        {"start": "2020-01-01", "end": "2020-03-31", "val": 50, "accn": "x1", "filed": "2020-05-01", "form": "10-Q"},
        {"start": "2020-01-01", "end": "2020-03-31", "val": 51, "accn": "x2", "filed": "2020-06-01", "form": "10-Q/A"},
        {"start": "2020-01-01", "end": "2020-03-31", "val": 80, "accn": "x3", "filed": "2020-05-01", "form": "8-K"},
    ]
    return {"facts": {"us-gaap": {"Revenues": {"units": {"USD": rows}}}}}


def test_sec_fact_preserves_filing_lag_and_amendments(facts):
    early = extract_filed_company_fact(facts, concept="Revenues", as_of="2020-05-15")
    late = extract_filed_company_fact(facts, concept="Revenues", as_of="2020-07-15")
    assert len(early) == 1
    assert early.iloc[0]["val"] == 50
    assert len(late) == 2
    assert set(late["val"]) == {50, 51}
    assert (late["filed"] <= "2020-07-15").all()


def test_sec_concept_error(facts):
    with pytest.raises(ProviderError):
        extract_filed_company_fact(facts, concept="Missing", as_of="2020-07-01")
