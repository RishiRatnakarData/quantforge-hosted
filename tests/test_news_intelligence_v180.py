"""News-topic and sentiment tests; provider calls are mocked and never reach the network."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cloud import api
from cloud.news_intelligence_v180 import alpaca_news, analyze_news

NOW = dt.datetime(2026, 11, 6, 17, tzinfo=dt.UTC)


def sample():
    return [
        {"id": 1, "headline": "Apple beats profit estimates and raises guidance",
         "created_at": "2026-11-05T15:00:00Z", "symbols": ["AAPL"],
         "source": "Example", "url": "https://example.org/story"},
        {"id": 2, "headline": "Apple shares fall after product recall",
         "created_at": "2026-11-04T15:00:00Z", "symbols": ["AAPL"],
         "source": "Example", "url": "javascript:alert(1)"},
        {"id": 3, "headline": "Old Microsoft earnings unexpectedly beat expectations",
         "created_at": "2026-09-05T15:00:00Z", "symbols": ["MSFT"],
         "source": "Example"},
    ]


def test_actual_dated_headlines_with_topics_and_no_untrusted_urls(monkeypatch):
    monkeypatch.delenv("QF_FINBERT_LOCAL_DIR", raising=False)
    result = analyze_news(sample(), ["AAPL", "MSFT"], as_of=NOW.isoformat())
    assert result["articles_analyzed"] == 2
    assert result["rows"][0]["articles"] == 2
    assert result["rows"][1]["tone"] == "No recent news"
    assert result["rows"][0]["headlines"][1]["url"] == ""
    assert result["method"].startswith("Financial-word baseline")
    assert "TF-IDF" in result["topic_method"]
    assert result["licensed_private"] is True


def test_future_headlines_and_wrong_company_cannot_be_used(monkeypatch):
    monkeypatch.delenv("QF_FINBERT_LOCAL_DIR", raising=False)
    items = sample() + [
        {"id": 4, "headline": "Apple sees future record profits",
         "created_at": "2026-11-09T00:00:00Z", "symbols": ["AAPL"]},
        {"id": 5, "headline": "Company sees unexpected profit improvement",
         "created_at": "2026-11-05T00:00:00Z", "symbols": ["GOOG"]},
    ]
    assert analyze_news(items, ["AAPL"], as_of=NOW.isoformat())["articles_analyzed"] == 2


def test_provider_headers_are_server_only_and_return_text_is_bounded(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY_ID", "not-a-real-account-key")
    monkeypatch.setenv("ALPACA_API_SECRET_KEY", "not-a-real-secret")

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {"news": sample()}

    class Session:
        def get(self, url, *, headers, params, timeout):
            assert url == "https://data.alpaca.markets/v1beta1/news"
            assert headers["APCA-API-KEY-ID"] == "not-a-real-account-key"
            assert headers["APCA-API-SECRET-KEY"] == "not-a-real-secret"
            assert params["symbols"] == "AAPL"
            assert params["include_content"] == "false"
            assert timeout <= 16
            return Response()

    result = alpaca_news(Session(), ["AAPL"], now=NOW)
    assert result["articles_analyzed"] == 2
    assert "not-a-real-secret" not in str(result)
    assert all("content" not in x for x in result["rows"][0]["headlines"])


def test_endpoint_is_closed_without_proxy_and_verified_owner():
    client = TestClient(api.app)
    result = client.get("/api/private/news-research?symbols=AAPL")
    assert result.status_code == 403
    assert "Forbidden" in result.text


def test_endpoint_query_is_validated_after_auth(monkeypatch):
    monkeypatch.setattr(api, "owner", lambda *args: ("test-owner", "test-token"))
    class Probe:
        called = False
        def __call__(self, *args, **kwargs):
            self.called = True
            return {"rows": []}
    probe = Probe()
    monkeypatch.setattr(api.news_intelligence_v180, "alpaca_news", probe)
    from starlette.requests import Request
    from starlette.responses import Response
    request = Request({"type": "http", "method": "GET", "path": "/api/private/news-research", "headers": []})
    with pytest.raises(Exception) as err:
        api.private_news_research(request, Response(), "AAPL,AAPL")
    assert getattr(err.value, "status_code", None) == 422
    assert not probe.called


def test_public_bundle_has_no_provider_headlines_or_credentials():
    html = (Path(__file__).resolve().parents[1] / "public/index.html").read_text(encoding="utf-8")
    assert "qf-v180-news" in html
    assert "APCA-API-SECRET-KEY" not in html
    assert "not-a-real-secret" not in html
    assert "Apple beats profit estimates" not in html
