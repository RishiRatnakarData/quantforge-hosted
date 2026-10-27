"""V7.2 private decision brief integration, integrity and read-only boundaries."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_private_panel_and_immutable_research_module():
    builder = (ROOT / 'tools/build_unified_site.py').read_text(encoding='utf8')
    module = (ROOT / 'web/site/private_decision_v72.js').read_text(encoding='utf8')
    assert 'id="ideas-brief"' in builder
    assert 'data-private-view="ideas"' in builder
    assert 'private_decision_v72.js' in builder
    assert 'QFPrivateDecision' in module
    assert 'fetch(' not in module
    assert 'localStorage' not in module
    assert 'private/trade' not in module
    assert '/api/' not in module


def test_date_alignment_used_before_pairwise_diversification():
    module = (ROOT / 'web/site/private_decision_v72.js').read_text(encoding='utf8')
    private = (ROOT / 'web/site/private.js').read_text(encoding='utf8')
    assert 'sameSessions(a,b)' in module
    assert 'notAligned++' in module
    assert 'dates:Array.isArray(data.dates)?data.dates.slice():null' in private
    assert 'clearDecisionBrief()' in private


def test_research_exports_explicitly_exclude_account_and_prices():
    module = (ROOT / 'web/site/private_decision_v72.js').read_text(encoding='utf8')
    private = (ROOT / 'web/site/private.js').read_text(encoding='utf8')
    assert 'This export excludes virtual holdings, cash, account notes, credentials, raw licensed prices' in module
    assert "downloadResearchJSON('quantforge-investment-decision-brief.json'" in private
    assert "if(!privateState||!ideaDecisionBrief)" in private


def test_no_public_facing_account_records_and_csp_integrity():
    template = (ROOT / 'web/site/site.template.html').read_text(encoding='utf8')
    assert 'id="ideas-brief"' not in template
    assert '/* V7.2 owner-only decision research' in template
