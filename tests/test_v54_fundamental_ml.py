"""V5.4 financial peer methods — deterministic fictional rows, no real issuer feed."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from quantforge.desk.engine import DeskError, PaperLedger
from quantforge.desk.fundamental_ml import analyze_fundamentals, research_peer_group
from quantforge.desk.market import DemoDeskMarket
from quantforge.desk.server import make_handler


def records(n=12):
    output = []
    for i in range(n):
        j = i / 10
        output.append({
            "symbol": f"S{i:02d}", "cik": 10000 + i, "company_name": f"Fictional Company {i}",
            "fiscal_end": "2026-06-30", "revenue_filing_date": "2026-08-10",
            "revenue_usd": 1_000_000_000 + i * 4_000_000,
            "revenue_growth_pct": 8 + j + 2 * (i % 3),
            "operating_margin_pct": 12 + .5 * (i % 5),
            "net_margin_pct": 7 + 1.3 * (i % 4),
            "free_cash_flow_usd": 110_000_000 + (i % 5) * 1_100_000,
            "long_term_debt_usd": 90_000_000 + (i % 6) * 4_000_000,
            "total_assets_usd": 1_200_000_000 + (i % 4) * 40_000_000,
        })
    return output


class FakeSEC:
    def __init__(self, rows):
        self.rows = {r["symbol"]: r for r in rows}

    def fundamentals(self, ticker):
        if ticker not in self.rows:
            raise DeskError("Issuer not found")
        return self.rows[ticker]


def test_neighbors_deterministic_and_interpretable():
    rows = records()
    r = analyze_fundamentals(rows, "S00")
    assert r == analyze_fundamentals(rows, "S00")
    assert r["sample_size"] == 12
    assert len(r["peers"]) == 5
    assert r["peers"][0]["symbol"] != "S00"
    assert r["peers"][0]["distance"] <= r["peers"][1]["distance"]
    assert r["anomaly"]["available"] is True
    assert 1 <= r["anomaly"]["unusualness_rank"] <= 12
    assert r["neighbor_stability"]["feature_drop_checks"] == 5
    assert r["imputed_values"] == 0
    assert r["financial_features"][3]["key"] == "fcf_margin_pct"
    assert "Not a predicted return" in r["limitations"]


def test_small_sample_does_not_claim_anomaly_detection():
    r = analyze_fundamentals(records(6), "S00")
    assert r["anomaly"]["available"] is False
    assert r["sample_size"] == 6
    with pytest.raises(DeskError, match="At least six"):
        analyze_fundamentals(records(5), "S00")


def test_missing_evidence_visible_and_excess_missing_blocked():
    rows = records()
    rows[0]["long_term_debt_usd"] = None
    result = analyze_fundamentals(rows, "S00")
    assert result["imputed_values"] == 1
    assert result["financial_features"][4]["target_imputed"]
    assert result["target_imputed_fields"] == ["long_term_debt_assets_pct"]
    rows[0]["free_cash_flow_usd"] = None
    with pytest.raises(DeskError, match="coverage"):
        analyze_fundamentals(rows, "S00")


def test_rejects_not_varying_financial_features():
    rows = records(8)
    for r in rows:
        r.update(revenue_growth_pct=5, operating_margin_pct=10, net_margin_pct=5,
                 free_cash_flow_usd=100_000_000, long_term_debt_usd=50_000_000,
                 total_assets_usd=1_000_000_000, revenue_usd=1_000_000_000)
    with pytest.raises(DeskError, match="varying"):
        analyze_fundamentals(rows, "S00")


def test_issuer_deduplication_and_skip_audit():
    rows = records(8)
    rows[3]["cik"] = rows[2]["cik"]
    rows[4]["revenue_usd"] = -1
    result = research_peer_group(FakeSEC(rows), target="S00",
                                 symbols=[r["symbol"] for r in rows])
    assert result["sample_size"] == 6
    assert result["requested_count"] == 8
    assert len(result["excluded_companies"]) == 2
    assert set(x["symbol"] for x in result["excluded_companies"]) == {"S03", "S04"}
    assert result["included_companies"][0]["symbol"] == "S00"
    with pytest.raises(DeskError, match="6–16"):
        research_peer_group(FakeSEC(rows), target="S00", symbols=["S01"])


def test_ml_peer_local_http_no_portfolio_mutation(tmp_path):
    sec = FakeSEC(records(12))
    ledger = PaperLedger(tmp_path / "paper.sqlite3")
    initial = ledger.snapshot()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(
        ledger, DemoDeskMarket(), demo=True, sec_research=sec))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    url = "http://127.0.0.1:" + str(httpd.server_address[1]) + "/api/ml-peers"
    try:
        data = json.dumps({"target": "S00", "symbols": [f"S{i:02d}" for i in range(12)]}).encode()
        req = Request(url, data=data, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=15) as reply:
            result = json.load(reply)
        assert result["sample_size"] == 12
        assert result["target"] == "S00"
        assert ledger.snapshot() == initial
        bad = Request(url, data=json.dumps({"target": "S00", "symbols": ["S01"]}).encode(),
                      headers={"Content-Type": "application/json"})
        with pytest.raises(HTTPError) as exc:
            urlopen(bad)
        assert exc.value.code == 422
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=10)


def test_peer_missing_count_excludes_observed_target():
    complete = analyze_fundamentals(records(12), "S00")
    assert all(field["missing_company_count"] == 0
               for field in complete["financial_features"])

    partially_missing = records(12)
    partially_missing[0]["long_term_debt_usd"] = None
    report = analyze_fundamentals(partially_missing, "S00")
    assert report["financial_features"][-1]["missing_company_count"] == 1
    assert report["financial_features"][-1]["target_imputed"] is True
