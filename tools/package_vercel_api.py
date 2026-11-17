"""Assemble the existing Vercel API from reviewed source; never copies local secrets.

This command only writes an isolated package. It does not deploy or contact a provider.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = (
    "cloud/__init__.py", "cloud/api.py", "cloud/paper_accounting.py", "cloud/asset_directory.py",
    "cloud/crypto_history.py", "cloud/news_intelligence_v180.py", "cloud/release_identity.py",
    "cloud/sec_fundamentals.py", "cloud/valuation_market_v73.py",
    "src/quantforge/__init__.py", "src/quantforge/desk/__init__.py",
    "src/quantforge/desk/catalog.py", "src/quantforge/desk/engine.py",
    "src/quantforge/desk/market.py", "src/quantforge/live/__init__.py",
    "src/quantforge/live/provider.py", "tools/__init__.py",
    "tools/build_public_sec_snapshot.py", "web/site/sec_snapshot.json",
)


def assemble(destination: Path, *, allow_dirty: bool = False) -> dict:
    destination = destination.resolve()
    if destination == ROOT or ROOT.is_relative_to(destination):
        raise ValueError("Choose a new isolated package directory, not the repository or its ancestor.")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Package destination must be empty; existing deployments are never overwritten.")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=normal"], cwd=ROOT, text=True
    ).strip())
    if dirty and not allow_dirty:
        raise ValueError("Commit reviewed source first, or use --allow-dirty for an explicitly unverified local package.")
    mapping = {name: name for name in RUNTIME_FILES}
    mapping.update({"app.py": "deploy/vercel-api/app.py",
                    "vercel.json": "deploy/vercel-api/vercel.json",
                    "requirements.txt": "cloud/requirements.txt"})
    contents = {}
    for target, source in mapping.items():
        file = ROOT / source
        if file.is_symlink():
            raise ValueError("Symlinks are not permitted in deployment inputs.")
        contents[target] = file.read_bytes().replace(b"\r\n", b"\n")
    manifest = {"source_revision": revision, "working_tree_dirty": dirty,
                "api_contract": "shared-research-v25",
                "files": {name: hashlib.sha256(data).hexdigest()
                          for name, data in sorted(contents.items())}}
    for name, data in contents.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (destination / "SOURCE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    manifest = assemble(args.destination, allow_dirty=args.allow_dirty)
    print(f"Assembled {len(manifest['files'])} source files; dirty={manifest['working_tree_dirty']}. No deployment performed.")


if __name__ == "__main__":
    main()
