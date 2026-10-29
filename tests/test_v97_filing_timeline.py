"""V9.7 historical filing-gated research and release interface boundaries."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_pure_filing_gated_engine_has_no_private_side_effects():
    source = read("web/site/private_pit_validation_v97.js")
    for marker in ("auditOne(", "replay(", "safeSummary(", "filed", "accession"):
        assert marker in source
    for prohibited in ("fetch(", "localStorage", "sessionStorage", "private/trade", "private/notes"):
        assert prohibited not in source


def test_all_connected_research_sections_are_built_from_one_assessment():
    source = read("web/site/private.js")
    assert "linkedPointInTimeV97=window.QFPrivatePointInTimeV97.replay({" in source
    assert "linkedPointInTimeV97=null;" in source
    assert "renderPointInTimeV97();" in source
    assert "filingTimelineV97:linkedPointInTimeV97?" in source
    for marker in ("qf-v97-hub", "qf-v97-brief", "qf-v97-lab-insight"):
        assert marker in source


def test_compiled_private_views_and_existing_mfa_remain_intact():
    source = read("public/index.html")
    builder = read("tools/build_unified_site.py")
    assert "private_pit_validation_v97.js').read_text" in builder
    for marker in ("qf-v97-hub", "qf-v97-brief", "qf-v97-lab-insight"):
        assert source.count(f'id="{marker}"') == 1
    assert source.count('id="private-mfa-code"') == 1
    assert source.count("<script") == 3


def test_no_unfounded_full_policy_claims_in_research_copy():
    engine = read("web/site/private_pit_validation_v97.js")
    assert "Only a restricted SEC filing-date-gated rule" in engine
    assert "Partial windows produce an evidence inventory" in engine
    assert "No complete historical replay" in engine
