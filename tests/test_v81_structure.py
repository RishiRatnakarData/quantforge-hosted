"""Regression checks for V8.1 location and security contracts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_public_routes_and_sources_unchanged():
    s = _read('web/site/site.template.html')
    for route in ('overview', 'sec', 'lab', 'portfolio', 'quant', 'valuation', 'ml', 'systems', 'methods'):
        assert f'id="page-{route}"' in s and f'data-page="{route}"' in s
    assert s.count('class="qf-nav-section"') == 3
    assert s.count('class="qf-secondary-details"') == 1
    assert s.index('id="qf-company-count-v81"') < s.index('id="home-sec-highlights"')
    assert s.index('id="page-sec"') < s.index('id="qf-sec-metric-v81"') < s.index('id="page-portfolio"')
    assert 'historical sec' in s.lower()
    assert 'share-price forecast' in s.lower()
    assert '/* QF_SEC_DATA */' not in s
    overview = s.split('id="page-overview"', 1)[1].split('</section>', 1)[0]
    assert 'id="private-guide-card-v79"' not in overview
    assert 'id="sec-margin-shock"' not in overview
    assert 'id="qf-sec-metric-v81"' not in overview
    assert 'id="home-sec-highlights"' in overview


def test_private_workflow_without_extra_tabs():
    s = _read('tools/build_unified_site.py')
    assert s.count('class="private-nav-group"') == 5
    for tab in ('home', 'trade', 'ideas', 'research', 'optimization', 'backtest', 'walkforward', 'valuation', 'settings'):
        assert f'data-private-view="{tab}"' in s
        assert f'data-private-tab="{tab}"' in s
    loc = {x: s.index(x) for x in ('data-private-view="home"', 'data-private-view="trade"',
                                  'data-private-view="ideas"', 'data-private-view="settings"',
                                  'id="private-guide-card-v79"', 'id="private-allocation-card-v74"',
                                  'id="private-capital-action"', 'id="private-total"')}
    assert loc['data-private-view="home"'] < loc['id="private-total"'] < loc['data-private-view="trade"']
    assert loc['data-private-view="trade"'] < loc['id="private-allocation-card-v74"'] < loc['data-private-view="ideas"']
    assert loc['data-private-view="trade"'] < loc['id="private-capital-action"'] < loc['data-private-view="ideas"']
    assert loc['data-private-view="settings"'] < loc['id="private-guide-card-v79"']
    assert 'id="private-research-loaded"' in s
    for marker in ('id="private-mfa-code"', 'id="private-login-submit"', 'id="private-logout"'):
        assert marker in s


def test_one_bundled_hashed_public_script_no_api_changes():
    s = _read('tools/build_unified_site.py')
    assert "visuals=(src/'site/sec_visuals_v81.js').read_text(encoding='utf-8')" in s
    assert 'scripts=re.findall' in s and 'assert len(scripts)==3' in s
    assert 'script-src ' in s and "connect-src 'self'" in s
    assert 'id="private-research-dataset"' in s
    app = _read('web/site/app.js')
    assert 'QFPublicVisualsV81' in app
    assert "$('sec-export').addEventListener('click',downloadSECCsv)" in app
    assert 'function renderSECTrend' in app
    assert "const PUBLIC_PAGES=new Set" in app
