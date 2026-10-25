"""V4 integration regressions: provenance, licensing, forecasts and valuation math."""

import json
from pathlib import Path

import pandas as pd
import pytest

from quantforge.data.simulation import simulated_market
from quantforge.financials.demo import synthetic_companyfacts
from quantforge.integration.v4 import EvidenceError, run_v4_integration
from quantforge.research.study import run_v1_study
from quantforge.research.v2 import run_v2_study
from quantforge.research.v3 import run_v3_study


@pytest.fixture(scope="module")
def source_bundle(tmp_path_factory):
    root = tmp_path_factory.mktemp("v4-bundle")
    prices = simulated_market(rows=520, seed=7)
    prices["symbol"] = prices["symbol"].replace({
        "SIM_ALPHA": "SPY", "SIM_BETA": "IWM", "SIM_GAMMA": "GLD", "SIM_DELTA": "TLT",
    })
    v1, v2, v3 = (root / name for name in ("v1", "v2", "v3"))
    run_v1_study(prices, output=v1, dataset="simulation")
    run_v2_study(v1_dir=v1, output=v2, mc_paths=250)
    v3.mkdir(parents=True)
    snapshot = v3 / "SYNTHETIC.json"
    snapshot.write_text(json.dumps(synthetic_companyfacts()), encoding="utf-8")
    run_v3_study(snapshot, as_of="2026-10-22", output=v3,
                 config_path=Path("configs/valuation_assumptions.json"),
                 origin="synthetic_demo")
    return root, v1, v2, v3


def test_v4_full_evidence_without_research_paper(source_bundle):
    root, v1, v2, v3 = source_bundle
    out = root / "final"
    results = run_v4_integration(v1_dir=v1, v2_dir=v2, v3_dir=v3, output=out)
    assert results["model_count"] == 7
    assert results["data_origins"] == ["simulation", "synthetic_demo"]
    expected = ["evidence_manifest.json", "integrated_dashboard.html", "INVESTMENT_MEMO.md", "capex_stress.json",
                "model_uncertainty.csv", "model_comparison.csv", "valuation_scenarios.csv"]
    assert all((out / p).stat().st_size > 100 for p in expected)
    assert not list(out.glob("RESEARCH_WORKING_PAPER*"))
    assert "SYNTHETIC" in (out / "integrated_dashboard.html").read_text(encoding="utf-8")
    manifest = json.loads((out / "evidence_manifest.json").read_text(encoding="utf-8"))
    assert manifest["market_data_origin"] == "simulation"
    assert manifest["holdout_2019_2025"] == "not_accessed"
    assert not list(out.rglob("*prices*"))
    assert all((out / "views" / name).stat().st_size > 100 for name in
               ("portfolio_risk.html", "advanced_models.html", "company_valuation.html"))
    stresses = json.loads((out / "capex_stress.json").read_text(encoding="utf-8"))
    assert stresses["intrinsic_value_per_share_usd"] < stresses["original_base_value_per_share_usd"]


def test_v4_refuses_tiingo_starter_results(source_bundle, tmp_path):
    _, v1, v2, v3 = source_bundle
    manifest_path = v1 / "manifest_v1.json"
    original = manifest_path.read_text(encoding="utf-8")
    try:
        value = json.loads(original)
        value["dataset"] = "external_tiingo"
        manifest_path.write_text(json.dumps(value), encoding="utf-8")
        with pytest.raises(EvidenceError, match="Tiingo"):
            run_v4_integration(v1_dir=v1, v2_dir=v2, v3_dir=v3, output=tmp_path / "fail")
    finally:
        manifest_path.write_text(original, encoding="utf-8")


def test_v4_refuses_bad_v2_linkage(source_bundle, tmp_path):
    _, v1, v2, v3 = source_bundle
    p = v2 / "manifest_v2.json"
    original = p.read_text(encoding="utf-8")
    try:
        obj = json.loads(original)
        obj["v1_manifest_sha256"] = "0" * 64
        p.write_text(json.dumps(obj), encoding="utf-8")
        with pytest.raises(EvidenceError, match="manifest"):
            run_v4_integration(v1_dir=v1, v2_dir=v2, v3_dir=v3, output=tmp_path / "bad")
    finally:
        p.write_text(original, encoding="utf-8")


def test_v4_refuses_future_lookahead(source_bundle, tmp_path):
    _, v1, v2, v3 = source_bundle
    path = v2 / "advanced_forecasts.csv"
    original = path.read_bytes()
    try:
        frame = pd.read_csv(path)
        frame.loc[0, "ml_fit_end"] = frame.loc[0, "date"]
        frame.to_csv(path, index=False)
        with pytest.raises(EvidenceError, match="Timing leakage"):
            run_v4_integration(v1_dir=v1, v2_dir=v2, v3_dir=v3, output=tmp_path / "bad")
    finally:
        path.write_bytes(original)


def test_v4_refuses_corrupt_dcf_identity(source_bundle, tmp_path):
    _, v1, v2, v3 = source_bundle
    path = v3 / "dcf_scenarios.csv"
    original = path.read_bytes()
    try:
        frame = pd.read_csv(path)
        frame.loc[0, "equity_value_usd_millions"] += 5000
        frame.to_csv(path, index=False)
        with pytest.raises(EvidenceError, match="DCF identity"):
            run_v4_integration(v1_dir=v1, v2_dir=v2, v3_dir=v3, output=tmp_path / "bad")
    finally:
        path.write_bytes(original)


def test_v4_refuses_source_output_collision(source_bundle):
    _, v1, v2, v3 = source_bundle
    with pytest.raises(EvidenceError, match="overwrite"):
        run_v4_integration(v1_dir=v1, v2_dir=v2, v3_dir=v3, output=v1)
