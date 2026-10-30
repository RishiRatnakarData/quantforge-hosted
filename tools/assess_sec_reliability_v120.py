"""Summarize historical SEC coverage attrition and disclosure timeliness offline.

Research-only: no prices, provider account, trading decisions, or publication.
The present-day issuer denominator is never reduced to optimize displayed coverage.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from io import StringIO
from pathlib import Path

from historical_sec_panel_v110 import atomic_write, panel
from report_sec_archive_v100 import make_decisions
from validate_local_sec_archive_v99 import ROOT, date


def longest_run(flags: list[bool]) -> int:
    """Find the longest consecutively eligible sequence without filling gaps."""
    best = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        best = max(best, current)
    return best


def assess(source: dict) -> dict:
    """Aggregate only after an independently validated V11.0 panel."""
    if source.get("schema") != "quantforge.local-sec-historical-panel.v11.0":
        raise ValueError("Unsupported historical panel schema")
    reference = source.get("reference_issuers")
    checkpoints = source.get("total_checkpoints")
    rows = source.get("detail_rows")
    if not isinstance(reference, int) or not isinstance(checkpoints, int) or reference < 1 or checkpoints < 1:
        raise ValueError("Invalid historical coverage denominator")
    if not isinstance(rows, list) or len(rows) != reference * checkpoints:
        raise ValueError("Incomplete historical panel: every issuer/date must be retained")
    cohorts = source.get("cohorts")
    if not isinstance(cohorts, list) or len(cohorts) != checkpoints:
        raise ValueError("Incomplete historical checkpoint cohorts")
    timeline = [cohort["checkpoint"] for cohort in cohorts]
    if sorted(set(timeline)) != timeline:
        raise ValueError("Invalid historical checkpoint order")
    by_issuer = defaultdict(dict)
    by_year = defaultdict(lambda: {"scheduled": 0, "eligible": 0, "gaps": Counter()})
    source_gaps = Counter()
    for row in rows:
        symbol = row.get("symbol")
        checkpoint = row.get("checkpoint")
        if not isinstance(symbol, str) or checkpoint not in timeline:
            raise ValueError("Invalid issuer or decision checkpoint")
        if checkpoint in by_issuer[symbol]:
            raise ValueError("Duplicate issuer and checkpoint")
        eligible = row.get("eligible")
        if not isinstance(eligible, bool):
            raise ValueError("Historical coverage eligibility must be boolean")
        if eligible:
            filed = row.get("latest_filed")
            if not isinstance(filed, str) or filed > checkpoint or date(filed) > date(checkpoint):
                raise ValueError("Future information detected in point-in-time evidence")
        by_issuer[symbol][checkpoint] = row
        year = checkpoint[:4]
        by_year[year]["scheduled"] += 1
        if eligible:
            by_year[year]["eligible"] += 1
        else:
            gap = str(row.get("reason") or "Unclassified gap")[:120]
            source_gaps[gap] += 1
            by_year[year]["gaps"][gap] += 1
    if len(by_issuer) != reference or any(len(items) != checkpoints for items in by_issuer.values()):
        raise ValueError("Issuer/date matrix is missing cells")
    issuers = []
    for symbol in sorted(by_issuer):
        ordered = [by_issuer[symbol][day] for day in timeline]
        good = [row for row in ordered if row["eligible"]]
        gaps = Counter(str(r.get("reason") or "Unclassified gap")[:120] for r in ordered if not r["eligible"])
        latencies = [(date(row["latest_filed"]) - date(row["fiscal_end"])).days for row in good]
        if any(lag < 0 for lag in latencies):
            raise ValueError("Negative reported filing lag")
        issuers.append({
            "symbol": symbol,
            "eligible": len(good),
            "scheduled": checkpoints,
            "coverage_pct": round(100 * len(good) / checkpoints, 2),
            "first_eligible": good[0]["checkpoint"] if good else None,
            "last_eligible": good[-1]["checkpoint"] if good else None,
            "longest_eligible_run": longest_run([r["eligible"] for r in ordered]),
            "later_version_windows": sum(bool(r.get("later_version_seen")) for r in good),
            "median_filing_lag_days": round(statistics.median(latencies), 1) if latencies else None,
            "leading_gap": gaps.most_common(1)[0][0] if gaps else None,
        })
    years = []
    for year, values in sorted(by_year.items()):
        years.append({
            "year": int(year),
            "scheduled": values["scheduled"],
            "eligible": values["eligible"],
            "coverage_pct": round(100 * values["eligible"] / values["scheduled"], 2),
            "leading_gap": values["gaps"].most_common(1)[0][0] if values["gaps"] else None,
        })
    eligible = sum(i["eligible"] for i in issuers)
    if eligible != source.get("eligible_issuer_checkpoints"):
        raise ValueError("Aggregate eligible count does not match input panel")
    return {
        "schema": "quantforge.sec-reliability.v12.0",
        "source_archive_sha256": source.get("source_sha256"),
        "archive_cutoff": source.get("archive_cutoff"),
        "reference_issuers": reference,
        "checkpoints": checkpoints,
        "scheduled_issuer_dates": len(rows),
        "eligible_issuer_dates": eligible,
        "withheld_issuer_dates": len(rows) - eligible,
        "coverage_pct": round(100 * eligible / len(rows), 2),
        "leading_missingness": dict(source_gaps.most_common(8)),
        "per_year": years,
        "per_issuer": issuers,
        "limitations": [
            "Reference universe is today's supported issuers, not historical index membership.",
            "SEC Company Facts does not guarantee complete superseded original filings.",
            "Later filing versions are not necessarily accounting restatements.",
            "Filing eligibility does not establish price availability, tradability or predictive returns.",
            "A complete issuer/date matrix is retained, including missing evidence.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "data/sec_filing_revisions_v98.json")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "web/site/sec_snapshot.json")
    parser.add_argument("--start-year", type=int, default=2011)
    parser.add_argument("--json", type=Path, default=ROOT / "data/sec_reliability_v120.json")
    parser.add_argument("--csv", type=Path, default=ROOT / "data/sec_reliability_issuers_v120.csv")
    args = parser.parse_args()
    archive = json.loads(args.archive.read_text(encoding="utf-8"))
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    decisions = make_decisions(args.start_year, date(archive["as_of"]).year, archive["as_of"])
    report = assess(panel(archive, snapshot, decisions))
    atomic_write(args.json, json.dumps(report, indent=2, sort_keys=True) + "\n")
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(report["per_issuer"][0]))
    writer.writeheader()
    writer.writerows(report["per_issuer"])
    atomic_write(args.csv, buffer.getvalue())
    print(
        f"V12.0 SEC reliability: {report['reference_issuers']} issuers, "
        f"{report['eligible_issuer_dates']}/{report['scheduled_issuer_dates']} "
        "eligible issuer-checkpoints; JSON/CSV remain in ignored data/."
    )


if __name__ == "__main__":
    main()
