"""Offline V13.0 audit of SEC archive -> historical panel -> coverage lineage.

Writes only to the Git-ignored data/ directory. No provider or brokerage access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from historical_sec_panel_v110 import atomic_write
from validate_local_sec_archive_v99 import ROOT, audit


def reconcile(archive: dict, snapshot: dict, panel: dict, reliability: dict) -> dict:
    """Refuse mismatched, incomplete, or stale evidence matrices."""
    audited = audit(archive, snapshot)
    if panel.get("schema") != "quantforge.local-sec-historical-panel.v11.0":
        raise ValueError("Incorrect historical-panel schema")
    if reliability.get("schema") != "quantforge.sec-reliability.v12.0":
        raise ValueError("Incorrect SEC reliability schema")
    digest = hashlib.sha256(
        json.dumps(archive, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if (panel.get("source_sha256") != digest or
        reliability.get("source_archive_sha256") != digest or
        panel.get("archive_cutoff") != archive["as_of"] or
        reliability.get("archive_cutoff") != archive["as_of"]):
        raise ValueError("Archived filing lineage or cutoff does not match")
    issuer_set = {row["symbol"] for row in snapshot["companies"]}
    n = len(issuer_set)
    if n != panel.get("reference_issuers") or n != reliability.get("reference_issuers"):
        raise ValueError("Full reference issuer denominator changed")
    dates = [row["checkpoint"] for row in panel.get("cohorts", [])]
    if (not dates or dates != sorted(set(dates)) or
        reliability.get("checkpoints") != len(dates)):
        raise ValueError("Historical checkpoint chronology mismatch")
    detail = panel.get("detail_rows")
    if not isinstance(detail, list) or len(detail) != n * len(dates):
        raise ValueError("Incomplete historical issuer/checkpoint matrix")
    observed = set()
    covered = 0
    by_issuer = Counter()
    by_checkpoint = Counter()
    for row in detail:
        pair = (row.get("symbol"), row.get("checkpoint"))
        if pair in observed or pair[0] not in issuer_set or pair[1] not in dates:
            raise ValueError("Duplicate or unsupported historical issuer checkpoint")
        observed.add(pair)
        if not isinstance(row.get("eligible"), bool):
            raise ValueError("Invalid SEC checkpoint eligibility")
        if row["eligible"]:
            if not isinstance(row.get("latest_filed"), str) or row["latest_filed"] > pair[1]:
                raise ValueError("Future SEC filing leaked into historical checkpoint")
            covered += 1
            by_issuer[pair[0]] += 1
            by_checkpoint[pair[1]] += 1
    reported_issuers = reliability.get("per_issuer", [])
    if (not isinstance(reported_issuers, list) or len(reported_issuers) != n or
        {r.get("symbol") for r in reported_issuers} != issuer_set or
        any(r.get("eligible") != by_issuer[r.get("symbol")] or
            r.get("scheduled") != len(dates) for r in reported_issuers)):
        raise ValueError("Issuer-level SEC coverage totals disagree with source rows")
    if any("eligible" in c and c["eligible"] != by_checkpoint[c["checkpoint"]]
           for c in panel["cohorts"]):
        raise ValueError("Checkpoint-level SEC coverage totals disagree with source rows")
    if (covered != panel.get("eligible_issuer_checkpoints") or
        covered != reliability.get("eligible_issuer_dates") or
        len(detail) != reliability.get("scheduled_issuer_dates") or
        len(detail) - covered != reliability.get("withheld_issuer_dates") or
        len(reliability.get("per_issuer", [])) != n):
        raise ValueError("SEC coverage aggregation or report denominator mismatch")
    return {
        "schema": "quantforge.research-chain-integrity.v13.0",
        "archive_cutoff": archive["as_of"],
        "archive_sha256": digest,
        "reference_issuers": n,
        "checkpoints": len(dates),
        "scheduled": len(detail),
        "eligible": covered,
        "withheld": len(detail) - covered,
        "coverage_pct": round(100 * covered / len(detail), 2),
        "source_validation": "pass",
        "lineage_validation": "pass",
        "caveat": "Point-in-time source coverage is not original-filing completeness, accuracy or investability.",
        "audit_issuer_count": audited.get("issuer_count", n),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "data/sec_filing_revisions_v98.json")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "web/site/sec_snapshot.json")
    parser.add_argument("--panel", type=Path, default=ROOT / "data/sec_historical_panel_v110.json")
    parser.add_argument("--reliability", type=Path, default=ROOT / "data/sec_reliability_v120.json")
    parser.add_argument("--out", type=Path, default=ROOT / "data/sec_research_integrity_v130.json")
    args = parser.parse_args()
    def load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    result = reconcile(load(args.archive), load(args.snapshot), load(args.panel), load(args.reliability))
    atomic_write(args.out, json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"V13.0 SEC lineage verified: {result['eligible']}/{result['scheduled']} eligible, "
          f"{result['reference_issuers']} current issuers. Only ignored data/ changed.")


if __name__ == "__main__":
    main()
