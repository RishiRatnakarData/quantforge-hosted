"""V8.4 private UI wiring, bundle and privacy boundaries."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_decision_center_is_mfa_protected_by_existing_private_shell():
    builder = read("tools/build_unified_site.py")
    source = read("web/site/private.js")
    assert 'id="private-signed" hidden' in builder
    assert 'data-private-view="decision" hidden' in builder
    assert 'data-private-tab="decision"' in builder
    assert 'id="private-decision-run-v84"' in builder
    assert "if(!privateState){message('Complete sign-in and MFA" in source
    assert "if(tab==='decision')clearDecisionCenterV84();" in source


def test_model_is_inline_in_existing_private_csp_bundle():
    builder = read("tools/build_unified_site.py")
    assert "(src/'site/private_decision_center_v84.js').read_text" in builder
    assert "(src/'site/private_decision_v72.js').read_text" in builder
    assert "len(scripts)==3" in builder
    assert "'sha256-" in builder
    assert "data-private-view=\"decision\"" in builder


def test_data_boundaries_are_explicit_and_no_trade_action_wired():
    model = read("web/site/private_decision_center_v84.js")
    source = read("web/site/private.js")
    assert "No network, storage, trades or external AI" in model
    assert "window.QFPrivateDecisionCenterV84.evaluate" in source
    assert "data-v84-go" in source
    assert "downloadResearchJSON('quantforge-decision" not in source
    assert "private/trade" not in model
    assert "ALPACA_API_SECRET_KEY" not in model
