"""Offline V16.0 private Decision Center contract checks; not authenticated browser acceptance."""

import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "qf-v160-decision-center",
    "qf-v160-setup",
    "qf-v160-method-trace",
    "qf-v99-file",
    "private-v90-run",
    "private-v90-candidate",
    "qf-v140-next",
    "qf-v150-acceptance",
    "private-mfa-code",
    "private-logout",
}


class IDs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.private_tabs = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if attrs.get("data-private-view"):
            self.private_tabs.add(attrs["data-private-view"])


def audit():
    html = (ROOT / "public/index.html").read_text(encoding="utf-8")
    private = (ROOT / "web/site/private.js").read_text(encoding="utf-8")
    helper = (ROOT / "web/site/private_unified_decision_v160.js").read_text(encoding="utf-8")
    builder = (ROOT / "tools/build_unified_site.py").read_text(encoding="utf-8")
    parser = IDs()
    parser.feed(html)
    missing = REQUIRED - parser.ids
    if missing:
        raise RuntimeError(f"Missing private interface components: {sorted(missing)}")
    routes = {
        "decision", "ideas", "home", "trade", "lab", "research", "candidate",
        "valuation", "optimization", "backtest", "walkforward", "settings",
    }
    if not routes.issubset(parser.private_tabs):
        raise RuntimeError("A legacy research route was removed.")
    for marker in (
        "arrangePrivateResearchV160();", "renderUnifiedDecisionV160();",
        "qf-v160-archive-details", "linkedUnifiedDecisionV160=null;",
        "window.QFPrivateUnifiedDecisionV160.exportSafe",
        "researchOSInternalLoadV90=true", "await loadHistory()",
    ):
        if marker not in private:
            raise RuntimeError(f"Missing wiring: {marker}")
    for marker in (
        "Predeclared weights:", "alignment:null", "integrity.classification",
        "blocked||observedWeight<40", "return {schema:'quantforge.decision-center-export.v16.0'",
    ):
        if marker not in helper:
            raise RuntimeError(f"Missing scoring guard: {marker}")
    for forbidden in (
        "fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "private/trade",
        "private/capital", "WebSocket(", "indexedDB", "document.cookie",
    ):
        if forbidden in helper:
            raise RuntimeError("The decision-score module contains I/O or trading code.")
    if "src/'site/private_unified_decision_v160.js'" not in builder:
        raise RuntimeError("Decision module is not bundled into the CSP-protected site.")
    # Site remains three scripts with CSP hashes; independent audit checks the headers.
    if html.count("<script>") != 3:
        raise RuntimeError("Unexpected script boundary; run public bundle audit.")
    report = {
        "schema": "quantforge.offline-v16-decision-audit",
        "ready": True,
        "private_routes": len(routes),
        "dashboard_elements": len(REQUIRED),
        "ui_compiled_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "automated_browser_authentication": False,
        "real_provider_data_verified": False,
        "manual_browser_acceptance": "PENDING",
        "statement": "Static source and generated-site evidence only; no live provider or investment outcome claims.",
    }
    out = ROOT / "data/private_decision_contract_v160.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"V16.0 private decision center offline audit PASSED ({len(routes)} routes).")
    print("Authenticated browser checks remain NOT VERIFIED; report remains in ignored data/.")
    return report


if __name__ == "__main__":
    audit()
