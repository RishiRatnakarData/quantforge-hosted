"""Public navigation, recruiter pathway, and private-data boundary for V8.1.1."""
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_public_sidebar_always_displays_every_route():
    page=(ROOT/'web/site/site.template.html').read_text(encoding='utf-8')
    nav=page.split('<nav id="navigation" aria-label="Main navigation">',1)[1].split('</nav>',1)[0]
    assert nav.count('class="qf-nav-section"') == 3
    assert '<details' not in nav and '<summary' not in nav and ' hidden' not in nav
    expected=['overview','sec','lab','portfolio','quant','valuation','ml','systems','methods']
    assert re.findall(r'data-page="([a-z]+)"',nav) == expected
    assert 'data-page="overview" aria-current="page">Overview</button>' in nav
    assert 'Interactive models' in nav and 'Methods &amp; engineering' in nav


def test_homepage_is_recruiter_accessible_and_source_linked():
    page=(ROOT/'web/site/site.template.html').read_text(encoding='utf-8')
    start=page.split('<section class="tabpage active" id="page-overview">',1)[1].split('</section>',1)[0]
    assert start.count('class="qf-roadmap-card"') == 4
    for route in ('sec','lab','quant','systems'):
        assert f'data-go="{route}"' in start
    assert 'data-go="private"' not in start
    assert 'View GitHub source and tests' in start
    assert 'rel="noopener noreferrer"' in start
    assert 'Financial research, built from the data up.' in start
    assert 'simulated returns and hypothetical forecasts' in start


def test_private_workspace_and_charts_stay_intact():
    builder=(ROOT/'tools/build_unified_site.py').read_text(encoding='utf-8')
    app=(ROOT/'web/site/app.js').read_text(encoding='utf-8')
    assert 'data-page="private">Private workspace</button>' in builder
    assert all(f'data-private-tab="{name}"' in builder for name in ('decision', 'home', 'settings', 'lab')) and 'qf-v170-nav' in builder
    assert 'id="private-mfa-code"' in builder
    assert 'id="private-research-loaded"' in builder
    assert 'QFPublicVisualsV81' in app
    assert "const PUBLIC_PAGES=new Set" in app
    assert "closest('details.qf-nav-fold')" not in app


def test_reliable_public_source_evidence_remains():
    page=(ROOT/'web/site/site.template.html').read_text(encoding='utf-8')
    assert '/* QF_SEC_DATA */' not in page
    assert 'Historical SEC data' in page
    assert 'Simulated returns' in page
    assert '<strong>Research data:</strong> Historical SEC company financials' in page
    assert 'simulated returns and hypothetical forecasts' in page
    assert 'Source lineage' in page or 'Data lineage' in page
