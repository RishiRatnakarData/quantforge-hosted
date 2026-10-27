"""Offline reproducible checks for the V6.9 CI and compiled-site audit."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'tools/audit_public_bundle.py'
spec = importlib.util.spec_from_file_location('qf_public_bundle_audit', MODULE_PATH)
assert spec is not None and spec.loader is not None
bundle_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle_audit)


def test_compiled_site_csp_matches_source():
    assert bundle_audit.inspect((ROOT / 'public/index.html').read_text(encoding='utf-8'),
                                (ROOT / 'public/_headers').read_text(encoding='utf-8')) == []


def test_detects_tampered_inline_script():
    html = (ROOT / 'public/index.html').read_text(encoding='utf-8')
    headers = (ROOT / 'public/_headers').read_text(encoding='utf-8')
    assert 'script-src hashes differ' in str(bundle_audit.inspect(html.replace('<script>', '<script>/* modified */', 1), headers))


def test_rejects_public_secrets_and_relaxed_csp():
    html = (ROOT / 'public/index.html').read_text(encoding='utf-8')
    headers = (ROOT / 'public/_headers').read_text(encoding='utf-8')
    assert any('QF_PROXY_SECRET' in v for v in bundle_audit.inspect(html + '\nQF_PROXY_SECRET', headers))
    assert any('missing CSP rule' in v for v in bundle_audit.inspect(html, headers.replace("connect-src 'self'", 'connect-src *')))


def test_ci_runs_every_private_javascript_test_and_restricts_permissions():
    workflow = (ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8')
    assert 'permissions:\n  contents: read' in workflow
    assert 'node --test web/tests/*.test.cjs' in workflow
    assert 'python tools/audit_public_bundle.py' in workflow
    assert 'for source in web/site/*.js functions/api/*.js;' in workflow
