"""Offline SEC-filing decision-date coverage audit for a local V9.8/V9.9 archive.

Records observed coverage, not claims about complete original filings or alpha.
All output stays in Git-ignored data/ and contains no broker information.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

from validate_local_sec_archive_v99 import ROOT, audit, date

FIELDS = ("revenue_usd", "operating_cash_flow_usd", "capex_usd")


def select_revision(entries: list[dict], fiscal: str, as_of: str) -> dict | None:
    """Use latest eligible filed version, resolving tags by recorded priority."""
    eligible = [
        row for row in entries
        if fiscal <= row["filed"] <= as_of
        and 330 <= (date(fiscal) - date(row["start"])).days <= 400
    ]
    if not eligible:
        return None
    last_filed = max(row["filed"] for row in eligible)
    same_date = [row for row in eligible if row["filed"] == last_filed]
    priority = min(row["tag_priority"] for row in same_date)
    best = [row for row in same_date if row["tag_priority"] == priority]
    if len({row["value"] for row in best}) != 1:
        return None
    return best[0]


def check_issuer(issuer: dict, as_of: str) -> tuple[bool, str, str | None]:
    """Mirror V9.9's fiscal/filing eligibility gate without exposing values."""
    annual = []
    for period in issuer["annual"]:
        fiscal = period["fiscal_end"]
        if fiscal > as_of:
            continue
        facts = {
            field: select_revision(period["revisions"][field], fiscal, as_of)
            for field in FIELDS
        }
        if any(facts[field] is None for field in FIELDS):
            continue
        if facts["revenue_usd"]["value"] <= 0:
            continue
        cash = facts["operating_cash_flow_usd"]["value"] - facts["capex_usd"]["value"]
        margin = cash / facts["revenue_usd"]["value"]
        if not math.isfinite(margin):
            continue
        annual.append(fiscal)
    annual.sort(reverse=True)
    if len(annual) < 2:
        return False, "Fewer than two fully filed fiscal periods", None
    latest, previous = annual[:2]
    if not 300 <= (date(latest) - date(previous)).days <= 430:
        return False, "Most recent available periods are not consecutive", latest
    if (date(as_of) - date(latest)).days > 800:
        return False, "Most recent available fiscal period is stale", latest
    return True, "Eligible", latest


def report(archive: dict, snapshot: dict, decisions: list[str], selection: list[str]) -> dict:
    """Validate first; never turn a missing issuer/date into a successful window."""
    audited = audit(archive, snapshot)
    if not decisions or len(set(decisions)) != len(decisions):
        raise ValueError("Require distinct decision dates")
    if any(date(point) > date(archive["as_of"]) for point in decisions):
        raise ValueError("Decision date cannot exceed the archive source cutoff")
    if len(selection) > 5 or len(selection) != len(set(selection)):
        raise ValueError("Selected comparison universe must have at most five distinct companies")
    registry = {issuer["symbol"]: issuer for issuer in archive["companies"]}
    reference = {item["symbol"] for item in snapshot["companies"]}
    if any(symbol not in reference for symbol in selection):
        raise ValueError("Selected universe contains unsupported issuer")
    rows = []
    eligible_dates_by_issuer = {}
    missing_reasons = Counter()
    for symbol in sorted(reference):
        issuer = registry.get(symbol)
        available = []
        unavailable = Counter()
        for decision in decisions:
            if issuer is None:
                reason = "Issuer absent from local archive"
                ready = False
            else:
                ready, reason, _ = check_issuer(issuer, decision)
            if ready:
                available.append(decision)
            else:
                unavailable[reason] += 1
                missing_reasons[reason] += 1
        primary_reason = unavailable.most_common(1)[0][0] if unavailable else None
        rows.append({
            "symbol": symbol,
            "imported": issuer is not None,
            "annual_periods": len(issuer["annual"]) if issuer else 0,
            "eligible_dates": len(available),
            "scheduled_dates": len(decisions),
            "coverage_pct": round(100 * len(available) / len(decisions), 2),
            "first_eligible": available[0] if available else None,
            "last_eligible": available[-1] if available else None,
            "main_gap": primary_reason,
        })
        eligible_dates_by_issuer[symbol] = set(available)
    full_dates = sorted(set(decisions).intersection(*(eligible_dates_by_issuer[s] for s in selection))) if selection else []
    return {
        "schema": "quantforge.sec-archive-coverage.v10.0",
        "as_of": archive["as_of"],
        "provenance": audited,
        "snapshot_issuers": len(reference),
        "archive_issuers": len(registry),
        "scheduled_dates": decisions,
        "selected_universe": selection,
        "selected_complete_dates": full_dates,
        "selected_complete_count": len(full_dates),
        "major_gaps": dict(missing_reasons.most_common(8)),
        "issuers": rows,
        "limitations": [
            "Coverage refers only to surviving current issuer definitions in the reference snapshot.",
            "SEC Company Facts can omit superseded original disclosures; this is not proof of complete historical filings.",
            "Price history, delistings, dividends, and action execution are not covered by this audit.",
            "No forecast, expected return or actual investor suitability is estimated.",
        ],
    }


def make_decisions(start_year: int, stop_year: int, cutoff: str) -> list[str]:
    if not 2009 <= start_year <= stop_year <= 2100:
        raise ValueError("Invalid date range")
    return [
        item for year in range(start_year, stop_year + 1)
        for item in (f"{year}-01-01", f"{year}-07-01")
        if item <= cutoff
    ]


def atomic_write(path: Path, content: str) -> None:
    allowed = (ROOT / "data").resolve()
    target = path.resolve()
    if target == allowed or not target.is_relative_to(allowed):
        raise ValueError("Coverage reports must remain under ignored data/")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".pending")
    temp.write_text(content, encoding="utf-8")
    temp.replace(target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "data/sec_filing_revisions_v98.json")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "web/site/sec_snapshot.json")
    parser.add_argument("--report", type=Path, default=ROOT / "data/sec_archive_coverage_v100.json")
    parser.add_argument("--csv", type=Path, default=ROOT / "data/sec_archive_coverage_v100.csv")
    parser.add_argument("--start-year", type=int, default=2011)
    parser.add_argument("--symbols", default="", help="Optional comma-separated selected universe (2–5)")
    args = parser.parse_args()
    archive = json.loads(args.archive.read_text(encoding="utf-8"))
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    decisions = make_decisions(args.start_year, date(archive["as_of"]).year, archive["as_of"])
    selection = [x.strip().upper() for x in args.symbols.split(",") if x.strip()]
    if selection and not 2 <= len(selection) <= 5:
        parser.error("Selected universe must contain 2–5 companies")
    results = report(archive, snapshot, decisions, selection)
    atomic_write(args.report, json.dumps(results, indent=2, sort_keys=True) + "\n")
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(results["issuers"][0]))
    writer.writeheader()
    writer.writerows(results["issuers"])
    atomic_write(args.csv, buffer.getvalue())
    print(f"Validated {results['archive_issuers']}/{results['snapshot_issuers']} issuers; "
          f"analyzed {len(decisions)} dated checkpoints. Local report: {args.report}")
    if selection:
        print(f"Selected universe {', '.join(selection)}: "
              f"{results['selected_complete_count']}/{len(decisions)} checkpoints eligible")


if __name__ == "__main__":
    main()
