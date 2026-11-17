"""Average-cost virtual bookkeeping; no I/O, tax method or historical reconstruction."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from quantforge.desk.engine import QTY, DeskError, cents, money


def initial_book() -> dict:
    return {"version": 1, "positions": {}, "realized_pnl": 0.0, "realized_complete": True}


def accounting_effect(state: dict, terms: dict) -> dict:
    """Return a new book. Unknown legacy basis stays unknown until a position is closed.

    Entry fees enter total position basis; exit fees reduce sale proceeds. Rounding
    allocates cents on partial sales and the complete remaining basis on final sale.
    """
    raw = state.get("basis_accounting")
    valid_book = isinstance(raw, dict) and raw.get("version") == 1
    positions = dict(raw.get("positions", {})) if valid_book and isinstance(raw.get("positions"), dict) else {}
    complete = bool(valid_book and raw.get("realized_complete") is True)
    try:
        realized = Decimal(str(raw.get("realized_pnl", 0))) if valid_book else Decimal(0)
        if not realized.is_finite():
            raise InvalidOperation
    except (InvalidOperation, ValueError, TypeError):
        realized = Decimal(0)
        complete = False
    symbol = terms["symbol"]
    owned = money(state.get("holdings", {}).get(symbol, 0), "owned units")
    units = money(terms["units"], "transaction units")
    remaining = money(terms["held_after"], "remaining units")
    old = positions.get(symbol)
    basis = None
    if isinstance(old, dict):
        try:
            if money(old.get("units"), "basis units").quantize(QTY) == owned.quantize(QTY):
                basis = money(old.get("total_basis"), "position basis")
        except DeskError:
            pass
    if owned and basis is None:
        complete = False
    allocated = trade_pnl = None
    if terms["side"] == "buy":
        cost = money(terms["gross"]) + money(terms["fee"])
        next_basis = cost if not owned else basis + cost if basis is not None else None
    else:
        if units <= 0 or units > owned:
            raise DeskError("Invalid units for virtual cost-basis accounting.")
        allocated = (basis if remaining == 0 else cents(basis * units / owned)) if basis is not None else None
        next_basis = basis - allocated if allocated is not None else None
        if allocated is not None:
            trade_pnl = cents(money(terms["gross"]) - money(terms["fee"]) - allocated)
            realized += trade_pnl
        else:
            complete = False
    if remaining > 0:
        positions[symbol] = {"units": float(remaining),
                             "total_basis": float(cents(next_basis)) if next_basis is not None else None}
    else:
        positions.pop(symbol, None)
    return {"accounting": {"version": 1, "positions": positions,
                           "realized_pnl": float(cents(realized)), "realized_complete": complete},
            "cost_basis_allocated": float(allocated) if allocated is not None else None,
            "realized_pnl": float(trade_pnl) if trade_pnl is not None else None}
