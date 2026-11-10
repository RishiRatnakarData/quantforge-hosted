"""Owner-only, version-checked marks. External providers and persistence are mocked."""
from __future__ import annotations

import copy
import datetime as dt

import pytest
from fastapi.testclient import TestClient

from cloud import api as service


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('QF_PROXY_SECRET', 'snapshot-proxy')
    monkeypatch.setenv('PUBLIC_SITE_ORIGIN', 'https://quantforge.example')
    return TestClient(service.app)


def headers():
    return {'x-qf-proxy-secret': 'snapshot-proxy', 'origin': 'https://quantforge.example',
            'x-qf-action': '1'}


def setup(monkeypatch, state=None):
    account = state or {'cash': 100, 'initial_cash': 500, 'holdings': {'MSFT': 2},
                        'notes': [{'text': 'Preserve this note'}]}
    monkeypatch.setattr(service, 'owner', lambda *_: ('owner', 'mock-session'))
    monkeypatch.setattr(service, 'read_state', lambda *_: (copy.deepcopy(account), 4))
    monkeypatch.setattr(service, 'quote', lambda s: {
        'symbol': s, 'price': 225, 'venue': 'MOCK',
        'timestamp': dt.datetime.now(dt.UTC).isoformat()})
    writes = []
    monkeypatch.setattr(service, 'save_state', lambda *args: writes.append(args[2]))
    return writes


def test_snapshot_requires_proxy_and_verified_owner(client):
    assert client.post('/api/private/valuation-snapshot', json={'expected_version': 0}).status_code == 403
    assert client.post('/api/private/valuation-snapshot', headers=headers(),
                       json={'expected_version': 0}).status_code == 401


def test_complete_mark_separates_capital_from_pnl_and_preserves_state(client, monkeypatch):
    writes = setup(monkeypatch)
    response = client.post('/api/private/valuation-snapshot', headers=headers(),
                           json={'expected_version': 4})
    assert response.status_code == 200
    result = response.json()
    assert result['version'] == 5
    point = result['portfolio']['valuations'][0]
    assert point['value'] == 550
    assert point['net_contributions'] == 500
    assert point['pnl'] == 50
    assert writes[0]['notes'][0]['text'] == 'Preserve this note'
    assert point['observations'][0]['symbol'] == 'MSFT'


def test_version_conflict_cannot_record_mark(client, monkeypatch):
    writes = setup(monkeypatch)
    response = client.post('/api/private/valuation-snapshot', headers=headers(),
                           json={'expected_version': 3})
    assert response.status_code == 409
    assert writes == []


@pytest.mark.parametrize('bad_quote', [
    {'symbol': 'MSFT', 'price': 225, 'venue': 'MOCK', 'timestamp': '2000-01-01T00:00:00Z'},
    {'symbol': 'AAPL', 'price': 225, 'venue': 'MOCK'},
    {'symbol': 'MSFT', 'price': -1, 'venue': 'MOCK'},
])
def test_partial_stale_or_invalid_price_never_writes(client, monkeypatch, bad_quote):
    writes = setup(monkeypatch)
    bad_quote.setdefault('timestamp', dt.datetime.now(dt.UTC).isoformat())
    monkeypatch.setattr(service, 'quote', lambda _: bad_quote)
    response = client.post('/api/private/valuation-snapshot', headers=headers(),
                           json={'expected_version': 4})
    assert response.status_code == 422
    assert writes == []


def test_cash_only_deposit_is_not_a_gain(client, monkeypatch):
    setup(monkeypatch, {'cash': 1500, 'initial_cash': 1500, 'holdings': {}, 'valuations': []})
    response = client.post('/api/private/valuation-snapshot', headers=headers(),
                           json={'expected_version': 4})
    point = response.json()['portfolio']['valuations'][0]
    assert point['pnl'] == 0
    assert point['value'] == point['net_contributions'] == 1500


def test_snapshot_history_is_bounded_and_reset_cannot_reuse_marks(client, monkeypatch):
    setup(monkeypatch, {'cash': 100, 'initial_cash': 100, 'holdings': {},
                        'valuations': [{'at': str(i)} for i in range(365)]})
    response = client.post('/api/private/valuation-snapshot', headers=headers(),
                           json={'expected_version': 4})
    marks = response.json()['portfolio']['valuations']
    assert len(marks) == 365
    assert marks[0]['at'] == '1'
    assert not service.default_state().get('valuations')



def test_public_health_reports_only_valid_revision_metadata(client, monkeypatch):
    monkeypatch.setenv('RENDER_GIT_COMMIT', 'a' * 40)
    result = client.get('/api/health').json()
    assert result['revision'] == 'a' * 40
    assert result['api_contract'] == 'shared-research-v25'
    monkeypatch.setenv('RENDER_GIT_COMMIT', 'unexpected-sensitive-value')
    assert client.get('/api/health').json()['revision'] == 'not-reported'
