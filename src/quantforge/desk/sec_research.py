"""On-demand SEC annual fundamentals for personal research; separate from the MSFT DCF.

No speculative fair value or missing-data substitution. Facts are extracted from
10-K US-GAAP records with explicit periods and filing dates. Network requests
require a genuine SEC_USER_AGENT; data are cached in memory, not published.
"""

from __future__ import annotations

import datetime as dt
import math
import os
import re
import threading
import time

import requests

from quantforge.desk.engine import DeskError, asset_type
from quantforge.financials.annual import ANNUAL, BALANCE

SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
UA_PATTERN = re.compile(r"\S+@\S+\.\S+")


def _annual_candidates(facts: dict, tags: tuple[str, ...]) -> list[dict]:
    output = []
    for rank, tag in enumerate(tags):
        for row in facts.get(tag, {}).get("units", {}).get("USD", []):
            if row.get("form") not in {"10-K", "10-K/A"}:
                continue
            if not all(k in row for k in ("start", "end", "val", "filed", "accn")):
                continue
            try:
                n_days = (dt.date.fromisoformat(row["end"]) - dt.date.fromisoformat(row["start"])).days
                n = float(row["val"])
            except (TypeError, ValueError, OverflowError):
                continue
            if not 330 <= n_days <= 400 or not math.isfinite(n):
                continue
            if row["filed"] > dt.date.today().isoformat():
                continue
            output.append({"value": n, "end": row["end"], "filed": row["filed"],
                           "accession": row["accn"], "tag": tag, "priority": rank})
    return output


def _instant_candidates(facts: dict, tags: tuple[str, ...], end: str) -> list[dict]:
    output = []
    for rank, tag in enumerate(tags):
        for row in facts.get(tag, {}).get("units", {}).get("USD", []):
            if (row.get("form") not in {"10-K", "10-K/A"} or row.get("end") != end
                    or "start" in row or not all(k in row for k in ("filed", "val", "accn"))):
                continue
            try:
                value = float(row["val"])
            except (TypeError, ValueError, OverflowError):
                continue
            if math.isfinite(value) and row["filed"] <= dt.date.today().isoformat():
                output.append({"value": value, "end": end, "filed": row["filed"],
                               "accession": row["accn"], "tag": tag, "priority": rank})
    return output


def _take(rows: list[dict], end: str) -> dict | None:
    valid = [r for r in rows if r["end"] == end]
    return (sorted(valid, key=lambda r: (r["priority"],
                                    -dt.date.fromisoformat(r["filed"]).toordinal()))[0]
            if valid else None)


def _ratio(n, d):
    if n is None or d is None or d == 0:
        return None
    value = n / d
    return round(value * 100, 2) if math.isfinite(value) else None


