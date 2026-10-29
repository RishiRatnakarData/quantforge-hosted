"""V9.2 decision-policy review, source checks and protected visual UX contract."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_v92_preserves_v91_orchestration_and_v90_policy():
    builder = read('tools/build_unified_site.py')
    app = read('web/site/private.js')
    assert builder.count("(src/'site/private_decision_review_v92.js').read_text") == 1
    assert builder.index("private_research_orchestrator_v91.js") < builder.index("private_research_os_v90.js") < builder.index("private_decision_review_v92.js")
    assert 'len(scripts)==3' in builder
    for part in ("await loadHistory()", "runOptimization()", "runWalkforward()",
                 "await runCandidateDossierV85()", "engine.reconcile(assessment,results)",
                 "window.QFPrivateDecisionReviewV92.review(result,historySeries,researchSelection)"):
        assert part in app
    assert 'No virtual or live trade is initiated' in read('web/site/private_research_os_v90.js')


def test_visual_flow_groups_selection_constraints_and_run_separately():
    page = read('public/index.html')
    builder = read('tools/build_unified_site.py')
    assert 'Select investments</h3>' in builder
    assert 'Set your research constraints</h3>' in builder
    assert 'Run your assessment' in builder
    for element in ('private-v90-report', 'private-v90-risk', 'private-v90-maxweight',
                    'private-v90-maxdrawdown', 'private-v90-run', 'private-v90-candidate',
                    'private-mfa-code', 'private-v87-factor-file'):
        assert page.count(f'id="{element}"') == 1
    assert page.count('<script') == 3
    assert page.count('data-private-view="decision"') == 1
    assert 'qf-v92-evidence-grid' in page
    assert 'qf-v92-metrics' in page


def test_comparison_explains_only_historical_price_risk():
    app = read('web/site/private.js')
    assert 'no dividends, forecast or overall investment ranking' in app
    assert 'What might change this assessment?' in app
    assert 'Hard constraints and unavailable required inputs' in app
    assert 'safe(m.detail)' in app and 'safe(m.source)' in app
    assert "api('private/trade'" not in app.split('async function runResearchOSV90(){', 1)[1].split('function clearDecisionCenterV84(){', 1)[0]


def test_v92_is_pure_and_keeps_sensitive_provider_boundaries():
    script = read('web/site/private_decision_review_v92.js')
    for forbidden in ('fetch(', 'XMLHttpRequest', 'localStorage', 'sessionStorage',
                      'private/trade', 'alpaca.markets', 'api/private'):
        assert forbidden not in script
    assert 'historicalComparison' in script and 'required' in script
    assert 'probability estimates' in script
