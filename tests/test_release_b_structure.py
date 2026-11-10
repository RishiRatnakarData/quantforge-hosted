"""Release B published layout, data-contract and privacy regression checks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_compare_and_portfolio_are_real_five_route_panels():
    html = source('web/site/site.template.html')
    for route in ('explore', 'compare', 'models', 'portfolio', 'methods'):
        assert html.count(f'id="page-{route}"') == 1
    for field in ('qf-b21-compare-chart', 'qf-b21-finance-table', 'qf-b21-risk-scatter',
                  'qf-b21-correlation', 'qf-b21-distribution', 'qf-b21-weight-controls',
                  'qf-b21-whatif-chart', 'qf-b21-analysis-corr', 'qf-b21-owner-account'):
        assert html.count(f'id="{field}"') == 1
    portfolio = html.split('id="page-portfolio"',1)[1].split('id="page-quant"',1)[0]
    assert '<details' not in portfolio
    assert 'Additional simulated portfolio and model examples' not in portfolio
    assert 'data-qf-portfolio="whatif"' in portfolio


def test_original_owner_security_and_legacy_computation_preserved():
    api = source('cloud/api.py')
    assert '@app.get("/api/private/history")' in api
    assert '@app.get("/api/private/history-single")' in api
    assert '@app.get("/api/private/quotes")' in api
    assert '@app.get("/api/private/state")' in api
    assert 'owner(request, response)' in api
    for file in ('web/site/private_optimizer.js','web/site/private_walkforward_v65.js',
                 'web/site/private_predictive_ml_v180.js','web/site/model.js'):
        assert (ROOT / file).is_file()
    assert 'QFResearchB21' in source('web/site/research_compare_portfolio_v21.js')


def test_three_csp_bundles_and_no_public_licensed_observations():
    html = source('public/index.html')
    assert html.count('<script>') == 3
    assert 'window.QFResearchB21' in html
    assert 'licensed_private' in html  # API-contract validation code only
    assert 'No real public stock-price feed is claimed.' in source('web/site/site.template.html')
    assert 'no real public stock-price feed' in html.lower()
    assert "fetch('/api/'" in source('web/site/research_app_v20.js')
    assert '/api/private/trade' not in source('web/site/research_compare_portfolio_v21.js')
