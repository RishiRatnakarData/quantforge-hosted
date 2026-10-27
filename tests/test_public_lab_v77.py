"""V7.7 release boundaries: public proof without changing authenticated research."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_analysis_dashboard_is_accessible_and_navigable():
    site = read("web/site/site.template.html")
    app = read("web/site/app.js")
    for fragment in (
        'data-page="lab"',
        'id="page-lab"',
        'id="lab-sec-results"',
        'id="lab-opt-results"',
        'id="lab-walk-results"',
        'id="lab-technical"',
        'aria-live="polite"',
    ):
        assert fragment in site
    assert "lab:'INTERACTIVE ANALYSIS'" in app
    assert "window.QFResearchLab.mount(SEC_DATA)" in app
    assert "'systems','lab'" in app


def test_all_five_career_disciplines_have_actual_exhibits():
    site = read("web/site/site.template.html")
    for text in (
        "Data engineering",
        "Data analytics &amp; BI",
        "Data science",
        "Financial analysis",
        "Quantitative finance",
        "Maximum weight per investment",
        "Rolling training window",
        "Company (SEC filings)",
        "Private data: sign-in required",
    ):
        assert text in site


def test_public_lab_is_bundled_into_existing_hash_protected_script():
    builder = read("tools/build_unified_site.py")
    assert "public_lab_v77.js" in builder
    assert "text=analytics+'\\n'+evidence+'\\n'+lab+'\\n'+text.replace" in builder
    assert "assert len(scripts)==3" in builder
    script = read("web/site/public_lab_v77.js")
    for forbidden in (
        "fetch(",
        "XMLHttpRequest",
        "localStorage",
        "sessionStorage",
        "ALPACA_API_SECRET_KEY",
        "SUPABASE_SERVICE_ROLE",
    ):
        assert forbidden not in script
    assert "synthetic" in script
    assert "snapshot" in script
    assert "walkforward" in script


def test_existing_private_workspace_identifiers_stay_in_source():
    builder = read("tools/build_unified_site.py")
    assert "'private.js'" in builder
    for key in (
        'data-private-view="home"',
        'data-private-view="ideas"',
        'data-private-view="walkforward"',
        'data-private-view="valuation"',
    ):
        assert key in builder
    assert "private_allocation_v74.js" in builder
    assert "private_decision_v72.js" in builder
