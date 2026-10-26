"""Generate a public, provenance-rich *annual filing* snapshot from SEC Company Facts.

No API keys, market prices, private positions, or proprietary Alpaca data.
Never substitute simulation for unavailable financial disclosures.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import time
from pathlib import Path

import requests

# A deliberately bounded cross-industry public exhibit, not an open-ended market feed.
# CIK identifiers are verified by the companyfacts CIK check before publication.
ISSUERS = {
    "MSFT": (789019, "Microsoft"),
    "AAPL": (320193, "Apple"),
    "NVDA": (1045810, "NVIDIA"),
    "GOOGL": (1652044, "Alphabet"),
    "AMZN": (1018724, "Amazon"),
    "META": (1326801, "Meta Platforms"),
    "COST": (909832, "Costco Wholesale"),
    "WMT": (104169, "Walmart"),
    "KO": (21344, "Coca-Cola"),
    "JNJ": (200406, "Johnson & Johnson"),
    "XOM": (34088, "Exxon Mobil"),
    "CAT": (18230, "Caterpillar"),
}
# Editorial categories, not SEC classifications; do not use them as GAAP metrics.
SECTORS = {
    "MSFT": "Technology", "AAPL": "Technology", "NVDA": "Technology",
    "GOOGL": "Communication", "AMZN": "Consumer discretionary",
    "META": "Communication", "COST": "Consumer staples",
    "WMT": "Consumer staples", "KO": "Consumer staples",
    "JNJ": "Healthcare", "XOM": "Energy", "CAT": "Industrials",
}
TAGS = {
    "revenue_usd": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax",
    ),
    "operating_income_usd": ("OperatingIncomeLoss",),
    "net_income_usd": ("NetIncomeLoss",),
    "operating_cash_flow_usd": ("NetCashProvidedByUsedInOperatingActivities",),
    "capex_usd": ("PaymentsToAcquirePropertyPlantAndEquipment",),
}


def _valid_annual(item: dict, as_of: dt.date) -> bool:
    try:
        if item.get("form") not in ("10-K", "10-K/A") or item.get("fp") != "FY":
            return False
        start, end = dt.date.fromisoformat(item["start"]), dt.date.fromisoformat(item["end"])
        filed = dt.date.fromisoformat(item["filed"])
        value = item["val"]
        return (330 <= (end - start).days <= 380 and end <= filed <= as_of
                and isinstance(value, (int, float)) and not isinstance(value, bool)
                and abs(value) < 1e15 and value == value)
    except (KeyError, ValueError, TypeError):
        return False


def _observations(us_gaap: dict, candidates: tuple[str, ...], as_of: dt.date) -> dict[str, dict]:
    """One filing-supported annual fact per fiscal end; tag priority stays explicit."""
    selected: dict[str, tuple[int, dict]] = {}
    for priority, tag in enumerate(candidates):
        facts = us_gaap.get(tag, {}).get("units", {}).get("USD", [])
        if not isinstance(facts, list):
            continue
        for fact in facts:
            if not isinstance(fact, dict) or not _valid_annual(fact, as_of):
                continue
            end = fact["end"]
            current = selected.get(end)
            if current is None or priority < current[0] or (priority == current[0] and fact["filed"] > current[1]["filed"]):
                selected[end] = (priority, fact)
    return {end: row for end, (_, row) in selected.items()}


def transform(companyfacts: dict, symbol: str, as_of: dt.date) -> dict:
    cik, label = ISSUERS[symbol]
    if int(companyfacts.get("cik", -1)) != cik:
        raise ValueError(f"{symbol}: CIK mismatch in SEC response")
    gaap = companyfacts.get("facts", {}).get("us-gaap")
    if not isinstance(gaap, dict):
        raise ValueError(f"{symbol}: missing SEC US-GAAP facts")

    series = {field: _observations(gaap, tags, as_of) for field, tags in TAGS.items()}
    # Annual periods are anchored on actual revenue disclosure period end.
    ends = sorted(series["revenue_usd"], reverse=True)[:3]
    if len(ends) < 2:
        raise ValueError(f"{symbol}: fewer than 2 eligible annual SEC revenues")
    annual = []
    for end in ends:
        row: dict = {"fiscal_end": end, "metrics": {}, "sources": {}}
        for field in TAGS:
            fact = series[field].get(end)
            row["metrics"][field] = fact["val"] if fact is not None else None
            if fact is not None:
                row["sources"][field] = {
                    "filed": fact["filed"],
                    "accession": fact.get("accn", ""),
                    "tag": next((tag for tag in TAGS[field]
                                 if fact in gaap.get(tag, {}).get("units", {}).get("USD", [])), ""),
                }
        ocf = row["metrics"]["operating_cash_flow_usd"]
        capex = row["metrics"]["capex_usd"]
        row["metrics"]["free_cash_flow_usd"] = ocf - capex if ocf is not None and capex is not None else None
        annual.append(row)

    return {
        "symbol": symbol, "name": label, "sector": SECTORS[symbol], "cik": cik,
        "source_url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
        "annual": annual,
    }


def build_snapshot(as_of: dt.date, user_agent: str, get=requests.get) -> dict:
    if "@" not in user_agent or len(user_agent) < 12 or "example.com" in user_agent:
        raise ValueError("SEC_USER_AGENT must identify a project/person and real contact email")
    companies = []
    for index, (symbol, (cik, _)) in enumerate(ISSUERS.items()):
        # Deliberately below the SEC fair-access rate, including fast/cache hits.
        if index:
            time.sleep(0.2)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
        response = get(url, headers={"User-Agent": user_agent, "Accept": "application/json"}, timeout=35)
        response.raise_for_status()
        companies.append(transform(response.json(), symbol, as_of))
    return {
        "dataset": "SEC EDGAR Company Facts, annual 10-K US-GAAP",
        "as_of": as_of.isoformat(),
        "source": "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        "methodology": "Annual period 330-380 days; 10-K/10-K/A; filing date <= as_of; latest eligible filing per period. Null means no comparable eligible fact. Free cash flow proxy = operating cash flow - cash capex. Editorial sector groups and non-synchronized fiscal years must not be interpreted as strict peers.",
        "companies": companies,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default=dt.date.today().isoformat())
    parser.add_argument("--output", type=Path, default=Path("web/site/sec_snapshot.json"))
    args = parser.parse_args()
    user_agent = os.environ.get("SEC_USER_AGENT", "")
    snapshot = build_snapshot(dt.date.fromisoformat(args.as_of), user_agent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    for c in snapshot["companies"]:
        print(f"{c['symbol']}: {', '.join(x['fiscal_end'] for x in c['annual'])} SEC revenue periods")
    print(f"Public SEC snapshot written to {args.output}; no credentials stored")


if __name__ == "__main__":
    main()
