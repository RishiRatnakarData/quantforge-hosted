"""V3 time integrity, numerical DCF identities and negative cases."""

import json

import numpy as np
import pytest

from quantforge.financials.annual import annual_financials, verify_financials
from quantforge.financials.demo import synthetic_companyfacts
from quantforge.valuation.dcf import (
    CapitalCosts,
    ForecastInputs,
    forecast_unlevered_fcf,
    run_valuation,
    value_forecast,
)


@pytest.fixture
def source():
    return synthetic_companyfacts()


@pytest.fixture
def frame(source):
    return annual_financials(source, as_of="2026-10-22")[0]


@pytest.fixture
def config():
    with open("configs/valuation_assumptions.json", encoding="utf-8") as f:
        return json.load(f)


def test_as_of_rejects_not_yet_filed_year(source):
    early, audit = annual_financials(source, as_of="2025-07-20")
    assert 2026 not in early.fiscal_year.tolist()
    assert all(audit.filed.dropna().le("2025-07-20"))
    assert early.fiscal_year.max() == 2024


def test_as_of_permitted_in_after_filing(source):
    frame, audit = annual_financials(source, as_of="2026-08-15")
    assert frame.fiscal_year.max() == 2026
    assert set(audit[audit.status == "selected"].accession) == {
        f"FAKE-DEMO-{y}" for y in (2023, 2024, 2025, 2026)
    }


def test_no_quarterly_duration_mistaken_for_annual(source):
    tag = "RevenueFromContractWithCustomerExcludingAssessedTax"
    source["facts"]["us-gaap"][tag]["units"]["USD"].append({
        "start": "2026-04-01", "end": "2026-06-30", "filed": "2026-09-01",
        "form": "10-K", "accn": "TEST_BAD_QUARTER", "val": 9_999_999_999_999,
    })
    frame, _ = annual_financials(source, as_of="2026-10-22")
    assert frame.iloc[-1].revenue == 280_000


def test_restated_value_used_only_if_filed_before_as_of(source):
    tag = "OperatingIncomeLoss"
    source["facts"]["us-gaap"][tag]["units"]["USD"].append({
        "start": "2025-07-01", "end": "2026-06-30", "filed": "2026-11-01",
        "form": "10-K/A", "accn": "LATER_AMENDMENT", "val": 132_000_000_000,
    })
    early, _ = annual_financials(source, as_of="2026-10-22")
    late, audit = annual_financials(source, as_of="2026-11-02")
    assert early.iloc[-1].operating_income == 125_000
    assert late.iloc[-1].operating_income == 132_000
    assert audit[(audit.fiscal_year == 2026) & (audit.metric == "operating_income")].iloc[0].accession == "LATER_AMENDMENT"


def test_units_rejects_lookalike_metric(source):
    tag = "PaymentsToAcquirePropertyPlantAndEquipment"
    source["facts"]["us-gaap"][tag]["units"] = {"shares": source["facts"]["us-gaap"][tag]["units"]["USD"]}
    frame, _ = annual_financials(source, as_of="2026-10-22")
    with pytest.raises(ValueError, match="capex"):
        verify_financials(frame, as_of="2026-10-22")


def test_balance_identity_and_valuation_gate(frame):
    audit = verify_financials(frame, as_of="2026-10-22")
    assert audit["latest_reconciliation_error_usd_millions"] == 0
    bad = frame.copy()
    bad.loc[bad.index[-1], "liabilities"] += 25_000
    bad.loc[bad.index[-1], "balance_reconciliation_error"] -= 25_000
    with pytest.raises(ValueError, match="reconcile"):
        verify_financials(bad, as_of="2026-10-22")


def test_fcff_accounting_identity(frame, config):
    base = ForecastInputs(**{k: tuple(v) if isinstance(v, list) else v
                             for k, v in config["scenarios"]["base"].items()})
    fc = forecast_unlevered_fcf(frame.iloc[-1], base)
    assert len(fc) == 5
    assert np.allclose(fc["unlevered_fcf"], fc["ebit"] - fc["tax_on_ebit"]
                       + fc["depreciation_amortization"] - fc["capex"] - fc["delta_nwc"])
    assert np.isclose(fc.iloc[0].delta_nwc,
                      fc.iloc[0].operating_nwc - frame.iloc[-1].operating_nwc)


def test_capex_and_nwc_direction(frame, config):
    data = config["scenarios"]["base"]
    args = {k: tuple(v) if isinstance(v, list) else v for k, v in data.items()}
    base = ForecastInputs(**args)
    higher_capex = ForecastInputs(**{**args, "capex_ratio": tuple(x + .05 for x in base.capex_ratio)})
    a = forecast_unlevered_fcf(frame.iloc[-1], base)
    b = forecast_unlevered_fcf(frame.iloc[-1], higher_capex)
    assert (b.unlevered_fcf < a.unlevered_fcf).all()


def test_wacc_weights_and_terminal_constraints(frame, config):
    capital = CapitalCosts(**config["cost_of_capital"])
    assert 0.05 < capital.wacc < 0.2
    fc, scenarios, sensitivity, _, _ = run_valuation(frame, config)
    assert len(fc) == 15 and len(scenarios) == 3
    assert len(sensitivity) == 35
    assert set(scenarios.scenario) == {"bear", "base", "bull"}
    for r in scenarios.itertuples(index=False):
        assert np.isclose(r.enterprise_value_usd_millions - r.net_debt_usd_millions,
                          r.equity_value_usd_millions)
        assert np.isclose(r.equity_value_usd_millions / r.diluted_shares_millions_proxy,
                          r.intrinsic_value_per_share_usd)
    with pytest.raises(ValueError, match="WACC"):
        value_forecast(fc[fc.scenario == "base"], discount_rate=0.03,
                       terminal_growth=0.03, net_debt=0, diluted_shares_millions=7400)


def test_cost_of_capital_sensitivity(frame, config):
    _, scenarios, _, _, _ = run_valuation(frame, config)
    base = scenarios.set_index("scenario").loc["base"]
    assert np.isfinite(base.intrinsic_value_per_share_usd)
    assert base.terminal_value_share_of_enterprise < 1


def test_invalid_share_count(frame, config):
    bad = frame.copy()
    bad.loc[bad.index[-1], "diluted_shares"] = 0
    with pytest.raises(ValueError, match="diluted_shares"):
        verify_financials(bad, as_of="2026-10-22")


def test_snapshot_is_not_actual_sec_filing(source):
    assert "SYNTHETIC" in source["entityName"]
    assert all("FAKE" in x["accn"] for group in source["facts"]["us-gaap"].values()
               for arr in group["units"].values() for x in arr)
