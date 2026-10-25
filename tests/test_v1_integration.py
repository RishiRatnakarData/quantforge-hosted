"""End-to-end development research and holdout defense."""

import json

import pandas as pd
import pytest

from quantforge.cli import main
from quantforge.data.simulation import simulated_market
from quantforge.research.study import run_v1_study


def test_v1_simulated_cli_writes_research_packet(tmp_path):
    output = tmp_path / "v1"
    assert main(["v1-demo", "--rows", "520", "--output", str(output)]) == 0
    expected = [
        "portfolio_paths.csv", "portfolio_metrics.csv", "portfolio_weights.csv",
        "risk_forecasts.csv", "risk_diagnostics.csv", "forecast_scoring.csv",
        "covariance.csv", "correlation.csv", "risk_dashboard.html",
        "data_audit.json", "manifest_v1.json", "RESEARCH_SUMMARY.md",
    ]
    for filename in expected:
        assert (output / filename).stat().st_size > 0
    manifest = json.loads((output / "manifest_v1.json").read_text())
    assert manifest["holdout_2019_to_2025"] == "excluded_unread"
    forecast = pd.read_csv(output / "risk_forecasts.csv")
    assert len(forecast) > 50
    assert (pd.to_datetime(forecast["training_end"]) < pd.to_datetime(forecast["date"])).all()


def test_v1_requires_source_attestation_before_external_analysis(tmp_path):
    prices = simulated_market(rows=550)
    prices["date"] = prices["date"] - pd.Timedelta(days=365)
    with pytest.raises(ValueError, match="source-manifest"):
        run_v1_study(prices, output=tmp_path, dataset="external_tiingo")
    assert not list(tmp_path.glob("*.csv"))


def test_v1_rejects_bad_external_source_attestation(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"provider": "unknown"}))
    prices = simulated_market(rows=550)
    with pytest.raises(ValueError, match="source manifest"):
        run_v1_study(prices, output=tmp_path, dataset="external_tiingo",
                     source_manifest=bad)
