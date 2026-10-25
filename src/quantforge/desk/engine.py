"""Private, forward-only paper ledger and transparent portfolio risk algorithms.

No orders leave QuantForge. Market observations are explicitly not executable fills.
Only user-initiated virtual transaction records persist; no quote-history database.
"""

from __future__ import annotations

import datetime as dt
import math
import re
import sqlite3
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import numpy as np

from quantforge.desk.catalog import ETF_CATALOG_SYMBOLS

USD = Decimal("0.01")
QTY = Decimal("0.00000001")
FEE_RATE = Decimal("0.0005")  # hypothetical, one-way 5 basis points
ASSET_CLASSES = {"stock", "etf", "crypto"}
ETF_SYMBOLS = {"SPY", "VOO", "VTI", "QQQ", "IVV", "DIA", "IWM", "EFA", "EEM", "TLT", "IEF", "LQD", "GLD", "BND", "SCHD", "VXUS"}
CRYPTO_SYMBOLS = {"BTC/USD", "ETH/USD", "SOL/USD", "LTC/USD", "AVAX/USD", "DOGE/USD", "LINK/USD"}
TICKER = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")


class DeskError(ValueError):
    """Clear, safe error that may be shown in the local interface."""


def asset_type(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise DeskError("Invalid investment symbol.")
    symbol = symbol.strip().upper()
    if symbol in CRYPTO_SYMBOLS:
        return "crypto"
    if TICKER.fullmatch(symbol):
        return "etf" if symbol in ETF_SYMBOLS or symbol in ETF_CATALOG_SYMBOLS else "stock"
    raise DeskError("Enter a ticker (MSFT or VOO) or supported crypto pair (BTC/USD).")


def money(value: Any, name: str = "amount") -> Decimal:
    try:
        result = Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation) as exc:
        raise DeskError(f"Invalid {name}.") from exc
    if not result.is_finite() or result < 0:
        raise DeskError(f"{name.capitalize()} must be a nonnegative finite number.")
    return result


def cents(value: Decimal) -> Decimal:
    return value.quantize(USD, rounding=ROUND_HALF_UP)


def valid_quote(quote: dict, *, now: dt.datetime | None = None, require_fresh: bool = False) -> dict:
    """Require authenticated quote timestamp, positive price, and known asset.

    Stale observations can be viewed for research but cannot execute a new virtual fill.
    """
    symbol = str(quote.get("symbol", "")).upper().strip()
    kind = asset_type(symbol)
    price = money(quote.get("price"), "quote price")
    if not price:
        raise DeskError("Market provider returned a zero quote.")
    timestamp = quote.get("timestamp")
    try:
        observed = dt.datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        if observed.tzinfo is None:
            raise ValueError("no timezone")
        observed = observed.astimezone(dt.UTC)
    except (TypeError, ValueError) as exc:
        raise DeskError("Quote has no valid timestamp. Paper trading is blocked.") from exc
    now = (now or dt.datetime.now(dt.UTC)).astimezone(dt.UTC)
    age = (now - observed).total_seconds()
    if age < -90:
        raise DeskError("Quote timestamp is in the future.")
    max_age = 300 if kind == "crypto" else 900
    fresh = age <= max_age
    if require_fresh and not fresh:
        raise DeskError("Quote is stale. Review the timestamp and try when fresh data is available.")
    return {**quote, "symbol": symbol, "asset_class": kind, "price": float(price),
            "timestamp": observed.isoformat(), "age_seconds": max(round(age), 0),
            "fresh_for_paper": fresh, "max_age_seconds": max_age}


