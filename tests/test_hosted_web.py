"""Hosted-mode security and ledger regressions. All external calls mocked."""
import datetime as dt

import pytest
from fastapi.testclient import TestClient

from cloud import api as service

@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv('QF_PROXY_SECRET','testproxysecret')
    monkeypatch.setenv('PUBLIC_SITE_ORIGIN','https://quantforge.pages.dev')
    monkeypatch.setenv('OWNER_USER_ID','owner-uuid')
    monkeypatch.setenv('SUPABASE_URL','https://unit-test.supabase.co')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY','test-public-key')
    return TestClient(service.app, base_url='https://quant-api.onrender.com')

def h(post=False):
    v={'x-qf-proxy-secret':'testproxysecret'}
    if post:
        v.update(origin='https://quantforge.pages.dev',**{'x-qf-action':'1'})
    return v

def test_public_health_without_credentials(client):
    r=client.get('/api/health')
    assert r.status_code==200
    assert 'key' not in r.text

def test_proxy_secret_required(client):
    assert client.get('/api/auth/session').status_code==403
    assert client.get('/api/private/state').status_code==403

def test_mutation_requires_origin_and_action(client):
    assert client.post('/api/auth/login',headers=h(),json={'email':'user@example.com','password':'123456789'}).status_code==403
    assert client.post('/api/auth/login',headers={**h(True),'origin':'https://attacker.example'},json={}).status_code==403

def test_anonymous_cannot_read_private_data(client,monkeypatch):
    monkeypatch.setattr(service,'sb_request',lambda *a,**kw:None)
    assert client.get('/api/private/state',headers=h()).status_code==401
    assert client.get('/api/private/quotes?symbols=MSFT',headers=h()).status_code==401
    assert client.post('/api/private/trade',headers=h(True),json={'symbol':'MSFT','side':'buy','amount':'100','expected_version':0}).status_code==401

def test_login_rejects_non_owner(client,monkeypatch):
    class R:
        status_code=200
        def json(self):return {'user':{'id':'wrong','email_confirmed_at':'now'},'access_token':'TOKEN','refresh_token':'REFRESH'}
    monkeypatch.setattr(service,'sb_request',lambda *a,**kw:R())
    r=client.post('/api/auth/login',headers=h(True),json={'email':'user@example.com','password':'123456789'})
    assert r.status_code==403 and 'set-cookie' not in r.headers

def test_login_sets_http_only_secure_cookies(client,monkeypatch):
    class R:
        status_code=200
        def json(self):return {'user':{'id':'owner-uuid','email_confirmed_at':'now'},'access_token':'TOKEN','refresh_token':'REFRESH'}
    monkeypatch.setattr(service,'sb_request',lambda *a,**kw:R())
    r=client.post('/api/auth/login',headers=h(True),json={'email':'user@example.com','password':'123456789'})
    assert r.status_code==200
    items=r.headers.get_list('set-cookie')
    assert len(items)==2 and all('httponly' in x.lower() and 'secure' in x.lower() for x in items)
    assert 'TOKEN' not in r.text and 'REFRESH' not in r.text

def test_wrong_owner_cannot_read_even_with_cookie(client,monkeypatch):
    class R:
        status_code=200
        def json(self):return {'id':'another-uuid','email_confirmed_at':'now'}
    monkeypatch.setattr(service,'sb_request',lambda *a,**kw:R())
    client.cookies.set('qf_access','SIMULATED-ACCESS')
    assert client.get('/api/private/state',headers=h()).status_code==403

def test_new_account_starts_10k_and_no_positions():
    assert service.default_state()['cash']==10000
    assert service.default_state()['holdings']=={}

def owner_stub(request,response):return ('owner-uuid','TESTJWT')

def fresh_quote(symbol):
    return {'symbol':symbol,'price':200.0,'timestamp':dt.datetime.now(dt.UTC).isoformat(),
            'venue':'IEX','source':'Alpaca private test stub'}

def test_private_buy_uses_quote_fee_and_persists(client,monkeypatch):
    monkeypatch.setattr(service,'owner',owner_stub)
    monkeypatch.setattr(service,'read_state',lambda uid,tok:(service.default_state(),0))
    monkeypatch.setattr(service,'quote',fresh_quote)
    writes=[]
    monkeypatch.setattr(service,'save_state',lambda *args:writes.append(args))
    r=client.post('/api/private/trade',headers=h(True),json={'symbol':'MSFT','side':'buy','amount':'100','expected_version':0})
    assert r.status_code==200, r.text
    s=r.json()['portfolio']
    assert 0<s['holdings']['MSFT']<0.5
    assert 9900<=s['cash']<10000
    assert len(writes)==1 and writes[0][3]==0
    assert s['trades'][0]['venue']=='IEX'

def test_buy_rejects_stale_market_quote(client,monkeypatch):
    monkeypatch.setattr(service,'owner',owner_stub)
    monkeypatch.setattr(service,'read_state',lambda *a:(service.default_state(),0))
    def stale(symbol):
        q=fresh_quote(symbol)
        q['timestamp']=(dt.datetime.now(dt.UTC)-dt.timedelta(hours=2)).isoformat()
        return q
    monkeypatch.setattr(service,'quote',stale)
    r=client.post('/api/private/trade',headers=h(True),json={'symbol':'MSFT','side':'buy','amount':'100','expected_version':0})
    assert r.status_code==422 and 'stale' in r.text.lower()

def test_trade_rejects_version_conflict(client,monkeypatch):
    monkeypatch.setattr(service,'owner',owner_stub)
    monkeypatch.setattr(service,'read_state',lambda *a:(service.default_state(),3))
    r=client.post('/api/private/trade',headers=h(True),json={'symbol':'MSFT','side':'buy','amount':'100','expected_version':2})
    assert r.status_code==409

def test_rejects_sell_not_owned(client,monkeypatch):
    monkeypatch.setattr(service,'owner',owner_stub)
    monkeypatch.setattr(service,'read_state',lambda *a:(service.default_state(),0))
    monkeypatch.setattr(service,'quote',fresh_quote)
    r=client.post('/api/private/trade',headers=h(True),json={'symbol':'MSFT','side':'sell','amount':'2','expected_version':0})
    assert r.status_code==422

def test_invalid_quote_symbol_rejected(client,monkeypatch):
    monkeypatch.setattr(service,'owner',owner_stub)
    monkeypatch.setattr(service,'read_state',lambda *a:(service.default_state(),0))
    monkeypatch.setattr(service,'quote',lambda sym:fresh_quote('AAPL'))
    r=client.post('/api/private/trade',headers=h(True),json={'symbol':'MSFT','side':'buy','amount':'100','expected_version':0})
    assert r.status_code==422

def test_demo_has_no_secrets_or_backend_calls_on_startup():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    html=(root/'public/index.html').read_text()
    script=(root/'web/site/private.js').read_text()
    assert 'My workspace' in html and 'FICTIONAL DATA' in html
    assert 'ALPACA_API_SECRET_KEY' not in html and 'SUPABASE_' not in html
    assert 'checkSession();\n})();' not in script


def test_supabase_schema_requires_auth_user_rls():
    from pathlib import Path
    text = (Path(__file__).resolve().parents[1] / 'cloud/supabase.sql').read_text()
    assert 'enable row level security' in text
    assert text.count('(select auth.uid()) = user_id') >= 3
    assert 'grant select, insert, update' in text
    assert 'service_role' not in text
