"""V8.7: pure daily FF3 source import and MFA-only research integration."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_authenticated_candidate_dossier_includes_independent_factor_import():
    builder = source("tools/build_unified_site.py")
    private = builder.split('<section class="tabpage" id="page-private">', 1)[1]
    signed = private.split('<div id="private-signed" hidden>', 1)[1]
    factor_study = signed.split('id="private-v87-title"', 1)[1]
    assert 'id="private-v87-factor-file"' in factor_study
    assert 'id="private-v87-factor-run"' in factor_study
    assert 'id="private-v87-factor-clear"' in factor_study
    assert 'id="private-v87-factor-output"' in factor_study
    assert "mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html" in factor_study
    assert "The file is read inside this authenticated browser session only" in factor_study
    assert 'id="private-v86-output"' in signed


def test_factor_module_is_integrated_into_existing_three_script_bundle():
    builder = source("tools/build_unified_site.py")
    assert builder.count("(src/'site/private_french_factors_v87.js').read_text") == 1
    assert builder.index("(src/'site/private_factor_scenarios_v86.js').read_text") < builder.index(
        "(src/'site/private_french_factors_v87.js').read_text"
    ) < builder.index("(src/'site/private_optimizer.js').read_text")
    page = source("public/index.html")
    assert page.count("private-v87-factor-run") == 2  # DOM id and listener string
    assert page.count('id="private-v87-title"') == 1
    assert page.count("<script") == 3


def test_source_only_pure_math_and_no_auto_trade_or_remote_import():
    factor = source("web/site/private_french_factors_v87.js")
    for forbidden in (
        "fetch(",
        "XMLHttpRequest",
        "localStorage",
        "sessionStorage",
        "placeOrder(",
        "submitTrade(",
    ):
        assert forbidden not in factor
    assert "const api=Object.freeze({parseDailyCsv,assess})" in factor
    assert "user supplied" in factor
    assert "Newey" in factor


def test_import_lifecycle_clears_on_logout_and_on_candidate_changes():
    app = source("web/site/private.js")
    assert "clearImportedFrenchV87();clearGuideV79();clearMFA()" in app
    assert "$('private-v87-factor-file').addEventListener('change',importFrenchV87)" in app
    assert "$('private-v87-factor-run').addEventListener('click',runFrenchV87)" in app
    assert "$('private-v87-factor-clear').addEventListener('click',clearImportedFrenchV87)" in app
    assert "const official=$('private-v87-factor-output');if(official)official.textContent=''" in app
    assert "session!==privateState" in app


def test_factor_study_has_distinct_research_methodology():
    doc = source("docs/V87_FRENCH_FACTOR_VALIDATION.md")
    assert "actual factor portfolios" in doc
    assert "holdout" in doc.lower()
    assert "risk-free" in doc.lower()
    assert "not a forecast" in doc.lower()
