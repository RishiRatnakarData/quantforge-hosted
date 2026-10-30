"""V9 decision-first private OS structure and existing security invariants."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_consolidated_private_nav_and_research_lab():
    s = read("tools/build_unified_site.py")
    assert s.count('class="private-nav-group"') == 4
    expected = ["01 · Decision Center", "02 · Companies",
                "03 · Research Methods", "04 · Portfolio &amp; Reports"]
    assert [s.index(x) for x in expected] == sorted(s.index(x) for x in expected)
    for view in ("decision", "ideas", "home", "trade", "lab", "candidate", "research", "optimization",
                 "backtest", "walkforward", "valuation", "settings"):
        assert f'data-private-tab="{view}"' in s
        assert f'data-private-view="{view}"' in s
    assert s.index('data-private-view="decision"') < s.index('data-private-view="trade"')
    assert s.index('data-private-view="candidate"') > s.index('data-private-view="decision"')


def test_existing_mfa_privacy_and_bundle_kept():
    builder = read("tools/build_unified_site.py")
    app = read("web/site/private.js")
    assert 'id="private-signed" hidden' in builder
    assert "'sha256-" in builder and "len(scripts)==3" in builder
    assert "(src/'site/private_research_os_v90.js').read_text" in builder
    assert "const init={credentials:'same-origin',cache:'no-store'}" in app
    assert "if(!privateState){message('Sign in with MFA" in app
    assert "clearResearchOSV90();" in app
    assert "runResearchOSV90" in app
    assert "await loadHistory()" in app
    assert "runOptimization()" in app
    assert "runWalkforward()" in app
    assert "await runCandidateDossierV85()" in app


def test_generated_html_includes_new_ui_and_legacy_ids():
    html = read("public/index.html")
    assert html.count("<script") == 3
    for tag in ("private-v90-run", "private-v90-report", "private-v90-risk", "private-v90-candidate",
                "private-v87-factor-file", "private-opt-run", "private-wf-run", "private-mfa-code"):
        assert f'id="{tag}"' in html
    assert html.count('data-private-view="lab"') == 1
    assert html.count('data-private-view="candidate"') == 1
    assert html.count('data-private-view="decision"') == 1


def test_policy_is_standalone_and_remains_private():
    policy = read("web/site/private_research_os_v90.js")
    for forbidden in ("fetch(", "localStorage", "sessionStorage", "XMLHttpRequest", "private/trade"):
        assert forbidden not in policy
    assert "Insufficient evidence" in policy
    assert "Consider a small position (conditional)" in policy
    assert "Review / consider reducing exposure" in policy
