"""SEC-sourced statement, DCF, dashboard and memo, with testable provenance."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd
from plotly import graph_objects as go
from plotly.subplots import make_subplots

from quantforge.data.storage import write_json
from quantforge.financials.annual import annual_financials, input_sha256, verify_financials
from quantforge.valuation.dcf import run_valuation


def _n(value: float) -> str:
    return f"{value:,.1f}"


def write_dashboard(
    annual: pd.DataFrame, forecast: pd.DataFrame, scenarios: pd.DataFrame,
    sensitivity: pd.DataFrame, target: Path, *, label: str,
) -> None:
    """Two research panels; used for synthetic and live SEC runs."""
    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=("Historical financials (USD millions)",
                                        "Base-case unlevered free cash flow",
                                        "Scenario intrinsic values (USD/share)",
                                        "DCF sensitivity (USD/share)"))
    for metric, name in (("revenue", "Revenue"), ("operating_income", "Operating income"),
                         ("operating_cash_flow", "Operating cash flow"), ("capex", "CapEx")):
        fig.add_trace(go.Scatter(x=annual["fiscal_year"], y=annual[metric],
                                 name=name, mode="lines+markers"), row=1, col=1)
    base = forecast[forecast["scenario"] == "base"]
    fig.add_trace(go.Bar(x=base["fiscal_year"], y=base["unlevered_fcf"],
                         name="Base-case FCFF"), row=1, col=2)
    fig.add_trace(go.Bar(x=scenarios["scenario"], y=scenarios["intrinsic_value_per_share_usd"],
                         name="Scenario/share"), row=2, col=1)
    surface = sensitivity.pivot(index="terminal_growth", columns="wacc",
                                values="intrinsic_value_per_share_usd").sort_index()
    fig.add_trace(go.Heatmap(z=surface.to_numpy(), x=[round(x * 100, 2) for x in surface.columns],
                             y=[round(x * 100, 2) for x in surface.index],
                             colorscale="Blues", name="DCF sensitivity", colorbar={"title": "USD/share"}), row=2, col=2)
    fig.update_layout(title=f"QuantForge V3 | {label}", height=850,
                      template="plotly_white", barmode="group",
                      legend={"orientation": "h", "y": -0.12},
                      margin={"t": 95, "b": 115})
    fig.update_xaxes(title_text="WACC (%)", row=2, col=2)
    fig.update_yaxes(title_text="Terminal growth (%)", row=2, col=2)
    target.write_text(fig.to_html(full_html=True, include_plotlyjs=True), encoding="utf-8")


def write_investment_memo(annual: pd.DataFrame, scenarios: pd.DataFrame, assumptions: dict,
                          audit: dict, *, output: Path, label: str, as_of: str,
                          source_file: str, source_hash: str) -> None:
    latest = annual.iloc[-1]
    base = scenarios.set_index("scenario").loc["base"]
    scenario_rows = "\n".join(
        f"| {str(r['scenario']).title()} | {_n(float(r['wacc']) * 100)}% | "
        f"{_n(float(r['terminal_growth']) * 100)}% | "
        f"${_n(float(r['enterprise_value_usd_millions']))}m | "
        f"${_n(float(r['intrinsic_value_per_share_usd']))} |"
        for _, r in scenarios.iterrows()
    )
    memo = f"""# QuantForge V3 — Microsoft Financial Analysis & DCF Research Memo

**Data designation:** {label}  
**Valuation information cutoff:** {as_of}  
**Source snapshot:** `{source_file}`  
**Source SHA-256:** `{source_hash}`  
**Financial unit:** USD millions unless noted; share count in millions.

## Executive assessment

The **base-case estimated intrinsic value is ${_n(float(base['intrinsic_value_per_share_usd']))} per share**, derived from explicitly assumed operating drivers, capital costs, and terminal growth. It is **not a target price, consensus estimate, or investment recommendation**. No live market price is included; therefore **no upside/downside or buy/sell call can be inferred**.

## Reported financial position and operating drivers

