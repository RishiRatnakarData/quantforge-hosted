"""Cross-provider health identity refuses unverified or credential-shaped values."""
import json

from cloud import release_identity


def test_revision_accepts_only_commit_identifiers_and_preserves_provider_priority(monkeypatch):
    for key in ("RENDER_GIT_COMMIT", "VERCEL_GIT_COMMIT_SHA", "QF_SOURCE_REVISION"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "b"*40)
    assert release_identity.revision() == "b"*40
    monkeypatch.setenv("RENDER_GIT_COMMIT", "a"*40)
    assert release_identity.revision() == "a"*40
    monkeypatch.setenv("RENDER_GIT_COMMIT", "private-server-setting-not-a-commit")
    assert release_identity.revision() == "b"*40


def test_cli_package_identity_requires_a_clean_manifest(monkeypatch, tmp_path):
    for key in ("RENDER_GIT_COMMIT", "VERCEL_GIT_COMMIT_SHA", "QF_SOURCE_REVISION"):
        monkeypatch.delenv(key, raising=False)
    cloud = tmp_path / "cloud"
    cloud.mkdir()
    monkeypatch.setattr(release_identity, "__file__", str(cloud / "release_identity.py"))
    manifest = tmp_path / "SOURCE_MANIFEST.json"
    manifest.write_text(json.dumps({"source_revision":"c"*40,"working_tree_dirty":True}))
    assert release_identity.revision() == "not-reported"
    manifest.write_text(json.dumps({"source_revision":"c"*40,"working_tree_dirty":False}))
    assert release_identity.revision() == "c"*40
    manifest.write_text('{broken')
    assert release_identity.revision() == "not-reported"
