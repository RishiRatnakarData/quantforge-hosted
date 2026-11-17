"""Isolated deployment must import without including private runtime state."""
import json
import os
import subprocess
import sys

import pytest

from tools.package_vercel_api import assemble


def test_package_is_allowlisted_and_importable_without_repo_on_pythonpath(tmp_path):
    package = tmp_path / "api"
    manifest = assemble(package, allow_dirty=True)
    names = set(manifest["files"])
    assert "web/site/sec_snapshot.json" in names
    assert "cloud/api.py" in names
    assert not any(part.startswith(".env") or part in {".vercel", ".wrangler", "outputs"}
                   for name in names for part in name.split("/"))
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", "from app import app; print(app.title)"],
        cwd=package, env=env, capture_output=True, text=True, check=True,
    )
    assert "QuantForge private API" in result.stdout
    assert json.loads((package / "SOURCE_MANIFEST.json").read_text())["files"] == manifest["files"]
    with pytest.raises(ValueError, match="empty"):
        assemble(package, allow_dirty=True)
