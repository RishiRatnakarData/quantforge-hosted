"""V6.8 regressions: same-window scenario comparisons and no new security surfaces."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_robustness_helpers_do_not_access_network_or_saved_portfolio():
    code = (ROOT / 'web/site/private_robustness_v68.js').read_text(encoding='utf-8')
    for prohibited in ('fetch(', 'XMLHttpRequest', 'localStorage', 'sessionStorage',
                       '/api/private/trade', '/api/private/capital', 'document.cookie'):
        assert prohibited not in code
    assert 'same fitted-through and evaluation dates' in code
    assert 'leaveOneWindowOut' in code


def test_bundle_is_protected_and_ui_is_explicit():
    builder = (ROOT / 'tools/build_unified_site.py').read_text(encoding='utf-8')
    assert "(src/'site/private_robustness_v68.js').read_text(encoding='utf-8')" in builder
    assert 'id="private-wf-v68-run"' in builder
    assert 'id="private-wf-v68-output"' in builder
    assert 'id="private-wf-v68-export"' in builder
    assert "assert len(scripts)==3" in builder
    assert "frame-ancestors 'none'" in builder


def test_robustness_cannot_show_when_signed_out_or_selection_changes():
    code = (ROOT / 'web/site/private.js').read_text(encoding='utf-8')
    assert 'if(!privateState||!walkforwardResult||!historySeries)' in code
    assert 'if(!privateState||!historySeries||!walkforwardResult||!robustnessResultV68)' in code
    assert 'robustnessResultV68=null;' in code
    assert "$('private-wf-v68-run').disabled=true" in code
    assert 'window.QFPrivateIntegrity.verifyMarketFingerprint' in code
    assert "'quantforge-walkforward-robustness.json'" in code


def test_source_provenance_is_attached_to_robustness_export():
    code = (ROOT / 'web/site/private_robustness_v68.js').read_text(encoding='utf-8')
    assert 'quantforge.robustness.v1' in code
    assert 'historicalOnly:true,manifest' in code
    assert "'walkforward'" in code
    assert 'wealth:undefined' in code
