"""Offline V14.0 workspace UI release audit; does not assert live MFA success."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_IDS = (
    "qf-v140-next",
    "qf-v140-status",
    "qf-v140-steps",
    "qf-v140-progress",
    "qf-v140-lab-insight",
    "qf-v140-brief-insight",
    "qf-v130-hub-result",
    "qf-v130-brief",
    "qf-v99-file",
    "private-v90-run",
    "private-logout",
    "private-mfa-submit",
)
MANUAL = (
    "Fresh sign-in and successful authenticator challenge",
    "Authenticated portfolio balances and provider quotes",
    "2-5 company price history and completed research assessment",
    "Real locally imported SEC archive and historical coverage",
    "Cross-checked Research Hub, Lab, and Briefing in browser",
    "Saved research note persistence, deletion, and clean sign-out",
)


def audit(html: str, headers: str) -> dict:
    missing = [ident for ident in REQUIRED_IDS if html.count(f'id="{ident}"') != 1]
    if missing:
        raise ValueError("Required private workflow identifiers missing or duplicated: " + ", ".join(missing))
    if html.count("<script>") != 3 or "Content-Security-Policy:" not in headers:
        raise ValueError("Compiled site must have exactly three CSP-protected scripts.")
    if "qf-v140-details" not in html or "qf-v140-acceptance" not in html:
        raise ValueError("Private disclosure groups or manual acceptance checklist absent.")
    if "QFPrivateWorkflowV140" not in html or "QFPrivateDecisionIntegrityV130" not in html:
        raise ValueError("Connected V14.0 and V13.0 research models missing from compiled site.")
    if "Local filing archive present" not in html or "MFA flow requires a separate live browser test" not in html:
        raise ValueError("Privacy or authentication evidence limitations are not declared.")
    return {
        "schema": "quantforge.private-workflow-release-audit.v14.0",
        "automated_static_contract": "passed",
        "checks": len(REQUIRED_IDS) + 5,
        "compiled_html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "manual_acceptance": "not_verified",
        "manual_checks": [{"name": name, "status": "not_verified"} for name in MANUAL],
        "qualification": "HTML integrity and offline tests do not verify MFA, provider API, saved-note persistence, or a complete real browser research assessment.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "data/private_workflow_acceptance_v140.json")
    options = parser.parse_args()
    html = (ROOT / "public/index.html").read_text(encoding="utf-8")
    headers = (ROOT / "public/_headers").read_text(encoding="utf-8")
    report = audit(html, headers)
    target = options.out
    if not target.is_absolute():
        target = ROOT / target
    if ROOT / "data" not in target.parents:
        raise ValueError("Acceptance report must remain in ignored data/ directory.")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(target)
    print(f"V14.0 offline UI audit PASSED ({report['checks']} static checks).")
    print("Live MFA/provider/saved-note browser acceptance remains NOT VERIFIED.")
    print(f"Local-only report: {target}")


if __name__ == "__main__":
    main()
