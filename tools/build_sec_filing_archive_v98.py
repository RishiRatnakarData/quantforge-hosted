"""Build a local, versioned SEC Company Facts archive with dated original facts.

No private account data or credentials are persisted. This command is optional,
never invoked by CI or website builds, and writes only to ignored data/.
It cannot itself certify a point-in-time backtest or survivorship-free universe.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import time
import urllib.request
from pathlib import Path

from extend_public_sec_v79 import TAGS

ROOT = Path(__file__).resolve().parents[1]
DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
ACCESSION = re.compile(r"\d{10}-\d{2}-\d{6}\Z")
SOURCE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{:010d}.json"


def as_date(value: object) -> dt.date | None:
    if not isinstance(value, str) or not DATE.fullmatch(value):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def extract_issuer(raw: dict, symbol: str, cik: int, cutoff: str, *, max_years: int = 15) -> dict:
    """Retain actual per-fact filing versions; never relabel as original values."""
    if not isinstance(raw, dict) or raw.get("cik") != cik:
        raise ValueError(f"{symbol}: SEC CIK/source mismatch")
    cutoff_date = as_date(cutoff)
    if cutoff_date is None or not 1 <= max_years <= 25:
        raise ValueError("Invalid archival cutoff or maximum fiscal-year count")
    gaap = raw.get("facts", {}).get("us-gaap", {})
    if not isinstance(gaap, dict):
        raise ValueError(f"{symbol}: US-GAAP facts unavailable")
    periods: dict[str, dict[str, list[dict]]] = {}
    for field, tags in TAGS.items():
        for priority, tag in enumerate(tags):
            usd = gaap.get(tag, {}).get("units", {}).get("USD", [])
            if not isinstance(usd, list):
                continue
            for fact in usd:
                if not isinstance(fact, dict) or fact.get("form") not in {"10-K", "10-K/A"}:
                    continue
                if fact.get("fp") != "FY":
                    continue
                start, end, filed = (as_date(fact.get(k)) for k in ("start", "end", "filed"))
                val = fact.get("val")
                acc = fact.get("accn")
                if (start is None or end is None or filed is None or
                    not 330 <= (end - start).days <= 400 or
                    filed < end or filed > cutoff_date or
                    not isinstance(val, (int, float)) or isinstance(val, bool) or
                    not math.isfinite(val) or abs(val) >= 1e16 or
                    not isinstance(acc, str) or not ACCESSION.fullmatch(acc)):
                    continue
                if field == "capex_usd" and val < 0:
                    continue
                entry = {"start": str(start), "filed": str(filed), "accession": acc,
                         "tag": tag, "value": val, "tag_priority": priority}
                periods.setdefault(str(end), {}).setdefault(field, []).append(entry)
    annual = []
    # Anchor fiscal periods to an actually reported annual revenue fact.
    years = sorted((end for end, data in periods.items() if data.get("revenue_usd")), reverse=True)
    for end in years[:max_years]:
        data = {}
        for field in TAGS:
            seen = set()
            versions = []
            for row in sorted(periods[end].get(field, []),
                              key=lambda x: (x["filed"], x["tag_priority"], x["accession"], x["start"])):
                key = (row["start"], row["filed"], row["accession"], row["tag"], row["value"])
                if key in seen:
                    continue
                seen.add(key)
                versions.append(row)
            data[field] = versions
        annual.append({"fiscal_end": end, "revisions": data})
    if not annual:
        raise ValueError(f"{symbol}: no valid annual SEC versions before cutoff")
    return {"symbol": symbol, "cik": cik, "source_url": SOURCE.format(cik),
            "annual": annual, "annual_periods": len(annual)}


def build(snapshot: dict, raws: dict[str, dict], cutoff: str, *, max_years: int = 15) -> dict:
    if snapshot.get("dataset") != "SEC EDGAR Company Facts, annual 10-K US-GAAP":
        raise ValueError("Require the verified current public SEC snapshot as the issuer seed")
    companies = snapshot.get("companies", [])
    if not isinstance(companies, list) or not 1 <= len(companies) <= 500:
        raise ValueError("Invalid issuer seed")
    output, seen = [], set()
    for company in companies:
        symbol, cik = company.get("symbol"), company.get("cik")
        if (not isinstance(symbol, str) or not re.fullmatch(r"[A-Z0-9.\-]{1,15}", symbol) or
            not isinstance(cik, int) or cik <= 0 or symbol in seen):
            raise ValueError("Duplicate or invalid issuer seed")
        seen.add(symbol)
        if symbol in raws:
            output.append(extract_issuer(raws[symbol], symbol, cik, cutoff, max_years=max_years))
    return {"schema": "quantforge.sec.filing-revisions.v9.8", "as_of": cutoff,
            "source": "SEC EDGAR XBRL Company Facts; original filing and amendment records as available",
            "coverage": {"seed_issuers": len(companies), "downloaded_issuers": len(output)},
            "limitations": [
                "Company Facts may not preserve every original value after an amended filing; do not assume it is a complete historical filing archive.",
                "Current issuer list is not an as-of historical or delisting-inclusive investment universe.",
                "This local artifact is not automatically published, included in the website, or used for brokerage trading.",
            ], "companies": output}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=ROOT / "web/site/sec_snapshot.json")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input-dir", type=Path, help="Directory of already obtained CIK##########.json SEC responses")
    source.add_argument("--download", action="store_true", help="Download bounded Company Facts from SEC under its fair access requirements")
    parser.add_argument("--max-issuers", type=int, default=25)
    parser.add_argument("--max-years", type=int, default=15)
    parser.add_argument("--cutoff", type=str, default=dt.date.today().isoformat())
    parser.add_argument("--output", type=Path, default=ROOT / "data/sec_filing_revisions_v98.json")
    args = parser.parse_args()
    if (not 1 <= args.max_issuers <= 100 or as_date(args.cutoff) is None or
            as_date(args.cutoff) > dt.date.today()):
        parser.error("Valid max-issuers (1–100) and nonfuture ISO cutoff required")
    # Keep private development artifacts in the repository's ignored data directory.
    allowed = (ROOT / "data").resolve()
    out = args.output.resolve()
    if not out.is_relative_to(allowed) or out == allowed:
        parser.error("Output must be a file under ignored repository data/")
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    companies = snapshot.get("companies", [])[: args.max_issuers]
    raw: dict[str, dict] = {}
    if args.download:
        agent = os.environ.get("SEC_USER_AGENT", "")
        if not re.fullmatch(r".{8,160}@[^\s@]+", agent) or "example.com" in agent.lower():
            parser.error("SEC_USER_AGENT must contain an actual descriptive identity and contact email")
    for index, company in enumerate(companies):
        symbol, cik = company["symbol"], company["cik"]
        if args.download:
            if index:
                time.sleep(1.1)
            request = urllib.request.Request(SOURCE.format(cik), headers={
                "User-Agent": agent, "Accept": "application/json", "Accept-Encoding": "identity"})
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read(18_000_001)
            if len(payload) > 18_000_000:
                raise ValueError(f"{symbol}: SEC response exceeds 18 MB; no archive written")
            raw[symbol] = json.loads(payload)
        else:
            p = args.input_dir / f"CIK{cik:010d}.json"
            if p.exists():
                if p.stat().st_size > 18_000_000:
                    raise ValueError(f"{symbol}: local SEC response too large")
                raw[symbol] = json.loads(p.read_text(encoding="utf-8"))
    result = build({**snapshot, "companies": companies}, raw, args.cutoff, max_years=args.max_years)
    if not result["companies"]:
        raise ValueError("No validated issuers; existing archive left untouched")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".pending")
    tmp.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(out)
    print(f"Wrote {len(result['companies'])} issuer archives to {out} (local and ignored by Git).")


if __name__ == "__main__":
    main()
