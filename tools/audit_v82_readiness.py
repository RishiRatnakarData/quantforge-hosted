"""Fail-closed static V8.2 production-readiness audit, independent of private accounts.

Does not claim live Cloudflare deployment, sign-in success, or live price correctness.
"""
from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path

from build_v82_case_study import DATASET, SYMBOLS, canonical_snapshot_sha256, load_companies

PUBLIC_ROUTES = ("overview", "sec", "lab", "portfolio", "quant", "valuation", "ml", "systems", "methods")
PRIVATE_ROUTES = ("home", "trade", "ideas", "research", "optimization", "backtest", "walkforward", "valuation", "settings")


class Analyzer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = {}
        self.nav = {}
        self.links = []
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if "id" in attr:
            self.ids[attr["id"]] = self.ids.get(attr["id"], 0) + 1
        if tag == "button" and attr.get("data-page"):
            self.nav[attr["data-page"]] = self.nav.get(attr["data-page"], 0) + 1
        if tag == "a" and attr.get("href"):
            self.links.append(attr["href"])
        if tag == "script":
            self.scripts += 1


def audit(repo: Path):
    snapshot = repo / "web/site/sec_snapshot.json"
    raw = snapshot.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    assert data.get("dataset") == DATASET
    companies = load_companies(data)
    assert [c["symbol"] for c in companies] == list(SYMBOLS)
    template = (repo / "web/site/site.template.html").read_text(encoding="utf-8")
    built = (repo / "public/index.html").read_text(encoding="utf-8")
    study = (repo / "public/research-case-study.html").read_text(encoding="utf-8")
    ledger = (repo / "public/research-case-study.csv").read_text(encoding="utf-8")
    assert template.count("QF V8.2 PUBLIC RESEARCH CASE STUDY") == 1
    assert template.count('href="research-case-study.html"') == 1
    assert built.count('href="research-case-study.html"') == 1
    assert study.count('href="./research-case-study.csv"') == 1
    assert "Historical disclosures only" in study and "different fiscal" in study.lower()
    assert "Source snapshot SHA-256: <code>" + canonical_snapshot_sha256(raw) in study
    assert "source_accession" in ledger and "issuer_as_of" in ledger and "sec_companyfacts_url" in ledger
    main = Analyzer()
    main.feed(built)
    case = Analyzer()
    case.feed(study)
    for route in PUBLIC_ROUTES:
        assert main.ids.get("page-" + route) == 1, f"Public route {route} missing or duplicated"
        assert main.nav.get(route) == 1, f"Public nav {route} missing or duplicated"
    assert main.ids.get("qf-v82-case-study") == 1
    assert main.ids.get("private-mfa-code") == 1
    assert main.ids.get("private-signed") == 1
    assert main.ids.get("private-research-dataset") == 1
    for route in PRIVATE_ROUTES:
        assert f'data-private-view="{route}"' in built, f"Private route {route} missing"
    assert main.scripts == 3, "Must preserve exactly three protected public scripts"
    assert case.scripts == 0, "Case study is static; no script or private API calls"
    assert not any(count > 1 for count in case.ids.values()), "Case study has duplicate element ids"
    assert not any(count > 1 for count in main.ids.values()), "Compiled site has duplicate element ids"
    for token in ("ALPACA_API_SECRET_KEY", "SUPABASE_SERVICE_ROLE", "private_positions", "private-password"):
        assert token not in study and token not in ledger, f"Potential private marker in case study: {token}"
    print(f"V8.2 static readiness PASS: {len(data['companies'])} SEC companies, {len(companies)}-company reproducible study, 9 public routes, 9 protected private views, three CSP scripts, 0 case-study scripts, snapshot SHA {canonical_snapshot_sha256(raw)[:16]}...")
    print("Not tested by this audit: live Cloudflare deployment, authenticated API access, MFA, or real broker/provider availability.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, required=True)
    args = p.parse_args()
    audit(args.repo.resolve())


if __name__ == "__main__":
    main()
