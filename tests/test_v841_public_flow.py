"""V8.4.1 reading-flow/attribution regression tests (public markup only)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def _check(page):
    assert page.count('id="page-methods"') == 1
    methods = page.split('<section class="tabpage" id="page-methods">', 1)[1]
    assert methods.index('<div class="pagehead">') < methods.index('id="qf-methods-guide-title"')
    assert methods.index('id="qf-methods-guide-title"') < methods.index('id="public-research-engine"')
    assert '<section class="qf-methods-guide" aria-labelledby="qf-methods-guide-title">' in methods
    assert '<h2 id="qf-methods-guide-title">How the research platform works</h2>' in methods
    assert 'What the project covers' in methods
    assert 'More research in the private workspace' in methods
    assert '<details class="qf-secondary-details"><summary>How the research platform works</summary>' not in methods
    assert page.count('class="qf-secondary-details"') == 0
    assert '<span>Designed and developed by</span><strong>Rishi&nbsp;Ratnakar</strong>' in page
    assert '.qf-v83-owner strong{display:block;white-space:nowrap;' in page
    for target in ('data-go="sec"', 'data-go="quant"', 'data-go="lab"'):
        assert target in methods


def test_template_has_correct_heading_flow_and_full_name():
    _check(read('web/site/site.template.html'))


def test_compiled_site_preserves_accessible_inline_research_guide():
    _check(read('public/index.html'))


def test_private_auth_unchanged_and_no_active_guide_toggle():
    page = read('web/site/site.template.html')
    builder = read('tools/build_unified_site.py')
    assert 'id="page-private"' in builder
    assert 'id="private-signed" hidden' in builder
    assert 'id="private-mfa-code"' in builder
    assert page.count('id="qf-methods-guide-title"') == 1
