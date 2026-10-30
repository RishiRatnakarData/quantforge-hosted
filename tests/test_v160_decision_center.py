"""V16.0 private-only dashboard integration and privacy contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_dashboard_is_inside_private_decision_view():
    b = source("tools/build_unified_site.py")
    before, after = b.split('id="qf-v160-decision-center"', 1)
    assert 'data-private-view="decision"' in before[-900:]
    assert 'id="qf-v160-setup"' in after
    assert 'id="qf-v160-method-trace"' in after


def test_advanced_analysis_keeps_all_existing_research_routes():
    b = source("tools/build_unified_site.py")
    for route in (
        "decision", "ideas", "candidate", "lab", "valuation", "optimization",
        "backtest", "walkforward", "research", "settings", "home", "trade",
    ):
        assert f'data-private-tab="{route}"' in b
    assert b.count('class="private-nav-group"') == 4
    for section in ("Decision Center", "Companies", "Research Methods", "Portfolio &amp; Reports"):
        assert section in b


def test_archive_importer_remains_optional_and_outside_primary_workflow():
    private = source("web/site/private.js")
    assert "folder.appendChild(archive);lab.appendChild(folder);" in private
    assert "lab.appendChild(launch);" in private
    assert "launch.hidden=tab!=='lab'" in private
    assert "lab.appendChild(oldDetails);" in private
    assert 'id="qf-v99-file"' in source("tools/build_unified_site.py")
    assert "await loadHistory()" in private
    assert "window.QFPublishedSEC" in private


def test_compatibility_preserves_prior_methods_and_signout():
    main = source("web/site/private.js")
    for marker in (
        "clearResearchOSV90()", "linkedUnifiedDecisionV160=null;", "renderUnifiedDecisionV160()",
        "renderWorkflowV140()", "renderDecisionIntegrityV130()", "importArchivedSECV99",
        "clearImportedSECV99", "privateTab('home')", "clearMFA()",
    ):
        assert marker in main


def test_workflow_compiles_without_changing_public_template_source():
    build = source("tools/build_unified_site.py")
    assert "src/'site/private_unified_decision_v160.js'" in build
    html = source("public/index.html")
    assert "qf-v160-decision-center" in html
    assert "qf-v150-data-scope-title" in html
    assert "qf-v160-method-trace" in html
    assert "private-mfa-code" in html


def test_output_has_private_only_css_and_no_new_backend_routes():
    module = source("web/site/private_unified_decision_v160.js")
    assert "quantforge.decision-center.v16.0" in module
    assert "quantforge.decision-center-export.v16.0" in module
    for bad in ("fetch(", "private/trade", "private/capital", "localStorage", "document.cookie"):
        assert bad not in module
    assert "#private-signed .qf-v160-hero" in source("tools/build_unified_site.py")


def test_no_dishonest_browser_acceptance_claim():
    audit = source("tools/audit_decision_center_v160.py")
    assert '"manual_browser_acceptance": "PENDING"' in audit
    assert '"real_provider_data_verified": False' in audit
