"""V8.5 candidate dossier integration and privacy checks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_private_candidate_is_bundled_after_other_private_pure_helpers():
    builder = read("tools/build_unified_site.py")
    assert builder.count("private_candidate_v85.js") == 1
    assert builder.index("private_decision_center_v84.js") < builder.index(
        "private_candidate_v85.js"
    )
    assert 'id="private-candidate-select-v85"' in builder
    assert 'id="private-candidate-output-v85"' in builder
    assert 'data-private-view="decision"' in builder
    assert 'id="private-mfa-code"' in builder


def test_candidate_is_private_and_not_on_public_home_page():
    template = read("web/site/site.template.html")
    compiled = read("public/index.html")
    assert 'id="private-candidate-select-v85"' not in template
    assert compiled.count('id="private-candidate-select-v85"') == 1
    assert compiled.index('id="private-candidate-select-v85"') > compiled.index(
        'id="private-signed" hidden'
    )
    assert compiled.count("QFPrivateCandidateV85") >= 1
    assert compiled.count("private-decision-run-v84") >= 1


def test_observed_valuation_uses_existing_private_authenticated_routes_only():
    app = read("web/site/private.js")
    assert "api('private/sec/company?symbol='" in app
    assert "api('private/valuation-capital?symbol='" in app
    assert "api('private/quotes?symbols='" in app
    assert "QFPrivateValueV73.build" in app
    assert "QFPrivateCandidateV85.evaluate" in app
    assert "Promise.allSettled" in app
    assert "session!==privateState" in app
    assert "selected!==researchSelection.join(',')" in app
    assert "private-candidate-run-v85" in app
    assert "privateTab(b.dataset.v85Go)" in app


def test_no_new_broker_or_export_routes():
    pure = read("web/site/private_candidate_v85.js")
    for forbidden in (
        "fetch(", "localStorage", "sessionStorage", "XMLHttpRequest",
        "private/trade", "downloadResearchJSON", "broker", "executeOrder",
    ):
        assert forbidden not in pure
