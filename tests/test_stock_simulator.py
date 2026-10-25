"""Historical replay causality, fills, cash conservation, and source publication gates."""

from __future__ import annotations

import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from quantforge.simulator.marketdata import (
    create_replay_data,
    kaggle_archive_bars,
    synthetic_bars,
    validate_bars,
)
from quantforge.simulator.replay import replay_portfolio
from quantforge.simulator.website import build_stock_site


def test_deterministic_synthetic_and_validation():
    a = synthetic_bars(sessions=45, seed=17)
    b = synthetic_bars(sessions=45, seed=17)
    pd.testing.assert_frame_equal(a, b)
    assert set(a.symbol).issuperset({"SPY", "AAPL"})
    broken = a.copy()
    broken.loc[0, "close"] = -2
    with pytest.raises(ValueError, match="strictly positive"):
        validate_bars(broken)
    with pytest.raises(ValueError, match="Duplicate"):
        validate_bars(pd.concat([a, a.iloc[:1]]))


def test_orders_execute_next_open_with_fees_and_cash():
    dates = pd.bdate_range("2024-01-02", periods=12)
    rows = []
    for i, date in enumerate(dates):
        for ticker, base in (("AAPL", 100), ("SPY", 100)):
            rows.append({"date": date, "symbol": ticker, "open": base + i, "close": base + i + 0.5})
    bars = pd.DataFrame(rows)
    result = replay_portfolio(bars, budget=1000, fee_bps=10,
                              decisions=[{"date": dates[0], "weights": {"AAPL": 1.0}}])
    assert result["curve"][0]["portfolio"] == 1000  # No same-day trade
    assert result["trades"][0]["date"] == "2024-01-03"  # next open
    assert result["trades"][0]["execution_price"] == 101
    assert result["stats"]["ending_value"] > 1000
    assert result["stats"]["trade_count"] == 1
    assert result["trades"][0]["fee"] > 0


def test_cash_only_does_not_invent_risk():
    rows = synthetic_bars(sessions=35)
    first = rows.date.min()
    result = replay_portfolio(rows, decisions=[{"date": first, "weights": {"AAPL": 0}}])
    assert result["stats"]["total_return"] == 0
    assert result["stats"]["annualized_volatility"] == 0
    assert result["stats"]["trade_count"] == 0


def test_changes_in_future_prices_do_not_change_earlier_replay():
    bars = synthetic_bars(sessions=40, seed=18)
    at = bars.date.min()
    decisions = [{"date": at, "weights": {"AAPL": 0.6, "MSFT": 0.4}}]
    baseline = replay_portfolio(bars, decisions=decisions)
    altered = bars.copy()
    cut = sorted(altered.date.unique())[20]
    altered.loc[altered.date >= cut, "close"] *= 20
    changed = replay_portfolio(altered, decisions=decisions)
    assert baseline["curve"][:20] == changed["curve"][:20]


def test_rebalance_orders_are_chronological():
    bars = synthetic_bars(sessions=55)
    sessions = sorted(bars.date.unique())
    decisions = [
        {"date": sessions[0], "weights": {"AAPL": 0.5, "MSFT": 0.5}},
        {"date": sessions[20], "weights": {"AAPL": 0.2, "MSFT": 0.4}},
    ]
    result = replay_portfolio(bars, decisions=decisions, fee_bps=5)
    assert {r["date"] for r in result["trades"]}.issubset(
        {str(sessions[1].date()), str(sessions[21].date())}
    )
    assert all(np.isfinite(v["portfolio"]) and v["portfolio"] > 0 for v in result["curve"])
    with pytest.raises(ValueError, match="exceed"):
        replay_portfolio(bars, decisions=[{"date": sessions[0],
                                           "weights": {"AAPL": 0.7, "MSFT": 0.8}}])


def test_private_stock_csv_cannot_be_published(tmp_path):
    frame = synthetic_bars(sessions=45)
    create_replay_data(output=tmp_path / "inputs", frame=frame,
                       origin="user_supplied_local")
    with pytest.raises(ValueError, match="license|private|redistribution"):
        build_stock_site(stock_dir=tmp_path / "inputs", output=tmp_path / "site")
    result = build_stock_site(stock_dir=tmp_path / "inputs", output=tmp_path / "private",
                              local_only=True)
    assert result["observations"] == 45


def test_fingerprint_blocks_modified_data(tmp_path):
    create_replay_data(output=tmp_path / "inputs", frame=synthetic_bars(sessions=30),
                       origin="synthetic")
    file = tmp_path / "inputs" / "stock_bars.csv"
    file.write_bytes(file.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="fingerprint"):
        build_stock_site(stock_dir=tmp_path / "inputs", output=tmp_path / "site")


def test_site_demo_cannot_pretend_real_prices(tmp_path):
    create_replay_data(output=tmp_path / "inputs", frame=synthetic_bars(sessions=35),
                       origin="synthetic")
    result = build_stock_site(stock_dir=tmp_path / "inputs", output=tmp_path / "site")
    html = (tmp_path / "site" / "index.html").read_text()
    evidence = json.loads((tmp_path / "site" / "evidence.json").read_text())
    assert result["market_origin"] == "synthetic"
    assert "FICTIONAL" in html
    assert evidence["dataset_origin"] == "synthetic"
    assert "research paper" not in html.lower()


def test_import_cc0_zip_and_cutoff(tmp_path):
    dates = pd.bdate_range("2015-01-02", periods=125)
    with zipfile.ZipFile(tmp_path / "sample.zip", "w") as z:
        for folder, name in (("Stocks", "aapl"), ("ETFs", "spy")):
            csv = "Date,Open,High,Low,Close,Volume,OpenInt\n"
            csv += "".join(f"{d.date()},100,102,99,101,1000,0\n" for d in dates)
            z.writestr(f"archive/{folder}/{name}.us.txt", csv)
    frame = kaggle_archive_bars(tmp_path / "sample.zip", stocks=("AAPL",),
                                start="2015-01-02", end="2015-08-01")
    assert len(frame) == 250
    with pytest.raises(ValueError, match="ends 2017"):
        kaggle_archive_bars(tmp_path / "sample.zip", end="2025-01-01")
    with pytest.raises(ValueError, match="acknowledge"):
        create_replay_data(output=tmp_path / "unapproved", frame=frame,
                           origin="cc0_kaggle_2017")
    create_replay_data(output=tmp_path / "approved", frame=frame,
                       origin="cc0_kaggle_2017", source_path=tmp_path / "sample.zip",
                       approved_redistribution=True)
    build_stock_site(stock_dir=tmp_path / "approved", output=tmp_path / "public")
