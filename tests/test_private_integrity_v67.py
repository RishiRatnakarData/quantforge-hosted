"""V6.7 checks privacy boundaries and the generated research UI."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_integrity_module_has_no_io_or_account_mutation():
    text = (ROOT / "web/site/private_integrity_v67.js").read_text(encoding="utf-8")
    for forbidden in (
        "fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "document.cookie",
        "api('private/", "APCA_API_KEY", "SUPABASE_", "privateState=",
        "save_state(", "provider_secret", "window.location",
    ):
        assert forbidden not in text
    assert "sha256" in text and "verifyMarketFingerprint" in text


def test_integrity_manifest_is_on_both_exports_and_ui():
    text = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    assert "attachWalkforward" in text
    assert "attachForecast" in text
    assert "Data integrity and evaluation coverage" in text
    assert "Model risk and SEC baseline" in text
    assert "verifyMarketFingerprint" in text


def test_no_fourth_script_or_broadened_csp():
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    html = (ROOT / "public/index.html").read_text(encoding="utf-8")
    headers = (ROOT / "public/_headers").read_text(encoding="utf-8")
    assert "private_integrity_v67.js" in builder
    assert html.count("<script>") == 3
    assert headers.count("'sha256-") == 3
    assert "QFPrivateIntegrity" in html