class PaperLedger:
    """SQLite virtual portfolio; cash is never linked to a broker account."""

    def __init__(self, db: Path, initial_cash: str = "10000") -> None:
        self.path = Path(db)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        start = money(initial_cash, "starting cash")
        if not 100 <= start <= 10_000_000:
            raise DeskError("Starting virtual cash must be between $100 and $10,000,000.")
        self.start = cents(start)
        with self._connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute("""CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY, asset_class TEXT NOT NULL,
                quantity TEXT NOT NULL, average_cost TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT, executed_utc TEXT NOT NULL,
                symbol TEXT NOT NULL, asset_class TEXT NOT NULL, side TEXT NOT NULL,
                quantity TEXT NOT NULL, price TEXT NOT NULL, fee TEXT NOT NULL,
                cash_after TEXT NOT NULL, realized_pnl TEXT NOT NULL,
                quote_timestamp TEXT NOT NULL, venue TEXT NOT NULL)""")
            conn.execute("INSERT OR IGNORE INTO settings VALUES ('cash', ?)", (str(self.start),))
            conn.execute("INSERT OR IGNORE INTO settings VALUES ('initial_cash', ?)", (str(self.start),))
            conn.execute("INSERT OR IGNORE INTO settings VALUES ('realized_pnl', '0')")

    def _connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=12)

    def snapshot(self) -> dict:
        with self._connection() as conn:
            setting = dict(conn.execute("SELECT key,value FROM settings").fetchall())
            positions = [dict(symbol=s, asset_class=k, quantity=float(q), average_cost=float(cost))
                         for s, k, q, cost in conn.execute(
                             "SELECT symbol,asset_class,quantity,average_cost FROM positions ORDER BY symbol")]
            transactions = [dict(id=id_, executed_utc=t, symbol=s, asset_class=k, side=side,
                                 quantity=float(q), price=float(price), fee=float(fee),
                                 cash_after=float(cash), realized_pnl=float(pnl),
                                 quote_timestamp=qt, venue=venue)
                            for id_, t, s, k, side, q, price, fee, cash, pnl, qt, venue
                            in conn.execute("""SELECT id,executed_utc,symbol,asset_class,side,quantity,
                                           price,fee,cash_after,realized_pnl,quote_timestamp,venue
                                           FROM trades ORDER BY id DESC LIMIT 80""")]
        return {"cash": float(setting["cash"]), "initial_cash": float(setting["initial_cash"]),
                "realized_pnl": float(setting["realized_pnl"]),
                "positions": positions, "transactions": transactions,
                "paper_only": True, "live_broker_trading": False}

    def trade(self, *, side: str, symbol: str, amount: str, quote: dict,
              now: dt.datetime | None = None) -> dict:
        """Buy with budget in USD; sell a quantity of shares/coins, for an observed quote.

        Orders are hypothetical instantaneous fills with explicit synthetic fees.
        No shorting, borrowing, tax accounting or margin.
        """
        symbol = symbol.strip().upper()
        kind = asset_type(symbol)
        if side not in {"buy", "sell"}:
            raise DeskError("Choose buy or sell.")
        q = valid_quote(quote, now=now, require_fresh=True)
        if q["symbol"] != symbol:
            raise DeskError("Quote does not match the requested symbol.")
        value = money(amount, "order size")
        if value <= 0:
            raise DeskError("Order size must be positive.")
        price = money(q["price"])
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cash = Decimal(conn.execute("SELECT value FROM settings WHERE key='cash'").fetchone()[0])
            realized = Decimal(conn.execute("SELECT value FROM settings WHERE key='realized_pnl'").fetchone()[0])
            row = conn.execute("SELECT quantity,average_cost FROM positions WHERE symbol=?", (symbol,)).fetchone()
            owned = Decimal(row[0]) if row else Decimal("0")
            old_cost = Decimal(row[1]) if row else Decimal("0")
            if side == "buy":
                if value < Decimal("1"):
                    raise DeskError("Buy budget must be at least $1.")
                if value > cash:
                    raise DeskError("Insufficient virtual cash.")
                # Budget includes fees; never overspend through rounding.
                qty = (value / (price * (Decimal("1") + FEE_RATE))).quantize(QTY, rounding=ROUND_DOWN)
                if qty <= 0:
                    raise DeskError("Budget too small for the quote and quantity precision.")
                gross = cents(qty * price)
                fee = cents(gross * FEE_RATE)
                total = gross + fee
                if total > cash or total > value:
                    raise DeskError("Budget cannot cover simulated price and fees.")
                qty_after = owned + qty
                average_cost = ((owned * old_cost) + total) / qty_after
                cash_after = cash - total
                pnl = Decimal("0")
            else:
                qty = value.quantize(QTY, rounding=ROUND_DOWN)
                if qty <= 0 or qty > owned:
                    raise DeskError("Cannot sell more virtual units than held.")
                gross = cents(qty * price)
                fee = cents(gross * FEE_RATE)
                cash_after = cash + gross - fee
                pnl = gross - fee - qty * old_cost
                realized += pnl
                qty_after = owned - qty
                average_cost = old_cost
            if qty_after == 0:
                conn.execute("DELETE FROM positions WHERE symbol=?", (symbol,))
            else:
                conn.execute("""INSERT INTO positions(symbol,asset_class,quantity,average_cost)
                              VALUES (?,?,?,?) ON CONFLICT(symbol) DO UPDATE SET
                              quantity=excluded.quantity,average_cost=excluded.average_cost""",
                             (symbol, kind, str(qty_after), str(average_cost)))
            conn.execute("UPDATE settings SET value=? WHERE key='cash'", (str(cash_after),))
            conn.execute("UPDATE settings SET value=? WHERE key='realized_pnl'", (str(realized),))
            when = (now or dt.datetime.now(dt.UTC)).astimezone(dt.UTC).isoformat()
            conn.execute("""INSERT INTO trades(executed_utc,symbol,asset_class,side,quantity,
                          price,fee,cash_after,realized_pnl,quote_timestamp,venue)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                         (when, symbol, kind, side, str(qty), str(price), str(fee),
                          str(cash_after), str(pnl), q["timestamp"], str(q.get("venue", "unspecified"))))
        return {"symbol": symbol, "side": side, "quantity": float(qty),
                "price": float(price), "fee": float(fee), "cash_after": float(cash_after),
                "realized_pnl": float(pnl), "virtual_fill": True,
                "execution_model": "observed_last_trade_plus_assumed_fee_not_executable"}


def portfolio_report(snapshot: dict, quotes: dict[str, dict], *, seed: int = 412) -> dict:
    """Point-in-time portfolio metrics, transparent assumed-risk model, no price history."""
    positions = snapshot["positions"]
    cash = float(snapshot["cash"])
    marked = []
    for position in positions:
        sym = position["symbol"]
        if sym not in quotes:
            raise DeskError(f"Cannot value {sym}: no market observation. No price guessed.")
        q = valid_quote(quotes[sym])
        value = position["quantity"] * q["price"]
        marked.append({**position, "price": q["price"], "value": value,
                       "unrealized_pnl": value - position["quantity"] * position["average_cost"],
                       "quote_timestamp": q["timestamp"], "quote_fresh": q["fresh_for_paper"],
                       "source": q.get("source", "unspecified"), "venue": q.get("venue", "unspecified")})
    total = cash + sum(p["value"] for p in marked)
    if total <= 0:
        raise DeskError("Invalid portfolio value")
    for p in marked:
        p["weight"] = p["value"] / total
    invested = sum(p["value"] for p in marked)
    hhi = sum(p["weight"] ** 2 for p in marked)
    largest = max((p["weight"] for p in marked), default=0)
    # Explicit, HYPOTHETICAL scenarios; NOT historical estimates.
    shock_loss = sum(p["value"] * (0.40 if p["asset_class"] == "crypto" else 0.20)
                     for p in marked)
    top_loss = 0.35 * max((p["value"] for p in marked), default=0)
    if marked:
        rng = np.random.default_rng(seed)
        n = 5000
        days = 21
        market_factor = rng.normal(size=n)
        names = []
        # One-factor covariance is PSD by construction. Shared shock plus idiosyncratic shock.
        for p in marked:
            vol = {"stock": 0.35, "etf": 0.20, "crypto": 0.80}[p["asset_class"]]
            shared = {"stock": 0.60, "etf": 0.75, "crypto": 0.20}[p["asset_class"]]
            noise = rng.normal(size=n)
            z = math.sqrt(shared) * market_factor + math.sqrt(1 - shared) * noise
            year_basis = 365 if p["asset_class"] == "crypto" else 252
            terminal = p["value"] * np.exp(-0.5 * (vol ** 2) * days / year_basis
                        + vol * math.sqrt(days / year_basis) * z)
            names.append(terminal)
        terminal_total = cash + np.sum(names, axis=0)
        losses = total - terminal_total
        var95 = max(float(np.quantile(losses, 0.95)), 0.0)
        es95 = max(float(np.mean(losses[losses >= np.quantile(losses, 0.95)])), 0.0)
        chance_loss = float(np.mean(losses > 0))
    else:
        var95 = es95 = chance_loss = 0.0
    categories = {kind: sum(p["value"] for p in marked if p["asset_class"] == kind) / total
                  for kind in ("stock", "etf", "crypto")}
    return {**snapshot, "positions": marked, "equity": total,
            "unrealized_pnl": sum(p["unrealized_pnl"] for p in marked),
            "return_since_start_pct": 100 * (total / snapshot["initial_cash"] - 1),
            "invested_pct": 100 * invested / total, "concentration_hhi": hhi,
            "largest_position_pct": largest * 100, "asset_weights": categories,
            "stress": {"stocks_etfs_down_20_crypto_down_40_usd": shock_loss,
                       "largest_holding_down_35_usd": top_loss},
            "hypothetical_risk": {"horizon_days": 21, "simulations": 5000,
                                  "horizon_convention": "equities_21_sessions_crypto_21_calendar_days",
                                  "var_95_usd": var95, "es_95_usd": es95,
                                  "probability_of_loss": chance_loss,
                                  "model": "one_factor_assumed_volatility_no_empirical_calibration",
                                  "annual_vol_assumptions": {"stock": .35, "etf": .20, "crypto": .80},
                                  "warning": "Assumption-driven scenarios only; not forecasts or measured VaR."},
            "data_warning": "IEX-only stock last trades, venue-specific crypto last trades; not executable quotes."}


def position_capacity(snapshot: dict, portfolio: dict, symbol: str) -> dict:
    """Deterministic maximum BUY budget respecting simple concentration rules.

    Weights are checked against pre-trade equity and include existing positions.
    This is a guardrail, not a buy recommendation.
    """
    symbol = symbol.strip().upper()
    kind = asset_type(symbol)
    equity = float(portfolio["equity"])
    existing = next((p["value"] for p in portfolio["positions"] if p["symbol"] == symbol), 0.)
    category = float(portfolio["asset_weights"][kind]) * equity
    cap_per_asset = 0.25 * equity
    cap_class = (0.15 if kind == "crypto" else 1.0) * equity
    reserve_cash = 0.05 * equity
    cash_spend = max(float(snapshot["cash"]) - reserve_cash, 0.)
    max_budget = max(min(cap_per_asset - existing, cap_class - category, cash_spend), 0.)
    return {"symbol": symbol, "asset_class": kind, "maximum_buy_budget_usd": round(max_budget, 2),
            "guardrail_single_asset_weight": 0.25, "guardrail_crypto_total_weight": 0.15,
            "guardrail_cash_reserve_weight": 0.05,
            "meaning": "Optional user-chosen limits, not personalized financial advice."}
