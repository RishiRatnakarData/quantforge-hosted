"""Source and security regressions for private SEC forecasts and walk-forward testing."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_new_research_helpers_are_pure_no_keys_or_external_calls():
    for filename in ("private_forecast_v65.js", "private_walkforward_v65.js"):
        data = (ROOT / "web/site" / filename).read_text(encoding="utf-8")
        for disallowed in (
            "fetch(", "XMLHttpRequest", "AlpacaClient", "SUPABASE_", "api('private/",
            "localStorage", "sessionStorage", "window.location", "document.cookie",
            "privateState=", "Record virtual trade",
        ):
            assert disallowed not in data


def test_forecasting_uses_cached_private_sec_company_not_public_model_fixtures():
    source = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    assert "window.QFPrivateForecast.run(company" in source
    assert "valuationCompanies[symbol]" in source
    assert 'id="private-fc-run"' in builder
    assert "Multi-year cash-flow scenarios" in builder
    assert "QFPrivateForecast" in (ROOT / "public/index.html").read_text(encoding="utf-8")


def test_walk_forward_loads_owner_private_history_and_never_trades():
    source = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    section = source.split("function runWalkforward(){", 1)[1].split(
        "function exportWalkforward(){", 1
    )[0]
    assert "window.QFPrivateWalkforward.run(historySeries" in section
    assert "privateState" in section
    for banned in ("api('private/trade'", "api('private/capital'", "save_state("):
        assert banned not in section
    assert 'data-private-tab="walkforward"' in builder
    assert "private_walkforward_v65.js" in builder


def test_bundled_scripts_preserve_three_hashes_and_data_boundary():
    html = (ROOT / "public/index.html").read_text(encoding="utf-8")
    headers = (ROOT / "public/_headers").read_text(encoding="utf-8")
    assert html.count("<script>") == 3
    assert headers.count("'sha256-") == 3
    assert "QFPrivateWalkforward" in html
    assert "QFPrivateForecast" in html
    assert 'id="private-wf-run"' in html
    assert 'id="private-fc-run"' in html
