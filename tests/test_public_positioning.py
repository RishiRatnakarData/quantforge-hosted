"""Public demo must distinguish authentic SEC reports from simulations."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_limited_public_presentation_is_truthful():
    html = (ROOT / "web/site/site.template.html").read_text(encoding="utf-8")
    app = (ROOT / "web/site/app.js").read_text(encoding="utf-8")
    assert 'RESEARCH OVERVIEW' in html
    assert 'SEC EDGAR' in html
    assert 'id="home-sec-highlights"' in html
    assert 'Reported annual revenue' in app
    assert 'renderSECHighlights();' in app
    assert 'SIMULATED PORTFOLIO' in app
    assert 'SIMULATED RISK MODEL' in app
    assert 'DCF ASSUMPTIONS' in app
    assert 'REPORTED SEC COMPANY COMPARISON' in app
    assert 'RESEARCH OVERVIEW' in app
    assert '<strong>Research data:</strong> Historical SEC company financials' in html
    assert 'simulated returns and hypothetical forecasts' in html
    assert 'SEC Company Comparison instead uses reported-derived financial ratios' in html
    assert 'Private account data and market feeds' in html
    assert 'FICTIONAL DATA' not in html


def test_private_authentication_logic_is_not_in_public_demo():
    app = (ROOT / "web/site/app.js").read_text(encoding="utf-8")
    assert 'fetch(' not in app
    assert 'localStorage' not in app
    assert 'sessionStorage' not in app
