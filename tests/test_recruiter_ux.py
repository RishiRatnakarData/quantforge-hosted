"""V5.8 recruiter navigation, disclosure and privacy regressions."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_public_research_first_and_navigation():
    html = read("web/site/site.template.html")
    assert 'Financial research, built end to end.' in html
    assert 'id="page-methods"' in html
    assert 'data-page="methods"' in html
    assert 'data-go="methods"' in html
    assert 'data-sec-symbol="WMT"' in html
    assert 'data-sec-symbol="XOM"' in html
    assert 'id="home-sec-highlights"' in html
    assert 'id="page-private"' not in html  # private pane inserted only by secure builder
    assert 'href="#main-content"' in html
    assert 'aria-label="Main navigation"' in html


def test_methods_disclosures_are_precise():
    html = read("web/site/site.template.html")
    for phrase in (
        "Company Facts", "10-K", "Operating income / revenue",
        "Missing values remain unavailable", "not calibrated forecasts",
        "not a stock quote", "not unlevered FCFF", "owner-only workspace",
        "not an investment recommendation",
    ):
        assert phrase.lower() in html.lower()


def test_public_badge_stays_correct_after_navigation():
    app = read("web/site/app.js")
    private = read("web/site/private.js")
    assert "METHODOLOGY & SOURCES" in app
    assert "PUBLIC_PAGES=new Set(" in app
    assert "aria-current" in app
    assert "history.replaceState" in app
    assert "data-sec-symbol" in app
    assert "FICTIONAL DATA" not in private
    assert "if(!active)return;" in private
    assert "fetch(" not in app


def test_recruiter_features_require_no_api_or_private_secret():
    html = read("web/site/site.template.html")
    for forbidden in ("ALPACA_API_SECRET_KEY", "SUPABASE_SERVICE_ROLE", "qf_access"):
        assert forbidden not in html
    assert 'SEC Financials' in html
    assert 'Simulated holdings and prices' in html
    assert 'METHODOLOGY & SOURCES' not in html or 'methods' in html
