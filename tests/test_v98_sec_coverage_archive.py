"""V9.8 issuer evidence coverage and local SEC filing revision archive boundaries."""

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ARCHIVE = importlib.import_module("build_sec_filing_archive_v98")
build = ARCHIVE.build
extract_issuer = ARCHIVE.extract_issuer


def fact(value, filed, accession, end="2024-12-31"):
    return {
        "form": "10-K",
        "fp": "FY",
        "start": "2024-01-01",
        "end": end,
        "filed": filed,
        "accn": accession,
        "val": value,
    }


def issuer_fixture():
    original = fact(100, "2025-02-28", "0000000001-25-000001")
    amended = {**fact(110, "2025-05-12", "0000000001-25-000002"), "form": "10-K/A"}
    invalid = fact(9999, "2027-02-28", "0000000001-27-000001")
    gaap = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {
            "units": {"USD": [original, amended, invalid]}
        },
        "NetCashProvidedByUsedInOperatingActivities": {
            "units": {"USD": [fact(50, "2025-02-28", "0000000001-25-000001")]}
        },
        "PaymentsToAcquirePropertyPlantAndEquipment": {
            "units": {"USD": [fact(12, "2025-02-28", "0000000001-25-000001")]}
        },
    }
    return {"cik": 1, "facts": {"us-gaap": gaap}}


def test_preserves_original_and_amended_values_without_future_leakage():
    data = extract_issuer(issuer_fixture(), "AAA", 1, "2026-10-29")
    revisions = data["annual"][0]["revisions"]["revenue_usd"]
    assert [x["filed"] for x in revisions] == ["2025-02-28", "2025-05-12"]
    assert [x["value"] for x in revisions] == [100, 110]
    assert all(x["accession"].startswith("0000000001") for x in revisions)
    assert data["source_url"].endswith("CIK0000000001.json")


def test_asof_cutoff_filters_amendment_and_bad_source_data():
    data = extract_issuer(issuer_fixture(), "AAA", 1, "2025-03-01")
    values = data["annual"][0]["revisions"]["revenue_usd"]
    assert len(values) == 1
    assert values[0]["value"] == 100
    with pytest.raises(ValueError, match="CIK/source mismatch"):
        extract_issuer(issuer_fixture(), "AAA", 2, "2025-03-01")
    with pytest.raises(ValueError, match="cutoff"):
        extract_issuer(issuer_fixture(), "AAA", 1, "not-a-date")


def test_validates_issuer_seed_and_discloses_snapshot_limitations():
    snap = {"dataset": "SEC EDGAR Company Facts, annual 10-K US-GAAP", "companies": [
        {"symbol": "AAA", "cik": 1}
    ]}
    result = build(snap, {"AAA": issuer_fixture()}, "2026-10-29")
    assert result["coverage"] == {"seed_issuers": 1, "downloaded_issuers": 1}
    assert "not" in result["limitations"][0].lower()
    assert "portfolio" not in json.dumps(result)
    with pytest.raises(ValueError, match="Duplicate"):
        build({**snap, "companies": [snap["companies"][0]] * 2}, {}, "2026-10-29")


def test_connected_research_uses_same_selected_universe_and_clears_stale_results():
    app = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    assert "linkedSECCoverageV98=window.QFPrivateSECCoverageV98.run({" in app
    assert "linkedSECCoverageV98=null;" in app
    assert "renderSECCoverageV98();" in app
    assert "secCoverageV98:linkedSECCoverageV98?" in app
    for marker in ("qf-v98-hub", "qf-v98-brief", "qf-v98-lab-insight"):
        assert marker in app or marker in (ROOT / "tools/build_unified_site.py").read_text(
            encoding="utf-8"
        )


def test_bundle_contains_bounded_pure_helper_and_private_signin_intact():
    generated = (ROOT / "public/index.html").read_text(encoding="utf-8")
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    assert "private_sec_coverage_v98.js').read_text" in builder
    for marker in ("qf-v98-hub", "qf-v98-brief", "qf-v98-lab-insight"):
        assert generated.count(f'id="{marker}"') == 1
    assert generated.count('id="private-mfa-code"') == 1
    assert generated.count("<script") == 3
    assert "QFPrivateSECCoverageV98" in generated


def test_collector_has_no_automatic_deployment_or_private_market_data():
    builder = (ROOT / "tools/build_sec_filing_archive_v98.py").read_text(encoding="utf-8")
    assert 'ROOT / "data/sec_filing_revisions_v98.json"' in builder
    assert "--download" in builder
    assert "SEC_USER_AGENT" in builder
    assert "time.sleep(1.1)" in builder
    assert "is_relative_to(allowed)" in builder
    for forbidden in ("Alpaca", "private/notes", "brokerage-order"):
        assert forbidden not in builder
