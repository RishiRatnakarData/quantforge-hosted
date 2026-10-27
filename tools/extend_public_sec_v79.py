"""Expand QuantForge's public SEC annual snapshot with keyless SEC Company Facts.

Run on an authorized developer machine or CI, NOT in public browsers. Source data:
SEC EDGAR Company Facts (https://data.sec.gov). A declared User-Agent is mandatory.
No paid market data, prices, analyst estimates, API keys, or private portfolio data.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DATASET = "SEC EDGAR Company Facts, annual 10-K US-GAAP"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "web/site/sec_snapshot.json"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{:010d}.json"
REVENUE = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
)
TAGS = {
    "revenue_usd": REVENUE,
    "operating_income_usd": ("OperatingIncomeLoss",),
    "net_income_usd": ("NetIncomeLoss",),
    "operating_cash_flow_usd": (
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ),
    "capex_usd": ("PaymentsToAcquirePropertyPlantAndEquipment",),
}
FIELDS = (*TAGS, "free_cash_flow_usd")


def annual_observations(raw: dict, tags: tuple[str, ...], cutoff: str) -> list[dict]:
    gaap = raw.get("facts", {}).get("us-gaap", {})
    output = []
    for rank, tag in enumerate(tags):
        values = gaap.get(tag, {}).get("units", {}).get("USD", [])
        for fact in values:
            if not isinstance(fact, dict) or fact.get("form") != "10-K" or fact.get("fp") != "FY":
                continue
            start, end, filed = fact.get("start"), fact.get("end"), fact.get("filed")
            value = fact.get("val")
            try:
                days = (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days
                dt.date.fromisoformat(filed)
            except (TypeError, ValueError):
                continue
            if not (330 <= days <= 400 and filed <= cutoff):
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not abs(value) < 1e18:
                continue
            accession = fact.get("accn")
            if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", str(accession)):
                continue
            output.append({"start": start, "end": end, "filed": filed, "accn": accession,
                           "val": value, "tag": tag, "rank": rank})
    return output


def build_company(raw: dict, symbol: str, cik: int, cutoff: str, *, min_years: int = 2) -> dict | None:
    """Prefer one true FY revenue interval, matching other metrics by fiscal end/start.

    This is *as-of the snapshot cutoff*, not point-in-time as of the fiscal year.
    Restated numbers filed before the snapshot cutoff can replace older filings.
    """
    if raw.get("cik") != cik:
        return None
    found = {metric: annual_observations(raw, tags, cutoff) for metric, tags in TAGS.items()}
    revenue = {}
    for item in found["revenue_usd"]:
        key = item["end"]
        # Prefer the most recently filed eligible 10-K, then preferred tag.
        if key not in revenue or (item["filed"], -item["rank"], item["accn"]) > (
            revenue[key]["filed"], -revenue[key]["rank"], revenue[key]["accn"]
        ):
            revenue[key] = item
    annual = []
    for end in sorted(revenue, reverse=True):
        parent = revenue[end]
        metrics = {}
        sources = {}
        for name in TAGS:
            valid = [x for x in found[name] if x["end"] == end and abs(
                (dt.date.fromisoformat(x["start"]) - dt.date.fromisoformat(parent["start"])).days
            ) <= 10]
            if name == "revenue_usd":
                candidate = parent
            else:
                candidate = max(valid, key=lambda x: (x["filed"], -x["rank"], x["accn"])) if valid else None
            metrics[name] = candidate["val"] if candidate else None
            if candidate:
                sources[name] = {"tag": candidate["tag"], "filed": candidate["filed"],
                                 "accession": candidate["accn"], "start": candidate["start"],
                                 "end": candidate["end"]}
        cash, capex = metrics["operating_cash_flow_usd"], metrics["capex_usd"]
        metrics["free_cash_flow_usd"] = cash - capex if cash is not None and capex is not None and capex >= 0 else None
        annual.append({"fiscal_end": end, "metrics": metrics, "sources": sources})
        if len(annual) == 3:
            break
    if len(annual) < min_years:
        return None
    name = str(raw.get("entityName") or "").strip()
    if not name or len(name) > 160:
        return None
    return {"symbol": symbol, "name": name, "cik": cik, "sector": "Not classified", "as_of": cutoff,
            "source_url": BASE_URL.format(cik), "annual": annual}


def request_json(url: str, user_agent: str, *, attempts: int = 3) -> dict:
    for index in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "identity",
                                                  "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=40) as response:
                if response.status != 200:
                    raise OSError(f"HTTP {response.status}")
                raw = response.read(12_000_001)
                if len(raw) > 12_000_000:
                    raise ValueError("SEC response exceeds 12 MB; skip this issuer")
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and index < attempts - 1:
                time.sleep(min(20, 3 * (index + 1)))
                continue
            raise OSError(f"SEC HTTP {exc.code} for {url}") from exc
    raise OSError("SEC request failed after retries")


def parse_symbols(raw: str) -> list[str]:
    parts = re.split(r"[,\s]+", raw.strip().upper())
    symbols = list(dict.fromkeys(x for x in parts if x))
    if not symbols or any(not re.fullmatch(r"[A-Z0-9.-]{1,15}", s) for s in symbols):
        raise ValueError("Provide one or more ordinary stock symbols separated by commas or whitespace")
    return symbols


def expand(snapshot_path: Path, symbols: list[str], user_agent: str, *, max_new: int = 50,
           min_new: int = 1, delay: float = 1.2) -> tuple[int, list[str]]:
    if not re.search(r"[^\s@]+@[^\s@]+\.[^\s@]+", user_agent) or len(user_agent) < 15:
        raise ValueError("Set SEC_USER_AGENT to a descriptive application name and real contact email")
    if not 0.5 <= delay <= 60:
        raise ValueError("Delay must be at least 0.5 seconds")
    if not 1 <= max_new <= 250 or min_new < 1 or min_new > max_new:
        raise ValueError("Choose max-new 1–250 and min-new 1–max-new")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot.get("dataset") != DATASET or len(snapshot.get("companies", [])) < 12:
        raise ValueError("Require the existing verified 12-company SEC snapshot")
    existing = {x["symbol"]: x for x in snapshot["companies"]}
    selected = [x for x in symbols if x not in existing][:max_new]
    if not selected:
        return 0, []
    directory = request_json(TICKERS_URL, user_agent)
    time.sleep(delay)
    tickers = {x["ticker"].upper(): int(x["cik_str"]) for x in directory.values() if isinstance(x, dict)
               and isinstance(x.get("ticker"), str) and isinstance(x.get("cik_str"), int)}
    accepted, skipped = [], []
    cutoff = dt.date.today().isoformat()
    for symbol in selected:
        cik = tickers.get(symbol)
        if not cik:
            skipped.append(f"{symbol}: not in SEC ticker directory")
            continue
        try:
            raw = request_json(BASE_URL.format(cik), user_agent)
            company = build_company(raw, symbol, cik, cutoff)
            if company is None:
                skipped.append(f"{symbol}: insufficient comparable annual 10-K US-GAAP facts")
            else:
                accepted.append(company)
        except (OSError, UnicodeDecodeError, ValueError, KeyError) as e:
            skipped.append(f"{symbol}: source unavailable ({type(e).__name__})")
        time.sleep(delay)
    if len(accepted) < min_new:
        raise ValueError(f"Only {len(accepted)} companies qualified, required {min_new}; snapshot unchanged. {skipped[:6]}")
    for item in accepted:
        existing[item["symbol"]] = item
    snapshot["companies"] = [*snapshot["companies"], *accepted]
    snapshot["expanded_as_of"] = cutoff
    snapshot["coverage_note"] = "Additional issuers were added at a later SEC filing cutoff; issuer reporting periods and snapshot ages differ."
    # Keep the original 12-issuer dataset cutoff rather than silently making its
    # unrefreshed company records appear freshly retrieved.
    # Keep source-backed facts only; no stock quotes or credentials in the snapshot.
    contents = json.dumps(snapshot, indent=2, ensure_ascii=True) + "\n"
    temp = snapshot_path.with_suffix('.json.v79tmp')
    temp.write_text(contents, encoding="utf-8")
    temp.replace(snapshot_path)
    return len(accepted), skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", default="", help="Comma-separated US stock tickers, e.g. AMD,COST,ADBE")
    parser.add_argument("--symbols-file", type=Path, help="Text file containing one stock symbol per line")
    parser.add_argument("--max-new", type=int, default=50)
    parser.add_argument("--min-new", type=int, default=1)
    parser.add_argument("--delay", type=float, default=1.2, help="SEC fair-use delay in seconds")
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()
    user_agent = os.environ.get("SEC_USER_AGENT", "")
    all_symbols = args.symbols
    # Drop full-line comment lines, not ticker strings.
    if args.symbols_file:
        lines = [line.strip() for line in args.symbols_file.read_text(encoding="utf-8").splitlines()]
        all_symbols = args.symbols + "," + ",".join(line for line in lines if line and not line.startswith("#"))
    symbols = parse_symbols(all_symbols)
    count, skipped = expand(args.snapshot, symbols, user_agent, max_new=args.max_new,
                            min_new=args.min_new, delay=args.delay)
    print(f"Added {count} verified SEC companies to {args.snapshot}; no paid API required.")
    for reason in skipped:
        print('Skipped:', reason)
    print('Build and test the public site before publication. Existing issuer records remain unchanged.')
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as e:
        print(f"SEC expansion stopped: {e}", file=sys.stderr)
        sys.exit(1)
