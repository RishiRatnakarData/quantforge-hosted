"""V9.1 integration contract and private-market safety boundaries."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_v91_loaded_inside_same_three_script_private_bundle():
    builder = source("tools/build_unified_site.py")
    assert builder.count("(src/'site/private_research_orchestrator_v91.js').read_text") == 1
    assert builder.index("private_research_orchestrator_v91.js") < builder.index("private_research_os_v90.js")
    assert "len(scripts)==3" in builder
    policy = source("web/site/private_research_orchestrator_v91.js")
    for forbidden in ("fetch(", "localStorage", "sessionStorage", "XMLHttpRequest", "private/trade"):
        assert forbidden not in policy


def test_v91_preserves_existing_models_and_authorization():
    app = source("web/site/private.js")
    assert "if(!privateState){message('Sign in with MFA before running research.')" in app
    for exact in (
        "await loadHistory()", "runOptimization()", "runWalkforward()", "runV68Robustness()",
        "await runCandidateDossierV85()", "QFPrivateFrenchFactorsV87.assess", "QFPrivateResearchOSV90.assess",
        "engine.reconcile(assessment,results)", "if(!current())return;", "candidateFactorV91=factorResult",
        "if(button)button.disabled=false",
    ):
        assert exact in app
    assert "api('private/trade'" not in app.split('async function runResearchOSV90(){', 1)[1].split('function clearDecisionCenterV84(){', 1)[0]


def test_v91_provenance_visible_with_escaping_and_existing_policy_unchanged():
    app = source("web/site/private.js")
    assert 'Model execution and data provenance' in app
    assert "safe(m.detail)" in app and "safe(m.source)" in app
    assert "private-v90-run" in source("tools/build_unified_site.py")
    policy = source("web/site/private_research_os_v90.js")
    assert "Consider a small position (conditional)" in policy
    assert "No virtual or live trade is initiated" in policy
