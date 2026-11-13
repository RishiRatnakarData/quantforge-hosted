"""Package the existing guarded API for a free Vercel Hobby deployment.

Copies only an explicit source allowlist. Never reads environment values, owner
records, credentials, local databases or market caches. Does not deploy anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    'cloud/__init__.py', 'cloud/api.py', 'cloud/asset_directory.py',
    'cloud/crypto_history.py', 'cloud/news_intelligence_v180.py',
    'cloud/sec_fundamentals.py', 'cloud/valuation_market_v73.py',
    'cloud/requirements.txt', 'tools/build_public_sec_snapshot.py',
    'src/quantforge/__init__.py', 'src/quantforge/desk/__init__.py',
    'src/quantforge/desk/engine.py', 'src/quantforge/desk/catalog.py',
    'src/quantforge/desk/market.py', 'src/quantforge/live/__init__.py',
    'src/quantforge/live/provider.py', 'web/site/sec_snapshot.json',
]


def build(destination: Path, revision: str | None = None) -> dict:
    destination = destination.resolve()
    # A fresh output folder prevents accidental inclusion of stale private files.
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Choose an empty output directory; no existing files are deleted.')
    if revision is None:
        dirty = subprocess.check_output(['git', 'status', '--porcelain', '--', *FILES], cwd=ROOT, text=True)
        if dirty.strip():
            raise ValueError('Commit runtime changes before packaging a deployable release.')
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('A full source revision is required.')
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {'revision': revision, 'source_hashes': {}}
    for name in FILES:
        content = (ROOT / name).read_bytes().replace(b'\r\n', b'\n')
        manifest['source_hashes'][name] = hashlib.sha256(content).hexdigest()
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    (destination / 'requirements.txt').write_bytes((destination / 'cloud/requirements.txt').read_bytes())
    (destination / '.python-version').write_text('3.12\n', encoding='utf-8')
    (destination / 'release.json').write_text(json.dumps(manifest, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    (destination / 'app.py').write_text(
        '"""Deployment adapter; authorization and arithmetic remain in cloud.api."""\n'
        'import json\nimport os\nimport sys\nfrom pathlib import Path\n'
        'root = Path(__file__).resolve().parent\n'
        'sys.path.insert(0, str(root / "src"))\n'
        'os.environ.setdefault("QF_RELEASE_COMMIT", json.loads((root / "release.json").read_text())["revision"])\n'
        'from cloud.api import app  # noqa: E402,F401\n', encoding='utf-8')
    (destination / 'vercel.json').write_text(json.dumps({
        '$schema': 'https://openapi.vercel.sh/vercel.json',
        'framework': 'fastapi', 'regions': ['iad1'],
        'functions': {'app.py': {'maxDuration': 300}},
    }, indent=2)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = build(args.output)
    print('Packaged', len(result['source_hashes']), 'allowed source files at', result['revision'])
