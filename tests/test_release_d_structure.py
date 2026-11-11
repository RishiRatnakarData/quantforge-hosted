"""Release D: shared five-route owner shell, no new authentication boundary."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def src(name: str) -> str:
    return (ROOT / name).read_text(encoding='utf-8')


def test_shared_routes_brand_landing_and_contextual_owner_controls() -> None:
    html = src('web/site/site.template.html')
    assert 'id="qf-v23-home-button"' in html
    assert html.count('id="qf-v23-landing"') == 1
    assert html.count('id="qf-v23-owner-panel"') == 1
    for page in ('explore', 'compare', 'models', 'portfolio', 'methods'):
        assert html.count(f'id="page-{page}"') == 1
    assert 'data-qf-v23-open="notes"' in html
    assert 'data-qf-v23-open="portfolio"' not in html  # redundant same-page scroll action removed
    workflow = src('web/site/portfolio_workflow_v27.js')
    assert 'qf27-buy' in workflow and 'qf27-sell' in workflow and 'qf27-confirm' in workflow
    assert 'id="qf-v23-signout"' in html
    assert 'qf-v83-owner' in html  # historical CSS remains; sidebar byline is removed
    assert '<p class="qf-v83-owner">' not in html
    assert '.qf-v23-owner-action[hidden]{display:none!important}' in html


def test_saved_data_uses_original_versioned_mfa_endpoint_only() -> None:
    bridge = src('web/site/private.js')
    shell = src('web/site/research_private_shell_v23.js')
    assert "api('private/notes',{expected_version:version" in bridge
    assert "api('private/trade',{symbol:sym" in bridge
    assert "async signOut(){await logout()" in bridge
    assert "privateState&&!$('private-signed').hidden" in bridge
    assert 'window.QFPrivateBridgeV23' in bridge
    assert 'window.QFPrivateBridgeV23' in shell
    assert "window.QFNavigate20('explore')" in shell
    for forbidden in ('localStorage', 'sessionStorage', 'alpaca-secret', 'SUPABASE_SERVICE_KEY'):
        assert forbidden not in shell
    assert 'https://' not in shell  # no separate third-party service


def test_three_script_csp_remains_deterministic() -> None:
    built = src('public/index.html')
    generator = src('tools/build_unified_site.py')
    assert built.count('<script>') == 3
    assert 'qf-v23-owner-panel' in built
    assert 'QFPrivateBridgeV23' in built
    assert 'research_private_shell_v23.js' in generator
    assert 'data-qf-v23-open="notes"' in built
    assert 'QF_SEC_DATA' not in built
    assert 'SYNTHETIC · NOT REAL MARKET PRICES' in built
    assert 'illustrative_index_100_at_first_date' in built
    assert 'private/history-single' in built
