"""Vercel entrypoint; assemble with tools/package_vercel_api.py."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from cloud.api import app  # noqa: E402,F401
