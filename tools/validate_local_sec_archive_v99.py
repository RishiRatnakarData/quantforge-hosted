"""Validate the optional locally stored SEC revision archive without network access.

Does not publish historical filings, touch private holdings, or claim that SEC
Company Facts contains every superseded source value. Keeps all outputs local.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path

from extend_public_sec_v79 import TAGS

ROOT = Path(__file__).resolve().parents[1]
DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
ACC = re.compile(r"\d{10}-\d{2}-\d{6}\Z")
SYMBOL = re.compile(r"[A-Z0-9.\-]{1,15}\Z")
FIELDS = ("revenue_usd", "operating_cash_flow_usd", "capex_usd")


def date(value: object) -> dt.date:
    if not isinstance(value, str) or not DATE.fullmatch(value):
        raise ValueError("Malformed filing date")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Impossible filing date") from exc


def audit(archive: dict, snapshot: dict) -> dict:
    """Fail closed on malformed lineage; report coverage, never claim completeness."""
    if archive.get("schema") != "quantforge.sec.filing-revisions.v9.8":
        raise ValueError("Unknown SEC revision archive schema")
    cutoff = date(archive.get("as_of"))
    if cutoff > dt.date.today():
        raise ValueError("Archive cutoff is in the future")
    companies = archive.get("companies")
    if not isinstance(companies, list) or not 1 <= len(companies) <= 100:
        raise ValueError("Archive issuer count outside 1–100")
    reference = snapshot.get("companies")
    if not isinstance(reference, list):
        raise ValueError("Valid published SEC issuer reference required")
    ciks = {company.get("symbol"): company.get("cik") for company in reference}
    if len(ciks) != len(reference):
        raise ValueError("Duplicate source reference identifiers")

    seen: set[str] = set()
    total_periods = total_revisions = later_versions = 0
    for company in companies:
        symbol = company.get("symbol")
        cik = company.get("cik")
        if (
            not isinstance(symbol, str)
            or not SYMBOL.fullmatch(symbol)
            or symbol in seen
            or not isinstance(cik, int)
            or isinstance(cik, bool)
            or cik <= 0
            or ciks.get(symbol) != cik
        ):
            raise ValueError("Duplicate issuer or mismatched SEC CIK")
        seen.add(symbol)
        periods = company.get("annual")
        if not isinstance(periods, list) or not 1 <= len(periods) <= 25:
            raise ValueError("Invalid fiscal period count")
        used_ends: set[str] = set()
        total_periods += len(periods)
        for period in periods:
            fiscal = date(period.get("fiscal_end"))
            if fiscal > cutoff or str(fiscal) in used_ends:
                raise ValueError("Duplicate/future fiscal year")
            used_ends.add(str(fiscal))
            data = period.get("revisions")
            if not isinstance(data, dict):
                raise ValueError("Missing filing revisions")
            for field in FIELDS:
                revisions = data.get(field)
                if not isinstance(revisions, list) or len(revisions) > 500:
                    raise ValueError("Missing/oversized field revision list")
                versions: dict[tuple, float] = {}
                dates: set[str] = set()
                for row in revisions:
                    start = date(row.get("start"))
                    filed = date(row.get("filed"))
                    accession = row.get("accession")
                    tag = row.get("tag")
                    priority = row.get("tag_priority")
                    value = row.get("value")
                    if (
                        not 330 <= (fiscal - start).days <= 400
                        or not fiscal <= filed <= cutoff
                        or not isinstance(accession, str)
                        or not ACC.fullmatch(accession)
                        or tag not in TAGS[field]
                        or not isinstance(priority, int)
                        or isinstance(priority, bool)
                        or priority != TAGS[field].index(tag)
                        or not isinstance(value, (int, float))
                        or isinstance(value, bool)
                        or not math.isfinite(value)
                        or abs(value) >= 1e16
                        or (field == "capex_usd" and value < 0)
                    ):
                        raise ValueError("Invalid SEC source fact or disclosure chronology")
                    identity = (str(start), str(filed), accession, tag)
                    if identity in versions and versions[identity] != value:
                        raise ValueError("Conflicting duplicate SEC source fact")
                    versions[identity] = value
                    dates.add(str(filed))
                    total_revisions += 1
                    if total_revisions > 250_000:
                        raise ValueError("Archive exceeds source fact limit")
                if len(dates) > 1:
                    later_versions += 1

    return {
        "schema": "quantforge.local-sec-audit.v9.9",
        "issuer_count": len(companies),
        "fiscal_periods": total_periods,
        "source_facts": total_revisions,
        "fields_with_later_versions": later_versions,
        "source_cutoff": str(cutoff),
        "caveat": "Validated source structure, not a certification of original-filing completeness or historical investability.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive", type=Path,
        default=ROOT / "data/sec_filing_revisions_v98.json",
    )
    parser.add_argument(
        "--snapshot", type=Path, default=ROOT / "web/site/sec_snapshot.json"
    )
    args = parser.parse_args()
    allowed = (ROOT / "data").resolve()
    target = args.archive.resolve()
    if not target.is_relative_to(allowed) or target == allowed:
        parser.error("Archive must remain under local ignored data/")
    if target.stat().st_size > 24 * 1024 * 1024:
        parser.error("Archive exceeds the 24 MB browser import limit")
    raw = target.read_bytes()
    result = audit(
        json.loads(raw), json.loads(args.snapshot.read_text(encoding="utf-8"))
    )
    result["archive_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
