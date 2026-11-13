"""Release C: new Models/Methods routes and source-boundary checks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_five_route_models_and_methods_have_normal_tabs_not_default_disclosures():
    html = source('web/site/site.template.html')
    models = html.split('<section class="tabpage" id="page-models"', 1)[1].split('</section>', 1)[0]
    methods = html.split('<section class="tabpage" id="page-methods">', 1)[1]
    for value in ('prediction', 'risk', 'valuation', 'strategy'):
        assert f'data-qf-model="{value}"' in models
    for value in ('results', 'evaluation', 'method'):
        assert f'data-qf-c22-phase="{value}"' in models
    for value in ('overview', 'data', 'statistical', 'engineering'):
        assert f'data-qf-c22-method="{value}"' in methods
    assert '<details' not in models
    assert 'id="qf-c22-legacy-methods" hidden aria-hidden="true"' in methods
    assert 'id="qf-c22-method-content"' in methods
    assert 'id="private-signed"' not in html


def test_all_model_calculations_are_pure_and_source_bound():
    ui = source('web/site/research_models_methods_ui_v22.js')
    core = source('web/site/research_models_core_v22.js')
    m = source('web/site/private_predictive_ml_v180.js')
    assert 'qf:research-context' in ui
    assert 'QFPrivatePredictiveMLV180?.analyze' in ui
    assert 'cash_flow' in core
    assert 'moving-block bootstrap' in core
    assert 'calibration' in m
    assert "fetch(" not in core
    assert 'localStorage' not in core
    assert 'owner account' not in core.lower()
    assert 'FCFF' in core


def test_generator_keeps_three_protected_scripts_and_private_modules():
    generator = source('tools/build_unified_site.py')
    assert "research_c=(src/'site/research_models_core_v22.js')" in generator
    assert "research_c_ui=(src/'site/research_models_methods_ui_v22.js')" in generator
    assert 'assert len(scripts)==3' in generator
    assert "(src/'site/private_predictive_ml_v180.js')" in generator
    assert 'id="private-mfa-code"' in generator
    assert 'data-private-view="settings"' in generator
    compiled = source('public/index.html')
    # Selector references are not additional rendered tabs. Verify the actual
    # three-tab DOM in smoke_final_release32; this unit checks script boundaries.
    assert compiled.count('<script>') == 3
    assert 'QFResearchModelsCore22' in compiled
    assert 'QFModelsMethods22' in compiled
