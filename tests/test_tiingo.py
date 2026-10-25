"""Offline mock-server tests for the private real-market-data connector."""

from __future__ import annotations

import json

import exchange_calendars as xcals
import pandas as pd
import pytest

from quantforge.data.sources import ProviderError
from quantforge.data.tiingo import audit_xnys_calendar, load_tiingo_history


class StubReply:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class StubSession:
    def __init__(self, by_symbol):
        self.by_symbol = by_symbol
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        symbol = url.split("/")[-2]
        return StubReply(self.by_symbol[symbol])


def rows(symbol, *, start="2024-01-02", end="2024-02-29"):
    cal = xcals.get_calendar("XNYS")
    days = cal.sessions_in_range(start, end)
    return [
        {
            "date": f"{date.date()}T00:00:00.000Z",
            "adjClose": 100.0 + 0.21 * i + (0.4 if symbol == "SPY" else 0.2),
            "close": 101.0 + 0.21 * i,
            "divCash": 0.0,
            "splitFactor": 1.0,
        }
        for i, date in enumerate(days)
    ]


def test_full_tiingo_retrieval_and_cache_are_private(tmp_path, monkeypatch):
    monkeypatch.delenv("TIINGO_API_TOKEN", raising=False)
    session = StubSession({"SPY": rows("SPY"), "IEF": rows("IEF")})
    folder = tmp_path / "data" / "private"
    prices, manifest = load_tiingo_history(authorized_persistent_storage=True, 
        symbols=["SPY", "IEF"],
        start="2024-01-02", end="2024-02-29", cache_dir=folder,
        token="secret_token_DO_NOT_SAVE", session=session,
    )
    assert prices.symbol.nunique() == 2
    assert manifest["calendar_audit"]["pass"] is True
    assert manifest["price_basis"] == "dividend_adjusted_close"
    assert all("Authorization" in call[1]["headers"] for call in session.calls)
    assert all("token" not in call[1]["params"] for call in session.calls)
    assert "secret_token_DO_NOT_SAVE" not in json.dumps(manifest)
    assert all("secret_token_DO_NOT_SAVE" not in f.read_text() for f in folder.iterdir())
    copied, cached_manifest = load_tiingo_history(authorized_persistent_storage=True, 
        symbols=["SPY", "IEF"],
        start="2024-01-02", end="2024-02-29", cache_dir=folder,
        offline=True, session=StubSession({}),
    )
    pd.testing.assert_frame_equal(copied, prices)
    assert all(item["status"] == "reused_snapshot" for item in cached_manifest["snapshots"])


def test_missing_tiingo_session_is_rejected(tmp_path):
    bad = rows("SPY")
    del bad[5]
    with pytest.raises(ProviderError, match="failed XNYS audit"):
        load_tiingo_history(authorized_persistent_storage=True, 
            symbols=["SPY"], start="2024-01-02", end="2024-02-29",
            cache_dir=tmp_path, token="private", session=StubSession({"SPY": bad}),
        )


def test_misaligned_asset_panels_are_rejected(tmp_path):
    second = rows("IEF")
    del second[10]
    with pytest.raises(ProviderError, match="missing symbol-session pairs"):
        load_tiingo_history(authorized_persistent_storage=True, 
            symbols=["SPY", "IEF"], start="2024-01-02", end="2024-02-29",
            cache_dir=tmp_path, token="private",
            session=StubSession({"SPY": rows("SPY"), "IEF": second}),
        )


def test_provider_cannot_silently_substitute_close_for_adjclose(tmp_path):
    data = rows("SPY")
    for item in data:
        del item["adjClose"]
    with pytest.raises(ProviderError, match="Missing Tiingo daily fields"):
        load_tiingo_history(authorized_persistent_storage=True, 
            symbols=["SPY"], start="2024-01-02", end="2024-02-29",
            cache_dir=tmp_path, token="private", session=StubSession({"SPY": data}),
        )


def test_duplicate_provider_sessions_fail(tmp_path):
    data = rows("SPY")
    data.append(dict(data[0]))
    with pytest.raises(ProviderError, match="Duplicate"):
        load_tiingo_history(authorized_persistent_storage=True, 
            symbols=["SPY"], start="2024-01-02", end="2024-02-29",
            cache_dir=tmp_path, token="private", session=StubSession({"SPY": data}),
        )


