"""V8.6: authenticated candidate add-on and source only regression tests."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_new_controls_are_private_not_public_home():
    builder = read("tools/build_unified_site.py")
    template = read("web/site/site.template.html")
    assert builder.count('id="private-v86-benchmark"') == 1
    assert builder.count('id="private-v86-proxy1"') == 1
    assert builder.count('id="private-v86-proxy2"') == 1
    assert builder.count('id="private-v86-years"') == 1
    assert builder.count('id="private-v86-output"') == 1
    assert 'id="private-v86-benchmark"' not in template
    assert builder.index('id="private-v86-benchmark"') > builder.index('id="private-candidate-select-v85"')
    assert 'id="private-mfa-code"' in builder


def test_new_module_bundled_before_existing_optimizer_and_app():
    source = read("tools/build_unified_site.py")
    assert source.count("private_factor_scenarios_v86.js") == 1
    assert source.index("private_candidate_v85.js") < source.index("private_factor_scenarios_v86.js")
    assert source.index("private_factor_scenarios_v86.js") < source.index("private_optimizer.js")


def test_controller_invalidates_on_selection_and_uses_existing_in_memory_history():
    app = read("web/site/private.js")
    assert "refreshFactorChoicesV86()" in app
    assert "QFPrivateFactorScenariosV86.assess" in app
    assert "renderFactorScenariosV86(factorResult)" in app
    assert "session!==privateState" in app
    assert "selected!==researchSelection.join(',')" in app
    assert "clearCandidateDossierV85()" in app
    assert "private-v86-output" in app


def test_factor_calculation_is_pure_local_and_unprivileged():
    module = read("web/site/private_factor_scenarios_v86.js")
    for forbidden in ("fetch(", "localStorage", "sessionStorage", "XMLHttpRequest", "WebSocket", "private/trade", "downloadResearchJSON", "executeOrder"):
        assert forbidden not in module
    assert "Fama–French" in module
    assert "NOT risk-free-adjusted CAPM alpha" in module
