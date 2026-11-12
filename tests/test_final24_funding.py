"""Real FastAPI route/Decimal integration with isolated versioned storage."""

from decimal import Decimal

import pytest
import test_product_transactions_v27 as transaction_cases
from fastapi.testclient import TestClient

from cloud import api

headers = transaction_cases.headers
request = transaction_cases.request


@pytest.fixture
def service(monkeypatch):
    return transaction_cases.service.__wrapped__(monkeypatch)


def body(**kwargs):
    return {
        "action": "deposit",
        "amount": "25.37",
        "expected_version": 4,
        "request_id": "funding-1",
        **kwargs,
    }


def test_funding_preview_commit_and_replay_preserve_profit(service):
    client, store = service
    preview = client.post("/api/private/capital-preview", headers=headers(), json=body()).json()[
        "preview"
    ]
    assert preview["cash_after"] == preview["contributions_after"] == 1025.37
    assert store["writes"] == 0
    saved = client.post("/api/private/capital", headers=headers(), json=body()).json()
    repeated = client.post("/api/private/capital", headers=headers(), json=body()).json()
    assert repeated["reconciled"] is True and store["writes"] == 1
    assert saved["portfolio"]["cash"] == preview["cash_after"]
    assert (
        Decimal(str(saved["portfolio"]["cash"])) - Decimal(str(saved["portfolio"]["initial_cash"]))
        == 0
    )
    assert (
        client.post("/api/private/capital", headers=headers(), json=body(amount="30")).status_code
        == 409
    )


@pytest.mark.parametrize(
    "payload",
    [
        body(action="withdraw", amount="1001"),
        body(amount="0"),
        body(amount="NaN"),
        body(expected_version=3),
    ],
)
def test_invalid_or_conflicting_funding_never_writes(service, payload):
    client, store = service
    assert client.post(
        "/api/private/capital-preview", headers=headers(), json=payload
    ).status_code in (409, 422)
    assert client.post("/api/private/capital", headers=headers(), json=payload).status_code in (
        409,
        422,
    )
    assert store["writes"] == 0


def test_withdraw_preview_uses_same_decimal_rounding_as_commit(service):
    client, store = service
    payload = body(action="withdraw", amount="10.005")
    preview = client.post("/api/private/capital-preview", headers=headers(), json=payload).json()[
        "preview"
    ]
    saved = client.post("/api/private/capital", headers=headers(), json=payload).json()["portfolio"]
    assert (
        preview["amount"] == 10.01
        and saved["cash"] == saved["initial_cash"] == preview["cash_after"] == 989.99
    )


def test_funding_preview_cannot_bypass_owner_or_origin(monkeypatch):
    monkeypatch.setenv("QF_PROXY_SECRET", "fixture-proxy")
    monkeypatch.setenv("PUBLIC_SITE_ORIGIN", "https://quantforge.example")
    client = TestClient(api.app)
    assert client.post("/api/private/capital-preview", json=body()).status_code == 403
    assert (
        client.post("/api/private/capital-preview", headers=headers(), json=body()).status_code
        == 401
    )


def test_safe_rejection_codes_expose_actionable_cause_without_structured_echo(service, monkeypatch):
    client, store = service
    monkeypatch.setattr(
        api,
        "quote",
        lambda symbol: {"symbol": symbol, "price": 200, "timestamp": "2020-01-01T00:00:00Z"},
    )
    rejected = client.post("/api/private/trade-preview", headers=headers(), json=request())
    assert rejected.status_code == 422 and rejected.json()["code"] == "quote_stale"
    assert (
        client.post(
            "/api/private/capital-preview",
            headers=headers(),
            json=body(action="withdraw", amount="1001"),
        ).json()["code"]
        == "withdraw_cash"
    )
    assert store["writes"] == 0


def test_simultaneous_confirmations_use_actual_versioned_save_contract(monkeypatch):
    """Both reads see v4; compare-and-set admits one write and replay reconciles."""
    import copy
    import datetime as dt
    import threading
    from concurrent.futures import ThreadPoolExecutor

    monkeypatch.setenv("QF_PROXY_SECRET", "fixture-proxy")
    monkeypatch.setenv("PUBLIC_SITE_ORIGIN", "https://quantforge.example")
    monkeypatch.setattr(api, "owner", lambda *_: ("fixture-owner", "fixture-token"))
    store = {
        "version": 4,
        "payload": {
            "cash": 1000.0,
            "initial_cash": 1000.0,
            "holdings": {},
            "trades": [],
            "notes": [],
        },
        "writes": 0,
    }
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    class Reply:
        status_code = 200

        def __init__(self, rows):
            self.rows = rows

        def json(self):
            return copy.deepcopy(self.rows)

    def storage(method, _path, **kwargs):
        with lock:
            if method == "GET":
                return Reply([{"version": store["version"], "payload": store["payload"]}])
            assert method == "PATCH"
            if kwargs["params"]["version"] != "eq." + str(store["version"]):
                return Reply([])
            store.update(kwargs["payload"])
            store["writes"] += 1
            return Reply([{"version": store["version"], "payload": store["payload"]}])

    def quote(symbol):
        barrier.wait(timeout=5)
        return {
            "symbol": symbol,
            "price": 200,
            "venue": "MOCK",
            "timestamp": dt.datetime.now(dt.UTC).isoformat(),
        }

    monkeypatch.setattr(api, "sb_request", storage)
    monkeypatch.setattr(api, "quote", quote)
    client = TestClient(api.app)
    payload = request()
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda _: client.post("/api/private/trade", headers=headers(), json=payload),
                range(2),
            )
        )
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert store["writes"] == 1 and store["version"] == 5
    assert store["payload"]["cash"] == 900
    assert len(store["payload"]["trades"]) == 1
    monkeypatch.setattr(api, "quote", lambda *_: pytest.fail("Replay must not reprice"))
    replay = client.post("/api/private/trade", headers=headers(), json=payload)
    assert replay.status_code == 200 and replay.json()["reconciled"] is True
    assert store["writes"] == 1
