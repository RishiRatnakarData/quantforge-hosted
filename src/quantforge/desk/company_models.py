"""Company-specific, assumption-driven FCFF valuation and comparable SEC fundamentals.

V5.2: not a fitted price target. Periods, selected tags and the analyst's
assumptions are separate. Missing mandatory SEC fields block the model.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

from quantforge.desk.engine import DeskError
from quantforge.desk.sec_research import _annual_candidates, _instant_candidates, _take
from quantforge.financials.annual import ANNUAL, BALANCE, SHARE_TAGS


def _picked(facts: dict, tags: tuple[str, ...], end: str, *, instant=False, unit="USD") -> dict | None:
    if unit == "USD":
        rows = _instant_candidates(facts, tags, end) if instant else _annual_candidates(facts, tags)
        return _take(rows, end)
    if unit != "shares" or instant:
        raise ValueError("Unrecognized SEC unit")
    choices = []
    for priority, tag in enumerate(tags):
        for row in facts.get(tag, {}).get("units", {}).get("shares", []):
            if row.get("form") not in ("10-K", "10-K/A") or row.get("end") != end:
                continue
            try:
                if not all(k in row for k in ("start", "filed", "val", "accn")):
                    continue
                if row["filed"] > dt.date.today().isoformat():
                    continue
                days = (dt.date.fromisoformat(end) - dt.date.fromisoformat(row["start"])).days
                val = float(row["val"])
                if not 330 <= days <= 400 or not math.isfinite(val) or val <= 0:
                    continue
            except (ValueError, TypeError, OverflowError):
                continue
            choices.append({"value": val, "end": end, "filed": row["filed"],
                            "accession": row["accn"], "tag": tag, "priority": priority})
    return _take(choices, end)


def _assumption(params: dict, key: str, default: float, lo: float, hi: float) -> float:
    raw = params.get(key, default)
    try:
        number = float(raw)
    except (TypeError, ValueError, OverflowError) as exc:
        raise DeskError(f"{key} must be numeric.") from exc
    if not math.isfinite(number) or not lo <= number <= hi:
        raise DeskError(f"{key} must be between {lo:g}% and {hi:g}%.")
    return number / 100


def calculate_company_dcf(payload: dict, *, ticker: str, cik: int, assumptions: dict | None = None) -> dict:
    """Five-year FCFF model with explicit user assumptions, never an investment rating.

    Forecast FCFF = EBIT*(1-tax rate) + D&A - CapEx - change in NWC.
    D&A and CapEx scale with sales using SEC annual observations. NWC change
    uses an explicit assumed percentage of incremental sales; not an SEC fact.
    PV terminal FCFF uses a constant-growth perpetuity. Current+long debt
    minus cash+short-term investments translates EV to equity value.
    """
    if not isinstance(payload, dict) or str(payload.get("cik")) != str(cik):
        raise DeskError("SEC company identifier did not match the requested stock.")
    facts = payload.get("facts", {}).get("us-gaap")
    if not isinstance(facts, dict):
        raise DeskError("Missing SEC US-GAAP facts.")
    revenue_rows = _annual_candidates(facts, ANNUAL["revenue"])
    if not revenue_rows:
        raise DeskError("Annual SEC revenue unavailable; DCF cannot be calculated.")
    end = max(r["end"] for r in revenue_rows)
    fields: dict[str, dict | None] = {
        "revenue": _take(revenue_rows, end),
        "ebit": _picked(facts, ANNUAL["operating_income"], end),
        "da": _picked(facts, ANNUAL["depreciation_amortization"][:3], end),
        "capex": _picked(facts, ANNUAL["capex"], end),
        "cash": _picked(facts, BALANCE["cash"], end, instant=True),
        "debt_current": _picked(facts, BALANCE["debt_current"], end, instant=True),
        "debt_long_term": _picked(facts, BALANCE["debt_long_term"], end, instant=True),
        "shares": _picked(facts, SHARE_TAGS, end, unit="shares"),
    }
    a = assumptions or {}
    if not isinstance(a, dict):
        raise DeskError("DCF assumptions must be an object.")
    # D&A is not always reported as a standard US-GAAP annual Company Facts tag.
    # An analyst can explicitly supply D&A / sales, but it is an ASSUMPTION, not
    # a reported financial statement number. Never fall back to zero or the
    # broader "depreciation, amortization, and OTHER" cash-flow line.
    manual_da = a.get("da_pct") not in (None, "")
    da_assumption = _assumption(a, "da_pct", 0, 0, 50) if manual_da else None
    missing = [k for k, row in fields.items() if row is None and not (k == "da" and manual_da)]
    if missing:
        if missing == ["da"]:
            raise DeskError("D&A was not available as a comparable annual SEC fact. "
                            "Enter a D&A / revenue % assumption under Additional assumptions "
                            "to run an illustrative DCF. No value was invented.")
        raise DeskError("DCF unavailable: missing standard SEC annual facts: " + ", ".join(missing)
                        + ". No values were substituted. Check the filing directly.")
    inv = _picked(facts, BALANCE["short_term_investments"], end, instant=True)
    d = {key: float(row["value"]) for key, row in fields.items() if row is not None}
    if d["revenue"] <= 0 or d["shares"] <= 0 or d["capex"] < 0 or (not manual_da and d["da"] < 0):
        raise DeskError("SEC facts contain unusable values for this DCF.")
    if fields["debt_long_term"]["tag"] != "LongTermDebtNoncurrent":
        raise DeskError("Noncurrent debt is ambiguous in SEC tags; review the original filing before valuation.")
    growth = _assumption(a, "growth_pct", 5, -20, 30)
    margin = _assumption(a, "margin_pct", round(100 * d["ebit"] / d["revenue"], 2), -20, 75)
    wacc = _assumption(a, "wacc_pct", 10, 3, 30)
    terminal_growth = _assumption(a, "terminal_growth_pct", 2.5, -2, 6)
    tax_rate = _assumption(a, "tax_pct", 21, 0, 45)
    nwc_increase = _assumption(a, "nwc_pct", 2, -30, 30)
    if wacc <= terminal_growth + .005:
        raise DeskError("WACC must be at least 0.5 percentage points above terminal growth.")
    da_ratio = da_assumption if manual_da else d["da"] / d["revenue"]
    capex_ratio = d["capex"] / d["revenue"]
    if da_ratio > .5 or capex_ratio > .9:
        raise DeskError("Unusual D&A/CapEx relative to revenue; review SEC fact selection.")
    net_debt = d["debt_current"] + d["debt_long_term"] - d["cash"]
    if inv is not None:
        net_debt -= float(inv["value"])
    shares = d["shares"]
    forecasts = []
    sales = d["revenue"]
    for year in range(1, 6):
        next_sales = sales * (1 + growth)
        change_nwc = (next_sales - sales) * nwc_increase
        ebit = next_sales * margin
        da = next_sales * da_ratio
        capex = next_sales * capex_ratio
        fcf = ebit - max(ebit, 0) * tax_rate + da - capex - change_nwc
        if not math.isfinite(fcf):
            raise DeskError("Forecast cash flows are not finite.")
        forecasts.append({"year": year, "revenue_usd": round(next_sales, 2),
                          "ebit_usd": round(ebit, 2), "da_usd": round(da, 2),
                          "capex_usd": round(capex, 2), "change_nwc_usd": round(change_nwc, 2),
                          "fcff_usd": round(fcf, 2)})
        sales = next_sales
    flows = [f["fcff_usd"] for f in forecasts]
    if flows[-1] <= 0:
        raise DeskError("Projected terminal FCFF is not positive; Gordon-growth DCF is not applicable.")
    def value_at(rate: float, tg: float) -> dict:
        explicit = sum(cf / ((1 + rate) ** t) for t, cf in enumerate(flows, 1))
        terminal = flows[-1] * (1 + tg) / (rate - tg)
        pv_terminal = terminal / ((1 + rate) ** 5)
        ev = explicit + pv_terminal
        equity = ev - net_debt
        return {"price_usd": round(equity / shares, 2),
                "enterprise_usd": round(ev, 2), "equity_usd": round(equity, 2),
                "terminal_share_pct": round(100 * pv_terminal / ev, 2) if ev else None,
                "pv_explicit_usd": round(explicit, 2), "pv_terminal_usd": round(pv_terminal, 2)}
    base = value_at(wacc, terminal_growth)
    sensitivity = []
    for dr in (1, 0, -1):
        rate = wacc + dr * .01
        line = {"wacc_pct": round(rate * 100, 2), "values": []}
        for dg in (-.005, 0, .005):
            tg = terminal_growth + dg
            line["values"].append({"growth_pct": round(tg * 100, 2),
                                    "price_usd": value_at(rate, tg)["price_usd"] if rate > tg else None})
        sensitivity.append(line)
    return {
        "ticker": ticker, "company_name": payload.get("entityName", ticker),
        "fiscal_end": end, "source": "SEC Company Facts (10-K US-GAAP)",
        "source_url": f"https://www.sec.gov/edgar/browse/?CIK={cik}",
        "model": "5-year unlevered free cash flow (FCFF)",
        "base": base, "forecast": forecasts, "sensitivity": sensitivity,
        "assumptions_pct": {"growth": round(growth * 100, 2), "margin": round(margin * 100, 2),
            "da_of_revenue": round(100 * da_assumption, 2) if manual_da else None,
            "wacc": round(wacc * 100, 2), "terminal_growth": round(terminal_growth * 100, 2),
            "tax": round(tax_rate * 100, 2), "nwc_of_incremental_sales": round(nwc_increase * 100, 2)},
        "observed": {"revenue_usd": d["revenue"], "da_to_sales_pct": round(100 * da_ratio, 2),
                     "da_is_assumed": manual_da,
                     "da_source": "User-supplied scenario assumption" if manual_da else fields["da"]["tag"],
                     "capex_to_sales_pct": round(100 * capex_ratio, 2),
                     "net_debt_usd": net_debt, "diluted_weighted_avg_shares": shares,
                     "short_term_investments_included": inv is not None,
                     "diluted_shares_are_fiscal_average": True},
        "provenance": {key: {"tag": row["tag"], "filed": row["filed"],
                              "accession": row["accession"]}
                       for key, row in fields.items() if row is not None and not (key == "da" and manual_da)},
        "limitations": ("Illustrative assumptions, NOT a buy signal or calibrated fair value. "
            "The NWC adjustment is assumed, not observed. "
            + ("D&A is a user-entered scenario assumption, NOT a reported SEC number. " if manual_da
               else ("The SEC D&A concept also includes accretion; review its scope. "
                     if fields["da"]["tag"] == "DepreciationAmortizationAndAccretionNet" else ""))
            + "Reinvestment ratios and the "
            "weighted-average diluted share count are historical proxies. "
            + ("Short-term investments not found; net debt excludes them. " if inv is None else "")
            + "Company Facts aggregates filings; reconcile selected tags with the original 10-K. "
            "May be inappropriate for banks, insurers, REITs, negative-FCFF and unusual capital structures."),
    }


def compare_fundamentals(sec_research: Any, symbols: list[str]) -> dict:
    """Read-only SEC fundamentals comparison, preserving missing values/errors."""
    if not isinstance(symbols, list) or not 2 <= len(symbols) <= 4:
        raise DeskError("Compare 2–4 companies.")
    cleaned = [str(s).strip().upper() for s in symbols]
    if len(set(cleaned)) != len(cleaned):
        raise DeskError("Choose different companies.")
    results = []
    for symbol in cleaned:
        try:
            f = sec_research.fundamentals(symbol)
            results.append({"symbol": symbol, "data": {
                "company_name": f["company_name"], "fiscal_end": f["fiscal_end"],
                "revenue_usd": f["revenue_usd"], "revenue_growth_pct": f["revenue_growth_pct"],
                "operating_margin_pct": f["operating_margin_pct"],
                "net_margin_pct": f["net_margin_pct"], "free_cash_flow_usd": f["free_cash_flow_usd"],
                "long_term_debt_usd": f["long_term_debt_usd"],
                "filings_url": f["filings_url"]}})
        except DeskError as exc:
            results.append({"symbol": symbol, "error": str(exc)})
    return {"source": "SEC annual US-GAAP facts; fiscal years may differ", "companies": results,
            "limitations": "Company accounting is not always directly comparable. Missing facts stay unavailable."}
