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
    assert 'SIMULATED PEER MODEL' in app
    assert 'RESEARCH OVERVIEW' in app
    assert 'not live stock prices' in html
    assert 'not actual market results, valuations, or investment recommendations.' in html
    assert 'Private account data and market feeds' in html
    assert 'FICTIONAL DATA' not in html


def test_private_authentication_logic_is_not_in_public_demo():
    app = (ROOT / "web/site/app.js").read_text(encoding="utf-8")
    assert 'fetch(' not in app
    assert 'localStorage' not in app
    assert 'sessionStorage' not in app
