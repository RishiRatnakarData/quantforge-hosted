"""Unlevered five-year DCF with fully explicit scenario/WACC assumptions.

All currency values are in USD millions; share values in millions. No market
price is assumed. Outputs are sensitivity estimates, not trading advice.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CapitalCosts:
    risk_free_rate: float
    equity_risk_premium: float
    levered_beta: float
    pretax_cost_of_debt: float
    marginal_tax_rate: float
    assumed_debt_weight: float

    def validate(self) -> None:
        if not (0 <= self.assumed_debt_weight < 1):
            raise ValueError("Debt weight must be in [0,1)")
        for name in ("risk_free_rate", "equity_risk_premium", "pretax_cost_of_debt", "marginal_tax_rate"):
            if not 0 <= getattr(self, name) < 1:
                raise ValueError(f"Invalid capital cost input {name}")
        if not 0.1 <= self.levered_beta <= 5:
            raise ValueError("Beta outside permitted stress range")

    @property
    def equity_cost(self) -> float:
        return self.risk_free_rate + self.levered_beta * self.equity_risk_premium

    @property
    def wacc(self) -> float:
        self.validate()
        w_d = self.assumed_debt_weight
        return (1 - w_d) * self.equity_cost + w_d * self.pretax_cost_of_debt * (1 - self.marginal_tax_rate)


@dataclass(frozen=True)
class ForecastInputs:
    growth: tuple[float, ...]
    margin: tuple[float, ...]
    capex_ratio: tuple[float, ...]
    da_ratio: tuple[float, ...]
    cash_tax_rate: float
    operating_nwc_to_sales: float
    terminal_growth: float
    wacc_delta: float = 0.0

    def validate(self) -> None:
        if not len(self.growth) == len(self.margin) == len(self.capex_ratio) == len(self.da_ratio) == 5:
            raise ValueError("Exactly five growth/margin/capex/D&A assumptions required")
        if not all(-0.8 < x < 1.5 for x in self.growth):
            raise ValueError("Growth rate outside documented scenario bounds")
        if not all(0 <= x <= 1 for x in (*self.margin, *self.capex_ratio, *self.da_ratio)):
            raise ValueError("Margin, CapEx and D&A shares must be in [0,1]")
        if not 0 <= self.cash_tax_rate < 1:
            raise ValueError("Invalid forecast cash tax rate")
        if not -1 < self.operating_nwc_to_sales < 1:
            raise ValueError("Invalid NWC revenue ratio")
        if not -0.05 <= self.terminal_growth <= 0.06:
            raise ValueError("Terminal growth exceeds supported sensitivity bounds")



def forecast_unlevered_fcf(latest: pd.Series, assumptions: ForecastInputs) -> pd.DataFrame:
    """FCFF = EBIT*(1-T) + D&A - capex - delta operating NWC."""
    assumptions.validate()
    sales = float(latest["revenue"])
    nwc = float(latest["operating_nwc"])
    if not math.isfinite(sales) or sales <= 0 or not math.isfinite(nwc):
        raise ValueError("Forecast requires latest annual revenue and complete operating NWC")
    rows = []
    for year, (growth, margin, capex_share, da_share) in enumerate(
        zip(assumptions.growth, assumptions.margin, assumptions.capex_ratio, assumptions.da_ratio, strict=True), start=1
    ):
        prior_sales = sales
        sales *= 1 + growth
        ebit = sales * margin
        tax_on_operating_income = ebit * assumptions.cash_tax_rate
        da = sales * da_share
        capex = sales * capex_share
        projected_nwc = sales * assumptions.operating_nwc_to_sales
        delta_nwc = projected_nwc - nwc
        fcff = ebit - tax_on_operating_income + da - capex - delta_nwc
        rows.append({
            "forecast_year": year,
            "fiscal_year": int(latest["fiscal_year"]) + year,
            "revenue": sales, "revenue_growth": sales / prior_sales - 1,
            "operating_margin": margin, "ebit": ebit,
            "tax_on_ebit": tax_on_operating_income, "depreciation_amortization": da,
            "capex": capex, "operating_nwc": projected_nwc,
            "delta_nwc": delta_nwc, "unlevered_fcf": fcff,
        })
        nwc = projected_nwc
    return pd.DataFrame(rows)


def value_forecast(forecast: pd.DataFrame, *, discount_rate: float, terminal_growth: float,
                   net_debt: float, diluted_shares_millions: float) -> dict:
    """FCFF enterprise-to-equity reconciliation, discrete fiscal year-end timing."""
    if not 0 < discount_rate < 0.50 or terminal_growth >= discount_rate:
        raise ValueError("WACC must be positive, under 50%, and strictly above terminal growth")
    if diluted_shares_millions <= 0 or not math.isfinite(diluted_shares_millions):
        raise ValueError("Diluted share-count proxy must be positive")
    if not math.isfinite(net_debt):
        raise ValueError("Net debt is not finite")
    if list(forecast["forecast_year"]) != [1, 2, 3, 4, 5]:
        raise ValueError("Valuation requires exactly five annual forecasts")
    fcf = forecast["unlevered_fcf"].astype(float)
    if not all(math.isfinite(x) for x in fcf):
        raise ValueError("Forecast FCFF must be finite")
    pv_explicit = sum(float(v) / ((1 + discount_rate) ** year)
                      for year, v in enumerate(fcf, start=1))
    terminal_fcf = float(fcf.iloc[-1]) * (1 + terminal_growth)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth)
    pv_terminal = terminal_value / ((1 + discount_rate) ** 5)
    enterprise = pv_explicit + pv_terminal
    equity = enterprise - net_debt
    return {
        "wacc": discount_rate, "terminal_growth": terminal_growth,
        "pv_explicit_fcf_usd_millions": pv_explicit,
        "terminal_fcf_usd_millions": terminal_fcf,
        "terminal_value_usd_millions": terminal_value,
        "pv_terminal_usd_millions": pv_terminal,
        "enterprise_value_usd_millions": enterprise,
        "net_debt_usd_millions": net_debt,
        "equity_value_usd_millions": equity,
        "diluted_shares_millions_proxy": diluted_shares_millions,
        "intrinsic_value_per_share_usd": equity / diluted_shares_millions,
        "terminal_value_share_of_enterprise": pv_terminal / enterprise if enterprise else None,
    }


def run_valuation(financials: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Return forecasts, scenarios, WACC/g sensitivity, historical ratios, assumptions."""
    latest = financials.iloc[-1]
    capital = CapitalCosts(**config["cost_of_capital"])
    base_wacc = capital.wacc
    net_debt = float(latest["interest_bearing_debt"] - latest["cash_plus_short_term_investments"])
    shares = float(latest["diluted_shares"])
    forecasts, valuations = [], []
    for scenario, source in config["scenarios"].items():
        inputs = ForecastInputs(
            **{k: tuple(v) if k in ("growth", "margin", "capex_ratio", "da_ratio") else v
               for k, v in source.items()}
        )
        fc = forecast_unlevered_fcf(latest, inputs)
        fc.insert(0, "scenario", scenario)
        forecasts.append(fc)
        metrics = value_forecast(fc, discount_rate=base_wacc + inputs.wacc_delta,
                                 terminal_growth=inputs.terminal_growth,
                                 net_debt=net_debt, diluted_shares_millions=shares)
        valuations.append({"scenario": scenario, **metrics})
    if "base" not in config["scenarios"]:
        raise ValueError("Must provide a base scenario")
    base_forecast = next(f for f in forecasts if f["scenario"].iloc[0] == "base")
    base_growth = config["scenarios"]["base"]["terminal_growth"]
    sensitivity = []
    for delta in (-0.015, -0.01, -0.005, 0.0, 0.005, 0.01, 0.015):
        for terminal in (base_growth - 0.01, base_growth - 0.005, base_growth, base_growth + 0.005, base_growth + 0.01):
            wacc = base_wacc + delta
            if terminal >= wacc:
                continue
            score = value_forecast(base_forecast, discount_rate=wacc, terminal_growth=terminal,
                                   net_debt=net_debt, diluted_shares_millions=shares)
            sensitivity.append({"wacc": wacc, "terminal_growth": terminal,
                                "intrinsic_value_per_share_usd": score["intrinsic_value_per_share_usd"]})
    assumptions = {
        "valuation_method": "unlevered_fcff_terminal_gordon_growth",
        "cash_flow_timing": "discrete_fiscal_year_end",
        "cost_of_capital": {
            **config["cost_of_capital"],
            "cost_of_equity_capm": capital.equity_cost,
            "derived_wacc": base_wacc,
            "methodology_limit": "CAPM beta, equity premium, debt spread and financing mix are assumed, not market-estimated",
        },
        "net_debt_formula": "current_debt + noncurrent_debt - cash - short_term_investments",
        "diluted_shares_basis": "latest fiscal-year weighted-average diluted shares; proxy, NOT period-end outstanding",
        "reinvestment_formula": "EBIT*(1-cash_tax_rate) + D&A - CapEx - change_operating_NWC",
        "nwc_formula": "receivables + inventory - payables - customer_deferred_revenue",
        "scenario_drivers": config["scenarios"],
    }
    history_cols = ["fiscal_year", "revenue", "revenue_growth", "operating_income", "operating_margin", "gross_margin", "net_margin", "current_ratio", "operating_cash_conversion", "capex_intensity", "roic_approximation", "operating_cash_flow", "capex", "fcf_operating_minus_capex", "reported_effective_tax_rate", "operating_nwc", "balance_reconciliation_error"]
    return (pd.concat(forecasts, ignore_index=True), pd.DataFrame(valuations),
            pd.DataFrame(sensitivity), financials[history_cols].copy(), assumptions)
