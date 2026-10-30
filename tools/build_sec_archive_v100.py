"""Resumable fair-access SEC Company Facts archive collection and coverage audit.

This tool is never invoked by the website build, CI, or authenticated API.
Only official public SEC responses are cached under Git-ignored data/. The
archive is eligible for private browser import only after offline validation.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from build_sec_filing_archive_v98 import ROOT, SOURCE, build, extract_issuer
from report_sec_archive_v100 import atomic_write, make_decisions, report
from validate_local_sec_archive_v99 import audit

MAX_BYTES = 18_000_000
MAX_ISSUERS = 100
SEC_CONTACT = re.compile(r"^[^\r\n]{4,160}\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b[^\r\n]*$")


def validate_user_agent(agent: str) -> str:
    if (not SEC_CONTACT.fullmatch(agent) or
        any(x in agent.lower() for x in ("example.com", "test@test", "sample@"))):
        raise ValueError("SEC_USER_AGENT must contain your truthful app/organization and actual contact email")
    return agent


def parse_payload(payload: bytes, cik: int, symbol: str) -> dict:
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError(f"{symbol}: SEC response empty or over 18 MB")
    try:
        data = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{symbol}: invalid SEC JSON response") from exc
    if not isinstance(data, dict) or data.get("cik") != cik:
        raise ValueError(f"{symbol}: SEC CIK mismatch or invalid response")
    if not isinstance(data.get("facts", {}).get("us-gaap"), dict):
        raise ValueError(f"{symbol}: no SEC US-GAAP source facts")
    return data


def fetch_sec(cik: int, agent: str, *, attempts: int = 4,
              opener=urllib.request.urlopen, sleeper=time.sleep) -> bytes:
    """Bounded retries; honor transient rate limiting without aggressive polling."""
    if not isinstance(cik, int) or cik <= 0 or attempts < 1 or attempts > 5:
        raise ValueError("Invalid SEC request parameters")
    validate_user_agent(agent)
    request = urllib.request.Request(SOURCE.format(cik), headers={
        "User-Agent": agent, "Accept": "application/json", "Accept-Encoding": "identity"
    })
    for attempt in range(attempts):
        try:
            with opener(request, timeout=45) as response:
                data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError("SEC response exceeds 18 MB")
            return data
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt + 1 == attempts:
                raise
            # Never hammer the SEC. Do not trust arbitrarily large Retry-After.
            retry = exc.headers.get("Retry-After") if exc.headers else None
            delay = min(60, max(4 * 2**attempt, int(retry))) if retry and retry.isdecimal() else 4 * 2**attempt
            sleeper(delay)
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 == attempts:
                raise
            sleeper(4 * 2**attempt)
    raise RuntimeError("SEC request exhausted retries")


def collect(snapshot: dict, *, cache_dir: Path, as_of: str,
            max_issuers: int = MAX_ISSUERS, max_years: int = 15,
            agent: str | None = None, offline: bool = False,
            overwrite_cache: bool = False, sleeper=time.sleep,
            fetcher=fetch_sec) -> tuple[dict, list[dict]]:
    """Validate every cached/downloaded CIK; keep failures visible, never invent facts."""
    if snapshot.get("dataset") != "SEC EDGAR Company Facts, annual 10-K US-GAAP":
        raise ValueError("Require validated public SEC seed snapshot")
    issuers = snapshot.get("companies")
    if not isinstance(issuers, list) or not 1 <= len(issuers) <= 500:
        raise ValueError("Invalid SEC seed universe")
    if not 1 <= max_issuers <= MAX_ISSUERS or not 1 <= max_years <= 25:
        raise ValueError("Requested issuer/year range outside bounded limits")
    if dt.date.fromisoformat(as_of) > dt.date.today():
        raise ValueError("SEC archive cutoff cannot be in the future")
    if not offline:
        validate_user_agent(agent or "")
    root = (ROOT / "data").resolve()
    cache_dir = cache_dir.resolve()
    if cache_dir == root or not cache_dir.is_relative_to(root):
        raise ValueError("Raw SEC cache must remain in ignored data/ subdirectory")
    cache_dir.mkdir(parents=True, exist_ok=True)
    selected = issuers[:max_issuers]
    raws = {}
    failures = []
    identities = set()
    for i, issuer in enumerate(selected):
        symbol, cik = issuer.get("symbol"), issuer.get("cik")
        if (not isinstance(symbol, str) or not re.fullmatch(r"[A-Z0-9.\-]{1,15}", symbol)
            or not isinstance(cik, int) or isinstance(cik, bool) or cik <= 0
            or symbol in identities):
            raise ValueError("Duplicate or invalid issuer in snapshot")
        identities.add(symbol)
        file = cache_dir / f"CIK{cik:010d}.json"
        payload = None
        try:
            if file.exists() and not overwrite_cache:
                if file.stat().st_size > MAX_BYTES:
                    raise ValueError("Cached SEC response too large")
                payload = file.read_bytes()
            elif offline:
                raise FileNotFoundError("No previously cached SEC Company Facts")
            else:
                # No more than one ordinary request each 1.2 seconds, including retries.
                if i:
                    sleeper(1.2)
                payload = fetcher(cik, agent)
            raw = parse_payload(payload, cik, symbol)
            # Only cache after full issuer structural check, not a 200/error-body.
            extract_issuer(raw, symbol, cik, as_of, max_years=max_years)
            if not file.exists() or overwrite_cache:
                tmp = file.with_suffix(".pending")
                tmp.write_bytes(payload)
                tmp.replace(file)
            raws[symbol] = raw
        except (ValueError, OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
            failures.append({"symbol": symbol, "reason": str(exc)[:160]})
    archival = build({**snapshot, "companies": selected}, raws, as_of, max_years=max_years)
    return archival, failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=ROOT / "web/site/sec_snapshot.json")
    parser.add_argument("--archive", type=Path, default=ROOT / "data/sec_filing_revisions_v98.json")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data/sec_companyfacts_cache")
    parser.add_argument("--report", type=Path, default=ROOT / "data/sec_archive_coverage_v100.json")
    parser.add_argument("--max-issuers", type=int, default=MAX_ISSUERS)
    parser.add_argument("--max-years", type=int, default=15)
    parser.add_argument("--start-year", type=int, default=2011)
    parser.add_argument("--cutoff", default=dt.date.today().isoformat())
    parser.add_argument("--symbols", default="", help="Optional 2–5 selected companies for complete-window audit")
    parser.add_argument("--offline", action="store_true", help="Use verified cached SEC API responses; do not fetch")
    parser.add_argument("--refresh", action="store_true", help="Fetch updated SEC responses even if cached")
    args = parser.parse_args()
    if args.offline and args.refresh:
        parser.error("--offline and --refresh cannot be combined")
    for path in (args.archive, args.report):
        target = path.resolve()
        root = (ROOT / "data").resolve()
        if target == root or not target.is_relative_to(root):
            parser.error("Local archive and report must be under ignored data/")
    try:
        cutoff = dt.date.fromisoformat(args.cutoff)
        if cutoff > dt.date.today():
            raise ValueError("future cutoff")
    except ValueError:
        parser.error("Cutoff must be a valid nonfuture ISO date")
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    archive, failures = collect(
        snapshot, cache_dir=args.cache_dir, as_of=args.cutoff,
        max_issuers=args.max_issuers, max_years=args.max_years,
        offline=args.offline, overwrite_cache=args.refresh,
        agent=os.environ.get("SEC_USER_AGENT"),
    )
    if not archive["companies"]:
        raise ValueError("No verified SEC issuers; existing archive preserved")
    audit(archive, snapshot)
    selected = [x.strip().upper() for x in args.symbols.split(",") if x.strip()]
    if selected and not 2 <= len(selected) <= 5:
        parser.error("--symbols requires 2–5 companies")
    dates = make_decisions(args.start_year, cutoff.year, args.cutoff)
    coverage = report(archive, snapshot, dates, selected)
    coverage["collection"] = {
        "requested_issuers": min(args.max_issuers, len(snapshot["companies"])),
        "collected_issuers": len(archive["companies"]),
        "failed_issuers": failures,
        "resumable_cache": True,
    }
    # The V9.9 browser importer rejects files over 24 MB; fail before overwriting.
    archive_text = json.dumps(archive, indent=2, sort_keys=True) + "\n"
    if len(archive_text.encode("utf-8")) > 24 * 1024 * 1024:
        raise ValueError("Validated archive exceeds 24 MB private browser import limit; reduce --max-years or --max-issuers")
    # Build both outputs before atomic replacement; no archive is written to public/.
    atomic_write(args.archive, archive_text)
    atomic_write(args.report, json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    print(f"SEC ARCHIVE: {len(archive['companies'])}/{coverage['collection']['requested_issuers']} "
          f"issuers collected. Source facts: {coverage['provenance']['source_facts']}. "
          f"Failures: {len(failures)}.")
    print(f"Validated local archive: {args.archive}\nCoverage report: {args.report}")
    if failures:
        print("Incomplete coverage (rerun to resume cached successful issuers):")
        for failure in failures[:12]:
            print(f"  {failure['symbol']}: {failure['reason']}")


if __name__ == "__main__":
    main()
