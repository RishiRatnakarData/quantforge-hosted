"""V14.0 page integration, read-only diagnostics, and release privacy checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_site_declares_readiness_and_manual_browser_acceptance():
    source = read("tools/build_unified_site.py")
    for marker in (
        'id="qf-v140-next"',
        'id="qf-v140-progress"',
        'id="qf-v140-steps"',
        'class="qf-v140-acceptance"',
        'id="qf-v140-lab-insight"',
        'id="qf-v140-brief-insight"',
        "private_workflow_v140.js",
    ):
        assert marker in source, marker
    assert "not yet independently verified" in source


def test_legacy_panels_are_accessible_by_expanding_details():
    source = read("web/site/private.js")
    assert "function compactResearchDetailsV140()" in source
    assert "document.createElement('details')" in source
    assert "box.appendChild(node)" in source
    assert "qf-v130-hub-result" not in source.split("function compactResearchDetailsV140()")[1].split("function refreshConnectedResearchV93()")[0]
    assert "compactResearchDetailsV140();" in source


def test_invalidating_inputs_recomputes_readiness():
    source = read("web/site/private.js")
    assert "function refreshResearchContext()" in source
    assert "renderWorkflowV140();" in source
    assert "history:historySeries" in source
    assert "archive:importedSECArchiveV99" in source
    assert "integrity:linkedDecisionIntegrityV130" in source


def test_report_export_is_sanitized_and_uses_no_sensitive_provider_access():
    source = read("web/site/private.js")
    assert "QFPrivateWorkflowV140.exportSafe(linkedWorkflowV140)" in source
    helper = read("web/site/private_workflow_v140.js")
    for forbidden in ("fetch(", "localStorage", "sessionStorage", "XMLHttpRequest(", "placeOrder(", "document."):
        assert forbidden not in helper
    assert "workflow-readiness.v14.0" in helper


def test_compiled_content_has_three_protected_scripts():
    compiled = (ROOT / "public/index.html").read_text(encoding="utf-8")
    assert compiled.count("<script>") == 3
    for token in ('qf-v140-next', 'qf-v140-steps', 'qf-v140-details', 'qf-v140-acceptance'):
        assert token in compiled


def test_compiled_contract_audit_labels_manual_work_as_unverified():
    from tools.audit_private_workflow_v140 import audit

    report = audit(read("public/index.html"), read("public/_headers"))
    assert report["automated_static_contract"] == "passed"
    assert report["manual_acceptance"] == "not_verified"
    assert len(report["manual_checks"]) == 6
    assert all(row["status"] == "not_verified" for row in report["manual_checks"])
    assert report["checks"] >= 17
