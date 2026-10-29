"""V9.4 connected issuer comparison and policy sensitivity release boundaries."""

from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding='utf-8')

def test_sec_market_comparison_uses_existing_observed_data_without_network():
    src=read('web/site/private_investment_intelligence_v94.js')
    assert 'compareSEC(snapshot,selection,asOf)' in src
    assert 'comovement(history,selection)' in src
    assert 'sensitivity(variants,base)' in src
    assert 'source_url' in src
    assert 'function build({' in src
    assert 'fetch(' not in src and 'private/trade' not in src

def test_one_shared_decision_connected_to_v94_and_original_report():
    src=read('web/site/private.js')
    assert 'QFPrivateResearchBriefV93.summarize(result,review,assetNames,researchSelection)' in src
    assert 'QFPrivateInvestmentIntelligenceV94.build({' in src
    assert 'window.QFPublishedSEC' in src
    assert "['conservative','balanced','growth'].map" in src
    assert 'engine.reconcile(assessment,results)' in src
    assert 'renderInvestmentIntelligenceV94();' in src

def test_source_changes_invalidate_both_linked_reports():
    src=read('web/site/private.js')
    block=src.split('function clearResearchOSV90(){',1)[1].split('function refreshResearchOSChoicesV90(){',1)[0]
    assert 'linkedResearchBriefV93=null;linkedResearchIntelligenceV94=null;' in block
    assert 'refreshConnectedResearchV93();' in block
    assert 'if(!researchOSInternalLoadV90)clearResearchOSV90();' in src

def test_csp_and_mfa_preserved_and_unique_v94_containers():
    builder=read('tools/build_unified_site.py')
    page=read('public/index.html')
    assert "(src/'site/private_investment_intelligence_v94.js').read_text" in builder
    assert page.count('id="qf-v94-intelligence-hub"')==1
    assert page.count('id="qf-v94-intelligence-brief"')==1
    assert page.count('id="qf-v94-lab-insight"')==1
    assert page.count('id="private-mfa-code"')==1
    assert page.count('id="private-v90-run"')==1
    assert page.count('<script')==3

def test_prior_v93_manual_panel_still_hidden_and_lab_navigable():
    page=read('public/index.html')
    assert 'Previously completed research review (manual)' not in page
    assert 'qf-v93-legacy-compat' in page
    assert 'qf-v93-lab-status' in page
    assert 'data-private-tab="lab"' in page


def test_export_contains_only_bounded_comparative_packet():
    s=read("web/site/private.js")
    assert "comparativeIntelligence:linkedResearchIntelligenceV94" in s
    assert "quantforge-v94-linked-research-briefing.json" in s
