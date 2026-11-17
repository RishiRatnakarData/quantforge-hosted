"""Freshness boundaries remain enforced while safe diagnostics explain refusals."""
import datetime as dt

import pytest
from fastapi import HTTPException

from cloud import api


@pytest.mark.parametrize(("symbol", "limit"), [("MSFT", 900), ("BTC/USD", 300)])
def test_stale_preview_and_commit_terms_refuse_with_observation_context(symbol, limit):
    now = dt.datetime.now(dt.UTC)
    observation = {"symbol": symbol, "price": 100,
                   "timestamp": (now-dt.timedelta(seconds=limit+120)).isoformat(),
                   "venue": "Controlled provider fixture"}
    request = api.TradeRequest(symbol=symbol, side="buy", amount="50", expected_version=1)
    with pytest.raises(HTTPException) as raised:
        api.trade_terms({"cash": 100, "holdings": {}}, request, observation)
    detail = raised.value.detail
    assert raised.value.status_code == 422
    assert detail["code"] == "quote_stale"
    assert detail["observation"]["observed_at"] == observation["timestamp"]
    assert detail["observation"]["max_age_seconds"] == limit
    assert detail["observation"]["age_seconds"] >= limit


def test_fresh_preview_terms_and_market_price_validation_are_preserved():
    observation = {"symbol": "MSFT", "price": 100,
                   "timestamp": dt.datetime.now(dt.UTC).isoformat(), "venue": "Fixture"}
    request = api.TradeRequest(symbol="MSFT", side="buy", amount="50", expected_version=1)
    result = api.trade_terms({"cash": 100, "holdings": {}}, request, observation)
    assert result["cash_after"] >= 50
    assert result["cash_impact"] < 0
    assert result["fee"] >= 0
