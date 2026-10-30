"""Build an offline, point-in-time SEC company-evidence panel (not a trading backtest).

Reads the validated locally collected V10.0 archive; writes only ignored data/ outputs.
The issuer list is today's snapshot, so historical membership is survivorship-biased.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from io import StringIO
from pathlib import Path

from report_sec_archive_v100 import FIELDS, make_decisions, select_revision
from validate_local_sec_archive_v99 import ROOT, audit, date


def evidence_at(issuer: dict, at: str) -> dict:
    """Use reported facts whose SEC filing date is no later than the checkpoint."""
    rows = []
    for period in issuer["annual"]:
        fiscal = period["fiscal_end"]
        if fiscal > at:
            continue
        facts = {
            name: select_revision(period["revisions"][name], fiscal, at)
            for name in FIELDS
        }
        if any(value is None for value in facts.values()):
            continue
        revenue = facts["revenue_usd"]["value"]
        if revenue <= 0:
            continue
        fcf = (
            facts["operating_cash_flow_usd"]["value"]
            - facts["capex_usd"]["value"]
        )
        if not math.isfinite(fcf / revenue):
            continue
        rows.append((fiscal, revenue, fcf, facts))
    rows.sort(key=lambda x: x[0], reverse=True)
    if len(rows) < 2:
        return {"ready": False, "reason": "Fewer than two complete filed annual periods"}
    recent, previous = rows[:2]
    if not 300 <= (date(recent[0]) - date(previous[0])).days <= 430:
        return {"ready": False, "reason": "Nonconsecutive fiscal periods"}
    if (date(at) - date(recent[0])).days > 800:
        return {"ready": False, "reason": "Stale fiscal periods"}
    growth = recent[1] / previous[1] - 1
    margin = recent[2] / recent[1]
    if not all(math.isfinite(x) for x in (growth, margin)):
        return {"ready": False, "reason": "Nonfinite reported ratios"}
    filed = max(
        item["filed"] for row in (recent, previous) for item in row[3].values()
    )
    revision = any(
        any(
            earlier["filed"] < selected["filed"]
            for earlier in next(p for p in issuer["annual"] if p["fiscal_end"] == row[0])["revisions"][name]
            if earlier["filed"] <= at
        )
        for row in (recent, previous)
        for name, selected in row[3].items()
    )
    return {
        "ready": True,
        "fiscal_end": recent[0],
        "latest_filed": filed,
        "revenue_growth": round(growth, 6),
        "fcf_margin": round(margin, 6),
        "later_version_seen": revision,
    }


def panel(archive: dict, snapshot: dict, decisions: list[str]) -> dict:
    """Entire snapshot denominator is retained; absent issuers are unavailable."""
    audit(archive, snapshot)
    if not decisions or len(set(decisions)) != len(decisions) or decisions != sorted(decisions):
        raise ValueError("Decision checkpoints must be unique and increasing")
    if any(date(day) > date(archive["as_of"]) for day in decisions):
        raise ValueError("A decision checkpoint exceeds SEC source cutoff")
    registry = {issuer["symbol"]: issuer for issuer in archive["companies"]}
    supported = sorted(company["symbol"] for company in snapshot["companies"])
    entries = []
    cohorts = []
    per_issuer = Counter()
    for day in decisions:
        qualified = []
        reasons = Counter()
        for symbol in supported:
            issuer = registry.get(symbol)
            result = evidence_at(issuer, day) if issuer else {
                "ready": False, "reason": "Issuer missing from archive"
            }
            if not result["ready"]:
                reasons[result["reason"]] += 1
            else:
                per_issuer[symbol] += 1
                qualified.append((symbol, result))
            entries.append({
                "checkpoint": day,
                "symbol": symbol,
                "eligible": result["ready"],
                "reason": None if result["ready"] else result["reason"],
                "fiscal_end": result.get("fiscal_end"),
                "latest_filed": result.get("latest_filed"),
                "revenue_growth": result.get("revenue_growth"),
                "fcf_margin": result.get("fcf_margin"),
                "later_version_seen": result.get("later_version_seen", False),
            })
        margins = [row["fcf_margin"] for _, row in qualified]
        growths = [row["revenue_growth"] for _, row in qualified]
        positive = [
            (symbol, row) for symbol, row in qualified
            if row["revenue_growth"] > 0 and row["fcf_margin"] > 0
        ]
        positive.sort(key=lambda pair: (-pair[1]["fcf_margin"], -pair[1]["revenue_growth"], pair[0]))
        cohorts.append({
            "checkpoint": day,
            "reference_issuers": len(supported),
            "eligible": len(qualified),
            "unavailable": len(supported) - len(qualified),
            "coverage_pct": round(100 * len(qualified) / len(supported), 2),
            "positive_screen_count": len(positive),
            "median_revenue_growth": round(statistics.median(growths), 6) if growths else None,
            "median_fcf_margin": round(statistics.median(margins), 6) if margins else None,
            "positive_screen_top5": [symbol for symbol, _ in positive[:5]],
            "main_gaps": dict(reasons.most_common(4)),
        })
    return {
        "schema": "quantforge.local-sec-historical-panel.v11.0",
        "archive_cutoff": archive["as_of"],
        "source_sha256": hashlib.sha256(
            json.dumps(archive, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "reference_issuers": len(supported),
        "archived_issuers": len(registry),
        "total_checkpoints": len(decisions),
        "issuer_checkpoint_rows": len(entries),
        "eligible_issuer_checkpoints": sum(row["eligible"] for row in entries),
        "issuer_coverage": [
            {"symbol": symbol, "eligible": per_issuer[symbol], "scheduled": len(decisions)}
            for symbol in supported
        ],
        "cohorts": cohorts,
        "detail_rows": entries,
        "limitations": [
            "The study uses today's surviving companies; historical members and delistings are not reconstructed.",
            "Company Facts may exclude superseded filings; recorded revisions do not prove original-data completeness.",
            "Cash flow is operating cash flow minus capital expenditures; industry accounting conventions can differ.",
            "Ranked screens describe historical reported characteristics, not return forecasts or executable investment rankings.",
            "No price history, dividend adjustment, transaction execution or performance attribution is analyzed here.",
        ],
    }


def atomic_write(path: Path, content: str) -> None:
    """Atomically write only beneath ignored local data/, never to a public path."""
    target = path.resolve()
    allowed = (ROOT / "data").resolve()
    if target == allowed or not target.is_relative_to(allowed):
        raise ValueError("Historical research outputs must remain under ignored data/")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".pending")
    temp.write_text(content, encoding="utf-8")
    temp.replace(target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "data/sec_filing_revisions_v98.json")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "web/site/sec_snapshot.json")
    parser.add_argument("--start-year", type=int, default=2011)
    parser.add_argument("--json", type=Path, default=ROOT / "data/sec_historical_panel_v110.json")
    parser.add_argument("--csv", type=Path, default=ROOT / "data/sec_historical_panel_v110.csv")
    args = parser.parse_args()
    archive = json.loads(args.archive.read_text(encoding="utf-8"))
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    checks = make_decisions(args.start_year, date(archive["as_of"]).year, archive["as_of"])
    result = panel(archive, snapshot, checks)
    # JSON includes aggregated and per-issuer ratio evidence, never brokerage data or raw filing figures.
    atomic_write(args.json, json.dumps(result, indent=2, sort_keys=True) + "\n")
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(result["detail_rows"][0]))
    writer.writeheader()
    writer.writerows(result["detail_rows"])
    atomic_write(args.csv, buf.getvalue())
    print(f"V11.0 SEC panel: {result['archived_issuers']}/{result['reference_issuers']} issuers, "
          f"{result['eligible_issuer_checkpoints']}/{result['issuer_checkpoint_rows']} eligible issuer-checkpoints; "
          f"JSON and CSV remain under ignored data/. Source SHA: {result['source_sha256']}")


if __name__ == "__main__":
    main()
