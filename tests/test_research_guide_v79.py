"""V7.9 integration invariants: private guide and expanded public SEC snapshot."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_private_guide_only_available_after_authentication():
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    client = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    assert 'id="private-signed" hidden' in builder
    assert 'id="private-guide-card-v79"' in builder
    assert "private_guide_v79.js" in builder
    assert "if(!privateState){message('Sign in and complete authenticator" in client
    assert "window.QFPrivateGuideV79.analyze" in client
    assert "clearGuideV79();clearMFA();showStep('login');privateState=null" in client
    assert "$('private-guide-run-v79').addEventListener('click',runGuideV79)" in client
    assert "api('private/trade'" in client  # Pre-existing virtual trade, not the guide.


def test_no_external_ai_calls_or_auto_trade_in_research_guide():
    guide = (ROOT / "web/site/private_guide_v79.js").read_text(encoding="utf-8")
    for marker in ("fetch(", "localStorage", "sessionStorage", "XMLHttpRequest", "OpenAI", "anthropic", "api('private/trade'"):
        assert marker not in guide
    assert "not a chat model" in guide


def test_public_expansion_preserves_original_issuer_guards():
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    code = (ROOT / "tools/extend_public_sec_v79.py").read_text(encoding="utf-8")
    assert "set(ISSUERS).issubset(symbols)" in builder
    assert 'get("form") != "10-K"' in code
    assert "filed <= cutoff" in code
    assert "source_url" in code
    assert "SEC_USER_AGENT" in code
    assert "No paid market data" in code


def test_company_search_works_with_name_and_ticker():
    html = (ROOT / "web/site/site.template.html").read_text(encoding="utf-8")
    app = (ROOT / "web/site/app.js").read_text(encoding="utf-8")
    assert 'id="sec-company-search-v79"' in html
    assert "function filterSECCompaniesV79()" in app
    assert "c.name.toLowerCase().includes(q)" in app
    assert "c.symbol.toLowerCase().includes(q)" in app
