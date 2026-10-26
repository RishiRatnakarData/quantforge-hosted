"""Offline guardrails for an intentionally private investment project."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepublish_check", ROOT / "tools" / "prepublish_check.py")
preflight = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(preflight)


def test_source_tree_is_free_of_obvious_private_artifacts():
    assert preflight.inspect(ROOT) == []


def test_refuses_databases_and_nonfictional_csv(tmp_path):
    (tmp_path / "portfolio.sqlite3").write_text("private")
    (tmp_path / "real_stock_prices.csv").write_text("date,symbol,close")
    messages = preflight.inspect(tmp_path)
    assert len(messages) == 2
    assert any("portfolio.sqlite3" in x for x in messages)
    assert any("real_stock_prices.csv" in x for x in messages)


def test_refuses_embedded_credentials_and_personal_contacts(tmp_path):
    (tmp_path / "notes.md").write_text("Key: " + "PK" + "Q" * 29 + "\n" +
                                     "Send to " + "realperson" + "@" + "private-domain.invalid\n")
    messages = preflight.inspect(tmp_path)
    assert any("credential" in x for x in messages)
    assert any("contact email" in x for x in messages)


def test_checks_local_doc_links(tmp_path):
    doc = tmp_path / "README.md"
    doc.write_text("[Good](docs/ok.md) and [Bad](docs/missing.md)")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ok.md").write_text("fine")
    messages = preflight.inspect(tmp_path)
    assert len(messages) == 1
    assert "missing.md" in messages[0]
