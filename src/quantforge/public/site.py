"""Generate a static recruiter site from audited, origin-labeled evidence."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from quantforge.data.storage import sha256_file
from quantforge.integration.v4 import _sustained_capex

from .ecb import CURRENCIES


def _json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Missing or malformed evidence file: {path.name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Evidence JSON must be an object: {path.name}")
    return value


def _company_evidence(sec_dir: Path | None) -> dict | None:
    if sec_dir is None:
        return None
    sec_dir = Path(sec_dir)
    manifest = _json(sec_dir / "manifest_v3.json")
    audit = _json(sec_dir / "financial_statement_audit.json")
    if manifest.get("data_origin") != "sec_companyfacts":
        raise ValueError("Public SEC page refuses synthetic or unknown company statements")
    if audit.get("status") != "latest_year_complete_and_balance_reconciled":
        raise ValueError("Latest SEC fiscal year did not pass internal accounting reconciliation")
    rows = pd.read_csv(sec_dir / "dcf_scenarios.csv")
    drivers = pd.read_csv(sec_dir / "forecast_drivers.csv")
    if set(rows["scenario"]) != {"bear", "base", "bull"}:
        raise ValueError("Must supply three audited DCF scenario rows")
    for r in rows.to_dict("records"):
        ev = float(r["pv_explicit_fcf_usd_millions"]) + float(r["pv_terminal_usd_millions"])
        eq = ev - float(r["net_debt_usd_millions"])
        val = eq / float(r["diluted_shares_millions_proxy"])
        if (not np.isclose(ev, r["enterprise_value_usd_millions"], rtol=1e-8)
                or not np.isclose(eq, r["equity_value_usd_millions"], rtol=1e-8)
                or not np.isclose(val, r["intrinsic_value_per_share_usd"], rtol=1e-8)
                or r["wacc"] <= r["terminal_growth"]):
            raise ValueError("SEC DCF scenarios do not reconcile")
    for r in drivers.to_dict("records"):
        fcf = (r["ebit"] - r["tax_on_ebit"] + r["depreciation_amortization"]
               - r["capex"] - r["delta_nwc"])
        if not np.isclose(fcf, r["unlevered_fcf"], rtol=1e-8, atol=1e-5):
            raise ValueError("SEC cash-flow forecast does not reconcile")
    stress = _sustained_capex(drivers, rows)
    return {"origin": "sec_companyfacts", "as_of": manifest["as_of"],
            "fiscal_year": int(audit["latest_fiscal_year"]),
            "scenarios": [{"scenario": r["scenario"],
                           "intrinsic_value_per_share_usd": float(r["intrinsic_value_per_share_usd"]),
                           "wacc": float(r["wacc"]),
                           "terminal_growth": float(r["terminal_growth"])}
                          for r in rows.to_dict("records")],
            "stress": stress, "financial_audit": "balance_identity_only_original_10k_review_pending"}


def build_public_site(*, fx_dir: Path, output: Path, sec_dir: Path | None = None) -> dict:
    """Write a complete static website. Reject unknown datasets and changed evidence."""
    fx_dir, output = Path(fx_dir), Path(output)
    manifest = _json(fx_dir / "fx_manifest.json")
    origin = manifest.get("data_origin")
    if origin not in {"ecb_reference_fx", "synthetic_fx_fixture"}:
        raise ValueError("Tiingo or unattributed data must never enter the public website")
    panel_path = fx_dir / "observed_fx_quotes.csv"
    if sha256_file(panel_path) != manifest.get("quote_sha256"):
        raise ValueError("Observed quote file has changed since the audit manifest was generated")
    panel = pd.read_csv(panel_path, parse_dates=["date"]).set_index("date")
    if list(panel.columns) != list(CURRENCIES):
        raise ValueError("Unexpected currencies in observed quote evidence")
    if len(panel) != manifest.get("observed_quote_days"):
        raise ValueError("Quote observation count is inconsistent with manifest")
    if origin == "ecb_reference_fx":
        raw = fx_dir / "ecb_original_source.csv"
        if not raw.is_file() or sha256_file(raw) != manifest["source_sha256"]:
            raise ValueError("ECB raw-source fingerprint missing or invalid")
    cover = pd.read_csv(fx_dir / "fx_coverage.csv")
    if cover.empty or set(cover["currency"]) != set(CURRENCIES):
        raise ValueError("Insufficient currency VaR evaluation evidence")
    company = _company_evidence(sec_dir)
    market = {"origin": origin, "days": int(len(panel)),
              "first": str(panel.index.min().date()), "last": str(panel.index.max().date()),
              "advanced": bool(manifest["advanced_usd_models"]),
              "summary": manifest["latest_summary"],
              "coverage": cover.replace({np.nan: None}).to_dict("records"),
              "source_sha": manifest.get("source_sha256"),
              "series": {currency: [[str(date.date()), round(float(value), 7)]
                                    for date, value in panel[currency].items()]
                         for currency in CURRENCIES}}
    data = {"market": market, "valuation": company}
    html = (Path(__file__).with_name("template.html")
            .read_text(encoding="utf-8")
            .replace("__DATA_PLACEHOLDER__", json.dumps(data, allow_nan=False,
                        separators=(",", ":")).replace("<", "\\u003c")))
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(html, encoding="utf-8")
    evidence = {"project": "QuantForge", "release": "4.1.0",
                "market": {key: manifest[key] for key in ("data_origin", "source_url",
                         "source_sha256", "quote_sha256", "sample_start", "sample_end",
                         "observed_quote_days", "return_definition", "sample_type",
                         "historical_etf_holdout_2019_2025")},
                "sec": {"origin": "sec_companyfacts", "as_of": company["as_of"],
                        "financial_audit": company["financial_audit"]} if company else None,
                "publication": ("ECB reference-rate analytics" if origin == "ecb_reference_fx"
                                else "SYNTHETIC DATA ONLY NOT EMPIRICAL RESULTS"),
                "disclaimer": "No licensed Tiingo Starter data or derived output used"}
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    (output / "fx_coverage.csv").write_bytes((fx_dir / "fx_coverage.csv").read_bytes())
    text = ("# QuantForge — Portfolio Case Study\n\n"
            "**Live artifact:** open `index.html`; inspect `evidence.json` and `fx_coverage.csv`.\n\n"
            "## Problem\nFinancial decisions require risk models that can be checked on observed data, "
            "not simply fitted to attractive backtests.\n\n"
            "## Data and reproducibility\n"
            f"FX origin: `{origin}`, {len(panel):,} observed dates. "
            "The ECB supplies euro reference rates, not executable trading quotes; no weekends are filled. "
            "`public-ecb` downloads unchanged official data, and unit/integration tests check pipeline behavior.\n\n"
            "## Findings\nSee the dashboard's *Risk Models* page for actual sample exception rates. "
            "Models are development/exploratory comparators, not guaranteed trading strategies.\n\n"
            "## Financial valuation\n"
            + ("Real Microsoft SEC facts drive three hypothetical DCF scenarios. "
               "The 35% sustained-CapEx sensitivity illustrates valuation uncertainty.\n\n"
               if company else "SEC company facts are not included in this site build.\n\n")
            + "## Scope and limitations\nNo research paper is required. No ETF holdout results are used. "
            "Market exchange-rate changes are not instrument total returns; results omit spreads, "
            "funding and transaction costs. Valuation is not investment advice.\n")
    (output / "CASE_STUDY.md").write_text(text, encoding="utf-8")
    return {"site": str((output / "index.html").resolve()),
            "origin": origin, "observations": len(panel),
            "sec_integrated": bool(company)}
