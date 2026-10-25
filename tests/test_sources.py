from __future__ import annotations

import pytest

from quantforge.data.sources import ProviderError, fred_vintage, read_market_csv, sec_companyfacts


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse(self.payload)


def test_fred_vintage_request_is_point_in_time():
    session = FakeSession(
        {"observations": [{"date": "2020-01-01", "value": "1.3", "realtime_start": "2020-02-01", "realtime_end": "2020-02-01"}]}
    )
    frame = fred_vintage("GDP", as_of="2020-02-01", observation_start="2018-01-01", api_key="x" * 32, session=session)
    params = session.calls[0][1]["params"]
    assert params["realtime_start"] == params["realtime_end"] == "2020-02-01"
    assert params["observation_end"] == "2020-02-01"
    assert frame.iloc[0]["value"] == 1.3


def test_fred_missing_key_fails(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="FRED_API_KEY"):
        fred_vintage("GDP", as_of="2020-01-01", observation_start="2010-01-01")


def test_sec_declared_user_agent():
    fake = FakeSession({"cik": 789019, "facts": {"us-gaap": {}}})
    facts = sec_companyfacts(789019, user_agent="Research analyst@example.org", session=fake)
    assert facts["cik"] == 789019
    assert "CIK0000789019" in fake.calls[0][0]
    assert "analyst@example.org" in fake.calls[0][1]["headers"]["User-Agent"]


def test_sec_user_agent_required(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with pytest.raises(ProviderError):
        sec_companyfacts(789019)


def test_csv_vendor_mandatory(tmp_path, price_frame):
    file = tmp_path / "input.csv"
    price_frame.to_csv(file, index=False)
    with pytest.raises(ValueError):
        read_market_csv(file, vendor=" ", price_basis="dividend_adjusted_close")
    assert len(read_market_csv(file, vendor="Research licensed file", price_basis="dividend_adjusted_close")) == 360
