"""Daily self-financing buy/sell replay; decision at close executes next observed open."""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from .marketdata import BENCHMARK, validate_bars


def _weights(weights: Mapping[str, float], tickers: set[str]) -> dict[str, float]:
    result = {str(k).upper(): float(v) for k, v in weights.items()}
    if not result or not set(result).issubset(tickers):
        raise ValueError("Allocation must reference valid non-benchmark stocks")
    if any(not math.isfinite(v) or v < 0 or v > 1 for v in result.values()):
        raise ValueError("Weights must be finite and between 0 and 1")
    if sum(result.values()) > 1 + 1e-9:
        raise ValueError("Long-only weights cannot exceed 100%")
    return result


def _rebalance(cash: float, shares: dict[str, float], opens: dict[str, float],
               target: dict[str, float], fee_rate: float) -> tuple[float, dict[str, float], list[dict]]:
    nav = cash + sum(shares[t] * opens[t] for t in shares)
    available = nav
    for _ in range(60):
        fee = fee_rate * sum(abs(available * target.get(t, 0) - shares.get(t, 0) * opens[t])
                             for t in opens if t != BENCHMARK)
        revised = nav - fee
        if abs(revised - available) < 1e-9:
            break
        available = revised
    if available < 0:
        raise ValueError("Fee exceeds available value")
    trades = []
    updated = shares.copy()
    for ticker in updated:
        before = shares[ticker]
        after = (available * target.get(ticker, 0)) / opens[ticker]
        difference = after - before
        if abs(difference) > 1e-10:
            trades.append({"symbol": ticker, "side": "BUY" if difference > 0 else "SELL",
                           "shares": float(abs(difference)), "execution_price": float(opens[ticker]),
                           "fee": float(fee_rate * abs(difference) * opens[ticker])})
        updated[ticker] = after
    cash_after = nav - available * sum(target.values()) - sum(t["fee"] for t in trades)
    # available = nav - fees, leaving only the uninvested percentage as cash.
    if cash_after < -1e-7:
        raise ValueError("Rebalance would create a negative cash balance")
    return max(0.0, cash_after), updated, trades


def replay_portfolio(
    bars: pd.DataFrame, *, decisions: list[dict], budget: float = 10_000,
    fee_bps: float = 5.0,
) -> dict:
    """Date-close orders execute at NEXT observed session opening price, never that close.

    All simulations are illustrative historical-adjusted-price backtests rather than
    executable trading simulations; the decisions must be authored without future data.
    """
    if not math.isfinite(budget) or budget <= 0 or not math.isfinite(fee_bps) or fee_bps < 0:
        raise ValueError("Budget must be positive and transaction costs nonnegative")
    frame = validate_bars(bars)
    sessions = list(sorted(frame["date"].unique()))
    tickers = set(frame["symbol"]) - {BENCHMARK}
    dates = set(sessions)
    ordered = []
    for item in decisions:
        day = pd.Timestamp(item["date"]).normalize()
        if day not in dates:
            raise ValueError("Decision day must be an observed trading session")
        ordered.append((day, _weights(item["weights"], tickers)))
    if len({x[0] for x in ordered}) != len(ordered):
        raise ValueError("Two decisions at the same timestamp")
    if ordered != sorted(ordered, key=lambda x: x[0]):
        raise ValueError("Decisions must be chronological")
    if not ordered or ordered[0][0] != sessions[0]:
        raise ValueError("First decision must be on the first observed session")
    if ordered[-1][0] == sessions[-1]:
        raise ValueError("At least one next-session fill is needed")
    fee_rate = fee_bps / 10000
    matrix = frame.set_index(["date", "symbol"])
    holdings = {s: 0.0 for s in tickers}
    cash = float(budget)
    benchmark_shares = 0.0
    benchmark_cash = float(budget)
    events = []
    equity = []
    upcoming = {date: weights for date, weights in ordered}
    pending = None
    for idx, date in enumerate(sessions):
        block = matrix.loc[date]
        opens = block["open"].to_dict()
        closes = block["close"].to_dict()
        if pending is not None:
            cash, holdings, trades = _rebalance(cash, holdings, opens, pending, fee_rate)
            for trade in trades:
                events.append({"date": str(date.date()), "decision_date": str(sessions[idx - 1].date()), **trade})
            pending = None
        if idx == 1:
            benchmark_shares = (budget / (1 + fee_rate)) / opens[BENCHMARK]
            benchmark_cash = budget - benchmark_shares * opens[BENCHMARK] * (1 + fee_rate)
        nav = cash + sum(holdings[t] * closes[t] for t in holdings)
        bench = benchmark_cash + benchmark_shares * closes[BENCHMARK]
        equity.append({"date": str(date.date()), "portfolio": float(nav),
                       "benchmark": float(bench), "cash": float(cash)})
        if date in upcoming:
            pending = upcoming[date]
    curve = pd.DataFrame(equity)
    returns = curve["portfolio"].pct_change().dropna()
    peak = curve["portfolio"].cummax()
    drawdown = curve["portfolio"] / peak - 1
    vol = float(returns.std(ddof=1) * np.sqrt(252)) if len(returns) > 1 else 0.0
    return {
        "curve": equity,
        "trades": events,
        "stats": {
            "ending_value": float(curve["portfolio"].iloc[-1]),
            "benchmark_value": float(curve["benchmark"].iloc[-1]),
            "total_return": float(curve["portfolio"].iloc[-1] / budget - 1),
            "benchmark_return": float(curve["benchmark"].iloc[-1] / budget - 1),
            "annualized_volatility": vol,
            "max_drawdown": float(drawdown.min()),
            "trade_count": len(events),
        },
    }
