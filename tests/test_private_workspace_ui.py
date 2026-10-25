"""V4.6 UI release invariants: personal, private, and task-first."""

from pathlib import Path

from quantforge.desk import server


def test_workspace_has_quick_research_and_private_navigation():
    page = Path(server.HTML).read_text(encoding="utf-8")
    assert "Investment desk" in page
    assert 'id="quickSymbol"' in page
    assert 'id="quickResearch"' in page
    assert 'id="watchHome"' in page
    assert 'id="preferencesDetails"' in page
    assert 'id="homeBalance"' in page
    assert "FICTIONAL DEMO" in page
    assert "researchFromHome" in page
    assert "window.scrollTo(0,0)" in page
    assert "api('/api/decision?symbol=" in page


def test_essential_investment_labels_without_marketing_copy():
    page = Path(server.HTML).read_text(encoding="utf-8")
    for expected in ("Investment desk", "Research", "Watchlist", "Portfolio", "Risk scenarios", "Valuation", "Paper trades only"):
        assert expected in page
    for removed in ("without the pressure", "Working principle", "Research my next move", "Keep the decisions honest"):
        assert removed not in page
