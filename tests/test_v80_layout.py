"""Standalone compatibility and reading-flow checks against an installed checkout."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_routes_and_disclosures_retained():
    page = (ROOT / 'web/site/site.template.html').read_text(encoding='utf-8')
    for route in ('overview', 'sec', 'lab', 'portfolio', 'quant', 'valuation', 'ml', 'systems', 'methods'):
        assert f'id="page-{route}"' in page
        assert f'data-page="{route}"' in page
    assert 'reported annual' in page.lower()
    assert 'Simulated returns' in page
    assert 'investment return examples are simulated' in page
    assert page.index('id="home-sec-highlights"') < page.index('class="project-story pane"')
    assert page.count('class="qf-nav-section"') == 3
    assert page.count('class="qf-secondary-details"') == 2
    assert 'SEC_DATA' not in page  # populated by CSP-protected build, not untrusted HTML.


def test_private_authentication_and_research_sections_retained():
    builder = (ROOT / 'tools/build_unified_site.py').read_text(encoding='utf-8')
    ast.parse(builder)
    for tab in ('home', 'trade', 'ideas', 'research', 'optimization', 'backtest', 'walkforward', 'valuation', 'settings'):
        assert f'data-private-tab="{tab}"' in builder
        assert f'data-private-view="{tab}"' in builder
    for anchor in ('id="private-mfa-code"', 'id="private-guide-card-v79"',
                   'id="private-research-loaded"', 'id="private-research-selected"'):
        assert anchor in builder
    assert builder.index('id="private-total"') < builder.index('id="private-guide-card-v79"')
    assert builder.count('class="private-nav-group"') == 3


def test_ui_only_changes_preserve_client_guardrails():
    private = (ROOT / 'web/site/private.js').read_text(encoding='utf-8')
    app = (ROOT / 'web/site/app.js').read_text(encoding='utf-8')
    for expr in ("function api(path, body)", "const init={credentials:'same-origin'", "api('private/state')"):
        assert expr in private
    assert 'closest(\'details.private-nav-group\')' in private
    assert "closest('details.qf-nav-fold')" not in app
    assert "const PUBLIC_PAGES=new Set" in app


def test_no_external_public_dependencies_added():
    page = (ROOT / 'web/site/site.template.html').read_text(encoding='utf-8')
    assert '/* V8.0: layout and reading-order refinement' in page
    assert 'https://cdn.' not in page
    assert '<script src=' not in page
