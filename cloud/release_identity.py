"""Report only a validated source revision, never deployment environment contents."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path


def revision() -> str:
    for key in ("RENDER_GIT_COMMIT", "VERCEL_GIT_COMMIT_SHA", "QF_SOURCE_REVISION"):
        value = os.getenv(key, "")
        if re.fullmatch(r"[0-9a-f]{40}", value):
            return value
    manifest = Path(__file__).resolve().parents[1] / "SOURCE_MANIFEST.json"
    try:
        if manifest.is_symlink() or manifest.stat().st_size > 32768:
            return "not-reported"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        value = data.get("source_revision")
        if data.get("working_tree_dirty") is False and isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value):
            return value
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return "not-reported"
