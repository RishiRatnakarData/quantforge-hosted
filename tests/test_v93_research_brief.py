"""V9.3 connected research integration and non-trading privacy checks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def test_manual_accordion_is_no_longer_visible_but_compatibility_endpoints_remain():
    page=read('public/index.html')
    assert 'Previously completed research review (manual)' not in page
    assert '<div id="qf-v93-legacy-compat" hidden aria-hidden="true">' in page
    assert 'id="private-decision-center-v84"' in page
    assert 'id="private-decision-run-v84"' in page
    assert '#private-signed #qf-v93-legacy-compat[hidden]{display:none!important}' in page


def test_nav_and_research_briefing_share_same_model_output():
    builder=read('tools/build_unified_site.py')
    private=read('web/site/private.js')
    assert '01 · Research Hub' in builder and '05 · Research Briefing &amp; Notes' in builder
    assert 'id="qf-v93-research-ribbon"' in builder
    assert 'id="qf-v93-lab-status"' in builder
    assert 'id="qf-v93-briefing"' in builder
    assert "linkedResearchBriefV93=window.QFPrivateResearchBriefV93.summarize(result,review,assetNames,researchSelection);" in private
    assert "if(tab==='settings')renderConnectedBriefV93();" in private
    assert "if(tab==='lab')refreshConnectedResearchV93();" in private


def test_protected_script_unchanged_count_and_mfa_retained():
    builder=read('tools/build_unified_site.py')
    page=read('public/index.html')
    assert "(src/'site/private_research_brief_v93.js').read_text" in builder
    assert "len(scripts)==3" in builder
    assert page.count('<script')==3
    assert 'id="private-mfa-code"' in page
    assert 'id="private-v87-factor-file"' in page
    assert 'id="private-v90-run"' in page


def test_stale_selection_or_session_deletes_linked_report():
    s=read('web/site/private.js')
    clear=s.split('function clearResearchOSV90(){',1)[1].split('function refreshResearchOSChoicesV90(){',1)[0]
    assert 'linkedResearchBriefV93=null;' in clear
    assert 'refreshConnectedResearchV93()' in clear
    assert "$(id).addEventListener('change',clearResearchOSV90);" in s
    assert "if(!researchOSInternalLoadV90)clearResearchOSV90();" in s
    assert 'clearResearchOSV90();' in s.split('async function loadState(){',1)[1][:200]


def test_all_lab_sections_and_private_actions_preserved():
    page=read('public/index.html')
    for id_ in ['private-valuation-run','private-wf-run','private-opt-run','private-guide-run-v79',
                'private-v90-report','private-research-dataset','private-v87-factor-file',
                'qf-v93-brief-refresh','qf-v93-brief-export','qf-v93-ribbon-assess']:
        assert page.count(f'id="{id_}"')==1
    assert "api('private/trade'" not in read('web/site/private_research_brief_v93.js')


def test_canonical_data_provenance_and_bridge_through_same_computation():
    source=read('web/site/private.js')
    assert 'engine.reconcile(assessment,results)' in source
    assert 'window.QFPrivateDecisionReviewV92.review(result,historySeries,researchSelection)' in source
    assert 'window.QFPrivateResearchBriefV93.summarize(result,review,assetNames,researchSelection)' in source
    assert "data-v93-method" in source
    assert 'No current briefing' in source
