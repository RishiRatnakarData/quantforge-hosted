"""Offline source-release preflight. Run before `git add`, commit, or push.

Rejects common private/market-data file types, exposed-looking credentials,
personal emails in published content, and broken relative Markdown links.
Not a replacement for human code review, Git history inspection or provider terms.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache",
                "build", "dist", ".private", "outputs", ".vscode", ".mypy_cache"}
PRIVATE_DIRS = {".private", "outputs", "private", "private_data", "real_etfs"}
PRIVATE_EXTENSIONS = {".sqlite", ".sqlite3", ".db", ".duckdb", ".parquet",
                      ".feather", ".pkl", ".pickle", ".pem", ".key", ".p12"}
SOURCE_EXTENSIONS = {".py", ".md", ".toml", ".yaml", ".yml", ".json", ".html", ".js", ".txt", ".sh", ".ps1"}
# Keys are split to avoid treating this detector as matching its own examples.
TOKEN = re.compile(r"\b(?:" + "PK" + r"[A-Z0-9]{20,}|" + "SK" + r"[A-Z0-9]{20,}|" +
                   r"gh[pousr]_[A-Za-z0-9_]{28,}|github_pat_[A-Za-z0-9_]{30,})\b")
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
ALLOW_EXAMPLE_EMAIL = {"example.com", "example.org", "example.net", "research.test", "myresearch.test"}


def source_paths(root: Path) -> list[Path]:
    """Include tracked and untracked nonignored Git files; fallback to source tree."""
    if (root / ".git").exists():
        p = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                           cwd=root, capture_output=True, check=True)
        return sorted({root / name.decode("utf-8", "surrogateescape")
                       for name in p.stdout.split(b"\0") if name})
    return sorted(p for p in root.rglob("*") if p.is_file() and
                  not any(part in IGNORED_DIRS for part in p.relative_to(root).parts))


def inspect(root: Path) -> list[str]:
    failures = []
    for path in source_paths(root):
        rel = path.relative_to(root)
        name = rel.as_posix()
        parts = rel.parts
        if path.is_symlink():
            failures.append(f"{name}: symlinks are not allowed in release files")
            continue
        if (path.name.startswith(".env") and path.name != ".env.example") or any(
                part in PRIVATE_DIRS for part in parts[:-1]):
            failures.append(f"{name}: private/ignored content must not be published")
            continue
        if path.suffix.lower() in PRIVATE_EXTENSIONS or (path.suffix.lower() == ".csv" and
                name != "examples/fictional_adjusted_prices.csv"):
            failures.append(f"{name}: dataset/key/database file needs explicit exclusion")
            continue
        if path.stat().st_size > 8_000_000:
            failures.append(f"{name}: file exceeds 8 MB; inspect before publication")
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS and path.name != ".env.example":
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if TOKEN.search(content) or PRIVATE_KEY.search(content):
            failures.append(f"{name}: possible embedded API credential or private key")
        for email in set(EMAIL.findall(content)):
            if email.lower().split("@", 1)[1] not in ALLOW_EXAMPLE_EMAIL:
                failures.append(f"{name}: contact email found; review before publication")
                break
        if path.suffix.lower() == ".md":
            for raw in LINK.findall(content):
                target = raw.split(" ", 1)[0].strip("<>").split("#", 1)[0].split("?", 1)[0]
                if not target or re.match(r"^(?:[a-z]+:|//)", target, re.I):
                    continue
                dest = (path.parent / unquote(target)).resolve()
                if not dest.is_relative_to(root.resolve()) or not dest.exists():
                    failures.append(f"{name}: broken/outside relative link to {target}")
    return sorted(set(failures))


def main() -> int:
    issues = inspect(ROOT)
    if issues:
        print(f"PREPUBLICATION CHECK FAILED ({len(issues)} issue(s)):")
        for issue in issues:
            print("  - " + issue)
        return 1
    print("Prepublication checks passed: file types, obvious secrets/emails, README/doc links.")
    print("Also review Git history, screenshots, data-provider rights, and CI before publishing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
