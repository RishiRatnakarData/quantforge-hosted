"""Public-facing structure checks for V6.5.1 private research context panel."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_shared_selection_widget_present_only_once():
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    assert builder.count('id="private-history-selection"') == 1
    assert builder.count('id="private-history-load"') == 1
    assert builder.count('id="private-research-dataset"') == 1
    assert builder.count('id="private-research-loaded"') == 1
    assert 'Used in Market data, Optimization, Backtests and Walk-forward' in builder


def test_research_widget_uses_real_loaded_history_not_selection_as_data():
    source = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    assert 'd.symbols.map(researchCompanyLabel)' in source
    assert "loaded.textContent='No historical data loaded'" in source
    assert 'historyLoadSequence++' in source
    assert 'request!==historyLoadSequence' in source
    assert "$('private-history-days').addEventListener('change'" in source
    assert "$('private-opt-export').disabled=true;$('private-wf-export').disabled=true" in source


def test_walkforward_labels_two_portfolios_not_underlying_assets():
    source = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    assert 'investments are combined into two portfolio lines' in source
    assert 'Green: optimized portfolio (all selected investments)' in source
    assert 'Orange: equal-weight benchmark (the same investments)' in source
