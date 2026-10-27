"""Verify built QuantForge public HTML and its strict inline-script CSP.

Does not read private credentials, market observations, or any remote service.
Run after tools/build_unified_site.py on a local or GitHub CI checkout.
"""
from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BundleAuditError(ValueError):
    """The static site or its defensive headers are inconsistent."""


def inspect(html: str, headers: str) -> list[str]:
    issues: list[str] = []
    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script\s*>", html, re.I | re.S)
    if len(scripts) != 3:
        issues.append(f"expected 3 inline scripts, found {len(scripts)}")
    if re.search(r"<script[^>]+\bsrc\s*=", html, re.I):
        issues.append("unexpected remotely loaded script")
    csp = re.search(r"^\s*Content-Security-Policy:\s*(.+)$", headers, re.M)
    if not csp:
        return issues + ["missing Content-Security-Policy in public/_headers"]
    policy = csp.group(1)
    for directive in ("default-src 'none'", "connect-src 'self'", "object-src 'none'", "frame-ancestors 'none'"):
        if directive not in policy:
            issues.append(f"missing CSP rule: {directive}")
    script_rule = re.search(r"(?:^|;)\s*script-src\s+([^;]+)", policy)
    if not script_rule:
        issues.append("missing script-src directive")
    else:
        listed = script_rule.group(1).strip().split()
        expected = ["'sha256-" + base64.b64encode(hashlib.sha256(item.encode('utf-8')).digest()).decode('ascii') + "'"
                    for item in scripts]
        if sorted(listed) != sorted(expected):
            issues.append("script-src hashes differ from compiled inline JavaScript")
    for token in ("ALPACA_API_SECRET_KEY", "QF_PROXY_SECRET", "SUPABASE_PUBLISHABLE_KEY", "OWNER_USER_ID"):
        if token in html:
            issues.append(f"server configuration identifier appears in public HTML: {token}")
    return issues


def main() -> int:
    errors = inspect((ROOT / 'public/index.html').read_text(encoding='utf-8'),
                     (ROOT / 'public/_headers').read_text(encoding='utf-8'))
    if errors:
        for err in errors:
            print('PUBLIC BUNDLE AUDIT FAILED:', err)
        return 1
    print('Public bundle audit passed: three CSP-matched scripts, restrictive headers, and no server-config identifiers.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
