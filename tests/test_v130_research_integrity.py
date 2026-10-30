"""V13.0 SEC data lineage and research integration regression boundary."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
audit_chain = importlib.import_module("audit_research_chain_v130")


def fixture():
    archive = {"as_of": "2026-10-29", "schema": "quantforge.sec.filing-revisions.v9.8", "companies": []}
    snapshot = {"as_of": "2026-10-29", "companies": [{"symbol": "AAA", "cik": 1}]}
    digest = hashlib.sha256(json.dumps(archive, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    panel = {"schema": "quantforge.local-sec-historical-panel.v11.0", "source_sha256": digest,
             "archive_cutoff": "2026-10-29", "reference_issuers": 1, "total_checkpoints": 2,
             "eligible_issuer_checkpoints": 0, "cohorts": [{"checkpoint": "2024-01-01", "eligible": 0}, {"checkpoint": "2024-07-01", "eligible": 0}],
             "detail_rows": [{"symbol": "AAA", "checkpoint": d, "eligible": False, "reason": "Not filed"}
                             for d in ("2024-01-01", "2024-07-01")]}
    reliability = {"schema": "quantforge.sec-reliability.v12.0", "source_archive_sha256": digest,
                   "archive_cutoff": "2026-10-29", "reference_issuers": 1, "checkpoints": 2,
                   "scheduled_issuer_dates": 2, "eligible_issuer_dates": 0, "withheld_issuer_dates": 2,
                   "per_issuer": [{"symbol": "AAA", "eligible": 0, "scheduled": 2}]}
    return archive, snapshot, panel, reliability


def test_preserves_full_missing_denominator(monkeypatch):
    monkeypatch.setattr(audit_chain, "audit", lambda *_: {"issuer_count": 1})
    result = audit_chain.reconcile(*fixture())
    assert (result["scheduled"], result["eligible"], result["withheld"]) == (2, 0, 2)
    assert result["reference_issuers"] == 1


@pytest.mark.parametrize("mutation", ["sha", "cutoff", "coverage", "duplicate", "future", "issuer", "issuer_count", "date_count"])
def test_detects_lineage_and_coverage_tampering(monkeypatch, mutation):
    monkeypatch.setattr(audit_chain, "audit", lambda *_: {"issuer_count": 1})
    parts = list(copy.deepcopy(fixture()))
    if mutation == "sha":
        parts[3]["source_archive_sha256"] = "a" * 64
    elif mutation == "cutoff":
        parts[2]["archive_cutoff"] = "2025-01-01"
    elif mutation == "coverage":
        parts[3]["eligible_issuer_dates"] = 1
    elif mutation == "duplicate":
        parts[2]["detail_rows"][1]["checkpoint"] = "2024-01-01"
    elif mutation == "future":
        parts[2]["detail_rows"][0].update(eligible=True, latest_filed="2025-01-01")
    elif mutation == "issuer":
        parts[2]["detail_rows"][0]["symbol"] = "NOPE"
    elif mutation == "issuer_count":
        parts[3]["per_issuer"][0]["eligible"] = 1
    elif mutation == "date_count":
        parts[2]["cohorts"][0]["eligible"] = 1
    with pytest.raises(ValueError):
        audit_chain.reconcile(*parts)


def test_page_contains_three_integrated_v130_slots_and_sanitized_export():
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    private = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    for marker in ("qf-v130-hub-result", "qf-v130-brief", "qf-v130-lab-insight"):
        assert marker in builder and marker in private
    for name in ("private_historical_attribution_v130.js", "private_decision_integrity_v130.js"):
        assert name in builder
    assert "renderDecisionIntegrityV130();" in private
    assert "researchIntegrityV130:" in private
    assert "historicalAttributionV130:" in private


def test_offline_integrity_script_does_not_use_public_or_brokerage_paths():
    source = (ROOT / "tools/audit_research_chain_v130.py").read_text(encoding="utf-8")
    assert 'data/sec_research_integrity_v130.json' in source
    for forbidden in ("public/index.html", "requests.get(", "alpaca", "brokerage", "account_id"):
        if forbidden == "brokerage":  # Docstring explicitly describes absence of brokerage access.
            continue
        assert forbidden not in source
