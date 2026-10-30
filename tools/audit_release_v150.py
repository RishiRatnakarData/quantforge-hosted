"""Offline V15.0 release-boundary audit; authenticated workflows remain unverified."""

import argparse
import base64
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_IDS = (
    "qf-v150-data-scope-title", "qf-v150-acceptance", "qf-v150-checks",
    "qf-v150-status", "qf-v150-download", "qf-v150-reset",
    "qf-v140-next", "qf-v130-hub-result", "qf-v99-file",
    "private-mfa-code", "private-mfa-submit", "private-logout",
)
LIVE_TESTS = (
    "mfa", "provider", "research", "sec", "briefing", "archive",
)


class ContractParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.duplicates = []
        self.manual = set()
        self.public_scope = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicates.append(element_id)
            self.ids.add(element_id)
        if attributes.get("data-v150-check"):
            self.manual.add(attributes["data-v150-check"])
        if "qf-v150-data-scope" in attributes.get("class", "").split():
            self.public_scope += 1


def audit(page: str, headers: str) -> dict:
    parser = ContractParser()
    parser.feed(page)
    absent = sorted(set(REQUIRED_IDS) - parser.ids)
    if absent or parser.duplicates:
        raise ValueError("Missing or duplicate required HTML IDs: " + str((absent, parser.duplicates)))
    if parser.public_scope != 1 or parser.manual != set(LIVE_TESTS):
        raise ValueError("Release-scope or owner-checklist markup does not match approved interface.")
    scripts = re.findall(r"<script>(.*?)</script>", page, re.DOTALL)
    if len(scripts) != 3:
        raise ValueError("Exactly three inline CSP-hashed scripts required.")
    for script in scripts:
        code = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode("ascii")
        if "'sha256-" + code + "'" not in headers:
            raise ValueError("Compiled script SHA-256 missing from CSP.")
    if "default-src 'none'" not in headers or "connect-src 'self'" not in headers:
        raise ValueError("Privacy CSP boundary changed.")
    if "QFPrivateReleaseAcceptanceV150" not in scripts[-1]:
        raise ValueError("Private acceptance helper not bundled in third script.")
    for phrase in (
        "SEC-reported fundamentals", "Illustrative quantitative models",
        "Owner-only research", "not independently verified",
        "Export redacted acceptance JSON",
    ):
        if phrase not in page:
            raise ValueError("Missing release disclosure: " + phrase)
    return {
        "schema": "quantforge.release-contract.v15.0",
        "static_contract": "passed", "compiled_scripts": len(scripts),
        "public_data_scope": "separated-reported-modeled-private",
        "manual_acceptance": "not_independently_verified",
        "manual_checks": [dict(key=k, status="not-tested") for k in LIVE_TESTS],
        "note": "Static source/CSP validation is not an MFA, provider, note-persistence, or archived-SEC-import live test.",
    }


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--out", type=Path, default=ROOT / "data/v150_release_contract.json")
    args = cli.parse_args()
    page = (ROOT / "public/index.html").read_text(encoding="utf-8")
    headers = (ROOT / "public/_headers").read_text(encoding="utf-8")
    report = audit(page, headers)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("V15.0 static release contract PASS; live MFA/provider checks NOT VERIFIED. "
          + str(args.out))


if __name__ == "__main__":
    main()
