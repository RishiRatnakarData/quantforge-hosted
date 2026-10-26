"""Regression tests for owner-only mixed equity/crypto history."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cloud import api as service
from cloud import crypto_history


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('QF_PROXY_SECRET', 'mock-proxy')
    monkeypatch.setenv('PUBLIC_SITE_ORIGIN', 'https://quantforge.example')
    return TestClient(service.app)


HEADERS = {'x-qf-proxy-secret': 'mock-proxy'}


def _observations(symbol: str, days: int = 45):
    start = dt.date(2026, 1, 1)
    return [{'date': (start + dt.timedelta(days=i)).isoformat(),
             'close': 100 * (1.001 ** i)} for i in range(days)]


def test_owner_required_for_mixed_history(client):
    path = '/api/private/history?symbols=MSFT,BTC%2FUSD&days=365'
    assert client.get(path, headers=HEADERS).status_code == 401
    assert client.get(path).status_code == 403


def test_mixed_history_only_joins_observed_dates(client, monkeypatch):
    monkeypatch.setattr(service, 'owner', lambda *_: ('owner', 'token'))
    class Stock:
        def history(self, symbol, start, end):
            return [x for x in _observations(symbol) if dt.date.fromisoformat(x['date']).weekday() < 5]
    monkeypatch.setattr(service.AlpacaClient, 'from_environment', lambda: Stock())
    monkeypatch.setattr(crypto_history, 'history', lambda symbol, start, end: _observations(symbol))
    response = client.get('/api/private/history', headers=HEADERS, params={'symbols': 'MSFT,BTC/USD', 'days': 365})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['sessions_per_year'] == 252
    assert data['asset_classes'] == {'MSFT': 'us_equity', 'BTC/USD': 'crypto'}
    assert all(dt.date.fromisoformat(day).weekday() < 5 for day in data['dates'])
    assert len(data['dates']) == len(data['closes']['MSFT']) == len(data['closes']['BTC/USD'])
    assert 'shared' in data['source'].lower()
    assert 'API_SECRET' not in response.text


def test_crypto_only_uses_calendar_day_convention(client, monkeypatch):
    monkeypatch.setattr(service, 'owner', lambda *_: ('owner', 'token'))
    monkeypatch.setattr(service.AlpacaClient, 'from_environment', lambda: (_ for _ in ()).throw(AssertionError('Stock provider called')))
    monkeypatch.setattr(crypto_history, 'history', lambda symbol, start, end: _observations(symbol))
    response = client.get('/api/private/history', headers=HEADERS, params={'symbols': 'BTC/USD,ETH/USD', 'days': 365})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['sessions_per_year'] == 365
    assert len(data['dates']) == 45
    assert data['calendar'] == 'UTC calendar days'


@pytest.mark.parametrize('symbols', [
    'BTC/EUR,MSFT', 'BTC/USD,BTC/USD', 'MSFT,BTC/USD,ABC,DEF,GHI,JKL',
    'BTC/USD', 'BTC/USD,,MSFT', 'BTC-USD,MSFT',
])
def test_invalid_mixed_symbols_do_not_call_providers(client, monkeypatch, symbols):
    monkeypatch.setattr(service, 'owner', lambda *_: ('owner', 'token'))
    monkeypatch.setattr(crypto_history, 'history', lambda *_: (_ for _ in ()).throw(AssertionError('Crypto provider called')))
    monkeypatch.setattr(service.AlpacaClient, 'from_environment', lambda: (_ for _ in ()).throw(AssertionError('Stock provider called')))
    response = client.get('/api/private/history', headers=HEADERS, params={'symbols': symbols, 'days': 365})
    assert response.status_code == 422


def test_crypto_fetch_is_paginated_and_caches_responses(monkeypatch):
    crypto_history._CACHE.clear()
    monkeypatch.setenv('ALPACA_API_KEY_ID', 'MOCK_KEY')
    monkeypatch.setenv('ALPACA_API_SECRET_KEY', 'MOCK_SECRET')
    calls = []

    class Response:
        def __init__(self, obj):
            self.obj = obj
        def raise_for_status(self):
            return None
        def json(self):
            return self.obj

    def fetch(url, headers, params, timeout):
        assert url == crypto_history.ENDPOINT
        assert headers['APCA-API-SECRET-KEY'] == 'MOCK_SECRET'
        calls.append(params.copy())
        first = params.get('page_token') is None
        value = {'bars': {'BTC/USD': [
            {'t': '2026-01-01T00:00:00Z' if first else '2026-01-02T00:00:00Z', 'c': 40000 if first else 41000}
        ]}, 'next_page_token': 'PAGE2' if first else None}
        return Response(value)

    monkeypatch.setattr(crypto_history.requests, 'get', fetch)
    rows = crypto_history.history('BTC/USD', '2025-12-01', '2026-02-01')
    assert [x['close'] for x in rows] == [40000., 41000.]
    assert len(calls) == 2
    again = crypto_history.history('BTC/USD', '2025-12-01', '2026-02-01')
    assert again == rows and len(calls) == 2
    crypto_history._CACHE.clear()


def test_crypto_bad_provider_data_does_not_leak_keys(monkeypatch):
    crypto_history._CACHE.clear()
    monkeypatch.setenv('ALPACA_API_KEY_ID', 'MOCK_KEY')
    monkeypatch.setenv('ALPACA_API_SECRET_KEY', 'MOCK_SECRET')
    class Response:
        def raise_for_status(self):
            return None
        def json(self):
            return {'bars': {'ETH/USD': [{'t': '2026-01-01T00:00:00Z', 'c': -1}]}}
    monkeypatch.setattr(crypto_history.requests, 'get', lambda *a, **k: Response())
    with pytest.raises(crypto_history.CryptoHistoryError) as error:
        crypto_history.history('ETH/USD', '2025-12-01', '2026-02-01')
    assert 'MOCK_SECRET' not in str(error.value)


def test_private_ui_reuses_picker_and_preserves_three_script_csp():
    root = Path(__file__).resolve().parents[1]
    js = (root / 'web/site/private.js').read_text(encoding='utf-8')
    build = (root / 'tools/build_unified_site.py').read_text(encoding='utf-8')
    assert 'window.QFPrivateMultiMarket.analyze(series)' in js
    assert 'function privateCrossAsset(series)' in js
    assert 'private_multimarket.js' in build
    assert "if(kind==='crypto'){message('Historical research currently" not in js
    html = (root / 'public/index.html').read_text(encoding='utf-8')
    headers = (root / 'public/_headers').read_text(encoding='utf-8')
    assert html.count('<script>') == 3
    assert headers.count("'sha256-") == 3
    assert 'Multi-asset comparison' in html
