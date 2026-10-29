"""V9.5 connected portfolio diagnostics, session journal and protected research boundaries."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_new_helper_is_pure_and_excludes_storage_or_trade():
    script = read("web/site/private_portfolio_validation_v95.js")
    for text in ("portfolioRisk(", "riskGateAudit(", "cashFlowScenarios(", "exportSafe("):
        assert text in script
    for forbidden in ("fetch(", "localStorage", "sessionStorage", "private/trade"):
        assert forbidden not in script


def test_shared_completed_assessment_connects_all_three_diagnostics():
    script = read("web/site/private.js")
    assert "QFPrivatePortfolioValidationV95.build({" in script
    assert "renderResearchDiagnosticsV95();" in script
    assert "portfolio:privateState,quotes:quoted,history:historySeries" in script
    assert "linkedResearchDiagnosticsV95=null;" in script
    assert "researchSessionJournalV95=researchSessionJournalV95.slice(0,8);" in script


def test_private_session_history_and_logout_privacy():
    script = read("web/site/private.js")
    assert "researchSessionJournalV95=[];clearResearchOSV90();" in script
    assert "qf-v95-journal-clear" in script
    assert "QFPrivatePortfolioValidationV95.exportSafe" in script
    assert "quantforge-v95-linked-research-briefing.json" in script


def test_protected_page_and_three_script_csp():
    builder = read("tools/build_unified_site.py")
    page = read("public/index.html")
    assert "private_portfolio_validation_v95.js').read_text" in builder
    for element in ("qf-v95-hub", "qf-v95-brief", "qf-v95-session-history", "qf-v95-journal-clear"):
        assert page.count(f'id="{element}"') == 1
    assert page.count('<script') == 3
    assert page.count('id="private-mfa-code"') == 1
    assert page.count('id="private-v90-run"') == 1
    assert 'Previously completed research review (manual)' not in page
