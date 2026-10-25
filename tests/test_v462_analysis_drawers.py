"""Private UI data integrity for optional quantitative detail."""
from pathlib import Path

from quantforge.desk import server


def test_detail_drawers_exist_and_start_collapsed():
    text = Path(server.HTML).read_text(encoding="utf-8")
    for marker in ('id="positionBreakdown"', 'id="riskBreakdown"', 'id="valuationBreakdown"'):
        assert marker in text
    assert '<details class="analysis-drawer" open' not in text
    assert 'id="detailUnits"' in text
    assert 'id="riskVols"' in text
    assert 'id="valuationDetailRows"' in text


def test_drawer_values_use_real_backend_fields():
    text = Path(server.HTML).read_text(encoding="utf-8")
    for marker in (
        'd.shares_preview', 'd.approx_fee_usd', 'd.position_weight_before_pct',
        'd.position_weight_after_pct', 'd.reserve_percent',
        'hr.annual_vol_assumptions', 'hr.probability_of_loss',
        'val.terminal_growth', 'val.terminal_share_pct',
    ):
        assert marker in text
    assert 'assumed volatilities' in text
    assert 'not historical loss probabilities' in text
