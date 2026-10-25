"""A beginner-first, locally stored decision workflow around existing quant engines.

This layer does not recommend securities or require historical price data.
Every dollar-loss scenario is a deterministic what-if, not a probability forecast.
"""

from __future__ import annotations

import datetime as dt
import math
import sqlite3
from pathlib import Path

from quantforge.desk.engine import DeskError, asset_type, money, valid_quote

GOALS = {"build_wealth": "Build long-term wealth", "explore": "Explore investing", "preserve": "Protect near-term money"}
HORIZONS = {"under_one": "Within one year", "one_to_five": "One to five years", "five_plus": "More than five years"}
COMFORTS = {"cautious": "Small losses feel difficult", "balanced": "Some ups and downs are acceptable", "adventurous": "I can tolerate large swings"}
DEFAULTS = {"goal": "explore", "horizon": "five_plus", "comfort": "balanced", "cash_buffer_pct": 20}


class CompanionStore:
    """The app's private workspace; uses the existing private ledger database."""

    def __init__(self, db: Path) -> None:
        self.path = Path(db)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS companion_profile (id INTEGER PRIMARY KEY CHECK (id=1), goal TEXT NOT NULL, horizon TEXT NOT NULL, comfort TEXT NOT NULL, cash_buffer_pct INTEGER NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS companion_watchlist (symbol TEXT PRIMARY KEY, added_at TEXT NOT NULL)")
            conn.execute("""CREATE TABLE IF NOT EXISTS companion_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                symbol TEXT NOT NULL, note TEXT NOT NULL, budget REAL,
                quote_timestamp TEXT NOT NULL, quote_source TEXT NOT NULL)""")

    def _db(self):
        return sqlite3.connect(self.path, timeout=12)

    def profile(self) -> dict:
        with self._db() as conn:
            row = conn.execute("SELECT goal,horizon,comfort,cash_buffer_pct FROM companion_profile WHERE id=1").fetchone()
        return dict(zip(DEFAULTS, row, strict=True)) if row else dict(DEFAULTS)

    def save_profile(self, data: dict) -> dict:
        if not isinstance(data, dict):
            raise DeskError("Expected an investment-preferences object.")
        p = {**self.profile(), **data}
        if p["goal"] not in GOALS or p["horizon"] not in HORIZONS or p["comfort"] not in COMFORTS:
            raise DeskError("Choose a valid goal, time horizon, and comfort level.")
        buffer = p["cash_buffer_pct"]
        if type(buffer) is not int or not 0 <= buffer <= 90:
            raise DeskError("Cash reserve must be a whole percentage from 0 to 90.")
        with self._db() as conn:
            conn.execute("""INSERT INTO companion_profile VALUES (1,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET goal=excluded.goal,horizon=excluded.horizon,
                comfort=excluded.comfort,cash_buffer_pct=excluded.cash_buffer_pct""",
                (p["goal"], p["horizon"], p["comfort"], buffer))
        return self.profile()

    def watchlist(self) -> list[dict]:
        with self._db() as conn:
            rows = conn.execute("SELECT symbol,added_at FROM companion_watchlist ORDER BY added_at DESC, symbol").fetchall()
        return [{"symbol": s, "added_at": d} for s, d in rows]

    def watch(self, symbol: str, *, remove: bool = False) -> list[dict]:
        symbol = str(symbol).upper().strip()
        asset_type(symbol)
        with self._db() as conn:
            if remove:
                conn.execute("DELETE FROM companion_watchlist WHERE symbol=?", (symbol,))
            else:
                conn.execute("INSERT OR IGNORE INTO companion_watchlist VALUES (?,?)", (symbol, dt.datetime.now(dt.UTC).isoformat()))
        return self.watchlist()

    def add_note(self, *, symbol: str, note: str, budget: float | None, quote: dict) -> dict:
        symbol = str(symbol).upper().strip()
        asset_type(symbol)
        if not isinstance(note, str) or not 5 <= len(note.strip()) <= 1200:
            raise DeskError("Write a short reason (5–1,200 characters) before saving.")
        if budget is not None:
            if not isinstance(budget, (int, float)) or not math.isfinite(budget) or budget < 0:
                raise DeskError("Invalid virtual budget in research note.")
        q = valid_quote(quote)
        if q["symbol"] != symbol:
            raise DeskError("Note and observed investment must match.")
        now = dt.datetime.now(dt.UTC).isoformat()
        with self._db() as conn:
            conn.execute("""INSERT INTO companion_notes(created_at,symbol,note,budget,quote_timestamp,quote_source)
                         VALUES (?,?,?,?,?,?)""", (now, symbol, note.strip(), budget,
                                                      q["timestamp"], str(q.get("source", "unspecified"))))
        return {"symbol": symbol, "created_at": now, "note": note.strip()}

    def notes(self) -> list[dict]:
        with self._db() as conn:
            rows = conn.execute("""SELECT id,created_at,symbol,note,budget,quote_timestamp,quote_source
                                   FROM companion_notes ORDER BY id DESC LIMIT 100""").fetchall()
        return [dict(zip(("id", "created_at", "symbol", "note", "budget", "quote_timestamp", "quote_source"), r, strict=True)) for r in rows]


def decision_brief(quote: dict, portfolio: dict, profile: dict, budget: float) -> dict:
    """Compute *exploratory* buy-impact math, not a suitability score or advice.

    Key invariant: cost is paid from existing cash, not conjured into new equity.
    Outcomes compare the current marked portfolio to a hypothetical after-buy state.
    """
    q = valid_quote(quote)
    b = money(budget, "virtual budget")
    cash = float(portfolio["cash"])
    equity = float(portfolio["equity"])
    if b < 1 or float(b) > cash:
        raise DeskError("Choose a virtual amount of at least $1, no more than your available cash.")
    symbol = q["symbol"]
    kind = q["asset_class"]
    amount = float(b)
    # PaperLedger's 5 bp fee is *inside* the budget; this is an approximate preview.
    fee_estimate = round(amount / 1.0005 * .0005, 2)
    invested = amount - fee_estimate
    post_equity = equity - fee_estimate
    previous_value = sum(p["value"] for p in portfolio["positions"] if p["symbol"] == symbol)
    new_value = previous_value + invested
    pre_weight = previous_value / equity * 100
    post_weight = new_value / post_equity * 100
    risk_limits = {"cautious": (12., 5.), "balanced": (20., 10.), "adventurous": (30., 15.)}
    single_limit, crypto_limit = risk_limits[profile["comfort"]]
    previous_crypto = sum(p["value"] for p in portfolio["positions"] if p["asset_class"] == "crypto")
    post_crypto = (previous_crypto + (invested if kind == "crypto" else 0)) / post_equity * 100
    post_cash = cash - amount
    reserve = float(profile["cash_buffer_pct"])
    flags = []
    if post_weight > single_limit + 1e-9:
        flags.append(f"This holding would make up {post_weight:.1f}% of your portfolio, above your chosen {single_limit:.0f}% exploration guideline.")
    if post_crypto > crypto_limit + 1e-9:
        flags.append(f"Crypto would make up {post_crypto:.1f}% of your portfolio, above the {crypto_limit:.0f}% guideline for your selected comfort level.")
    if post_cash / post_equity * 100 < reserve - 1e-9:
        flags.append("Your virtual cash would fall below the reserve percentage you selected.")
    if profile["horizon"] == "under_one" and kind in {"stock", "crypto"}:
        flags.append("Individual stocks and crypto can fall sharply. A short time horizon may leave little time to recover.")
    if kind == "crypto":
        category_explainer = "A crypto asset is not a company. It does not have earnings or a normal stock DCF valuation."
        stress = .40
    elif kind == "etf":
        category_explainer = "An exchange-traded fund holds a basket of assets. Check its actual holdings and fees separately; a price quote cannot tell us these."
        stress = .20
    else:
        category_explainer = "A stock represents ownership in one company. Its financial health and valuation deserve separate research."
        stress = .30
    loss = new_value * stress
    result = {
        "symbol": symbol, "asset_class": kind, "price": q["price"],
        "quote_timestamp": q["timestamp"], "source": q.get("source", "unspecified"),
        "coverage": q.get("coverage", ""), "fresh_for_paper": q["fresh_for_paper"],
        "budget_usd": amount, "approx_fee_usd": fee_estimate,
        "shares_preview": invested / q["price"], "post_cash_usd": post_cash,
        "position_weight_before_pct": pre_weight, "position_weight_after_pct": post_weight,
        "post_crypto_weight_pct": post_crypto, "reserve_percent": reserve,
        "stress_assumption_pct": stress * 100, "scenario_loss_usd": loss, "scenario_loss_added_usd": invested * stress,
        "scenario_loss_of_portfolio_pct": loss / post_equity * 100,
        "position_guideline_pct": single_limit, "crypto_guideline_pct": crypto_limit,
        "flags": flags, "asset_explainer": category_explainer,
        "guidance": "Educational what-if only. No expected-return forecast, buy recommendation or guaranteed loss ceiling.",
        "execution": "Approximate observed-last-trade paper preview; 0.05% hypothetical fee included. No real order.",
    }
    return result
