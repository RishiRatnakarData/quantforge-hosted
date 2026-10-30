"""V9.9 local original-filing archive, dated replay, and privacy boundaries."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
collector = importlib.import_module("build_sec_filing_archive_v98")
validator = importlib.import_module("validate_local_sec_archive_v99")


def sample_fact(value: int, filed: str, accession: str) -> dict:
    return {
        "form": "10-K",
        "fp": "FY",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "filed": filed,
        "accn": accession,
        "val": value,
    }


def sample_raw() -> dict:
    def facts(v):
        return {"units": {"USD": [
            sample_fact(v, "2025-03-01", "0000000001-25-000001"),
            {**sample_fact(v + 10, "2025-06-01", "0000000001-25-000002"), "form": "10-K/A"},
        ]}}

    return {"cik": 1, "facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": facts(100),
        "NetCashProvidedByUsedInOperatingActivities": facts(30),
        "PaymentsToAcquirePropertyPlantAndEquipment": facts(10),
    }}}


def test_official_collector_records_accepted_by_independent_local_validator():
    reference = {"dataset": "SEC EDGAR Company Facts, annual 10-K US-GAAP", "companies": [
        {"symbol": "AAA", "cik": 1}
    ]}
    archive = collector.build(reference, {"AAA": sample_raw()}, "2026-10-29")
    result = validator.audit(archive, reference)
    assert result["issuer_count"] == 1
    assert result["source_facts"] == 6
    assert result["fields_with_later_versions"] == 3
    assert "not a certification" in result["caveat"]


def test_archive_refuses_tampered_cik_and_temporal_source_lineage():
    reference = {"dataset": "SEC EDGAR Company Facts, annual 10-K US-GAAP", "companies": [
        {"symbol": "AAA", "cik": 1}
    ]}
    archive = collector.build(reference, {"AAA": sample_raw()}, "2026-10-29")
    archive["companies"][0]["cik"] = 2
    with pytest.raises(ValueError, match="CIK"):
        validator.audit(archive, reference)
    archive["companies"][0]["cik"] = 1
    revenue = archive["companies"][0]["annual"][0]["revisions"]["revenue_usd"]
    revenue[0]["filed"] = "2024-01-02"
    with pytest.raises(ValueError, match="chronology"):
        validator.audit(archive, reference)


def test_private_interface_is_connected_and_filing_archive_stays_opt_in():
    app = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    helper = (ROOT / "web/site/private_archived_sec_v99.js").read_text(encoding="utf-8")
    for expected in (
        "QFPrivateArchivedSECValidationV99.run({",
        "renderArchivedSECV99();",
        "function importArchivedSECV99()",
        "archivedSECv99:linkedArchivedSECV99?",
        "if(!privateState){importedSECArchiveV99=null;",
        "archiveReadTokenV99++",
        "clearImportedSECV99(); // Invalidate imported financial records",
    ):
        assert expected in app
    for expected in (
        'id="qf-v99-file"',
        'id="qf-v99-hub-result"',
        'id="qf-v99-brief"',
        'id="qf-v99-lab-insight"',
        "private_archived_sec_v99.js').read_text",
    ):
        assert expected in builder
    for forbidden in (
        "localStorage", "sessionStorage", "fetch(", "private/trade", "private/notes"
    ):
        assert forbidden not in helper


def test_generated_three_script_csp_and_unique_research_views():
    page = (ROOT / "public/index.html").read_text(encoding="utf-8")
    assert page.count("<script>") == 3
    assert "QFPrivateArchivedSECValidationV99" in page
    for element in (
        "qf-v99-file", "qf-v99-clear", "qf-v99-hub-result",
        "qf-v99-brief", "qf-v99-lab-insight"
    ):
        assert page.count(f'id="{element}"') == 1
    assert page.count('id="private-mfa-code"') == 1


def test_validator_is_local_and_archive_never_written_to_published_site():
    source = (ROOT / "tools/validate_local_sec_archive_v99.py").read_text(
        encoding="utf-8"
    )
    assert 'ROOT / "data/sec_filing_revisions_v98.json"' in source
    assert "is_relative_to(allowed)" in source
    for forbidden in ("urllib.request", "Alpaca", "public/index.html", "brokerage order"):
        assert forbidden not in source
