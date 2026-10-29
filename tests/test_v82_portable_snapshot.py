"""V8.2 public SEC snapshots must reproduce across Git line-ending modes."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(file: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, file)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_snapshot_digest_is_independent_of_windows_line_endings():
    builder = module(ROOT / "tools/build_v82_case_study.py", "qf82_portable_builder")
    data = b'{\n  "dataset": "public"\n}\n'.replace(b"\\n", b"\n")
    assert builder.canonical_snapshot_sha256(data) == builder.canonical_snapshot_sha256(data.replace(b"\n", b"\r\n"))
    assert builder.canonical_snapshot_sha256(data) != builder.canonical_snapshot_sha256(data + b" ")


def test_case_study_public_guard_accepts_git_normalized_snapshot(tmp_path):
    builder = module(ROOT / "tools/build_v82_case_study.py", "qf82_portable_builder_fixture")
    guard = module(ROOT / "tools/prepublish_check.py", "qf82_portable_guard_fixture")
    dest = tmp_path / "repo"
    files = ("tools/build_v82_case_study.py", "web/site/sec_snapshot.json")
    for name in files:
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    source = dest / "web/site/sec_snapshot.json"
    raw_data = json.loads(source.read_text(encoding="utf-8"))
    lf = (json.dumps(raw_data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    crlf = lf.replace(b"\n", b"\r\n")
    assert crlf != lf
    source.write_bytes(crlf)
    builder.write_outputs(dest)
    initial_html = (dest / "public/research-case-study.html").read_bytes()
    assert guard._qf82_verified_public_case_study(dest)
    # Model the Git checkout on Linux without regenerating the committed HTML.
    source.write_bytes(lf)
    assert guard._qf82_verified_public_case_study(dest)
    builder.write_outputs(dest)
    assert (dest / "public/research-case-study.html").read_bytes() == initial_html
    # LF/CRLF in generated text itself is also a benign checkout difference.
    ledger = dest / "public/research-case-study.csv"
    ledger.write_bytes(ledger.read_bytes().replace(b"\n", b"\r\n"))
    assert guard._qf82_verified_public_case_study(dest)
    ledger.write_bytes(ledger.read_bytes() + b"\r\nINVALID,EXTRA\r\n")
    assert not guard._qf82_verified_public_case_study(dest)
    # Actual financial-record mutations may never pass the guard.
    ledger.write_bytes(builder.csv_report(builder.load_companies(raw_data)).encode("utf-8"))
    source.write_bytes(lf + b" ")
    assert not guard._qf82_verified_public_case_study(dest)


def test_checked_out_snapshot_matches_committed_git_blob_semantically():
    raw = (ROOT / "web/site/sec_snapshot.json").read_bytes()
    committed = subprocess.check_output(
        ["git", "show", "HEAD:web/site/sec_snapshot.json"], cwd=ROOT
    )
    # No data changes permitted. Only line endings may vary on Windows.
    assert raw.replace(b"\r\n", b"\n") == committed.replace(b"\r\n", b"\n")
