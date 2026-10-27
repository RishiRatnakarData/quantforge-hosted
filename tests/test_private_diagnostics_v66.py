"""Source and privacy boundaries for owner-only V6.6 research diagnostics."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_diagnostics_use_existing_private_results_without_provider_access():
    source = (ROOT / "web/site/private_diagnostics_v66.js").read_text(encoding="utf-8")
    for forbidden in (
        "fetch(",
        "XMLHttpRequest",
        "localStorage",
        "sessionStorage",
        "document.cookie",
        "api('private/",
        "APCA_API_KEY",
        "SUPABASE_",
        "privateState=",
    ):
        assert forbidden not in source
    assert "summarizeWalkforward" in source
    assert "forecastSensitivity" in source
    assert "costSensitivity" in source


def test_no_private_holdings_or_transaction_mutation_in_new_analytics():
    source = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    section = source.split("/* V6.6: derived reports", 1)[1].split(
        "const fcMoney=", 1
    )[0]
    for forbidden in ("api('private/trade'", "api('private/capital'", "save_state("):
        assert forbidden not in section
    assert "downloadResearchJSON" in section
    assert "showV66WalkforwardDiagnostics" in source
    assert "showV66ForecastDiagnostics" in source


def test_three_script_csp_and_local_export_controls():
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    html = (ROOT / "public/index.html").read_text(encoding="utf-8")
    headers = (ROOT / "public/_headers").read_text(encoding="utf-8")
    assert "private_diagnostics_v66.js" in builder
    assert 'id="private-fc-report"' in html
    assert 'id="private-wf-report"' in html
    assert 'id="private-wf-robustness"' in html
    assert html.count("<script>") == 3
    assert headers.count("'sha256-") == 3
    assert "QFPrivateDiagnostics" in html
