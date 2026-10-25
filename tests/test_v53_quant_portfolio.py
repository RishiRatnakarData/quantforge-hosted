"""V5.3 historical evidence validation, optimization and read-only local APIs."""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import numpy as np
import pytest

from quantforge.desk.engine import DeskError, PaperLedger
from quantforge.desk.market import DemoDeskMarket
from quantforge.desk.quant_portfolio import (
    HistoricalPriceStore,
    analyze_prices,
    parse_price_csv,
)
from quantforge.desk.server import make_handler


def sample_csv(symbols=("MSFT", "VOO", "BTC/USD"), n=180):
    """Deterministic fictional adjusted prices for tests only."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(("date", "symbol", "close"))
    rng = np.random.default_rng(1337)
    factor = rng.normal(0, 0.007, size=n)
    days = [dt.date(2026, 1, 1) + dt.timedelta(days=i) for i in range(n + 90)]
    days = [day for day in days if day.weekday() < 5][:n]
    for j, symbol in enumerate(symbols):
        log_rets = (0.65 - j * .12) * factor + rng.normal(0, 0.006 + .004 * j, size=n)
        closes = 100 * np.exp(np.cumsum(log_rets))
        for day, close in zip(days, closes, strict=True):
            writer.writerow((day.isoformat(), symbol, f"{close:.8f}"))
    return out.getvalue()


def blank_portfolio():
    return {"positions": [], "cash": 10000, "equity": 10000}


def test_rejects_invalid_prices_and_duplicates():
    base = sample_csv()
    assert len(parse_price_csv(base)["symbols"]) == 3
    with pytest.raises(DeskError, match="Duplicate"):
        parse_price_csv(base + base.splitlines(True)[1])
    with pytest.raises(DeskError, match="positive"):
        parse_price_csv(base.replace(",100.", ",-100.", 1))
    with pytest.raises(DeskError, match="columns"):
        parse_price_csv("symbol,date,close\n")
    with pytest.raises(DeskError, match="at least two"):
        parse_price_csv(sample_csv(symbols=("MSFT",)))


def test_import_private_atomic_and_history(tmp_path):
    store = HistoricalPriceStore(tmp_path / "quant.sqlite3")
    assert not store.status()["available"]
    result = store.save(raw=sample_csv(), source="Fictional unit-test series")
    assert result["observations"] == 540
    original = store.status()
    assert {x["symbol"] for x in original["symbols"]} == {"MSFT", "VOO", "BTC/USD"}
    with pytest.raises(DeskError):
        store.save(raw="broken", source="Bad import")
    assert store.status() == original


def test_baseline_and_optimizer_constraints(tmp_path):
    store = HistoricalPriceStore(tmp_path / "quant.sqlite3")
    store.save(raw=sample_csv(), source="Fictional unit-test series")
    result = analyze_prices(store, blank_portfolio(), symbols=["MSFT", "VOO", "BTC/USD"])
    baseline, optimized = result["allocations"]
    assert result["matched_return_dates"] >= 90
    assert result["baseline_definition"].startswith("Equal-weight")
    assert sum(optimized["risk"]["allocation_pct"].values()) == pytest.approx(100, abs=.001)
    assert optimized["risk"]["allocation_pct"]["BTC/USD"] <= 15.0001
    assert max(optimized["risk"]["allocation_pct"].values()) <= 60.0001
    assert baseline["risk"]["annual_volatility_pct"] > 0
    assert optimized["monte_carlo"]["es_95_usd"] >= optimized["monte_carlo"]["var_95_usd"]
    assert result["correlations"][0][0] == 1
    assert baseline["risk"]["sum_risk_contributions_pct_points"] == pytest.approx(
        baseline["risk"]["annual_volatility_pct"], abs=.002
    )
    assert result == analyze_prices(store, blank_portfolio(), symbols=["MSFT", "VOO", "BTC/USD"])


def test_existing_portfolio_weight_normalization(tmp_path):
    store = HistoricalPriceStore(tmp_path / "quant.sqlite3")
    store.save(raw=sample_csv(), source="Fictional unit-test series")
    portfolio = {"positions": [{"symbol": "MSFT", "value": 400},
                               {"symbol": "VOO", "value": 100}], "cash": 9500, "equity": 10000}
    result = analyze_prices(store, portfolio, symbols=["MSFT", "VOO"])
    assert result["allocations"][0]["risk"]["allocation_pct"] == {"MSFT": 80, "VOO": 20}
    assert result["baseline_definition"].startswith("Existing")


def test_infeasible_crypto_caps(tmp_path):
    store = HistoricalPriceStore(tmp_path / "quant.sqlite3")
    store.save(raw=sample_csv(), source="Fictional unit-test series")
    with pytest.raises(DeskError, match="infeasible"):
        analyze_prices(store, blank_portfolio(), symbols=["MSFT", "BTC/USD"],
                       max_weight_pct=60, crypto_cap_pct=15)
    with pytest.raises(DeskError, match="unique"):
        analyze_prices(store, blank_portfolio(), symbols=["MSFT", "MSFT"])
    with pytest.raises(DeskError, match="Maximum"):
        analyze_prices(store, blank_portfolio(), symbols=["MSFT", "VOO"], max_weight_pct=101)


def test_misaligned_dates_fail(tmp_path):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["date", "symbol", "close"])
    for i in range(130):
        w.writerow([(dt.date(2025, 1, 1) + dt.timedelta(days=i)).isoformat(), "MSFT", i + 100])
        w.writerow([(dt.date(2026, 1, 1) + dt.timedelta(days=i)).isoformat(), "VOO", i + 101])
    store = HistoricalPriceStore(tmp_path / "quant.sqlite3")
    store.save(raw=out.getvalue(), source="Unmatched fictional sample")
    with pytest.raises(DeskError, match="overlapping"):
        analyze_prices(store, blank_portfolio(), symbols=["MSFT", "VOO"])


def test_api_import_and_analysis_do_not_mutate_ledger(tmp_path):
    ledger = PaperLedger(tmp_path / "paper.sqlite3")
    original = ledger.snapshot()
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ledger, DemoDeskMarket(), demo=True))
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def call(path, data=None):
        request = Request(base + path, headers={"Host": f"127.0.0.1:{server.server_port}",
                                             "Content-Type": "application/json"},
                          data=json.dumps(data).encode() if data is not None else None)
        with urlopen(request, timeout=25) as response:
            return json.loads(response.read())

    try:
        assert not call("/api/quant-history")["available"]
        imported = call("/api/quant-import", {"csv": sample_csv(), "source": "Fictional integration test"})
        assert imported["observations"] == 540
        result = call("/api/quant-analysis", {"symbols": ["MSFT", "VOO", "BTC/USD"],
                                              "budget": 3000})
        assert result["hypothetical_budget_usd"] == 3000
        assert len(result["correlations"]) == 3
        assert ledger.snapshot() == original
        with pytest.raises(HTTPError) as exc:
            call("/api/quant-import", {"csv": "bad", "source": "Fictional source"})
        assert exc.value.code == 422
    finally:
        server.shutdown()
        server.server_close()
        t.join(timeout=5)


def test_alpaca_fetch_uses_adjusted_historical_bars_and_private_store(tmp_path):
    from quantforge.desk.quant_portfolio import fetch_alpaca_daily_prices

    class Client:
        def __init__(self):
            self.calls = []

        def _get(self, endpoint, params, ttl):
            self.calls.append((endpoint, params, ttl))
            dates = [dt.date(2026, 1, 1) + dt.timedelta(days=i) for i in range(220)]
            dates = [day for day in dates if day.weekday() < 5]
            return {"bars": [{"t": d.isoformat() + "T00:00:00Z", "c": 100 + i}
                             for i, d in enumerate(dates)]}

    client = Client()
    store = HistoricalPriceStore(tmp_path / "quant.sqlite3")
    info = fetch_alpaca_daily_prices(store, client, symbols=["MSFT", "VOO"],
                                     now=dt.date(2026, 10, 24))
    assert info["observations"] > 200
    assert info["personal_only"] is True
    assert all(params["adjustment"] == "all" and params["feed"] == "iex"
               for _, params, _ in client.calls)
    with pytest.raises(DeskError, match="crypto"):
        fetch_alpaca_daily_prices(store, client, symbols=["MSFT", "BTC/USD"])
    with pytest.raises(DeskError, match="different"):
        fetch_alpaca_daily_prices(store, client, symbols=["MSFT", "MSFT"])


def test_unsafe_alpaca_fetch_never_changes_previous_evidence(tmp_path):
    from quantforge.desk.quant_portfolio import fetch_alpaca_daily_prices

    class BrokenClient:
        def _get(self, endpoint, params, ttl):
            return {"bars": []}

    store = HistoricalPriceStore(tmp_path / "quant.sqlite3")
    store.save(raw=sample_csv(), source="Fictional prior file")
    original = store.status()
    with pytest.raises(DeskError, match="fewer than 91"):
        fetch_alpaca_daily_prices(store, BrokenClient(), symbols=["MSFT", "VOO"])
    assert store.status() == original
