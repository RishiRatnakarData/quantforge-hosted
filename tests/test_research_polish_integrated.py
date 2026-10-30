"""Editorial polish: no visible release tags and no missing public jump links."""
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def source(name):
    return (ROOT/name).read_text(encoding="utf-8")

def test_private_navigation_and_public_exit():
    build=source("tools/build_unified_site.py")
    for title in ("Research", "Portfolio", "Saved reports", "Advanced research"):
        assert title in build
    assert 'data-page="overview">Public research</button>' in build
    assert 'qf-private-exit' in source("web/site/site.template.html")
    for route in (
        "decision", "ideas", "candidate", "lab", "valuation",
        "optimization", "backtest", "walkforward", "research",
        "settings", "home", "trade",
    ):
        assert f'data-private-tab="{route}"' in build

def test_no_numbered_release_titles_in_dynamic_reports():
    js=source("web/site/private.js")
    assert not re.search(r"<span class=\"eyebrow\">V\d+\.\d+",js)
    assert not re.search(r"<summary>V\d+\.\d+",js)
    assert "CURRENT RESEARCH ASSESSMENT" in js

def test_missing_evidence_has_neutral_state():
    core=source("web/site/private_unified_decision_v160.js")
    assert "signal='gray'" in core
    assert "integrity.classification==='evidence-complete'" in core
    assert "Not evaluated" in core

def test_current_readme_and_original_data_limits():
    readme=source("README.md")
    assert "V7.0 — Current hosted platform" not in readme
    assert "MFA" in readme and "SEC" in readme
    assert "No live trading" in readme