Latest included fiscal year: **{int(latest['fiscal_year'])}**, year ending {latest['fiscal_end']}. Fiscal year-end June 30. Most recent annual revenue **${_n(float(latest['revenue']))}m**, operating profit **${_n(float(latest['operating_income']))}m** (margin **{_n(float(latest['operating_margin']) * 100)}%**), gross profit margin **{_n(float(latest['gross_margin']) * 100)}%**, current ratio **{_n(float(latest['current_ratio']))}x**, and illustrative ROIC proxy **{_n(float(latest['roic_approximation']) * 100)}%**. Operating cash flow **${_n(float(latest['operating_cash_flow']))}m**, and reported cash purchases of PP&E **${_n(float(latest['capex']))}m**. These are drawn from the snapshot and individually attributed in `sec_fact_audit.csv`; check the underlying filing, tag definitions, and adjusted representations.

Balance reconciliation: assets minus liabilities minus stockholders' equity = **${_n(float(latest['balance_reconciliation_error']))}m**. Audit gate: `{audit['status']}`. An automatic balance identity check is not equivalent to reviewing the original consolidated statements.

Cash and short-term investments: **${_n(float(latest['cash_plus_short_term_investments']))}m**. Interest-bearing current plus noncurrent debt: **${_n(float(latest['interest_bearing_debt']))}m**. Net debt, defined as debt less cash/investments, **${_n(float(base['net_debt_usd_millions']))}m**. The denominator for per-share value is **{_n(float(latest['diluted_shares']))} million weighted-average diluted shares** from the latest fiscal year. This is only a proxy for valuation-date diluted shares outstanding.

## DCF methodology and assumptions

Forecast five annual periods of unlevered free cash flow: EBIT × (1 – scenario tax assumption) + forecast D&A – forecast cash CapEx – change in operating net working capital. Forecast drivers for each scenario are preserved in `valuation_assumptions.json`. The operating-NWC definition is receivables plus inventory minus trade payables and customer deferred revenue; it excludes cash and financing debt.

The SEC historical D&A field may be unavailable because the statement groups "depreciation, amortization, and other." In that case the historical D&A cell stays missing, while scenario D&A remains a separately disclosed modeling assumption rather than a fabricated SEC figure.

Historical ratios and the ROIC proxy are analytical derivations and are not company-provided non-GAAP guidance. ROIC uses NOPAT based on the reported effective tax rate and an ending-balance capital proxy rather than average invested capital. Any missing standardized SEC concept blocks the complete valuation rather than being interpreted as zero.

The CAPM cost of equity uses **assumed**, not independently market-estimated, beta, risk-free yield and equity risk premium. The capital weights are an explicit assumption; no live market capitalization is reverse-engineered. The base WACC is **{_n(float(base['wacc'])*100)}%**, base terminal perpetual growth **{_n(float(base['terminal_growth'])*100)}%**. A discounted Gordon-growth terminal value is added to explicit projected cash flows. Net debt is subtracted from enterprise value to obtain equity value; no additional non-operating investments, minority interest or equity-linked adjustments are included.

## Scenario valuation

| Case | WACC | Terminal growth | Enterprise value (USD m) | Intrinsic value/share |
|---|---:|---:|---:|---:|
{scenario_rows}

The base model's terminal value represents **{_n(float(base['terminal_value_share_of_enterprise'])*100)}%** of enterprise value. High terminal dependence increases uncertainty. The WACC-by-growth sensitivity table, `dcf_sensitivity.csv`, quantifies these assumptions.

## Principal risks and interpretation

This model is materially sensitive to cloud and AI infrastructure capital intensity, top-line growth, margins, marginal tax assumptions, share count, the cost of capital, and terminal growth. CapEx is modeled as an **outflow**, and D&A as a noncash **add-back**. Negative changes in operating working capital are cash inflows under the stated convention. Revenue growth, annual capex intensity and the capital structure are **assumptions** rather than management guidance.

