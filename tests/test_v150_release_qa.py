"""V15.0 final release provenance, sanitized owner attestation, and source guardrails."""

from pathlib import Path

from tools.audit_release_v150 import LIVE_TESTS, audit

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_compiled_public_data_scope_and_private_acceptance_exists():
    html = source("public/index.html")
    headers = source("public/_headers")
    result = audit(html, headers)
    assert result["static_contract"] == "passed"
    assert result["manual_acceptance"] == "not_independently_verified"
    assert len(result["manual_checks"]) == 6
    assert result["compiled_scripts"] == 3
    assert {x["key"] for x in result["manual_checks"]} == set(LIVE_TESTS)


def test_modified_source_keeps_v14_readiness_and_v13_integrity():
    builder = source("tools/build_unified_site.py")
    private = source("web/site/private.js")
    for mark in ("qf-v140-next", "qf-v130-hub-result", "qf-v99-file"):
        assert mark in builder
    assert "renderWorkflowV140()" in private
    assert "compactResearchDetailsV140();" in private
    assert "private_release_acceptance_v150.js" in builder


def test_owner_status_export_is_isolated_from_brokerage_data():
    private = source("web/site/private.js")
    marker = "$('qf-v150-download').addEventListener('click'"
    assert marker in private
    export_action = private.split(marker, 1)[1].split("});", 1)[0]
    assert "if(!privateState)return;" in export_action
    assert "QFPrivateReleaseAcceptanceV150.exportSafe(manualAcceptanceV150)" in export_action
    assert "quantforge-v15-manual-browser-acceptance.json" in export_action
    assert "privateState.portfolio" not in export_action


def test_public_disclosures_do_not_claim_a_validated_trading_record():
    html = source("public/index.html")
    assert "do not establish predictive investment performance" in html
    assert "The local multi-year SEC revision archive is not part of this public site" in html
    assert "Public portfolio returns" in html


def test_static_release_audit_rejects_invalid_csp():
    import pytest

    html = source("public/index.html")
    headers = source("public/_headers")
    with pytest.raises(ValueError, match="CSP"):
        audit(html, headers.replace("'sha256-", "'sha999-"))


def test_static_audit_rejects_missing_manual_check():
    import pytest

    html = source("public/index.html")
    headers = source("public/_headers")
    with pytest.raises(ValueError, match="approved interface"):
        audit(html.replace('data-v150-check="archive"', 'data-v150-check="removed"'), headers)
