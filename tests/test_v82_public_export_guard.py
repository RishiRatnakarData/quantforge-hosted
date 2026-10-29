"""V8.2 public export privacy exception must fail closed for tampering."""
from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def scanner():
    spec = importlib.util.spec_from_file_location("qf82_prepublication_module", ROOT / "tools/prepublish_check.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_fixture(tmp_path):
    paths = (
        "tools/build_v82_case_study.py",
        "web/site/sec_snapshot.json",
        "public/research-case-study.csv",
        "public/research-case-study.html",
    )
    for name in paths:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    return tmp_path


def test_public_sec_csv_allowed_only_when_reproduced_exactly(tmp_path):
    module = scanner()
    sandbox = make_fixture(tmp_path)
    assert module._qf82_verified_public_case_study(sandbox)
    ledger = sandbox / "public/research-case-study.csv"
    ledger.write_bytes(ledger.read_bytes() + b"\nPRIVATE,UNKNOWN\n")
    assert not module._qf82_verified_public_case_study(sandbox)


def test_case_study_html_must_match_exact_deterministic_output(tmp_path):
    module = scanner()
    sandbox = make_fixture(tmp_path)
    assert module._qf82_verified_public_case_study(sandbox)
    report = sandbox / "public/research-case-study.html"
    report.write_bytes(report.read_bytes().replace(b"Historical disclosures", b"UNVERIFIED research"))
    assert not module._qf82_verified_public_case_study(sandbox)


def test_missing_or_modified_source_blocks_exception(tmp_path):
    module = scanner()
    sandbox = make_fixture(tmp_path)
    assert module._qf82_verified_public_case_study(sandbox)
    snapshot = sandbox / "web/site/sec_snapshot.json"
    snapshot.write_bytes(snapshot.read_bytes() + b" ")
    assert not module._qf82_verified_public_case_study(sandbox)


def test_unrelated_private_artifact_warnings_remain_visible(monkeypatch):
    module = scanner()
    marker = "private/accounts.csv: dataset/key/database file needs explicit exclusion"
    other = "public/research-case-study.csv: dataset/key/database file needs explicit exclusion"
    monkeypatch.setattr(module, "_qf82_original_prepublication_inspect", lambda _root: [marker, other])
    monkeypatch.setattr(module, "_qf82_verified_public_case_study", lambda _root: True)
    assert module.inspect(ROOT) == [marker]
    monkeypatch.setattr(module, "_qf82_verified_public_case_study", lambda _root: False)
    assert module.inspect(ROOT) == [marker, other]


def test_existing_scanner_passes_with_verified_public_ledger():
    assert scanner().inspect(ROOT) == []
