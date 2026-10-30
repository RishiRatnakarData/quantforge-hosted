"""V10.0 resumable official SEC archive collection and coverage-boundary tests."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
collector = importlib.import_module("build_sec_archive_v100")
coverage = importlib.import_module("report_sec_archive_v100")


def source_fact(value: int, year: int) -> dict:
    return {
        "form": "10-K", "fp": "FY", "start": f"{year}-01-01",
        "end": f"{year}-12-31", "filed": f"{year + 1}-03-01",
        "accn": f"0000000001-{(year + 1) % 100:02d}-000001", "val": value,
    }


def raw(cik: int) -> dict:
    def unit(values):
        return {"units": {"USD": [source_fact(v, year) for year, v in values]}}

    return {"cik": cik, "facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": unit([(2023, 100), (2024, 120)]),
        "NetCashProvidedByUsedInOperatingActivities": unit([(2023, 30), (2024, 40)]),
        "PaymentsToAcquirePropertyPlantAndEquipment": unit([(2023, 8), (2024, 10)]),
    }}}


def reference() -> dict:
    return {"dataset": "SEC EDGAR Company Facts, annual 10-K US-GAAP", "companies": [
        {"symbol": "AAA", "cik": 1}, {"symbol": "BBB", "cik": 2},
    ]}


def test_validated_cached_offline_archive_is_compatible_with_v99(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "ROOT", tmp_path)
    cache = tmp_path / "data" / "source_cache"
    cache.mkdir(parents=True)
    for issuer in reference()["companies"]:
        (cache / f"CIK{issuer['cik']:010d}.json").write_text(
            json.dumps(raw(issuer["cik"])), encoding="utf-8"
        )
    archive, failures = collector.collect(
        reference(), cache_dir=cache, as_of="2026-10-29", offline=True,
    )
    assert not failures
    assert len(archive["companies"]) == 2
    assert all(len(c["annual"]) == 2 for c in archive["companies"])
    report = coverage.report(
        archive, reference(), ["2024-07-01", "2025-07-01", "2026-01-01"], ["AAA", "BBB"]
    )
    assert report["selected_complete_dates"] == ["2025-07-01", "2026-01-01"]
    assert report["provenance"]["source_facts"] == 12


def test_invalid_cik_does_not_poison_archive_and_missing_remains_visible(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "ROOT", tmp_path)
    cache = tmp_path / "data" / "source_cache"
    cache.mkdir(parents=True)
    (cache / "CIK0000000001.json").write_text(json.dumps(raw(1)), encoding="utf-8")
    (cache / "CIK0000000002.json").write_text(json.dumps(raw(99)), encoding="utf-8")
    archive, failures = collector.collect(
        reference(), cache_dir=cache, as_of="2026-10-29", offline=True,
    )
    assert len(archive["companies"]) == 1
    assert failures and failures[0]["symbol"] == "BBB"
    report = coverage.report(archive, reference(), ["2025-07-01"], ["AAA", "BBB"])
    assert report["selected_complete_count"] == 0
    assert not report["issuers"][1]["imported"]


def test_source_contact_and_response_size_are_enforced():
    at = chr(64)
    assert collector.validate_user_agent("QuantForge Research researcher" + at + "validdomain.org")
    for agent in ("Bot", "QuantForge bot" + at + "example.com", "hello\nfoo" + at + "bar.com"):
        with pytest.raises(ValueError):
            collector.validate_user_agent(agent)
    with pytest.raises(ValueError, match="CIK"):
        collector.parse_payload(json.dumps(raw(9)).encode(), 1, "AAA")
    with pytest.raises(ValueError, match="18 MB"):
        collector.parse_payload(b"a" * (collector.MAX_BYTES + 1), 1, "AAA")


def test_report_never_fabricates_future_or_uncollected_financial_evidence():
    with pytest.raises(ValueError, match="schema"):
        coverage.report({"schema": "none"}, reference(), [], [])
    assert coverage.make_decisions(2025, 2026, "2025-10-29") == [
        "2025-01-01", "2025-07-01"
    ]


def test_production_build_retains_three_scripts_and_private_archive_components():
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    app = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    assert "private_archive_quality_v100.js').read_text" in builder
    for marker in ("qf-v100-hub-result", "qf-v100-brief", "qf-v100-lab-insight"):
        assert builder.count(f'id="{marker}"') == 1
    assert "function renderArchiveQualityV100()" in app
    assert "secArchiveReadinessV100:" in app
    assert "clearImportedSECV99();" in app


def test_raw_sec_archive_stays_ignored_and_separate_from_public_build():
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/data/*" in ignored
    for name in ("build_sec_archive_v100.py", "report_sec_archive_v100.py"):
        content = (ROOT / "tools" / name).read_text(encoding="utf-8")
        assert "public/index.html" not in content
        assert "private/trade" not in content
