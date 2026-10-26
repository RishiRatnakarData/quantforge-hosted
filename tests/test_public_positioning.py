"""Public demo must distinguish authentic SEC reports from simulations."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_limited_public_presentation_is_truthful():
    html = (ROOT / "web/site/site.template.html").read_text(encoding="utf-8")
    app = (ROOT / "web/site/app.js").read_text(encoding="utf-8")
    assert 'REAL SEC DATA + SIMULATIONS' in html
    assert 'SEC EDGAR' in html
    assert '12 companies' in html
    assert 'id="home-sec-highlights"' in html
    assert 'Reported annual revenue' in app
    assert 'renderSECHighlights();' in app
    assert 'SIMULATED PORTFOLIO' in app
    assert 'SIMULATED RETURNS' in app
    assert 'ILLUSTRATIVE DCF' in app
    assert 'SIMULATED PEER INPUTS' in app
    assert 'REAL SEC DATA + SIMULATIONS' in app
    assert 'not live stock prices' in html
    assert 'not actual company valuations' in html
    assert 'No private holdings, credentials, Alpaca feeds, or brokerage trades' in html
    assert 'FICTIONAL DATA' not in html


def test_private_authentication_logic_is_not_in_public_demo():
    app = (ROOT / "web/site/app.js").read_text(encoding="utf-8")
    assert 'fetch(' not in app
    assert 'localStorage' not in app
    assert 'sessionStorage' not in app
