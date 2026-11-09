"""Editorial contract: precise labels, evidence categories and unchanged navigation IDs."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_overview_is_specific_without_unearned_claims():
    page = source("web/site/site.template.html")
    assert 'Financial research, built from the data up.' in page
    assert "SEC-reported company financials, statistical experiments, and portfolio scenarios" in page
    assert "<strong>Research data:</strong> Historical SEC company financials" in page
    assert "<strong>Research data:</strong> Historical SEC company financials" in page
    assert "Financial research, built end to end" not in page
    assert "PERSONAL SOFTWARE &amp; DATA SCIENCE PROJECT" not in page


def test_analysis_dashboard_is_named_plainly_and_keeps_bookmarks():
    page = source("web/site/site.template.html")
    app = source("web/site/app.js")
    assert 'data-page="lab">Analysis dashboard</button>' in page
    assert '<h1>Analysis dashboard</h1>' in page
    assert 'id="page-lab"' in page
    assert 'id="lab-sec"' in page
    assert 'id="lab-walkforward"' in page
    assert "lab:'INTERACTIVE ANALYSIS'" in app
    assert "Research lab" not in page


def test_financial_evidence_distinctions_remain_explicit():
    page = source("web/site/site.template.html")
    lab = source("web/site/public_lab_v77.js")
    assert "Historical SEC data" in page
    assert "Simulated returns" in page
    assert "market returns are simulated" in page or "investment return examples are simulated" in page
    assert "Historical financials do not predict stock returns" in lab
    assert "neither curve represents actual historical trading" in lab
    assert "Private data: sign-in required" in page


def test_public_pages_keep_existing_route_identifiers():
    page = source("web/site/site.template.html")
    for slug in ("overview", "sec", "portfolio", "quant", "valuation", "ml", "lab", "systems", "methods"):
        assert f'id="page-{slug}"' in page
        assert f'data-page="{slug}"' in page


def test_private_workflow_sections_and_data_selection_survive_rewrite():
    builder = source("tools/build_unified_site.py")
    for slug in ("home", "trade", "ideas", "research", "optimization", "backtest", "walkforward", "valuation", "settings"):
        assert f'data-private-tab="{slug}"' in builder
        assert f'data-private-view="{slug}"' in builder
    assert 'id="private-research-selected"' in builder
    assert 'id="private-research-loaded"' in builder
    assert 'id="private-mfa-code"' in builder
    assert "load their price history" in builder


def test_private_copy_explains_simulation_and_read_only_data():
    builder = source("tools/build_unified_site.py")
    assert "no brokerage order is sent" in builder
    assert "do not move actual money" in builder
    assert "price-only, excluding dividends" in builder
    assert "Scenario values are not price targets" in builder
    assert "Investment screening" in builder
    assert "historical" in builder.lower()


def test_private_js_references_match_new_navigation_without_api_changes():
    private = source("web/site/private.js")
    assert "Open Investment screening" in private or "in Investment screening" in private
    assert "Market data" in private
    assert "function api(path, body)" in private
    assert "'/api/'+path" in private
    assert "const init={credentials:'same-origin'" in private


def test_public_lab_remains_credential_free():
    lab = source("web/site/public_lab_v77.js")
    for forbidden in ("fetch(", "XMLHttpRequest", "ALPACA_API_SECRET_KEY", "SUPABASE_SERVICE_ROLE"):
        assert forbidden not in lab
    assert re.search(r'\bsynthetic\(', lab)
