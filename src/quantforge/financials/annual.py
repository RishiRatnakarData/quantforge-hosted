"""Auditable annual US-GAAP financial statements from SEC Company Facts.

The SEC Company Facts API aggregates facts, not standardized statements.
Every chosen value retains unit, concept, period and filing accession. Missing
accounting data stops valuation rather than being silently filled.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path

import pandas as pd
import requests

CIK_MSFT = "0000789019"
SEC_URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK_MSFT}.json"

# Ordered fallback tags; audit records disclose which tag was used.
ANNUAL = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "operating_income": ("OperatingIncomeLoss",),
    "pretax_income": ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"),
    "tax_expense": ("IncomeTaxExpenseBenefit",),
    "net_income": ("NetIncomeLoss",),
    "gross_profit": ("GrossProfit",),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment",),
    # Optional in Company Facts; a cash-flow item named "D&A and other"
    # must not be mislabeled as pure depreciation/amortization.
    "depreciation_amortization": ("DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "DepreciationAmortizationAndAccretionNet", "DepreciationDepletionAndAmortizationPropertyPlantAndEquipment"),
}
BALANCE = {
    "cash": ("CashAndCashEquivalentsAtCarryingValue",),
    "short_term_investments": ("ShortTermInvestments", "AvailableForSaleSecuritiesCurrent"),
    "receivables": ("AccountsNotesAndOtherReceivablesNetCurrent", "AccountsReceivableNetCurrent"),
    "inventory": ("InventoryNet",),
    "payables": ("AccountsPayableCurrent",),
    "deferred_revenue": ("ContractWithCustomerLiabilityCurrent", "DeferredRevenueCurrent"),
    "debt_current": ("LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent"),
    "debt_long_term": ("LongTermDebtNoncurrent", "LongTermDebt", "LongTermDebtAndCapitalLeaseObligations"),
    "assets": ("Assets",),
    "current_assets": ("AssetsCurrent",),
    "current_liabilities": ("LiabilitiesCurrent",),
    "ppe_net": ("PropertyPlantAndEquipmentNet",),
    "liabilities": ("Liabilities",),
    "stockholders_equity": ("StockholdersEquity",),
}
SHARE_TAGS = ("WeightedAverageNumberOfDilutedSharesOutstanding",)


def download_companyfacts(*, user_agent: str, target: Path, session: requests.Session | None = None) -> Path:
    """One rate-conscious SEC GET; never embed private contact strings in reports."""
    if not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", user_agent):
        raise ValueError("SEC User-Agent must identify an organization/person and working email")
    client = session or requests.Session()
    response = client.get(
        SEC_URL,
        headers={"User-Agent": user_agent, "Accept": "application/json", "Accept-Encoding": "gzip, deflate"},
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    if str(payload.get("cik", "")) not in ("789019", CIK_MSFT):
        raise ValueError("SEC response CIK does not match Microsoft")
    if not isinstance(payload.get("facts", {}).get("us-gaap"), dict):
        raise ValueError("SEC response does not contain us-gaap facts")
    target.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    fingerprint = hashlib.sha256(data).hexdigest()[:16]
    # Immutable content-addressed snapshots preserve reproducibility across SEC
    # filing changes, rather than overwriting a previous research input.
    saved = target.with_name(f"{target.stem}_{fingerprint}{target.suffix}")
    if not saved.exists():
        saved.write_bytes(data)
    return saved


def _usable(payload: dict, tags: tuple[str, ...], fiscal_end: str, *, as_of: str, annual: bool, units: str) -> list[dict]:
    """Return all exact-end candidates from 10-K filings received by as_of."""
    candidates: list[dict] = []
    facts = payload.get("facts", {}).get("us-gaap", {})
    for rank, tag in enumerate(tags):
        entries = facts.get(tag, {}).get("units", {}).get(units, [])
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("form") not in ("10-K", "10-K/A"):
                continue
            if entry.get("end") != fiscal_end or not entry.get("filed") or entry["filed"] > as_of:
                continue
            if not entry.get("accn") or not isinstance(entry.get("val"), (int, float)):
                continue
            if annual:
                start = entry.get("start")
                if not start:
                    continue
                try:
                    duration = (date.fromisoformat(fiscal_end) - date.fromisoformat(start)).days
                except ValueError:
                    continue
                if not 330 <= duration <= 400:
                    continue
            else:
                if "start" in entry:
                    continue
            candidates.append({
                "val": float(entry["val"]), "tag": tag, "units": units,
                "end": fiscal_end, "start": entry.get("start"), "filed": entry["filed"],
                "accn": entry["accn"], "form": entry["form"], "priority": rank,
            })
    return candidates


def _choose(payload: dict, tags: tuple[str, ...], period: str, *, as_of: str, annual: bool, units: str = "USD") -> dict | None:
    options = _usable(payload, tags, period, as_of=as_of, annual=annual, units=units)
    if not options:
        return None
    # Prefer first taxonomy tag when multiple equivalent tags exist; among facts
    # using that tag, use latest available filing (including amendments).
    options.sort(key=lambda x: (x["priority"], -date.fromisoformat(x["filed"]).toordinal(), x["accn"]))
    return options[0]


def annual_financials(payload: dict, *, as_of: str, fiscal_years: tuple[int, ...] = (2023, 2024, 2025, 2026)) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract June-fiscal Microsoft annuals; never use post-cutoff filings.

    USD converted into USD millions. Shares converted into millions. A fact
    missing from the standardized taxonomy remains missing (never zero).
    """
    date.fromisoformat(as_of)
    if str(payload.get("cik", "")) not in ("789019", CIK_MSFT):
        raise ValueError("CompanyFacts CIK does not identify Microsoft")
    records, audit = [], []
    for fiscal_year in fiscal_years:
        fiscal_end = f"{fiscal_year}-06-30"
        if fiscal_end > as_of:
            continue
        row = {"fiscal_year": fiscal_year, "fiscal_end": fiscal_end}
        for field, tags in {**ANNUAL, **BALANCE, "diluted_shares": SHARE_TAGS}.items():
            is_annual = field in ANNUAL or field == "diluted_shares"
            units = "shares" if field == "diluted_shares" else "USD"
            chosen = _choose(payload, tags, fiscal_end, as_of=as_of, annual=is_annual, units=units)
            row[field] = None if chosen is None else chosen["val"] / 1_000_000
            audit.append({
                "fiscal_year": fiscal_year, "metric": field,
                "status": "selected" if chosen else "missing",
                "selected_value_millions": row[field],
                "selected_tag": chosen["tag"] if chosen else None,
                "filed": chosen["filed"] if chosen else None,
                "accession": chosen["accn"] if chosen else None,
                "period_end": fiscal_end,
                "source_unit": units,
                "alternatives": " | ".join(tags),
            })
        # A completed fiscal period is not publicly observable until at least
        # one actual annual fact has been filed. Do not emit all-null pre-filing
        # rows that appear to be financial statements.
        if all(pd.isna(row[field]) for field in ANNUAL):
            audit = [item for item in audit if item["fiscal_year"] != fiscal_year]
            continue
        records.append(row)
    if not records:
        raise ValueError("No Microsoft annual fiscal periods before as-of")
    frame = pd.DataFrame(records).sort_values("fiscal_year").reset_index(drop=True)
    # Derived measures require explicit nonmissing inputs and signed conventions.
    frame["fcf_operating_minus_capex"] = frame["operating_cash_flow"] - frame["capex"]
    frame["operating_margin"] = frame["operating_income"] / frame["revenue"]
    frame["gross_margin"] = frame["gross_profit"] / frame["revenue"]
    frame["net_margin"] = frame["net_income"] / frame["revenue"]
    frame["current_ratio"] = frame["current_assets"] / frame["current_liabilities"]
    frame["operating_cash_conversion"] = frame["operating_cash_flow"] / frame["net_income"]
    frame["capex_intensity"] = frame["capex"] / frame["revenue"]
    frame["reported_effective_tax_rate"] = frame["tax_expense"] / frame["pretax_income"]
    frame["revenue_growth"] = frame["revenue"].pct_change(fill_method=None)
    frame["operating_nwc"] = (
        frame["receivables"] + frame["inventory"] - frame["payables"] - frame["deferred_revenue"]
    )
    frame["cash_plus_short_term_investments"] = frame["cash"] + frame["short_term_investments"]
    frame["interest_bearing_debt"] = frame["debt_current"] + frame["debt_long_term"]
    # Simple illustrative invested-capital proxy, not a company-defined ROIC.
    frame["invested_capital_proxy"] = (
        frame["interest_bearing_debt"] + frame["stockholders_equity"]
        - frame["cash_plus_short_term_investments"]
    )
    frame["roic_approximation"] = (
        frame["operating_income"] * (1 - frame["reported_effective_tax_rate"])
        / frame["invested_capital_proxy"].where(frame["invested_capital_proxy"] > 0)
    )
    frame["balance_reconciliation_error"] = (
        frame["assets"] - frame["liabilities"] - frame["stockholders_equity"]
    )
    return frame, pd.DataFrame(audit)


