"""V6.1: full-name, no-symbol-typing private asset browser with MFA."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cloud import api as service
from cloud import asset_directory as directory


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("QF_PROXY_SECRET", "test-proxy")
    monkeypatch.setenv("PUBLIC_SITE_ORIGIN", "https://quantforge.example")
    return TestClient(service.app)


def headers():
    return {"x-qf-proxy-secret": "test-proxy"}


def test_browse_requires_owner_mfa_and_proxy(client):
    assert client.get("/api/private/assets").status_code == 403
    assert client.get("/api/private/assets", headers=headers()).status_code == 401


def test_directory_uses_paper_endpoint_and_never_leaks_credentials(monkeypatch):
    directory._CACHE.clear()
    monkeypatch.setenv("ALPACA_API_KEY_ID", "secret-id")
    monkeypatch.setenv("ALPACA_API_SECRET_KEY", "private-secret")
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {"symbol": "MSFT", "name": "Microsoft Corporation", "status": "active", "tradable": True, "exchange": "NASDAQ"},
                {"symbol": "JPM", "name": "JPMorgan Chase", "status": "active", "tradable": True, "exchange": "NYSE"},
                {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "status": "active", "tradable": True, "exchange": "ARCA"},
                {"symbol": "ABCD", "name": "Inactive", "status": "inactive", "tradable": True},
                {"symbol": "NOPE", "name": "Not tradable", "status": "active", "tradable": False},
            ]

    def get(url, headers, params, timeout):
        calls.append((url, headers, params, timeout))
        return Response()

    monkeypatch.setattr(directory.requests, "get", get)
    result = directory.browse(category="all", letter="M")
    assert [a["name"] for a in result["items"]] == ["Microsoft Corporation"]
    assert result["total"] == 1
    assert "secret-id" not in str(result) and "private-secret" not in str(result)
    assert calls[0][0] == "https://paper-api.alpaca.markets/v2/assets"
    assert calls[0][2] == {"status": "active", "asset_class": "us_equity"}
    directory.browse(category="popular")
    assert len(calls) == 1  # one provider request, served from cache on subsequent browsing
    directory._CACHE.clear()


def test_directory_mfa_passes_and_search_is_optional(client, monkeypatch):
    monkeypatch.setattr(service, "owner", lambda *_: ("owner", "token"))
    monkeypatch.setattr(directory, "browse", lambda **kwargs: {
        "items": [{"symbol": "MSFT", "name": "Microsoft", "exchange": "NASDAQ", "asset_class": "us_equity"}],
        "total": 1,
        "page": kwargs.get("page", 0),
        "pages": 1,
        "has_previous": False,
        "has_next": False,
        "licensed_private": True,
    })
    result = client.get("/api/private/assets?category=all&letter=M", headers=headers())
    assert result.status_code == 200
    assert result.json()["items"][0]["name"] == "Microsoft"


@pytest.mark.parametrize("category,letter,query,page", [
    ("unknown", "", "", 0), ("all", "12", "", 0), ("all", "", "A" * 61, 0), ("all", "", "", -1),
])
def test_invalid_browse_inputs_do_not_fetch(category, letter, query, page, monkeypatch):
    monkeypatch.setattr(directory, "_get_assets", lambda _: (_ for _ in ()).throw(AssertionError("called provider")))
    with pytest.raises(ValueError):
        directory.browse(category=category, letter=letter, query=query, page=page)


def test_frontend_is_browse_only_and_keeps_three_csp_scripts():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    builder = (root / "tools/build_unified_site.py").read_text(encoding="utf-8")
    private = (root / "web/site/private.js").read_text(encoding="utf-8")
    api = (root / "cloud/api.py").read_text(encoding="utf-8")
    for needle in ("private-browse-trade", "private-browse-research", "asset-browser-results", "asset-browser-letters"):
        assert needle in builder or needle in private
    assert 'id="private-symbol" list=' not in builder
    assert 'id="private-history-symbols" value="MSFT' not in builder
    assert "private/assets?" in private
    assert "owner(request, response)" in api
    assert "ALPACA_API_SECRET_KEY" not in private
    built = (root / "public/index.html").read_text(encoding="utf-8")
    assert built.count("<script>") == 3