def parse_annual_fundamentals(payload: dict, *, ticker: str, cik: int) -> dict:
    """Return the most recent 10-K year and a comparable previous annual revenue.

    No annualization of quarterly financials, no assumed zeros, no stock valuation.
    """
    if not isinstance(payload, dict) or payload.get("cik") not in (cik, str(cik)):
        raise DeskError("SEC company identifier did not match the requested stock.")
    facts = payload.get("facts", {}).get("us-gaap")
    if not isinstance(facts, dict):
        raise DeskError("No comparable US-GAAP financial facts for this stock.")
    revenues = _annual_candidates(facts, ANNUAL["revenue"])
    # A company may use a custom revenue taxonomy. Do not silently assume it.
    if not revenues:
        raise DeskError("No standard annual 10-K revenue found. Review this company's SEC filing directly.")
    ends = sorted({r["end"] for r in revenues}, reverse=True)
    end = ends[0]
    current = _take(revenues, end)
    previous = _take(revenues, ends[1]) if len(ends) > 1 else None
    def annual(field):
        return _take(_annual_candidates(facts, ANNUAL[field]), end)
    def instant(field):
        return _take(_instant_candidates(facts, BALANCE[field], end), end)
    op, net, operating_cash, capex = (annual(n) for n in ("operating_income", "net_income", "operating_cash_flow", "capex"))
    assets, debt = instant("assets"), instant("debt_long_term")
    def get(x):
        return x["value"] if x is not None else None
    fcf = get(operating_cash) - get(capex) if operating_cash is not None and capex is not None else None
    adjacent_year = (previous is not None and 330 <= (dt.date.fromisoformat(end) - dt.date.fromisoformat(previous["end"])).days <= 400)
    revenue_growth = _ratio(get(current) - get(previous), get(previous)) if adjacent_year else None
    return {
        "symbol": ticker,
        "cik": cik,
        "company_name": payload.get("entityName", ticker),
        "fiscal_end": end,
        "revenue_usd": get(current),
        "previous_revenue_usd": get(previous),
        "revenue_growth_pct": revenue_growth,
        "operating_income_usd": get(op),
        "operating_margin_pct": _ratio(get(op), get(current)),
        "net_income_usd": get(net),
        "net_margin_pct": _ratio(get(net), get(current)),
        "operating_cash_flow_usd": get(operating_cash),
        "capex_usd": get(capex),
        "free_cash_flow_usd": fcf,
        "total_assets_usd": get(assets),
        "long_term_debt_usd": get(debt),
        "revenue_source_tag": current["tag"],
        "revenue_filing_date": current["filed"],
        "revenue_accession": current["accession"],
        "source": "SEC EDGAR Company Facts, 10-K US-GAAP",
        "filings_url": f"https://www.sec.gov/edgar/browse/?CIK={cik}",
        "limitations": "Latest available annual 10-K facts only; different metrics may come from different amendments. Missing data is shown as unavailable. Not a stock price valuation or investment recommendation.",
    }


class SECResearch:
    def __init__(self, user_agent: str | None = None, session=None):
        self.user_agent = user_agent if user_agent is not None else os.environ.get("SEC_USER_AGENT", "")
        self.session = session or requests.Session()
        self._cache = {}
        self._lock = threading.RLock()

    def _request(self, url: str, ttl: int):
        with self._lock:
            if url in self._cache and time.monotonic() - self._cache[url][0] < ttl:
                return self._cache[url][1]
            try:
                response = self.session.get(url, headers={"User-Agent": self.user_agent,
                                        "Accept": "application/json"}, timeout=15)
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError) as exc:
                raise DeskError("SEC data unavailable. Try again later or inspect the filing directly.") from exc
            self._cache[url] = (time.monotonic(), payload)
            return payload

    def companyfacts(self, symbol: str) -> tuple[dict, int]:
        """Return issuer-verified SEC payload to internal calculations; never publish raw data."""
        symbol = str(symbol).upper().strip()
        if asset_type(symbol) != "stock":
            raise DeskError("SEC company financials apply to individual U.S. stocks, not ETFs or crypto.")
        if not UA_PATTERN.search(self.user_agent) or "example." in self.user_agent.lower():
            raise DeskError("Set SEC_USER_AGENT with your name and email in PowerShell before starting QuantForge.")
        mapping = self._request(SEC_TICKERS, 24 * 3600)
        if not isinstance(mapping, dict):
            raise DeskError("SEC ticker directory returned an invalid response.")
        by_symbol = {str(r["ticker"]).upper().replace("-", "."): int(r["cik_str"]) for r in mapping.values()
                     if isinstance(r, dict) and "ticker" in r and "cik_str" in r}
        cik = by_symbol.get(symbol)
        if not cik:
            raise DeskError("No matching SEC-listed U.S. company found. Try a different symbol.")
        return self._request(SEC_FACTS.format(cik=cik), 6 * 3600), cik

    def fundamentals(self, symbol: str) -> dict:
        ticker = str(symbol).upper().strip()
        payload, cik = self.companyfacts(ticker)
        return parse_annual_fundamentals(payload, ticker=ticker, cik=cik)
