"""User-supplied ETF look-through and read-only, fee-aware portfolio rebalancing.

ETF constituent weights are NEVER inferred from price quotes. Holdings must be imported
with an explicit as-of date and source. No planned trades execute automatically.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import math
import re
import sqlite3
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

from quantforge.desk.engine import FEE_RATE, QTY, DeskError, asset_type, cents

STOCK = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")
ETF = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")
WEIGHTS = {"weightpct", "weightpercent", "weightpercentage", "weight"}
SYMBOLS = {"symbol", "ticker", "holdingticker", "securityticker"}


def _col(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower().replace("%", "pct"))


def parse_holdings_csv(raw: str) -> list[tuple[str, Decimal]]:
    """Read a 2-column CSV or a fund-provider CSV with a recognizable header row.

    Weight column is always interpreted as PERCENT, never decimal fractions. Only
    identified ticker rows contribute to *identified* coverage; no unknowns guessed.
    """
    if not isinstance(raw, str) or not 1 <= len(raw) <= 1_000_000:
        raise DeskError("CSV must contain at most 1 MB of text.")
    lines = raw.lstrip("\ufeff").splitlines()
    if len(lines) > 15000:
        raise DeskError("CSV has too many rows.")
    header_index = sym_index = weight_index = None
    for i, line in enumerate(lines[:120]):
        try:
            fields = next(csv.reader([line]))
        except csv.Error:
            continue
        cols = [_col(c) for c in fields]
        syms = [j for j, c in enumerate(cols) if c in SYMBOLS]
        weights = [j for j, c in enumerate(cols) if c in WEIGHTS]
        if syms and weights:
            header_index, sym_index, weight_index = i, syms[0], weights[0]
            break
    if header_index is None:
        raise DeskError("CSV needs Ticker and Weight (%) columns (percent, not fraction).")
    combined: dict[str, Decimal] = {}
    try:
        rows = csv.reader(io.StringIO("\n".join(lines[header_index + 1:])))
        for row in rows:
            if len(row) <= max(sym_index, weight_index):
                continue
            ticker = row[sym_index].strip().upper()
            number = row[weight_index].strip().replace("%", "").replace(",", "")
            if not ticker or ticker in {"-", "--", "N/A", "CASH", "USD"} or not number:
                continue  # omitted entries stay part of unknown ETF exposure
            if not STOCK.fullmatch(ticker):
                continue
            try:
                weight = Decimal(number)
            except ArithmeticError as exc:
                raise DeskError(f"Invalid holding weight for {ticker}.") from exc
            if not weight.is_finite() or weight < 0 or weight > 100:
                raise DeskError(f"Invalid percentage for {ticker}.")
            if weight:
                combined[ticker] = combined.get(ticker, Decimal(0)) + weight
    except csv.Error as exc:
        raise DeskError("Could not read holdings CSV.") from exc
    if not combined:
        raise DeskError("No ticker and percentage rows found.")
    if len(combined) > 5000:
        raise DeskError("Too many distinct holdings.")
    if sum(combined.values()) > Decimal("100.25"):
        raise DeskError("Constituent percentages exceed 100%; check units or duplicate rows.")
    return sorted(combined.items())


class HoldingsStore:
    """Private SQLite cache of holdings pasted/downloaded by the user."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS etf_imports (
                etf TEXT PRIMARY KEY, as_of TEXT NOT NULL, source TEXT NOT NULL,
                imported_utc TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS etf_constituents (
                etf TEXT NOT NULL, ticker TEXT NOT NULL, weight_pct TEXT NOT NULL,
                PRIMARY KEY(etf,ticker), FOREIGN KEY(etf) REFERENCES etf_imports(etf))""")

    def _db(self):
        return sqlite3.connect(self.path, timeout=12)

    def save(self, *, etf: str, raw: str, as_of: str, source: str) -> dict:
        etf = str(etf).strip().upper()
        if not ETF.fullmatch(etf) or asset_type(etf) != "etf":
            raise DeskError("Choose a supported ETF ticker, such as VOO.")
        source = str(source).strip()
        if not 5 <= len(source) <= 240:
            raise DeskError("Describe the holdings source (for example: issuer CSV URL).")
        try:
            date = dt.date.fromisoformat(str(as_of))
        except ValueError as exc:
            raise DeskError("Enter the fund holdings as-of date (YYYY-MM-DD).") from exc
        if date > dt.datetime.now(dt.UTC).date():
            raise DeskError("Holdings as-of date cannot be in the future.")
        constituents = parse_holdings_csv(raw)
        when = dt.datetime.now(dt.UTC).isoformat()
        # Transaction keeps source and holdings consistent if insertion fails.
        with self._db() as conn:
            conn.execute("INSERT OR REPLACE INTO etf_imports VALUES (?,?,?,?)", (etf, date.isoformat(), source, when))
            conn.execute("DELETE FROM etf_constituents WHERE etf=?", (etf,))
            conn.executemany("INSERT INTO etf_constituents VALUES (?,?,?)",
                             [(etf, ticker, str(pct)) for ticker, pct in constituents])
        return {"etf": etf, "as_of": date.isoformat(), "source": source,
                "holdings": len(constituents),
                "identified_pct": round(float(sum(x[1] for x in constituents)), 4)}

    def all(self) -> dict:
        with self._db() as conn:
            info = conn.execute("SELECT etf,as_of,source,imported_utc FROM etf_imports ORDER BY etf").fetchall()
            rows = conn.execute("SELECT etf,ticker,weight_pct FROM etf_constituents ORDER BY etf,ticker").fetchall()
        funds = {etf: {"as_of": date, "source": src, "imported_utc": imported,
                       "holdings": {}} for etf, date, src, imported in info}
        for etf, ticker, weight in rows:
            funds[etf]["holdings"][ticker] = float(weight) / 100
        return funds


def lookthrough(portfolio: dict, imported: dict) -> dict:
    """Known equity exposures; unobserved holdings are explicitly 'unknown'.

    ETF-ETF overlap is the minimum share of each known common constituent;
    not price correlation and not a claim about all constituent identities.
    """
    total = float(portfolio["equity"])
    if not math.isfinite(total) or total <= 0:
        raise DeskError("Portfolio value must be positive.")
    known: dict[str, float] = {}
    funds = []
    unknown_dollars = 0.0
    for p in portfolio["positions"]:
        symbol, value, kind = p["symbol"], float(p["value"]), p["asset_class"]
        if kind == "stock":
            known[symbol] = known.get(symbol, 0) + value
        elif kind == "etf":
            info = imported.get(symbol)
            weights = info["holdings"] if info else {}
            identified = sum(weights.values())
            if identified > 1.0025:
                raise DeskError(f"ETF holdings weights exceed 100% for {symbol}.")
            for ticker, w in weights.items():
                known[ticker] = known.get(ticker, 0) + value * w
            unknown_dollars += value * max(0, 1 - identified)
            funds.append({"etf": symbol, "portfolio_value_usd": round(value, 2),
                          "as_of": info["as_of"] if info else None,
                          "source": info["source"] if info else None,
                          "identified_weight_pct": round(100 * identified, 2),
                          "unidentified_value_usd": round(value * max(0, 1 - identified), 2),
                          "constituents": len(weights)})
        else:
            # Crypto risk stays separate, not misrepresented as equity look-through.
            pass
    etfs = [p for p in portfolio["positions"] if p["asset_class"] == "etf"]
    pairs = []
    for i, a in enumerate(etfs):
        for b in etfs[i + 1:]:
            ha = imported.get(a["symbol"], {}).get("holdings", {})
            hb = imported.get(b["symbol"], {}).get("holdings", {})
            if not ha or not hb:
                continue
            common = sorted(set(ha) & set(hb))
            overlap = sum(min(ha[t], hb[t]) for t in common) * 100
            pairs.append({"a": a["symbol"], "b": b["symbol"],
                          "identified_common_holdings": len(common),
                          "known_min_weight_overlap_pct": round(overlap, 4),
                          "meaning": "Lower bound from imported constituent percentages, not return correlation."})
    exposures = sorted(({"ticker": ticker, "value_usd": round(value, 2),
                         "portfolio_weight_pct": round(100 * value / total, 4)}
                        for ticker, value in known.items()),
                       key=lambda x: (-x["value_usd"], x["ticker"]))
    return {"exposures": exposures, "funds": funds, "etf_pairs": pairs,
            "unknown_etf_value_usd": round(unknown_dollars, 2),
            "unknown_etf_weight_pct": round(100 * unknown_dollars / total, 2),
            "method": "stock direct exposure + ETF value × imported constituent weight",
            "warning": "ETF results are incomplete unless each fund's dated constituent file is comprehensive. No data inferred from quotes. Imports are user-provided, not independently verified."}


def rebalance_plan(portfolio: dict, targets: dict) -> dict:
    """Sell first, then scale buys to available cash; no writes, no trade execution.

    Targets are percentages of current marked equity and include CASH. Buy quantities
    respect an 8-place precision and hypothetical 5 bp buy/sell fees.
    """
    positions = {p["symbol"]: p for p in portfolio["positions"]}
    required = set(positions) | {"CASH"}
    if not isinstance(targets, dict) or set(targets) != required:
        raise DeskError("Targets must include every held symbol and CASH, with no extras.")
    try:
        t = {s: Decimal(str(v)) for s, v in targets.items()}
    except (ValueError, ArithmeticError) as exc:
        raise DeskError("All target allocations must be numbers.") from exc
    if any(not v.is_finite() or not 0 <= v <= 100 for v in t.values()):
        raise DeskError("Target percentages must be between 0 and 100.")
    if abs(sum(t.values()) - 100) > Decimal("0.01"):
        raise DeskError("Targets must total 100% including CASH.")
    equity = Decimal(str(portfolio["equity"]))
    if not equity.is_finite() or equity <= 0:
        raise DeskError("Invalid marked portfolio value.")
    cash = Decimal(str(portfolio["cash"]))
    sells = []
    buys_requested = []
    post = {}
    total_fees = Decimal("0")
    for sym, p in sorted(positions.items()):
        price = Decimal(str(p["price"]))
        qty = Decimal(str(p["quantity"]))
        if not price.is_finite() or price <= 0 or not qty.is_finite() or qty < 0:
            raise DeskError("A holding has invalid units or price.")
        value = qty * price
        target_value = equity * t[sym] / 100
        post[sym] = qty
        if value > target_value:
            sell_qty = min(qty, ((value - target_value) / price).quantize(QTY, rounding=ROUND_DOWN))
            if sell_qty > 0:
                gross = cents(sell_qty * price)
                fee = cents(gross * FEE_RATE)
                cash += gross - fee
                total_fees += fee
                post[sym] -= sell_qty
                sells.append({"symbol": sym, "side": "sell", "quantity": float(sell_qty),
                              "value_usd": float(gross), "fee_usd": float(fee)})
        elif value < target_value:
            buys_requested.append((sym, price, target_value - value))
    # Reserve explicit target cash; scale every buy proportionately if fees make targets infeasible.
    reserve = equity * t["CASH"] / 100
    available = max(cash - reserve, Decimal("0"))
    requested_gross = sum((v for _, _, v in buys_requested), Decimal(0))
    scale = min(Decimal("1"), available / (requested_gross * (1 + FEE_RATE))) if requested_gross > 0 else Decimal(0)
    buys = []
    for sym, price, gap in buys_requested:
        qty = (gap * scale / price).quantize(QTY, rounding=ROUND_DOWN)
        if qty <= 0:
            continue
        gross = cents(qty * price)
        fee = cents(gross * FEE_RATE)
        if gross + fee > cash:
            raise DeskError("Cannot fund hypothetical buys.")
        cash -= gross + fee
        total_fees += fee
        post[sym] += qty
        buys.append({"symbol": sym, "side": "buy", "quantity": float(qty),
                     "value_usd": float(gross), "fee_usd": float(fee)})
    new_equity = cash + sum(post[s] * Decimal(str(positions[s]["price"])) for s in post)
    # Trades rounded to cents; marking uses full precision. A few cents of drift are expected.
    after = {s: float(post[s] * Decimal(str(positions[s]["price"])) / new_equity * 100)
             for s in post}
    after["CASH"] = float(cash / new_equity * 100)
    result = {"trades": sells + buys, "target_pct": {s: float(t[s]) for s in sorted(t)},
              "after_weight_pct": {s: round(v, 4) for s, v in sorted(after.items())},
              "estimated_fees_usd": float(cents(total_fees)),
              "cash_after_usd": float(cents(cash)),
              "equity_after_usd": round(float(new_equity), 2),
              "largest_target_drift_pct_points": round(max(abs(after[s] - float(t[s])) for s in t), 4),
              "quote_timestamps": {s: positions[s]["quote_timestamp"] for s in positions},
              "assumptions": "Read-only approximation: observed last trade; fractional units; 0.05% hypothetical fee each side; no spread, slippage, taxes or execution. Quotes may be stale.",
              "executed": False}
    return result
