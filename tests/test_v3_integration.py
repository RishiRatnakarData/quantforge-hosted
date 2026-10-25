"""SEC network mock and offline file-production smoke tests."""

import json
from pathlib import Path

import pandas as pd
import pytest

from quantforge.financials.annual import download_companyfacts
from quantforge.financials.demo import synthetic_companyfacts
from quantforge.research.v3 import run_v3_study


class MockResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class MockSession:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    def get(self, url, **kwargs):
        self.requests.append((url, kwargs))
        return MockResponse(self.payload)


def test_declared_user_agent_and_content_addressed_cache(tmp_path):
    session = MockSession(synthetic_companyfacts())
    target = tmp_path / "CIK0000789019_companyfacts.json"
    stored = download_companyfacts(
        user_agent="QuantForge Research qa@example.org", target=target, session=session
    )
    assert stored.exists() and stored != target
    assert len(session.requests) == 1
    url, opts = session.requests[0]
    assert "CIK0000789019" in url
    assert "qa@example.org" in opts["headers"]["User-Agent"]
    assert not any("qa@example.org" in x for x in stored.read_text(encoding="utf-8").splitlines())
    previous_bytes = stored.read_bytes()
    assert download_companyfacts(user_agent="QuantForge Research qa@example.org",
                                 target=target, session=session) == stored
    assert stored.read_bytes() == previous_bytes


def test_refuse_unnamed_sec_bot(tmp_path):
    session = MockSession(synthetic_companyfacts())
    with pytest.raises(ValueError, match="User-Agent"):
        download_companyfacts(user_agent="QuantForge", target=tmp_path / "x.json", session=session)
    assert not session.requests


def test_reject_mismatched_cik(tmp_path):
    payload = synthetic_companyfacts()
    payload["cik"] = 123456
    with pytest.raises(ValueError, match="CIK"):
        download_companyfacts(user_agent="QuantForge qa@example.org",
                              target=tmp_path / "x.json", session=MockSession(payload))


def test_v3_full_artifacts_and_memo_math(tmp_path):
    input_path = tmp_path / "synthetic.json"
    input_path.write_text(json.dumps(synthetic_companyfacts()), encoding="utf-8")
    output = tmp_path / "research"
    result = run_v3_study(input_path, as_of="2026-10-22", output=output,
                          config_path=Path("configs/valuation_assumptions.json"),
                          origin="synthetic_demo")
    assert result["scenarios"] == 3
    expected = ("sec_fact_audit.csv", "sec_financials.csv", "historical_fundamentals.csv",
                "dcf_scenarios.csv", "dcf_sensitivity.csv", "forecast_drivers.csv",
                "INVESTMENT_MEMO.md", "valuation_dashboard.html", "manifest_v3.json",
                "financial_statement_audit.json", "valuation_assumptions.json")
    assert all((output / filename).stat().st_size > 100 for filename in expected)
    audit = pd.read_csv(output / "sec_fact_audit.csv")
    assert len(audit) > 75
    assert audit["filed"].dropna().le("2026-10-22").all()
    values = pd.read_csv(output / "dcf_scenarios.csv").set_index("scenario")
    memo = (output / "INVESTMENT_MEMO.md").read_text(encoding="utf-8")
    assert f"${values.loc['base', 'intrinsic_value_per_share_usd']:,.1f}" in memo
    assert "SYNTHETIC" in memo
    manifest = json.loads((output / "manifest_v3.json").read_text(encoding="utf-8"))
    assert manifest["portfolio_2019_2025_holdout_accessed"] is False
    assert manifest["as_of"] == "2026-10-22"


def test_cannot_disguise_demo_as_real_sec(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(synthetic_companyfacts()), encoding="utf-8")
    with pytest.raises(ValueError, match="synthetic"):
        run_v3_study(path, as_of="2026-10-22", output=tmp_path / "out",
                     config_path=Path("configs/valuation_assumptions.json"))
