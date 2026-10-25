import json
import sqlite3

import pandas as pd

from quantforge.cli import main
from quantforge.data.simulation import simulated_market


def test_simulation_is_deterministic_and_labeled():
    a = simulated_market(60, seed=42)
    b = simulated_market(60, seed=42)
    pd.testing.assert_frame_equal(a, b)
    assert a["symbol"].str.startswith("SIM_").all()


def test_end_to_end_offline_cli(tmp_path):
    destination = tmp_path / "results"
    result = main(["demo", "--rows", "160", "--lookback", "40", "--output", str(destination)])
    assert result == 0
    summary = json.loads((destination / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    assert summary["dataset_type"] == "simulation"
    assert summary["evaluation_dates"] == 119
    assert "simulat" in summary["disclaimer"].lower()
    assert manifest["no_interpolation"] is True
    for name in (
        "prices.csv", "returns.csv", "risk_forecasts.csv", "risk_coverage.csv",
        "portfolio_paths.csv", "portfolio_comparison.csv", "research_dashboard.html",
        "quantforge.sqlite",
    ):
        assert (destination / name).stat().st_size > 100
    with sqlite3.connect(destination / "quantforge.sqlite") as db:
        assert db.execute("SELECT COUNT(*) FROM market_returns").fetchone()[0] == 159 * 4


def test_ingest_csv_records_vendor_and_hash(tmp_path):
    source = tmp_path / "toy.csv"
    simulated_market(70).to_csv(source, index=False)
    destination = tmp_path / "out"
    assert main([
        "ingest-csv", "--path", str(source), "--vendor", "Toy test fixture",
        "--basis", "dividend_adjusted_close", "--lookback", "25", "--output", str(destination),
    ]) == 0
    manifest = json.loads((destination / "manifest.json").read_text())
    assert manifest["vendor"] == "Toy test fixture"
    assert len(manifest["original_input_sha256"]) == 64
