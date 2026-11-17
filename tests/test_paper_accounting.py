"""Financial invariants, fee treatment and conservative legacy-state handling."""
from copy import deepcopy

from cloud.paper_accounting import accounting_effect, initial_book


def apply(state, side, units, gross, fee, remaining):
    terms = {"symbol": "CASE", "side": side, "units": units, "gross": gross,
             "fee": fee, "held_after": remaining}
    before = deepcopy(state)
    result = accounting_effect(state, terms)
    assert state == before
    state["basis_accounting"] = result["accounting"]
    state["holdings"] = {"CASE": remaining} if remaining else {}
    return result


def test_partial_and_final_sales_reconcile_all_basis_and_both_fees():
    state = {"holdings": {}, "basis_accounting": initial_book()}
    apply(state, "buy", 2, 200, 1, 2)
    apply(state, "buy", 1, 120, 1, 3)
    assert state["basis_accounting"]["positions"]["CASE"]["total_basis"] == 322
    first = apply(state, "sell", 1, 150, 1, 2)
    assert first["cost_basis_allocated"] == 107.33
    assert first["realized_pnl"] == 41.67
    last = apply(state, "sell", 2, 160, 1, 0)
    assert last["cost_basis_allocated"] == 214.67
    assert last["realized_pnl"] == -55.67
    assert state["basis_accounting"]["realized_pnl"] == -14
    assert state["basis_accounting"]["positions"] == {}
    assert state["basis_accounting"]["realized_complete"] is True


def test_legacy_holdings_and_unused_old_cost_basis_are_not_reconstructed():
    state = {"holdings": {"CASE": 2}, "cost_basis": {"CASE": 1}}
    result = apply(state, "sell", 1, 100, 1, 1)
    assert result["realized_pnl"] is None
    assert state["basis_accounting"]["positions"]["CASE"]["total_basis"] is None
    assert state["basis_accounting"]["realized_complete"] is False
    apply(state, "sell", 1, 100, 1, 0)
    apply(state, "buy", 1, 80, 1, 1)
    assert state["basis_accounting"]["positions"]["CASE"]["total_basis"] == 81
    final = apply(state, "sell", 1, 100, 1, 0)
    assert final["realized_pnl"] == 18
    assert state["basis_accounting"]["realized_complete"] is False


def test_corrupt_or_quantity_mismatched_basis_is_withheld():
    state = {"holdings": {"CASE": 2}, "basis_accounting": initial_book()}
    state["basis_accounting"]["positions"]["CASE"] = {"units": 1, "total_basis": 50}
    assert apply(state, "sell", 1, 100, 1, 1)["realized_pnl"] is None


def test_lost_trade_response_reconciles_without_applying_cost_basis_twice(monkeypatch):
    import datetime as dt

    from fastapi.testclient import TestClient

    from cloud import api

    monkeypatch.setenv("QF_PROXY_SECRET", "fixture-only-secret")
    monkeypatch.setenv("PUBLIC_SITE_ORIGIN", "https://research.test")
    monkeypatch.setattr(api, "owner", lambda *_: ("fixture-owner", "fixture-token"))
    state = api.default_state()
    version = 0
    writes = []

    def read(*_):
        return deepcopy(state), version

    def save(_uid, _token, payload, expected):
        nonlocal state, version
        assert expected == version
        state = deepcopy(payload)
        version += 1
        writes.append(expected)

    monkeypatch.setattr(api, "read_state", read)
    monkeypatch.setattr(api, "save_state", save)
    monkeypatch.setattr(api, "quote", lambda symbol: {
        "symbol": symbol, "price": 100, "timestamp": dt.datetime.now(dt.UTC).isoformat(),
        "venue": "Controlled fixture", "synthetic": False,
    })
    client = TestClient(api.app, base_url="https://api.test")
    headers = {"x-qf-proxy-secret": "fixture-only-secret", "x-qf-action": "1", "origin": "https://research.test"}
    payload = {"symbol": "CASE", "side": "buy", "amount": "100", "expected_version": 0, "request_id": "fixture-once"}
    first = client.post("/api/private/trade", headers=headers, json=payload)
    second = client.post("/api/private/trade", headers=headers, json=payload)
    assert first.status_code == second.status_code == 200
    assert second.json()["reconciled"] is True
    assert len(writes) == 1
    assert state["basis_accounting"]["positions"]["CASE"]["total_basis"] == 100
