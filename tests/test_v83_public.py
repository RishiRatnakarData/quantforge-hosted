"""Focused V8.3 presentation tests; no market/network/private data used."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(p: str) -> str:
    return (ROOT / p).read_text(encoding='utf-8')


def test_public_home_research_breadth_and_owner():
    page = read('web/site/site.template.html')
    home = page.split('id="page-overview"', 1)[1].split('</section>', 1)[0]
    assert 'Financial research, portfolio analytics, and quantitative modeling.' in home
    assert 'id="qf-company-count-v81"' in home
    assert home.count('class="qf-roadmap-card"') == 4
    for route in ('sec', 'lab', 'quant', 'systems'):
        assert f'data-go="{route}"' in home
    assert '<div hidden aria-hidden="true"><div id="home-sec-highlights"' in home
    assert 'Designed and developed by <strong>Rishi Ratnakar</strong>' in page


def test_dashboard_responds_to_the_correct_inputs():
    page = read('web/site/site.template.html')
    controller = read('web/site/public_lab_v77.js')
    lab = page.split('id="page-lab"', 1)[1].split('id="page-systems"', 1)[0]
    assert 'only the SEC performance exhibit' in lab
    assert 'id="qf-v83-active-company"' in lab
    assert 'id="qf-v83-model-settings"' in lab
    assert 'id="lab-recalculate" hidden' in lab
    assert "issuer.addEventListener('change',refreshSec)" in controller
    for ident in ('lab-cap','lab-fee','lab-train'):
        assert ident in controller
    assert "const label=byId('qf-v83-active-company')" in controller
    assert "const note=byId('qf-v83-model-settings')" in controller
    assert "for(const id of ['lab-cap','lab-fee','lab-train'])" in controller


def test_methods_have_verified_code_and_math():
    page = read('web/site/site.template.html')
    assert page.count('id="qf-v83-method-atlas"') == 1
    methods = page.split('id="qf-v83-method-atlas"', 1)[1].split('id="systems-public-evidence"', 1)[0]
    assert methods.count('class="qf-v83-method"') == 6
    for phrase in ('Revenue growth', 'Portfolio variance', 'Minimize',
                   'Walk-forward', 'PV =', 'fingerprint', 'Python 3.11/3.12'):
        assert phrase in methods
    assert 'does not imply an implemented OLS return-prediction model' in methods
    assert 'RishiRatnakarData/quantforge-hosted' in methods


def test_existing_private_protection_and_source_integrity_remain():
    page = read('web/site/site.template.html')
    assert '<script>/* QF_MODEL */</script>' in page
    assert '<script>/* QF_APP */</script>' in page
    assert '/* QF SEC SNAPSHOT' not in page  # no second public data pipeline
    assert 'id="page-methods"' in page
    assert 'id="page-systems"' in page
    assert 'QF V8.2 PUBLIC RESEARCH CASE STUDY' in page
