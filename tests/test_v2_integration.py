"""Complete V1 -> V2 demo and validation against adversarial manifests."""

import json

import pandas as pd
import pytest

from quantforge.cli import main
from quantforge.research.v2 import _load_v1, run_v2_study


@pytest.fixture(scope="module")
def baseline_folder(tmp_path_factory):
    base = tmp_path_factory.mktemp("v2") / "sim"
    assert main(["v1-demo", "--rows", "520", "--output", str(base)]) == 0
    return base


def test_v2_simulated_study_creates_all_evidence(baseline_folder, tmp_path):
    result = run_v2_study(v1_dir=baseline_folder, output=tmp_path / "v2", mc_paths=2000)
    assert result["dataset"] == "simulation"
    assert result["evaluation_dates"] > 50
    for filename in ["advanced_forecasts.csv", "forecast_model_scores.csv",
                     "var_coverage_comparison.csv", "option_sensitivity.csv",
                     "option_model_validation.json", "portfolio_monte_carlo.json",
                     "advanced_dashboard.html", "V2_RESEARCH_REPORT.md", "manifest_v2.json"]:
        assert (tmp_path / "v2" / filename).stat().st_size > 50
    forecasts = pd.read_csv(tmp_path / "v2" / "advanced_forecasts.csv", parse_dates=["date"])
    assert len(forecasts) == result["evaluation_dates"]
    for col in ("ml_fit_end", "feature_training_end", "model_fit_end", "filter_training_end"):
        assert (pd.to_datetime(forecasts[col]) < forecasts["date"]).all()
    manifest = json.loads((tmp_path / "v2" / "manifest_v2.json").read_text())
    assert manifest["holdout_2019_to_2025"] == "excluded_unread"


def test_v2_rejects_future_holdout_tampering(baseline_folder, tmp_path):
    new = tmp_path / "tampered"
    new.mkdir()
    for filename in ["portfolio_paths.csv", "risk_forecasts.csv", "manifest_v1.json", "data_audit.json"]:
        (new / filename).write_bytes((baseline_folder / filename).read_bytes())
    paths = pd.read_csv(new / "portfolio_paths.csv")
    paths["date"] = "2024-01-01"
    paths.to_csv(new / "portfolio_paths.csv", index=False)
    data = json.loads((new / "manifest_v1.json").read_text())
    data["dataset"] = "external_tiingo"
    data["research_window"] = "development_through_2018_only"
    (new / "manifest_v1.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="holdout|incomplete|reconcile|Invalid"):
        _load_v1(new)


def test_v2_rejects_modified_baseline_target(baseline_folder, tmp_path):
    new = tmp_path / "target"
    new.mkdir()
    for filename in ["portfolio_paths.csv", "risk_forecasts.csv", "manifest_v1.json", "data_audit.json"]:
        (new / filename).write_bytes((baseline_folder / filename).read_bytes())
    frame = pd.read_csv(new / "risk_forecasts.csv")
    frame.loc[0, "realized_return"] = 2.0
    frame.to_csv(new / "risk_forecasts.csv", index=False)
    with pytest.raises(ValueError, match="reconcile"):
        _load_v1(new)


def test_missing_v1_inputs_refuse_to_create_report(tmp_path):
    out = tmp_path / "report"
    with pytest.raises(ValueError, match="Complete V1"):
        run_v2_study(v1_dir=tmp_path / "missing", output=out)
    assert not out.exists()
