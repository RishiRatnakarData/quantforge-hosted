"""SEC explorer must bundle source-backed math without touching private APIs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sec_explorer_real_data_controls():
    html = (ROOT / 'web/site/site.template.html').read_text(encoding='utf-8')
    for identifier in (
        'id="sec-trend"', 'id="sec-rank-metric"', 'id="sec-export"',
        'id="sec-provenance"', 'id="sec-ranking-note"',
    ):
        assert identifier in html
    assert 'Download source-backed CSV' in html
    assert 'Fiscal year-end dates may differ' in html or 'not a synchronized period' in html


def test_real_data_analytics_module_is_bundled_not_externally_fetched():
    builder = (ROOT / 'tools/build_unified_site.py').read_text(encoding='utf-8')
    app = (ROOT / 'web/site/app.js').read_text(encoding='utf-8')
    analytics = (ROOT / 'web/site/sec_analytics.js').read_text(encoding='utf-8')
    assert "analytics=(src/'site/sec_analytics.js').read_text(encoding='utf-8')" in builder
    assert "const M=window.QFModel,$=id=>document.getElementById(id),SEC=window.QFSecAnalytics" in app
    assert 'function ranking(' in analytics
    assert 'function snapshotCsv(' in analytics
    assert 'fetch(' not in analytics
    assert 'fetch(' not in app
    assert 'private' not in analytics.lower()


def test_public_sec_provenance_includes_missingness():
    app = (ROOT / 'web/site/app.js').read_text(encoding='utf-8')
    assert 'Not reported' in app
    assert 'renderSECRanking()' in app
    assert 'renderSECProvenance(company)' in app
    assert 'renderSECTrend(company)' in app
    assert "$('sec-rank-metric').addEventListener('change',renderSECRanking)" in app
    assert "$('sec-export').addEventListener('click',downloadSECCsv)" in app
    assert 'Data is synthetic' not in app
