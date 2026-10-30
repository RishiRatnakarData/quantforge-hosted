"""V12.0 complete-cohort SEC reliability and source/integration contract."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
reliability = importlib.import_module("assess_sec_reliability_v120")


def sample():
    dates = ["2024-01-01", "2024-07-01", "2025-01-01"]
    rows = []
    for symbol in ("AAA", "BBB"):
        for i, day in enumerate(dates):
            ready = symbol == "AAA" and i > 0
            rows.append({
                "symbol": symbol,
                "checkpoint": day,
                "eligible": ready,
                "reason": None if ready else "No filed years",
                "fiscal_end": "2023-12-31" if ready else None,
                "latest_filed": "2024-03-01" if ready else None,
                "later_version_seen": ready and i == 2,
            })
    return {
        "schema": "quantforge.local-sec-historical-panel.v11.0",
        "reference_issuers": 2,
        "total_checkpoints": 3,
        "eligible_issuer_checkpoints": 2,
        "archive_cutoff": "2025-03-01",
        "source_sha256": "a" * 64,
        "cohorts": [{"checkpoint": day} for day in dates],
        "detail_rows": rows,
    }


def test_issuer_and_year_denominators_never_hide_missing_periods():
    report = reliability.assess(sample())
    assert report["scheduled_issuer_dates"] == 6
    assert report["eligible_issuer_dates"] == 2
    assert report["withheld_issuer_dates"] == 4
    assert report["coverage_pct"] == 33.33
    assert [row["longest_eligible_run"] for row in report["per_issuer"]] == [2, 0]
    assert report["leading_missingness"] == {"No filed years": 4}
    assert report["per_issuer"][0]["later_version_windows"] == 1


def test_incomplete_matrix_duplicate_and_future_filing_rejected():
    source = sample()
    source["detail_rows"].pop()
    with pytest.raises(ValueError):
        reliability.assess(source)
    source = sample()
    source["detail_rows"][1]["latest_filed"] = "2024-09-01"
    with pytest.raises(ValueError):
        reliability.assess(source)
    source = sample()
    source["detail_rows"][0]["checkpoint"] = "2024-07-01"
    with pytest.raises(ValueError):
        reliability.assess(source)


def test_no_brokerage_or_public_output_capability():
    code = (ROOT / "tools/assess_sec_reliability_v120.py").read_text(encoding="utf-8")
    assert "atomic_write(args.json" in code
    assert "atomic_write(args.csv" in code
    assert "public/index.html" not in code
    assert "requests.get(" not in code


def test_page_connects_hub_lab_brief_and_sanitized_export():
    build = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    private = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    for tag in ("qf-v120-hub-result", "qf-v120-brief", "qf-v120-lab-insight"):
        assert tag in build and private
    assert "private_robustness_v120.js" in build
    assert "historicalSensitivityV120:" in private
    assert "renderHistoricalRobustnessV120();" in private
