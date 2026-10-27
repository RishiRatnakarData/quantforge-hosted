"""Hosted-mode security and ledger regressions. All external calls mocked."""

import base64
import datetime as dt
import json

import pytest
from fastapi.testclient import TestClient

from cloud import api as service


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("QF_PROXY_SECRET", "testproxysecret")
    monkeypatch.setenv("PUBLIC_SITE_ORIGIN", "https://quantforge.pages.dev")
    monkeypatch.setenv("OWNER_USER_ID", "owner-uuid")
    monkeypatch.setenv("SUPABASE_URL", "https://unit-test.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "test-public-key")
    return TestClient(service.app, base_url="https://quant-api.onrender.com")


FACTOR_ID = "11111111-1111-4111-8111-111111111111"


def fake_token(aal="aal1", uid="owner-uuid"):
    def enc(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")

    return (
        enc({"alg": "HS256"})
        + "."
        + enc({"sub": uid, "role": "authenticated", "aal": aal})
        + ".mock-signature"
    )


def user(with_factor=False, uid="owner-uuid"):
    return {
        "id": uid,
        "email_confirmed_at": "now",
        "factors": (
            [{"id": FACTOR_ID, "factor_type": "totp", "status": "verified"}] if with_factor else []
        ),
    }


class R:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status

    def json(self):
        return self.payload


def h(post=False):
    v = {"x-qf-proxy-secret": "testproxysecret"}
    if post:
        v.update(origin="https://quantforge.pages.dev", **{"x-qf-action": "1"})
    return v


def test_public_health_without_credentials(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert "key" not in r.text


def test_proxy_secret_required(client):
    assert client.get("/api/auth/session").status_code == 403
    assert client.get("/api/private/state").status_code == 403


def test_mutation_requires_origin_and_action(client):
    assert (
        client.post(
            "/api/auth/login",
            headers=h(),
            json={"email": "user@example.com", "password": "123456789"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/login", headers={**h(True), "origin": "https://attacker.example"}, json={}
        ).status_code
        == 403
    )


def test_anonymous_cannot_read_private_data(client, monkeypatch):
    monkeypatch.setattr(service, "sb_request", lambda *a, **kw: None)
    assert client.get("/api/private/state", headers=h()).status_code == 401
    assert client.get("/api/private/quotes?symbols=MSFT", headers=h()).status_code == 401
    assert (
        client.post(
            "/api/private/trade",
            headers=h(True),
            json={"symbol": "MSFT", "side": "buy", "amount": "100", "expected_version": 0},
        ).status_code
        == 401
    )


def test_login_rejects_non_owner(client, monkeypatch):
    class R:
        status_code = 200

        def json(self):
            return {
                "user": {"id": "wrong", "email_confirmed_at": "now"},
                "access_token": "TOKEN",
                "refresh_token": "REFRESH",
            }

    monkeypatch.setattr(service, "sb_request", lambda *a, **kw: R())
    r = client.post(
        "/api/auth/login",
        headers=h(True),
        json={"email": "user@example.com", "password": "123456789"},
    )
    assert r.status_code == 403 and "set-cookie" not in r.headers


def test_login_sets_http_only_secure_cookies(client, monkeypatch):
    token = fake_token("aal1")

    def stub(method, path, **kw):
        if path == "/auth/v1/token":
            return R({"user": user(), "access_token": token, "refresh_token": "REFRESH"})
        if path == "/auth/v1/user":
            return R(user())
        raise AssertionError(path)

    monkeypatch.setattr(service, "sb_request", stub)
    r = client.post(
        "/api/auth/login",
        headers=h(True),
        json={"email": "user@example.com", "password": "123456789"},
    )
    assert r.status_code == 200
    assert r.json() == {"signed_in": False, "mfa_required": True, "mfa_setup": True}
    items = r.headers.get_list("set-cookie")
    assert len(items) == 2 and all("httponly" in x.lower() and "secure" in x.lower() for x in items)
    assert token not in r.text and "REFRESH" not in r.text


def test_wrong_owner_cannot_read_even_with_cookie(client, monkeypatch):
    class R:
        status_code = 200

        def json(self):
            return {"id": "another-uuid", "email_confirmed_at": "now"}

    monkeypatch.setattr(service, "sb_request", lambda *a, **kw: R())
    client.cookies.set("qf_access", "SIMULATED-ACCESS")
    assert client.get("/api/private/state", headers=h()).status_code == 403


def test_new_account_starts_10k_and_no_positions():
    assert service.default_state()["cash"] == 10000
    assert service.default_state()["holdings"] == {}


def owner_stub(request, response):
    return ("owner-uuid", "TESTJWT")


def fresh_quote(symbol):
    return {
        "symbol": symbol,
        "price": 200.0,
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
        "venue": "IEX",
        "source": "Alpaca private test stub",
    }


def test_private_buy_uses_quote_fee_and_persists(client, monkeypatch):
    monkeypatch.setattr(service, "owner", owner_stub)
    monkeypatch.setattr(service, "read_state", lambda uid, tok: (service.default_state(), 0))
    monkeypatch.setattr(service, "quote", fresh_quote)
    writes = []
    monkeypatch.setattr(service, "save_state", lambda *args: writes.append(args))
    r = client.post(
        "/api/private/trade",
        headers=h(True),
        json={"symbol": "MSFT", "side": "buy", "amount": "100", "expected_version": 0},
    )
    assert r.status_code == 200, r.text
    s = r.json()["portfolio"]
    assert 0 < s["holdings"]["MSFT"] < 0.5
    assert 9900 <= s["cash"] < 10000
    assert len(writes) == 1 and writes[0][3] == 0
    assert s["trades"][0]["venue"] == "IEX"


def test_buy_rejects_stale_market_quote(client, monkeypatch):
    monkeypatch.setattr(service, "owner", owner_stub)
    monkeypatch.setattr(service, "read_state", lambda *a: (service.default_state(), 0))

    def stale(symbol):
        q = fresh_quote(symbol)
        q["timestamp"] = (dt.datetime.now(dt.UTC) - dt.timedelta(hours=2)).isoformat()
        return q

    monkeypatch.setattr(service, "quote", stale)
    r = client.post(
        "/api/private/trade",
        headers=h(True),
        json={"symbol": "MSFT", "side": "buy", "amount": "100", "expected_version": 0},
    )
    assert r.status_code == 422 and "stale" in r.text.lower()


def test_trade_rejects_version_conflict(client, monkeypatch):
    monkeypatch.setattr(service, "owner", owner_stub)
    monkeypatch.setattr(service, "read_state", lambda *a: (service.default_state(), 3))
    r = client.post(
        "/api/private/trade",
        headers=h(True),
        json={"symbol": "MSFT", "side": "buy", "amount": "100", "expected_version": 2},
    )
    assert r.status_code == 409


def test_rejects_sell_not_owned(client, monkeypatch):
    monkeypatch.setattr(service, "owner", owner_stub)
    monkeypatch.setattr(service, "read_state", lambda *a: (service.default_state(), 0))
    monkeypatch.setattr(service, "quote", fresh_quote)
    r = client.post(
        "/api/private/trade",
        headers=h(True),
        json={"symbol": "MSFT", "side": "sell", "amount": "2", "expected_version": 0},
    )
    assert r.status_code == 422


def test_invalid_quote_symbol_rejected(client, monkeypatch):
    monkeypatch.setattr(service, "owner", owner_stub)
    monkeypatch.setattr(service, "read_state", lambda *a: (service.default_state(), 0))
    monkeypatch.setattr(service, "quote", lambda sym: fresh_quote("AAPL"))
    r = client.post(
        "/api/private/trade",
        headers=h(True),
        json={"symbol": "MSFT", "side": "buy", "amount": "100", "expected_version": 0},
    )
    assert r.status_code == 422


def test_demo_has_no_secrets_or_backend_calls_on_startup():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    html = (root / "public/index.html").read_text(encoding="utf-8")
    script = (root / "web/site/private.js").read_text(encoding="utf-8")
    assert "Private workspace" in html and "PUBLIC OVERVIEW" in html
    assert "ALPACA_API_SECRET_KEY" not in html and "SUPABASE_" not in html
    assert "checkSession();\n})();" not in script


def test_supabase_schema_requires_auth_user_rls():
    from pathlib import Path

    text = (Path(__file__).resolve().parents[1] / "cloud/supabase.sql").read_text(encoding="utf-8")
    assert "enable row level security" in text
    assert text.count("(select auth.uid()) = user_id") >= 3
    assert "grant select, insert, update" in text
    assert "service_role" not in text


def test_password_only_is_denied_all_private_endpoints(client, monkeypatch):
    token = fake_token("aal1")
    client.cookies.set("qf_access", token)
    monkeypatch.setattr(service, "sb_request", lambda *a, **kw: R(user(with_factor=True)))
    for path in ("/api/private/state", "/api/private/quotes?symbols=MSFT"):
        r = client.get(path, headers=h())
        assert r.status_code == 403 and "Authenticator" in r.text
    r = client.post(
        "/api/private/notes",
        headers=h(True),
        json={"expected_version": 0, "watchlist": [], "notes": []},
    )
    assert r.status_code == 403
    r = client.post(
        "/api/private/trade",
        headers=h(True),
        json={"symbol": "MSFT", "side": "buy", "amount": "100", "expected_version": 0},
    )
    assert r.status_code == 403
    s = client.get("/api/auth/session", headers=h())
    assert s.json() == {"signed_in": False, "mfa_required": True, "mfa_setup": False}


def test_unenrolled_owner_can_start_setup_and_get_qr(client, monkeypatch):
    token = fake_token("aal1")
    client.cookies.set("qf_access", token)
    calls = []

    def stub(method, path, **kw):
        calls.append((method, path))
        if path == "/auth/v1/user":
            return R(user())
        if path == "/auth/v1/factors":
            return R(
                {
                    "id": FACTOR_ID,
                    "totp": {"qr_code": '<svg xmlns="http://www.w3.org/2000/svg"></svg>'},
                }
            )
        raise AssertionError(path)

    monkeypatch.setattr(service, "sb_request", stub)
    r = client.post("/api/auth/mfa/enroll", headers=h(True), json={})
    assert r.status_code == 200 and r.json()["factor_id"] == FACTOR_ID
    assert r.json()["qr_svg"].startswith("<svg")
    assert "secret" not in r.text.lower()
    assert calls == [("GET", "/auth/v1/user"), ("POST", "/auth/v1/factors")]


def test_enroll_forbidden_if_verified_factor_exists(client, monkeypatch):
    client.cookies.set("qf_access", fake_token("aal1"))
    calls = []

    def stub(method, path, **kw):
        calls.append(path)
        return R(user(with_factor=True))

    monkeypatch.setattr(service, "sb_request", stub)
    r = client.post("/api/auth/mfa/enroll", headers=h(True), json={})
    assert r.status_code == 409
    assert calls == ["/auth/v1/user"]


def test_valid_mfa_verify_upgrades_cookie_to_aal2(client, monkeypatch):
    client.cookies.set("qf_access", fake_token("aal1"))
    calls = []
    upgraded = fake_token("aal2")

    def stub(method, path, **kw):
        calls.append((method, path, kw))
        if path == "/auth/v1/user":
            return R(user(with_factor=(kw["token"] == upgraded)))
        if path.endswith("/challenge"):
            return R({"id": "challenge-id"})
        if path.endswith("/verify"):
            assert kw["payload"] == {"challenge_id": "challenge-id", "code": "123456"}
            return R({"access_token": upgraded, "refresh_token": "REFRESH-AAL2"})
        raise AssertionError(path)

    monkeypatch.setattr(service, "sb_request", stub)
    r = client.post(
        "/api/auth/mfa/verify", headers=h(True), json={"factor_id": FACTOR_ID, "code": "123456"}
    )
    assert r.status_code == 200, r.text
    assert r.json()["signed_in"] is True
    assert "REFRESH-AAL2" not in r.text
    assert any(upgraded in ck for ck in r.headers.get_list("set-cookie"))
    # The upgraded session passes protected authorization after Supabase verifies it.
    assert (
        service.owner(
            client._transport.app.router.routes[0]
            if False
            else type("RequestStub", (), {"cookies": {"qf_access": upgraded}})(),
            service.Response(),
        )[0]
        == "owner-uuid"
    )


def test_invalid_code_never_issues_mfa_cookie(client, monkeypatch):
    client.cookies.set("qf_access", fake_token("aal1"))

    def stub(method, path, **kw):
        if path == "/auth/v1/user":
            return R(user(with_factor=True))
        if path.endswith("/challenge"):
            return R({"id": "challenge"})
        if path.endswith("/verify"):
            return R({"error": "invalid"}, 401)
        raise AssertionError(path)

    monkeypatch.setattr(service, "sb_request", stub)
    r = client.post(
        "/api/auth/mfa/verify", headers=h(True), json={"factor_id": FACTOR_ID, "code": "123456"}
    )
    assert r.status_code == 401
    assert "set-cookie" not in r.headers


def test_verified_session_rejected_if_token_claims_do_not_match_owner(client, monkeypatch):
    client.cookies.set("qf_access", fake_token("aal2", uid="different-user"))
    monkeypatch.setattr(service, "sb_request", lambda *a, **kw: R(user(with_factor=True)))
    r = client.get("/api/private/state", headers=h())
    assert r.status_code == 401


def test_verified_session_requires_enrolled_totp(client, monkeypatch):
    client.cookies.set("qf_access", fake_token("aal2"))
    monkeypatch.setattr(service, "sb_request", lambda *a, **kw: R(user()))
    r = client.get("/api/private/state", headers=h())
    assert r.status_code == 403


def test_mfa_sql_rls_and_browser_controls():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    sql = (root / "cloud/supabase.sql").read_text(encoding="utf-8")
    assert sql.count("(select auth.jwt()->>'aal') = 'aal2'") >= 3
    ui = (root / "public/index.html").read_text(encoding="utf-8")
    script = (root / "web/site/private.js").read_text(encoding="utf-8")
    for selector in (
        "private-mfa-code",
        "private-mfa-qr",
        "private-mfa-submit",
        "private-mfa-start",
    ):
        assert selector in ui
    assert "auth/mfa/verify" in script
    assert "auth/mfa/enroll" in script
    assert "checkSession();\n})();" not in script
