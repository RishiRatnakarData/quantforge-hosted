"""Owner-only intersection of covered SEC issuers and supported provider listings.

This is eligibility metadata, not a market-wide investment ranking or price feed.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from cloud import asset_directory


def intersect(snapshot: dict, assets: list[dict]) -> dict:
    companies = snapshot.get("companies")
    if not isinstance(companies, list) or not 1 <= len(companies) <= 500:
        raise ValueError("The covered SEC research universe is unavailable.")
    supported = {row["symbol"] for row in assets
                 if isinstance(row, dict) and row.get("asset_class") == "us_equity"
                 and row.get("tradable") is True and isinstance(row.get("symbol"), str)}
    items = []
    excluded = []
    seen = set()
    for company in companies:
        symbol = company.get("symbol") if isinstance(company, dict) else None
        if not isinstance(symbol, str) or not asset_directory._SYMBOL.fullmatch(symbol) or symbol in seen:
            raise ValueError("The covered SEC research universe has invalid issuer identifiers.")
        seen.add(symbol)
        if symbol not in supported:
            excluded.append({"symbol": symbol, "reason": "Not in the current supported active/tradable US listing catalogue."})
            continue
        items.append({"symbol": symbol, "name": str(company.get("name") or symbol)[:120],
                      "sector": str(company.get("sector") or "Not reported")[:80]})
    return {"schema": "quantforge.research-universe.v34", "items": items,
            "excluded": excluded, "catalog_count": len(companies),
            "eligible_count": len(items), "excluded_count": len(excluded),
            "financial_cutoff": str(snapshot.get("expanded_as_of") or snapshot.get("as_of") or "Not reported"),
            "eligibility_checked_at": dt.datetime.now(dt.UTC).isoformat(),
            "licensed_private": True,
            "scope": "Covered SEC company issuers intersected with cached Alpaca active/tradable US listings.",
            "limitations": "Not the whole market. Eligibility is not suitability, personal trading permission, current liquidity or a successful investment assessment. Funds and crypto require their own evidence; missing issuer financials are never imputed."}


def get_universe() -> dict:
    file = Path(__file__).resolve().parents[1] / "web/site/sec_snapshot.json"
    try:
        snapshot = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("The covered SEC research universe is unavailable.") from exc
    # Reuse the existing bounded, hourly cached, read-only provider catalogue.
    assets = asset_directory._get_assets("us_equity")
    return intersect(snapshot, assets)
