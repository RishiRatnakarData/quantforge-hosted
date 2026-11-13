"""Free-host adapter parity. No network, secrets or owner records are used."""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from tools.build_free_backend import FILES, build

REVISION = 'a' * 40


def test_bundle_starts_existing_guarded_api_without_repository_imports(tmp_path):
    target = tmp_path / 'backend'
    manifest = build(target, revision=REVISION)
    assert set(manifest['source_hashes']) == set(FILES)
    assert not list(target.rglob('.env*'))
    assert not list(target.rglob('*.sqlite*'))
    assert not list(target.rglob('*.csv'))
    code = r"""
import json, pathlib, sys
sys.path.insert(0, sys.argv[1])
import app
import cloud.api
import quantforge.desk.engine
import tools.build_public_sec_snapshot
import requests
from fastapi.testclient import TestClient
root=pathlib.Path(sys.argv[1]).resolve()
for module in [app,cloud.api,quantforge.desk.engine,tools.build_public_sec_snapshot]:
 assert pathlib.Path(module.__file__).resolve().is_relative_to(root),module.__file__
def forbidden(*args,**kwargs):
 raise AssertionError('No outbound network allowed in this test')
requests.Session.request=forbidden
client=TestClient(app.app,base_url='https://fixture.vercel.app')
health=client.get('/api/health')
assert health.status_code==200
assert health.json()['revision']=='a'*40
assert health.json()['paper_only'] is True
assert client.get('/api/private/state').status_code==403
assert client.get('/api/private/state',headers={'x-qf-proxy-secret':'fixture'}).status_code==401
assert client.post('/api/private/notes',headers={'x-qf-proxy-secret':'fixture','origin':'https://quantforge.pages.dev','x-qf-action':'1'},json={'expected_version':0,'notes':[],'watchlist':[]}).status_code==401
assert client.get('/docs').status_code==403
print('Packaged API imports, revision, anonymous denial and write denial PASS')
"""
    env = dict(os.environ)
    for key in ['RENDER_GIT_COMMIT','VERCEL_GIT_COMMIT_SHA','QF_RELEASE_COMMIT']:
        env.pop(key, None)
    env.update(QF_PROXY_SECRET='fixture',PUBLIC_SITE_ORIGIN='https://quantforge.pages.dev')
    result = subprocess.run([sys.executable,'-I','-c',code,str(target)],env=env,cwd=target,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    config=json.loads((target/'vercel.json').read_text())
    assert config['functions']['app.py']['maxDuration']==300
    assert not any(k in config for k in ['crons','env','build','builds'])


def test_packager_refuses_nonempty_folder_without_deleting_records(tmp_path):
    note=tmp_path/'owner-note.txt'
    note.write_text('preserve')
    with pytest.raises(ValueError,match='empty'):
        build(tmp_path,revision=REVISION)
    assert note.read_text()=='preserve'


def test_packager_rejects_untraceable_release(tmp_path):
    with pytest.raises(ValueError,match='full source revision'):
        build(tmp_path/'bundle',revision='main')


@pytest.mark.parametrize(('render','vercel','release','expected'), [
    ('1'*40,'2'*40,'3'*40,'1'*40),
    ('','2'*40,'3'*40,'2'*40),
    ('','','3'*40,'3'*40),
    ('','','invalid','not-reported'),
])
def test_health_revision_uses_validated_deployment_provenance(monkeypatch,render,vercel,release,expected):
    from fastapi.testclient import TestClient

    from cloud.api import app
    monkeypatch.setenv('RENDER_GIT_COMMIT',render)
    monkeypatch.setenv('VERCEL_GIT_COMMIT_SHA',vercel)
    monkeypatch.setenv('QF_RELEASE_COMMIT',release)
    assert TestClient(app).get('/api/health').json()['revision']==expected