This is a **single-company fundamental valuation module**, separate from the historical eight-ETF VaR research. No 2019–2025 portfolio risk holdout is accessed. The historical SEC inputs are selected as of the stated filing-date cutoff, but latest-as-of comparative facts may include restatements and are not a historical point-in-time backtest.

## Reproduction and limitations

Reproduce the output from the saved SEC companyfacts snapshot and the versioned assumptions file. Verify the original SEC filing line items, the treatment of D&A, noncash adjustments, leases and non-operating investments, the fiscal end share count, and any effects of later reporting changes. Financial-statement values are not normalized for one-time gains, accounting changes, or capital expenditure commitments. Neither scenario probabilities nor a quoted share price are provided. This document is an analyst-generated valuation exercise, **not a professional securities recommendation or externally reviewed investment report**.
"""
    output.write_text(memo, encoding="utf-8")


def run_v3_study(snapshot: Path, *, as_of: str, output: Path, config_path: Path,
                 origin: str = "sec_companyfacts") -> dict:
    """One auditable SEC→statements→forecasts→DCF→report pipeline."""
    dt.date.fromisoformat(as_of)
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    if origin != "synthetic_demo" and "SYNTHETIC" in str(payload.get("entityName", "")).upper():
        raise ValueError("Cannot relabel synthetic Company Facts as real SEC evidence")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    financials, fact_audit = annual_financials(payload, as_of=as_of)
    output.mkdir(parents=True, exist_ok=True)
    # Preserve the forensic records even when a real SEC concept is unavailable
    # and the strict valuation gate refuses to complete.
    financials.to_csv(output / "sec_financials.csv", index=False, float_format="%.12g")
    fact_audit.to_csv(output / "sec_fact_audit.csv", index=False, float_format="%.12g")
    audit = verify_financials(financials, as_of=as_of)
    forecast, scenarios, sensitivity, historical, assumptions = run_valuation(financials, config)
    for name, frame in (
        ("sec_financials.csv", financials), ("sec_fact_audit.csv", fact_audit),
        ("historical_fundamentals.csv", historical), ("forecast_drivers.csv", forecast),
        ("dcf_scenarios.csv", scenarios), ("dcf_sensitivity.csv", sensitivity),
    ):
        frame.to_csv(output / name, index=False, float_format="%.12g")
    output.joinpath("valuation_assumptions.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    write_json(output / "financial_statement_audit.json", audit)
    label = ("SYNTHETIC TEST FIXTURE — NOT REAL MICROSOFT DATA" if origin == "synthetic_demo"
             else "SEC COMPANY FACTS — FILED-BY CUTOFF")
    source_hash = input_sha256(snapshot)
    write_dashboard(financials, forecast, scenarios, sensitivity,
                    output / "valuation_dashboard.html", label=label)
    write_investment_memo(financials, scenarios, assumptions, audit,
                          output=output / "INVESTMENT_MEMO.md", label=label, as_of=as_of,
                          source_file=snapshot.name, source_hash=source_hash)
    manifest = {
        "project": "QuantForge", "release": "3.0.0", "data_origin": origin,
        "as_of": as_of, "company": "Microsoft Corporation" if origin != "synthetic_demo" else "SYNTHETIC TEST DATA",
        "cik": "0000789019", "fiscal_year_end": "06-30", "source_url": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json",
        "source_file": str(snapshot), "source_sha256": source_hash,
        "selected_financial_years": financials["fiscal_year"].astype(int).tolist(),
        "data_contract": audit, "assumption_file": "valuation_assumptions.json",
        "valuation_basis": assumptions, "research_qualification": (
            "Fictional accounting fixture; no empirical valuation claims" if origin == "synthetic_demo"
            else "Public SEC fact extraction with modeled valuation; independent disclosure-line audit pending"
        ),
        "portfolio_2019_2025_holdout_accessed": False,
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
    }
    write_json(output / "manifest_v3.json", manifest)
    return {"output": str(output.resolve()), "fiscal_year": audit["latest_fiscal_year"],
            "scenarios": len(scenarios), "data_origin": origin}