def test_offline_cache_miss_and_invalid_dates_fail(tmp_path):
    with pytest.raises(ProviderError, match="Missing cached"):
        load_tiingo_history(authorized_persistent_storage=True, 
            symbols=["SPY"], start="2024-01-02", end="2024-02-29",
            cache_dir=tmp_path, offline=True,
        )
    with pytest.raises(ProviderError, match="after end"):
        load_tiingo_history(authorized_persistent_storage=True, symbols=["SPY"], start="2025-01-02", end="2024-01-02")
    with pytest.raises(ProviderError, match="distinct"):
        load_tiingo_history(authorized_persistent_storage=True, symbols=["SPY", "SPY"])
    with pytest.raises(ProviderError, match="uppercase"):
        load_tiingo_history(authorized_persistent_storage=True, symbols=["../../secret"])


def test_calendar_audit_exposes_nonmarket_dates():
    prices = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-05", "2024-01-06", "2024-01-08"]),
        "symbol": ["SPY"] * 3,
        "adjusted_close": [100.0, 101.0, 102.0],
    })
    audit = audit_xnys_calendar(prices)
    assert "2024-01-06" in audit["nonmarket_dates"]
    assert not audit["pass"]


def test_invalid_dividend_field_is_rejected(tmp_path):
    data = rows("SPY")
    data[4]["divCash"] = "unknown"
    with pytest.raises(ProviderError, match="Invalid divCash"):
        load_tiingo_history(authorized_persistent_storage=True, 
            symbols=["SPY"], start="2024-01-02", end="2024-02-29",
            cache_dir=tmp_path, token="private", session=StubSession({"SPY": data}),
        )


def test_provider_truncated_start_is_not_accepted(tmp_path):
    data = rows("SPY")[1:]
    with pytest.raises(ProviderError, match="does not cover requested"):
        load_tiingo_history(authorized_persistent_storage=True, 
            symbols=["SPY"], start="2024-01-02", end="2024-02-29",
            cache_dir=tmp_path, token="private", session=StubSession({"SPY": data}),
        )


def test_refresh_archives_prior_immutable_revision(tmp_path):
    original = rows("SPY")
    revised = rows("SPY")
    revised[10]["adjClose"] += 1.0
    session = StubSession({"SPY": original})
    load_tiingo_history(authorized_persistent_storage=True, 
        symbols=["SPY"], start="2024-01-02", end="2024-02-29",
        cache_dir=tmp_path, token="private", session=session,
    )
    session.by_symbol["SPY"] = revised
    load_tiingo_history(authorized_persistent_storage=True, 
        symbols=["SPY"], start="2024-01-02", end="2024-02-29",
        cache_dir=tmp_path, token="private", session=session, refresh=True,
    )
    assert len(list(tmp_path.glob("*_archived_*.json"))) == 1
    assert len(list(tmp_path.glob("tiingo_SPY_*.json"))) == 2


def test_v4_tiingo_cli_disables_persistent_starter_workflow(tmp_path, monkeypatch):
    """V4 rejects persistence even when a token and mocked provider are present."""
    from quantforge.cli import main
    from quantforge.data import tiingo

    sample = {"SPY": rows("SPY", start="2018-10-01", end="2019-03-01")}
    fake = StubSession(sample)
    monkeypatch.setenv("TIINGO_API_TOKEN", "fixture_only_secret")
    monkeypatch.setattr(tiingo.requests, "Session", lambda: fake)
    destination = tmp_path / "outputs"
    rc = main([
        "tiingo", "--symbols", "SPY",
        "--start", "2018-10-01", "--end", "2019-03-01",
        "--cache-dir", str(tmp_path / "private"),
        "--output", str(destination), "--lookback", "30",
    ])
    assert rc == 2
    assert not destination.exists()
    assert not (tmp_path / "private").exists()


def test_starter_default_refuses_legacy_persistent_snapshot(tmp_path):
    from quantforge.data.sources import ProviderError

    with pytest.raises(ProviderError, match="Starter/Trial"):
        load_tiingo_history(
            symbols=["SPY"], start="2024-01-02", end="2024-02-29",
            cache_dir=tmp_path,
        )
    assert not list(tmp_path.iterdir())
