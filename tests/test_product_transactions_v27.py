"""Read-only previews, exact ledger effects and replay guards. All services mocked."""
from __future__ import annotations

import copy
import datetime as dt
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from cloud import api


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setenv('QF_PROXY_SECRET','fixture-proxy')
    monkeypatch.setenv('PUBLIC_SITE_ORIGIN','https://quantforge.example')
    state={'cash':1000.0,'initial_cash':1000.0,'holdings':{'MSFT':2.0},'trades':[],'notes':[]}
    store={'version':4,'state':state,'writes':0}
    monkeypatch.setattr(api,'owner',lambda *_:('owner','fixture-token'))
    monkeypatch.setattr(api,'read_state',lambda *_:(copy.deepcopy(store['state']),store['version']))
    def save(_uid,_token,state,version):
        assert version==store['version']
        store.update(state=copy.deepcopy(state),version=version+1,writes=store['writes']+1)
    monkeypatch.setattr(api,'save_state',save)
    monkeypatch.setattr(api,'quote',lambda symbol:{'symbol':symbol,'price':200,'venue':'MOCK','timestamp':dt.datetime.now(dt.UTC).isoformat()})
    return TestClient(api.app),store


def headers():
    return {'x-qf-proxy-secret':'fixture-proxy','origin':'https://quantforge.example','x-qf-action':'1'}


def request(**kwargs):
    return {'symbol':'MSFT','side':'buy','amount':'100','expected_version':4,'request_id':'fixture-request-1',**kwargs}


def test_preview_is_read_only_and_same_decimal_values_reach_receipt(service):
    client,store=service
    preview=client.post('/api/private/trade-preview',headers=headers(),json=request()).json()['preview']
    assert store['writes']==0
    response=client.post('/api/private/trade',headers=headers(),json=request(reference_price=str(preview['price'])))
    assert response.status_code==200
    account=response.json()['portfolio']
    receipt=account['trades'][0]
    for key in ('units','price','gross','fee','cash_impact'):
        assert receipt[key]==preview[key]
    assert Decimal(str(account['cash']))==Decimal('1000')+Decimal(str(receipt['cash_impact']))
    assert account['cash']==preview['cash_after']
    assert store['writes']==1


def test_repeated_identifier_reconciles_without_second_write_or_quote(service,monkeypatch):
    client,store=service
    first=client.post('/api/private/trade',headers=headers(),json=request())
    monkeypatch.setattr(api,'quote',lambda *_:pytest.fail('Reconciliation must not place or reprice another transaction'))
    again=client.post('/api/private/trade',headers=headers(),json=request())
    assert first.status_code==again.status_code==200
    assert again.json()['reconciled'] is True
    assert store['writes']==1 and len(store['state']['trades'])==1
    assert client.post('/api/private/trade',headers=headers(),json=request(amount='200')).status_code==409


@pytest.mark.parametrize('body',[request(side='sell',amount='3'),request(side='sell',symbol='AAPL',amount='1'),request(amount='1001'),request(reference_price='100')])
def test_invalid_sale_budget_or_changed_price_never_writes(service,body):
    client,store=service
    assert client.post('/api/private/trade',headers=headers(),json=body).status_code==422
    assert store['writes']==0


def test_sale_conserves_cash_and_cannot_exceed_owned_position(service):
    client,store=service
    response=client.post('/api/private/trade',headers=headers(),json=request(side='sell',amount='2'))
    assert response.status_code==200
    account=response.json()['portfolio']
    assert 'MSFT' not in account['holdings']
    assert account['cash']==1399.8
    assert account['initial_cash']==1000 and account['trades'][0]['fee']==.2
    assert store['writes']==1


def test_preview_rejects_version_conflict_and_stale_price(service,monkeypatch):
    client,store=service
    assert client.post('/api/private/trade-preview',headers=headers(),json=request(expected_version=3)).status_code==409
    monkeypatch.setattr(api,'quote',lambda symbol:{'symbol':symbol,'price':200,'venue':'MOCK','timestamp':'2020-01-01T00:00:00Z'})
    assert client.post('/api/private/trade-preview',headers=headers(),json=request()).status_code in (422,503)
    assert store['writes']==0


def test_preview_requires_proxy_and_owner(monkeypatch):
    monkeypatch.setenv('QF_PROXY_SECRET','fixture-proxy')
    monkeypatch.setenv('PUBLIC_SITE_ORIGIN','https://quantforge.example')
    client=TestClient(api.app)
    assert client.post('/api/private/trade-preview',json=request()).status_code==403
    assert client.post('/api/private/trade-preview',headers=headers(),json=request()).status_code==401


def test_existing_owned_crypto_position_uses_the_same_decimal_sell_guards(service):
    client, store = service
    store['state']['holdings']['BTC/USD'] = .25
    response = client.post('/api/private/trade', headers=headers(),
                           json=request(symbol='BTC/USD', side='sell', amount='.1'))
    assert response.status_code == 200
    assert response.json()['portfolio']['holdings']['BTC/USD'] == .15
    assert response.json()['portfolio']['cash'] == 1019.99
