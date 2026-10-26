"""Release-structure regressions for the private historical optimizer."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_optimizer_uses_current_private_history_and_name_selection():
    js = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    assert "window.QFPrivateOptimizer.run(historySeries" in js
    assert "$('private-opt-export').disabled=true" in js
    assert 'data-private-tab="optimization"' in builder
    assert 'data-private-view="optimization"' in builder
    assert 'id="private-opt-run"' in builder
    assert 'id="private-opt-risk"' in builder
    assert "private_optimizer.js" in builder


def test_optimizer_is_pure_and_cannot_access_private_credentials_or_endpoints():
    js = (ROOT / "web/site/private_optimizer.js").read_text(encoding="utf-8")
    assert "module.exports" in js
    assert "20% diagonal shrinkage" in js
    for banned in (
        "fetch(",
        "XMLHttpRequest",
        "ALPACA_API",
        "SUPABASE_",
        "/api/private/trade",
        "/api/private/capital",
        "localStorage",
    ):
        assert banned not in js


def test_private_optimized_results_do_not_mutate_virtual_positions():
    js = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    start = js.index("function runOptimization(){")
    end = js.index("function exportOptimization(){")
    isolated = js[start:end]
    assert "api('private/trade'" not in isolated
    assert "api('private/capital'" not in isolated
    assert "save_state" not in isolated
    assert "privateState=" not in isolated


def test_bundled_site_still_uses_three_csp_protected_scripts():
    html = (ROOT / "public/index.html").read_text(encoding="utf-8")
    headers = (ROOT / "public/_headers").read_text(encoding="utf-8")
    assert html.count("<script>") == 3
    assert "Portfolio optimization" in html
    assert "QFPrivateOptimizer" in html
    assert "Content-Security-Policy:" in headers
    assert headers.count("'sha256-") == 3
