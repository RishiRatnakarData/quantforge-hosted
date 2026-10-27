"""Owner-only SEC XBRL capital structure facts for price-aware valuation research.

This module NEVER supplies a stock quote, price target, or trade decision.
All SEC HTTP traffic runs through existing throttled, agent-identified server helpers.
"""
from __future__ import annotations

import datetime as dt
import math
import threading
import time
from typing import Any

from cloud import sec_fundamentals

_CACHE: dict[str, tuple[float, dict]] = {}
_LOCK = threading.Lock()
_CACHE_SECONDS = 6 * 3600
_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A"}


def _fact(facts: dict, taxonomy: str, tag: str, unit: str, *,
          as_of: dt.date, end: str | None = None) -> dict | None:
    """Return most-recent disclosed instant fact; never a duration or future filing."""
    rows = (facts.get(taxonomy) or {}).get(tag, {}).get("units", {}).get(unit, [])
    matches: list[tuple[str, str, dict]] = []
    for item in rows:
        if not isinstance(item, dict) or item.get("form") not in _FORMS:
            continue
        if "start" in item or not isinstance(item.get("end"), str):
            continue
        try:
            measured = dt.date.fromisoformat(item["end"])
            filed = dt.date.fromisoformat(item["filed"])
        except (ValueError, TypeError, KeyError):
            continue
        value = item.get("val")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            continue
        if measured > as_of or filed > as_of or filed < measured:
            continue
        if (as_of - measured).days > 550:
            continue
        if end is not None and item["end"] != end:
            continue
        matches.append((item["end"], item["filed"], item))
    if not matches:
        return None
    _, _, best = max(matches, key=lambda row: (row[0], row[1]))
    return {"value": best["val"], "periodEnd": best["end"], "filed": best["filed"],
            "tag": tag, "taxonomy": taxonomy, "unit": unit, "form": best["form"]}


def _first(facts: dict, options: list[tuple[str, str, str]], as_of: dt.date,
           end: str | None = None) -> dict | None:
    eligible = []
    for order, (ns, tag, unit) in enumerate(options):
        row = _fact(facts, ns, tag, unit, as_of=as_of, end=end)
        if row is not None:
            eligible.append((row["periodEnd"], row["filed"], -order, row))
    return max(eligible, key=lambda entry: entry[:3])[3] if eligible else None


def extract(raw: Any, *, symbol: str, cik: int, as_of: dt.date) -> dict:
    """Extract filing-dated disclosures. Absence is explicit null, never zero."""
    try:
        observed_cik = int(raw.get("cik")) if isinstance(raw, dict) else -1
    except (TypeError, ValueError):
        observed_cik = -1
    if observed_cik != cik:
        raise sec_fundamentals.SECFundamentalsError("SEC company identity mismatch.")
    facts = raw.get("facts")
    if not isinstance(facts, dict) or not isinstance(facts.get("us-gaap"), dict):
        raise sec_fundamentals.SECFundamentalsError("No SEC US-GAAP capital facts are available.")

    # DEI cover shares approximate point-in-time capitalization, not diluted EPS denominator.
    shares = _first(facts, [
        ("dei", "EntityCommonStockSharesOutstanding", "shares"),
        ("us-gaap", "CommonStockSharesOutstanding", "shares"),
    ], as_of)
    if shares is not None and shares["value"] <= 0:
        shares = None

    cash = _first(facts, [
        ("us-gaap", "CashAndCashEquivalentsAtCarryingValue", "USD"),
    ], as_of)
    balance_end = cash["periodEnd"] if cash else None
    current = _first(facts, [("us-gaap", "LongTermDebtCurrent", "USD")], as_of,
                     end=balance_end) if balance_end else None
    noncurrent = _first(facts, [("us-gaap", "LongTermDebtNoncurrent", "USD")], as_of,
                        end=balance_end) if balance_end else None
    # Deliberately do NOT combine potentially inclusive 'LongTermDebt' with current debt.
    # Short-term borrowing, debt leases, minority interest, investments remain unmodeled.
    debt = current["value"] + noncurrent["value"] if current and noncurrent else None
    return {
        "symbol": symbol, "cik": cik,
        "source": "SEC EDGAR companyfacts (reported instant facts)",
        "sourceUrl": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
        "asOf": as_of.isoformat(), "shares": shares, "cash": cash,
        "currentLongTermDebt": current, "noncurrentLongTermDebt": noncurrent,
        "reportedDebtComponentsTotal": debt,
        "debtCashSamePeriod": bool(cash and current and noncurrent),
        "disclosure": ("Common shares may not reflect every share class or subsequent issuance. "
                       "Balance sheet cash excludes investments. Debt components exclude certain "
                       "borrowings, leases and other enterprise-value adjustments. "
                       "Do not interpret this as a complete valuation or a share-price target."),
    }


def get_capital(symbol: str) -> dict:
    symbol = symbol.strip().upper()
    if not sec_fundamentals._TICKER_RE.fullmatch(symbol):
        raise sec_fundamentals.SECFundamentalsError("Choose a valid listed stock.")
    now = time.monotonic()
    with _LOCK:
        hit = _CACHE.get(symbol)
        if hit and hit[0] > now:
            return hit[1]
    issuer = sec_fundamentals._ticker_directory().get(symbol)
    if issuer is None:
        raise sec_fundamentals.SECFundamentalsError("SEC issuer unavailable for this symbol.")
    cik, _name = issuer
    raw = sec_fundamentals._fetch_json(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
    )
    result = extract(raw, symbol=symbol, cik=cik, as_of=dt.date.today())
    with _LOCK:
        if len(_CACHE) >= 24:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[symbol] = (time.monotonic() + _CACHE_SECONDS, result)
    return result
