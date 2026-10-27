"""Source-level acceptance for V7.5 risk labeling and private boundaries."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_risk_clarity_calculator_has_separate_concentration_metrics():
    source = (ROOT / "web/site/private_allocation_v74.js").read_text(encoding="utf-8")
    assert "investmentHhi" in source
    assert "largestInvestedWeight" in source
    assert "investmentHhi:round" not in source
    assert "preInvestedOnlyHhi:" in source
    assert "postInvestedOnlyHhi:" in source
    assert "historicalVolatilityInterpretation:" in source


def test_risk_clarity_ui_distinguishes_cash_and_invested_exposure():
    source = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    assert source.count("Invested-only HHI (before / after)") == 1
    assert source.count("Cash-inclusive allocation HHI (not a risk measure)") == 1
    assert "It can fall when cash is invested even as stock-market volatility rises" in source


def test_private_research_remains_read_only_and_not_bundled_multiple_times():
    source = (ROOT / "web/site/private_allocation_v74.js").read_text(encoding="utf-8")
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    assert builder.count("private_allocation_v74.js") == 1
    assert "fetch(" not in source
    assert "private/trade" not in source
    assert "private/capital" not in source
    assert "localStorage" not in source


def test_v75_rejects_mixed_crypto_volatility_annualization():
    source = (ROOT / "web/site/private_allocation_v74.js").read_text(encoding="utf-8")
    assert "symbols.some(s=>s.includes('/'))" in source
    assert "365-session or mixed-calendar risk model" in source
