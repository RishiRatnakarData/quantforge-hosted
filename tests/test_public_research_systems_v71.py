"""V7.1 public technical showcase and confidentiality boundary."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def site():
    return (ROOT / "web/site/site.template.html").read_text(encoding="utf-8")

def test_systems_is_visible_and_navigable():
    content = site()
    app = (ROOT / "web/site/app.js").read_text(encoding="utf-8")
    assert 'id="page-systems"' in content
    assert 'data-page="systems"' in content
    assert content.count('data-go="systems"') >= 2
    assert "'systems'" in app
    assert "systems:'RESEARCH METHODS'" in app

def test_engineering_mathematics_and_bias_limits_are_substantive():
    content = site()
    for phrase in ("wᵀΣw", "Train[t₀:t₁]", "FCFₜ", "SHA-256", "look-ahead",
        "survivorship bias", "terminal", "inverse-volatility", "Model portfolio",
        "Supabase MFA", "FastAPI", "Cloudflare Pages", "price-only returns"):
        assert phrase.lower() in content.lower()
    assert content.count('<article class="tech-feature"') >= 4

def test_no_private_data_or_unsafe_script_added():
    content = site()
    assert content.count("<script>") == 2  # builder adds the protected private third script
    for secret in ("ALPACA_API_SECRET_KEY", "SUPABASE_SERVICE_ROLE", "qf_access"):
        assert secret not in content
    assert "Diagrams" not in content or "private" in content
    assert "Illustrative positions" in content
    assert "not copied from private analysis" in content

def test_methods_reflects_deep_private_explanations():
    content = site()
    assert "Data and model validation" in content
    assert "Trace a result to the code" in content
    assert "Five-session up/down classification" in content
    assert "TF-IDF weighting" not in content
    assert "not evidence of stock-market accuracy" in content
    assert "tests provide scoped evidence" in content
