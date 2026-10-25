"""Read a *verified SEC* V3 valuation; never replace missing facts with fiction."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from quantforge.desk.engine import DeskError


def load_sec_valuation(directory: Path | None) -> dict:
    if directory is None:
        return {"status": "not_attached", "message": "Attach your real V3 SEC output with --sec-dir."}
    root = Path(directory)
    try:
        manifest = json.loads((root / "manifest_v3.json").read_text(encoding="utf-8"))
        audit = json.loads((root / "financial_statement_audit.json").read_text(encoding="utf-8"))
        with (root / "dcf_scenarios.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        raise DeskError("SEC valuation input is missing or unreadable; no figures were substituted.") from exc
    if manifest.get("data_origin") != "sec_companyfacts":
        raise DeskError("Only real, SEC-attributed V3 valuation results may appear here.")
    if audit.get("status") != "latest_year_complete_and_balance_reconciled":
        raise DeskError("The SEC reconciliation audit is not complete.")
    if len(rows) != 3 or {row.get("scenario") for row in rows} != {"bear", "base", "bull"}:
        raise DeskError("Expected one each of the bear, base, and bull scenarios.")
    values = []
    try:
        for row in rows:
            wacc = float(row["wacc"])
            growth = float(row["terminal_growth"])
            shares = float(row["diluted_shares_millions_proxy"])
            enterprise = float(row["enterprise_value_usd_millions"])
            equity = float(row["equity_value_usd_millions"])
            explicit = float(row["pv_explicit_fcf_usd_millions"])
            terminal = float(row["pv_terminal_usd_millions"])
            net_debt = float(row["net_debt_usd_millions"])
            per_share = float(row["intrinsic_value_per_share_usd"])
            nums = (wacc, growth, shares, enterprise, equity, explicit, terminal, net_debt, per_share)
            if not all(math.isfinite(n) for n in nums) or shares <= 0 or growth >= wacc:
                raise ValueError("nonfinite or invalid parameters")
            if not math.isclose(enterprise, explicit + terminal, rel_tol=1e-8, abs_tol=0.1):
                raise ValueError("enterprise value reconciliation")
            if not math.isclose(equity, enterprise - net_debt, rel_tol=1e-8, abs_tol=0.1):
                raise ValueError("equity value reconciliation")
            if not math.isclose(per_share, equity / shares, rel_tol=1e-8, abs_tol=.0001):
                raise ValueError("per-share reconciliation")
            values.append({"scenario": row["scenario"], "wacc": wacc,
                           "terminal_growth": growth, "intrinsic_value_per_share_usd": per_share,
                           "terminal_share_pct": round(100 * terminal / enterprise, 1)})
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        raise DeskError("DCF scenario values failed independent numerical reconciliation.") from exc
    return {"status": "verified_calculation_not_investment_recommendation",
            "company": "Microsoft Corporation", "ticker": "MSFT",
            "fiscal_year": audit["latest_fiscal_year"],
            "as_of": manifest.get("as_of") or "See V3 source manifest",
            "scenarios": values,
            "limitation": "DCF scenarios use illustrative assumptions, not consensus. Original filing-level cross-review is still required.",
            "cross_filing_review": audit.get("cross_filing_review", "unknown")}
