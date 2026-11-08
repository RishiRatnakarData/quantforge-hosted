"""V7.0 presentation and trust-boundary regression tests."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ideas_private_only_and_company_selection():
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    public_template = (ROOT / "web/site/site.template.html").read_text(encoding="utf-8")
    private = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    assert "private_ideas_v70.js" in builder
    assert 'data-private-view="ideas"' in builder
    assert 'data-private-tab="ideas"' in builder
    assert 'data-private-tab="ideas"' not in public_template
    assert "openAssetBrowser('ideas')" in private
    assert "private/history?symbols=" in private


def test_public_project_case_study_is_concrete():
    template = (ROOT / "web/site/site.template.html").read_text(encoding="utf-8")
    assert 'Financial research, built from the data up.' in template
    assert "SEC data preparation" in template
    assert "Rolling evaluation and robustness" in template
    assert "System architecture" in template
    assert "reviewer" not in template.lower()


def test_investment_research_is_read_only():
    js = (ROOT / "web/site/private_ideas_v70.js").read_text(encoding="utf-8")
    assert "fetch(" not in js
    assert "private/trade" not in js
    assert "localStorage" not in js
    assert "priceTarget" not in js
    assert "Math.random" not in js


def test_public_bundle_csp_does_not_gain_extra_script_tag():
    build = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    assert "assert len(scripts)==3" in build
    assert "private_ideas_v70.js" in build
