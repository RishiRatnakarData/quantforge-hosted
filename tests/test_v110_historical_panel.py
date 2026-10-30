"""V11.0 point-in-time cross-sectional SEC research and publication boundaries."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
panel = importlib.import_module("historical_sec_panel_v110")


def fact(value: int, year: int, *, filed: str | None = None) -> dict:
    return {
        "start": f"{year}-01-01",
        "filed": filed or f"{year + 1}-03-01",
        "accession": "0000000001-25-000001",
        "tag": "RevenueFromContractWithCustomerExcludingAssessedTax",
        "tag_priority": 0,
        "value": value,
    }


def archive_and_snapshot() -> tuple[dict, dict]:
    issuers = []
    for symbol, cik in [("AAA", 1), ("BBB", 2)]:
        annual = []
        for year in (2023, 2024):
            income = 1000 if year == 2023 else 1300
            revenue = fact(income, year)
            cash = {**revenue, "tag": "NetCashProvidedByUsedInOperatingActivities", "value": 240}
            capex = {**revenue, "tag": "PaymentsToAcquirePropertyPlantAndEquipment", "value": 40}
            annual.append({
                "fiscal_end": f"{year}-12-31",
                "revisions": {
                    "revenue_usd": [revenue],
                    "operating_cash_flow_usd": [cash],
                    "capex_usd": [capex],
                },
            })
        issuers.append({"symbol": symbol, "cik": cik, "annual": annual})
    archive = {
        "schema": "quantforge.sec.filing-revisions.v9.8",
        "as_of": "2026-10-29",
        "companies": issuers,
    }
    snap = {
        "dataset": "SEC EDGAR Company Facts, annual 10-K US-GAAP",
        "companies": [{"symbol": s, "cik": c} for s, c in (("AAA", 1), ("BBB", 2))],
    }
    return archive, snap


def test_filing_date_not_fiscal_end_controls_historical_ratios():
    archive, _ = archive_and_snapshot()
    before = panel.evidence_at(archive["companies"][0], "2025-02-01")
    after = panel.evidence_at(archive["companies"][0], "2025-04-01")
    assert not before["ready"]
    assert after["ready"]
    assert after["revenue_growth"] == 0.3
    assert after["latest_filed"] == "2025-03-01"


def test_later_revisions_do_not_rewrite_earlier_evidence():
    archive, _ = archive_and_snapshot()
    issuer = archive["companies"][0]
    before = panel.evidence_at(issuer, "2025-04-01")
    issuer["annual"][1]["revisions"]["revenue_usd"].append(
        fact(5000, 2024, filed="2026-02-01")
    )
    assert panel.evidence_at(issuer, "2025-04-01") == before
    assert panel.evidence_at(issuer, "2026-04-01")["revenue_growth"] != before["revenue_growth"]


def test_full_panel_keeps_missing_issuer_and_dates_in_denominator():
    archive, snap = archive_and_snapshot()
    snap["companies"].append({"symbol": "CCC", "cik": 3})
    r = panel.panel(archive, snap, ["2025-02-01", "2025-07-01"])
    assert r["issuer_checkpoint_rows"] == 6
    assert r["eligible_issuer_checkpoints"] == 2
    assert r["cohorts"][0]["eligible"] == 0
    assert r["cohorts"][1]["eligible"] == 2
    assert r["cohorts"][1]["reference_issuers"] == 3
    assert r["issuer_coverage"][-1]["eligible"] == 0


def test_unsupported_cutoffs_and_duplicate_decisions_fail_closed():
    archive, snap = archive_and_snapshot()
    for checks in (["2026-11-01"], ["2025-07-01", "2025-07-01"], ["2025-07-01", "2025-01-01"]):
        with pytest.raises(ValueError):
            panel.panel(archive, snap, checks)


def test_offline_output_cannot_escape_ignored_data_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(panel, "ROOT", tmp_path)
    for path in (tmp_path / "../outside.json", tmp_path / "bad.json"):
        with pytest.raises(ValueError):
            panel.atomic_write(path, "{}")
    good = tmp_path / "data/sec_historical_panel_v110.json"
    panel.atomic_write(good, json.dumps({"ready": True}))
    assert json.loads(good.read_text()) == {"ready": True}


def test_new_interface_is_connected_and_keeps_all_existing_private_navigation():
    private = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    build = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    for marker in ("qf-v110-hub-result", "qf-v110-brief", "qf-v110-lab-insight"):
        assert marker in private and marker in build
    assert "historicalComparisonV110:" in private
    assert "private_historical_panel_v110.js" in build
    assert "qf-v99-file" in private
    assert "private-v90-run" in private