def verify_financials(frame: pd.DataFrame, *, as_of: str, min_years: int = 3) -> dict:
    """Strict gate for valuation inputs; no silent estimates for SEC gaps."""
    required = ["revenue", "operating_income", "pretax_income", "tax_expense", "capex", "cash", "short_term_investments", "receivables", "inventory", "payables", "deferred_revenue", "debt_current", "debt_long_term", "diluted_shares", "assets", "liabilities", "stockholders_equity", "operating_cash_flow", "net_income", "gross_profit", "current_assets", "current_liabilities"]
    eligible = frame[frame["fiscal_end"].le(as_of)].copy()
    if len(eligible) < min_years:
        raise ValueError(f"Need {min_years} published annual periods; got {len(eligible)}")
    latest = eligible.iloc[-1]
    missing = [key for key in required if pd.isna(latest[key])]
    if missing:
        raise ValueError("SEC missing required latest-fiscal concepts: " + ", ".join(missing) + ". Review concept audit before valuation; do not substitute zero")
    for field in ("revenue", "operating_income", "capex", "diluted_shares", "pretax_income", "assets"):
        if latest[field] <= 0:
            raise ValueError(f"Nonpositive required metric: {field}")
    if latest["reported_effective_tax_rate"] < 0 or latest["reported_effective_tax_rate"] > 0.60:
        raise ValueError("Effective-tax estimate out of range; check data or override assumptions")
    bserr = abs(float(latest["balance_reconciliation_error"]))
    tolerance = max(1, float(latest["assets"]) * 0.001)
    if bserr > tolerance:
        raise ValueError(f"Balance sheet does not reconcile (USD millions): {bserr:.3f}")
    if latest["interest_bearing_debt"] < 0:
        raise ValueError("Negative interest-bearing debt")
    return {"latest_fiscal_year": int(latest["fiscal_year"]), "years_present": len(eligible), "latest_reconciliation_error_usd_millions": float(latest["balance_reconciliation_error"]), "tolerance_usd_millions": tolerance, "status": "latest_year_complete_and_balance_reconciled", "cross_filing_review": "still_required"}


def input_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
