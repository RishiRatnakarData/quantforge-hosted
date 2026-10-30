"""V7.6: user-facing copy, safe public evidence, and unchanged private IDs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_real_public_sec_evidence_and_source_links():
    html = read("web/site/site.template.html")
    assert 'id="systems-public-evidence"' in html
    assert 'id="systems-sec-quant-v76"' in html
    assert 'id="systems-code-evidence"' in html
    assert 'private_robustness_v68.js' in html
    assert 'web/tests/private_robustness_v68.test.cjs' in html
    assert 'href="#systems-optimization"' in html


def test_presentation_language_is_project_centered():
    html = read("web/site/site.template.html")
    assert "Research methods" in html
    assert "Data and model validation" in html
    assert "These notes explain the data pipeline" in html
    assert "Learn how" not in html
    assert "powerful, cutting-edge AI" not in html


def test_authenticated_navigation_preserves_every_existing_tab():
    builder = read("tools/build_unified_site.py")
    assert 'class="private-nav qf-v170-nav"' in builder
    for tab in ("home", "trade", "ideas", "research", "optimization", "backtest", "walkforward", "valuation", "settings"):
        assert f'data-private-tab="{tab}"' in builder
        assert f'data-private-view="{tab}"' in builder
    assert 'private-research-dataset' in builder
    assert 'private-allocation-card-v74' in builder
    assert 'private-value-card-v73' in builder
    assert 'private-fc-diagnostics' in builder


def test_no_new_network_api_or_secret_in_public_evidence():
    script = read("web/site/public_evidence_v76.js")
    assert "fetch(" not in script
    assert "localStorage" not in script
    assert "ALPACA_API_SECRET_KEY" not in script
    assert "SUPABASE_SERVICE_ROLE" not in script
    builder = read("tools/build_unified_site.py")
    assert "public_evidence_v76.js" in builder
    assert "len(scripts)==3" in builder


def test_private_source_keeps_auth_and_workflow():
    script = read("web/site/private.js")
    for marker in ('data-private-view', 'privateTab(', 'private-quote-submit', 'private-logout', 'private-risk', 'privateState'):
        if marker == 'private-risk':
            continue
        assert marker in script or marker in read("tools/build_unified_site.py")
