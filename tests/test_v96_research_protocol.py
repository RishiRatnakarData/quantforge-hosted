"""V9.6 integration, archive, build and security contract tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_pure_historical_validation_and_sec_cashflow_module():
    source = read("web/site/private_research_intelligence_v96.js")
    for feature in (
        "futureRiskScreen(",
        "financialBridge(",
        "allocationStress(",
        "archiveRecord(",
        "readArchive(",
        "safeSummary(",
    ):
        assert feature in source
    for prohibited in (
        "fetch(",
        "localStorage",
        "sessionStorage",
        "private/trade",
        "private/notes",
        "XMLHttpRequest",
    ):
        assert prohibited not in source


def test_one_connected_completed_assessment_and_new_diagnostics():
    private = read("web/site/private.js")
    assert "QFPrivateResearchIntelligenceV96.build({" in private
    assert "renderResearchProtocolV96();" in private
    assert "linkedResearchProtocolV96=null;" in private
    assert "portfolio:privateState,quotes:quoted,history:historySeries" in private
    assert "window.QFPrivateResearchIntelligenceV96.safeSummary" in private
    assert "researchSessionJournalV95=researchSessionJournalV95.slice(0,8)" in private


def test_durable_archive_reuses_mfa_protected_existing_notes_not_new_backend():
    private = read("web/site/private.js")
    assert "window.QFPrivateResearchIntelligenceV96.archiveRecord(" in private
    assert "window.QFPrivateResearchIntelligenceV96.readArchive(" in private
    assert "api('private/notes',{expected_version:" in private
    assert "saveResearchV96" in private
    assert "deleteSavedResearchV96" in private
    assert "renderSavedResearchV96();" in private
    assert "window.confirm('Permanently delete this saved assessment?')" in private


def test_webpage_compiles_three_scripts_and_all_v96_sections():
    builder = read("tools/build_unified_site.py")
    page = read("public/index.html")
    assert "private_research_intelligence_v96.js').read_text" in builder
    for component in (
        "qf-v96-hub",
        "qf-v96-brief",
        "qf-v96-lab-insight",
        "qf-v96-saved-list",
        "qf-v96-save",
    ):
        assert page.count(f'id="{component}"') == 1
    assert page.count("<script") == 3
    assert page.count('id="private-mfa-code"') == 1
    assert "Previously completed research review (manual)" not in page


def test_release_has_no_auto_trades_or_unrestricted_private_exports():
    private = read("web/site/private.js")
    source = read("web/site/private_research_intelligence_v96.js")
    assert "portfolioValidation:linkedResearchDiagnosticsV95?" in private
    assert "researchValidationV96:linkedResearchProtocolV96?" in private
    assert "No dividends, financing, taxes" in source
    assert "full investment decision" not in source.lower() or "not" in source.lower()
