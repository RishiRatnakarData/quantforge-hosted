"""Side-by-side, same-dollar paper what-ifs; no return predictions or rankings."""

from __future__ import annotations

from quantforge.desk.companion import decision_brief
from quantforge.desk.engine import DeskError, asset_type, money


def compare_ideas(symbols: list[str], budget: object, market, portfolio: dict, profile: dict) -> dict:
    """Compare independently deploying the SAME budget to each asset.

    Each row is an alternative scenario starting from the same original portfolio;
    no purchases occur and the rows should not be added together.
    """
    if not isinstance(symbols, list) or not 2 <= len(symbols) <= 4:
        raise DeskError("Compare 2 to 4 different investments.")
    checked = [str(s).strip().upper() for s in symbols]
    for symbol in checked:
        asset_type(symbol)
    if len(set(checked)) != len(checked):
        raise DeskError("Choose different investments for the comparison.")
    amount = money(budget, "comparison amount")
    if amount < 1 or amount > money(portfolio["cash"], "available cash"):
        raise DeskError("Comparison amount must be at least $1 and within virtual cash.")

    rows = []
    for symbol in checked:
        q = market.quote(symbol)
        d = decision_brief(q, portfolio, profile, amount)
        rows.append({
            "symbol": symbol,
            "name": q.get("name", symbol),
            "asset_class": d["asset_class"],
            "price": d["price"],
            "quote_timestamp": d["quote_timestamp"],
            "source": d["source"],
            "coverage": d["coverage"],
            "synthetic": bool(q.get("synthetic", False)),
            "fresh_for_paper": d["fresh_for_paper"],
            "units": d["shares_preview"],
            "fee_usd": d["approx_fee_usd"],
            "post_cash_usd": d["post_cash_usd"],
            "position_weight_pct": d["position_weight_after_pct"],
            "scenario_decline_pct": d["stress_assumption_pct"],
            "scenario_total_loss_usd": d["scenario_loss_usd"],
            "scenario_added_loss_usd": d["scenario_loss_added_usd"],
            "flags": d["flags"],
        })
    return {
        "budget_usd": float(amount),
        "rows": rows,
        "method": "Independent equal-budget hypothetical purchases, including a 0.05% simulated fee.",
        "limitations": "Scenarios use different assumed declines by asset class; losses are not forecasts, estimates of maximum losses, or risk rankings. Quotes may be stale or venue-specific.",
        "no_orders": True,
    }
