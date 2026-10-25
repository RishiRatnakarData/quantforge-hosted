"""Private price-evidence portfolio research: statistics, scenarios, constraints.

Never requests or manufactures historical quotes. Observations must be user-imported
with source attribution, and all outputs are read-only hypothetical calculations.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import math
import sqlite3
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

from quantforge.desk.engine import DeskError, asset_type

MAX_ROWS = 60000
MIN_RETURN_DATES = 90
MAX_ASSETS = 12


def parse_price_csv(text: str) -> dict:
    if not isinstance(text, str) or not text.strip() or len(text.encode("utf-8")) > 5_000_000:
        raise DeskError("Choose a price CSV under 5 MB.")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or [v.strip().lower() for v in reader.fieldnames] != [
        "date", "symbol", "close"
    ]:
        raise DeskError("CSV columns must be date,symbol,close (in this order).")
    rows = []
    seen = set()
    symbols = set()
    today = dt.datetime.now(dt.UTC).date()
    for row in reader:
        if len(rows) >= MAX_ROWS:
            raise DeskError("Too many price observations (maximum 60,000).")
        if None in row or any(v is None for v in row.values()):
            raise DeskError("Invalid CSV row.")
        try:
            day = dt.date.fromisoformat(row["date"].strip())
            symbol = row["symbol"].strip().upper()
            asset_type(symbol)
            price = float(row["close"].strip())
        except (ValueError, TypeError, KeyError) as exc:
            raise DeskError("Invalid date, symbol, or close price.") from exc
        if day > today or day < dt.date(1990, 1, 1):
            raise DeskError("Price dates must be between 1990 and today.")
        if not math.isfinite(price) or price <= 0 or price > 10**9:
            raise DeskError("Closing prices must be finite and positive.")
        if (day.isoformat(), symbol) in seen:
            raise DeskError("Duplicate date/symbol observation.")
        seen.add((day.isoformat(), symbol))
        symbols.add(symbol)
        if len(symbols) > MAX_ASSETS:
            raise DeskError("Limit imports to 12 assets at a time.")
        rows.append((day.isoformat(), symbol, price))
    if len(symbols) < 2:
        raise DeskError("Import at least two investments for correlation analysis.")
    if len(rows) < (MIN_RETURN_DATES + 1) * 2:
        raise DeskError("Provide at least 91 dated prices per investment.")
    per_symbol = {symbol: 0 for symbol in symbols}
    for _, symbol, _ in rows:
        per_symbol[symbol] += 1
    if min(per_symbol.values()) < MIN_RETURN_DATES + 1:
        raise DeskError("Each investment needs at least 91 dated closing prices.")
    return {"rows": rows, "symbols": sorted(symbols), "first_date": min(x[0] for x in rows),
            "last_date": max(x[0] for x in rows)}


class HistoricalPriceStore:
    """A single replaceable evidence set stored beside the private paper ledger."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS quant_prices (
                date TEXT NOT NULL, symbol TEXT NOT NULL, close REAL NOT NULL,
                PRIMARY KEY(date, symbol))""")
            conn.execute("""CREATE TABLE IF NOT EXISTS quant_evidence (
                name TEXT PRIMARY KEY, value TEXT NOT NULL)""")

    def save(self, *, raw: str, source: str) -> dict:
        if not isinstance(source, str) or not 5 <= len(source.strip()) <= 300:
            raise DeskError("Enter the data source (provider, URL, or report name).")
        data = parse_price_csv(raw)
        with sqlite3.connect(self.path, timeout=12) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM quant_prices")
            conn.executemany("INSERT INTO quant_prices(date,symbol,close) VALUES (?,?,?)", data["rows"])
            meta = {"source": source.strip(), "first_date": data["first_date"],
                    "last_date": data["last_date"], "imported_utc": dt.datetime.now(dt.UTC).isoformat()}
            conn.execute("DELETE FROM quant_evidence")
            conn.executemany("INSERT INTO quant_evidence VALUES (?,?)", list(meta.items()))
        return {**meta, "symbols": data["symbols"], "observations": len(data["rows"])}

    def status(self) -> dict:
        with sqlite3.connect(self.path) as conn:
            evidence = dict(conn.execute("SELECT name,value FROM quant_evidence").fetchall())
            counts = conn.execute("SELECT symbol,COUNT(*) FROM quant_prices GROUP BY symbol ORDER BY symbol").fetchall()
        return {"available": bool(counts), "source": evidence.get("source"),
                "first_date": evidence.get("first_date"), "last_date": evidence.get("last_date"),
                "imported_utc": evidence.get("imported_utc"),
                "symbols": [{"symbol": s, "prices": n} for s, n in counts],
                "warning": "Imported historical prices are private, unverified and not from Alpaca current quotes."}

    def rows(self, symbols: list[str]) -> list[tuple[str, str, float]]:
        if not symbols:
            return []
        marks = ",".join("?" for _ in symbols)
        with sqlite3.connect(self.path) as conn:
            return conn.execute(f"SELECT date,symbol,close FROM quant_prices WHERE symbol IN ({marks}) "
                                "ORDER BY date,symbol", symbols).fetchall()


def _input_number(value, name: str, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DeskError(f"Invalid {name}.") from exc
    if not math.isfinite(number) or not low <= number <= high:
        raise DeskError(f"{name} must be between {low} and {high}.")
    return number


def _return_matrix(data: list[tuple], symbols: list[str]) -> tuple[np.ndarray, list[str]]:
    """Compute each asset's log returns before inner-joining dates; no interpolation."""
    prices: dict[str, list[tuple[str, float]]] = {s: [] for s in symbols}
    for day, symbol, close in data:
        prices[symbol].append((day, close))
    dated_returns: dict[str, dict[str, float]] = {}
    for s in symbols:
        records = sorted(prices[s])
        if len(records) < MIN_RETURN_DATES + 1:
            raise DeskError(f"{s}: at least 91 dated prices required.")
        dated_returns[s] = {}
        for i in range(1, len(records)):
            day, close = records[i]
            dated_returns[s][day] = math.log(close / records[i - 1][1])
    days = sorted(set.intersection(*(set(dated_returns[s]) for s in symbols)))
    if len(days) < MIN_RETURN_DATES:
        raise DeskError("Fewer than 90 overlapping daily return dates; import a longer shared period.")
    matrix = np.array([[dated_returns[s][d] for s in symbols] for d in days], dtype=float)
    if not np.isfinite(matrix).all():
        raise DeskError("Non-finite historical return data.")
    if np.any(np.abs(matrix) > math.log(3)):
        raise DeskError("Extreme price changes detected (possible stock splits); use adjusted close prices.")
    return matrix, days


def _risk_stats(weights: np.ndarray, covariance: np.ndarray, *, annual_days: int) -> dict:
    variance = max(float(weights @ covariance @ weights), 0)
    sigma = math.sqrt(variance)
    annual_vol = sigma * math.sqrt(annual_days) * 100
    marginal = covariance @ weights
    contributions = weights * marginal / sigma if sigma > 1e-12 else np.zeros_like(weights)
    return {"annual_volatility_pct": round(annual_vol, 3),
            "risk_contributions_pct_points": [round(float(x) * math.sqrt(annual_days) * 100, 3)
                                               for x in contributions],
            "sum_risk_contributions_pct_points": round(float(sum(contributions)) * math.sqrt(annual_days) * 100, 3)}


def _simulate(weights: np.ndarray, covariance: np.ndarray, returns: np.ndarray,
              budget: float, *, seed: int = 124, n: int = 3000, days: int = 21) -> dict:
    """Same seeded daily draws for both allocations; constant-mix rebalancing assumed."""
    rng = np.random.default_rng(seed)
    k = len(weights)
    # Set historical mean to zero deliberately; this is a risk model, not an alpha forecast.
    draws = rng.multivariate_normal(np.zeros(k), covariance, size=(n, days),
                                    check_valid="raise", method="svd")
    daily_simple = np.expm1(draws - np.diag(covariance) / 2)
    gross_daily = 1 + np.tensordot(daily_simple, weights, axes=([2], [0]))
    final = budget * np.prod(gross_daily, axis=1)
    losses = budget - final
    cutoff = float(np.quantile(losses, .95))
    var = max(0.0, cutoff)
    es = max(0.0, float(np.mean(losses[losses >= cutoff])))
    return {"var_95_usd": round(var, 2), "es_95_usd": round(es, 2),
            "probability_of_loss_pct": round(float(np.mean(losses > 0) * 100), 2),
            "outcome_5_pct_usd": round(float(np.quantile(final, .05)), 2),
            "outcome_median_usd": round(float(np.median(final)), 2),
            "outcome_95_pct_usd": round(float(np.quantile(final, .95)), 2)}


def _optimize(covariance: np.ndarray, base: np.ndarray, symbols: list[str],
              max_weight: float, crypto_cap: float, turnover_penalty: float):
    n = len(base)
    crypto_idx = [i for i, s in enumerate(symbols) if asset_type(s) == "crypto"]
    max_effective = [min(max_weight, crypto_cap) if i in crypto_idx else max_weight for i in range(n)]
    if sum(max_effective) < 1 - 1e-8:
        raise DeskError("Allocation limits are infeasible for these investments. Increase limits or add assets.")
    constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]
    if crypto_idx:
        constraints.append({"type": "ineq", "fun": lambda x: crypto_cap - np.sum(x[crypto_idx])})
    def objective(x):
        return float(x @ covariance @ x + turnover_penalty * np.sum((x - base) ** 2))
    solution = minimize(objective, np.full(n, 1 / n), method="SLSQP",
                        bounds=[(0, max_weight) for _ in range(n)], constraints=constraints,
                        options={"maxiter": 600, "ftol": 1e-12})
    weights = np.asarray(solution.x, dtype=float)
    if (not solution.success or not np.all(np.isfinite(weights)) or
            abs(weights.sum() - 1) > .00001 or np.any(weights < -1e-7) or
            np.any(weights > max_weight + 1e-6) or
            sum(weights[i] for i in crypto_idx) > crypto_cap + 1e-6):
        raise DeskError("Optimizer did not find a valid feasible allocation. Try different limits.")
    return weights


def analyze_prices(store: HistoricalPriceStore, portfolio: dict, *, symbols: list[str] | None = None,
                   budget=10000, max_weight_pct=60, crypto_cap_pct=15,
                   turnover_penalty=0.003) -> dict:
    evidence = store.status()
    available = {r["symbol"] for r in evidence["symbols"]}
    if not available:
        raise DeskError("Import a dated historical closing-price CSV first.")
    if symbols is None:
        owned = [p["symbol"] for p in portfolio.get("positions", []) if p["symbol"] in available]
        symbols = owned if len(owned) >= 2 else sorted(available)[:min(len(available), 5)]
    if not isinstance(symbols, list) or not 2 <= len(symbols) <= 8:
        raise DeskError("Select 2–8 different investments.")
    symbols = [str(s).strip().upper() for s in symbols]
    if len(set(symbols)) != len(symbols) or any(s not in available for s in symbols):
        raise DeskError("Select unique investments from the imported price evidence.")
    budget = _input_number(budget, "Hypothetical budget", 100, 10_000_000)
    max_weight = _input_number(max_weight_pct, "Maximum single allocation %", 1, 100) / 100
    crypto_cap = _input_number(crypto_cap_pct, "Maximum total crypto allocation %", 0, 100) / 100
    turnover_penalty = _input_number(turnover_penalty, "Turnover penalty", 0, 0.1)
    matrix, days = _return_matrix(store.rows(symbols), symbols)
    if np.any(matrix.std(axis=0) < 1e-10):
        raise DeskError("At least one asset has zero observed return variation.")
    covariance = LedoitWolf().fit(matrix).covariance_
    sd = np.sqrt(np.diag(covariance))
    corr = covariance / np.outer(sd, sd)
    positions = {p["symbol"]: float(p["value"]) for p in portfolio.get("positions", [])}
    amounts = np.array([positions.get(s, 0) for s in symbols], dtype=float)
    if amounts.sum() > 0 and all(s in available for s in positions) and len(set(positions) - set(symbols)) == 0:
        current = amounts / amounts.sum()
        base_description = "Existing virtual holdings; cash excluded; weights normalized within invested assets."
    else:
        current = np.full(len(symbols), 1 / len(symbols))
        base_description = "Equal-weight illustrative basket; not your actual holdings."
    optimized = _optimize(covariance, current, symbols, max_weight, crypto_cap, turnover_penalty)
    annual_days = 365 if all(asset_type(s) == "crypto" for s in symbols) else 252
    base_risk = _risk_stats(current, covariance, annual_days=annual_days)
    opt_risk = _risk_stats(optimized, covariance, annual_days=annual_days)
    models = []
    for name, w, risk in (("baseline", current, base_risk), ("constrained", optimized, opt_risk)):
        exposure = {s: round(float(w[i] * 100), 4) for i, s in enumerate(symbols)}
        risk["allocation_pct"] = exposure
        risk["risk_contribution_by_symbol_pct_points"] = {
            s: risk["risk_contributions_pct_points"][i] for i, s in enumerate(symbols)
        }
        scenario_loss = sum(float(w[i]) * (0.40 if asset_type(s) == "crypto" else 0.20)
                            for i, s in enumerate(symbols)) * budget
        models.append({"kind": name, "risk": risk, "monte_carlo": _simulate(w, covariance, matrix, budget),
                       "stress_loss_usd": round(scenario_loss, 2)})
    age = (dt.datetime.now(dt.UTC).date() - dt.date.fromisoformat(evidence["last_date"])).days
    return {"symbols": symbols, "source": evidence["source"], "price_period": [
                evidence["first_date"], evidence["last_date"]],
            "matched_return_dates": len(days), "aligned_period": [days[0], days[-1]],
            "annualization_days": annual_days, "last_observation_age_days": age,
            "history_is_old": age > 30, "hypothetical_budget_usd": budget,
            "baseline_definition": base_description,
            "estimator": "Ledoit-Wolf shrinkage daily log-return covariance; no expected-return forecast",
            "historical_annual_vol_pct": {s: round(float(sd[i] * math.sqrt(annual_days) * 100), 3)
                                          for i, s in enumerate(symbols)},
            "correlations": [[round(float(v), 3) for v in row] for row in corr],
            "allocations": models,
            "estimated_one_way_turnover_pct": round(float(0.5 * sum(abs(current - optimized))) * 100, 3),
            "rules": {"max_per_asset_pct": 100 * max_weight, "crypto_total_max_pct": 100 * crypto_cap,
                      "turnover_penalty": turnover_penalty},
            "assumptions": "Historical source is user-provided and unverified. Overlapping return dates only; "
                           "correlations are not stable forecasts. Optimizer minimizes historical shrinkage "
                           "variance with a squared turnover penalty under nonnegative caps, ignoring "
                           "fees/taxes/lot sizes. Simulation: 3,000 paths, 21 daily steps, zero assumed "
                           "expected arithmetic return, multivariate normal daily log shocks, daily "
                           "constant-mix rebalancing, unchanged covariance. No historical or live price "
                           "forecasts. Equity/crypto calendar synchronization and annualization are approximate. "
                           "All modeled allocations use the hypothetical budget, exclude cash, and do not trade."}


def fetch_alpaca_daily_prices(store: HistoricalPriceStore, client, *, symbols: list[str],
                             feed: str = "iex", lookback_days: int = 400,
                             now: dt.date | None = None) -> dict:
    """Explicit personal historical download; no redistribution or unattended polling.

    SIP bars older than 15 min may be accessible with Alpaca Basic; do not silently
    replace a denied SIP request with the narrower IEX-only feed.
    """
    if not isinstance(symbols, list) or not 2 <= len(symbols) <= 6:
        raise DeskError("Select 2–6 stock or ETF symbols to fetch.")
    checked = []
    for symbol in symbols:
        symbol = str(symbol).strip().upper()
        if asset_type(symbol) == "crypto":
            raise DeskError("Alpaca historical download currently supports U.S. stocks and ETFs; use CSV for crypto.")
        checked.append(symbol)
    if len(set(checked)) != len(checked):
        raise DeskError("Choose different investments.")
    if feed not in {"sip", "iex"}:
        raise DeskError("Use the SIP or IEX historical feed.")
    if not isinstance(lookback_days, int) or not 120 <= lookback_days <= 1095:
        raise DeskError("Choose 120–1,095 calendar days of history.")
    today = now or dt.datetime.now(dt.UTC).date()
    end = today - dt.timedelta(days=1)
    start = end - dt.timedelta(days=lookback_days)
    lines = ["date,symbol,close"]
    for symbol in checked:
        token = None
        seen_tokens = set()
        seen_dates = set()
        for _ in range(15):
            params = {"timeframe": "1Day", "start": start.isoformat(),
                      "end": end.isoformat(), "adjustment": "all", "feed": feed,
                      "limit": 10000, "sort": "asc"}
            if token:
                params["page_token"] = token
            # Live authenticated call using the same user-only client as quotes.
            result = client._get(f"/v2/stocks/{symbol}/bars", params, ttl=600)
            bars = result.get("bars")
            if not isinstance(bars, list):
                raise DeskError("Alpaca returned no valid historical bars. Check access to the selected feed.")
            for bar in bars:
                if not isinstance(bar, dict):
                    raise DeskError("Invalid Alpaca historical bar.")
                day = str(bar.get("t", ""))[:10]
                try:
                    dt.date.fromisoformat(day)
                except ValueError as exc:
                    raise DeskError("Alpaca returned an invalid historical timestamp.") from exc
                if day in seen_dates:
                    raise DeskError("Alpaca returned a duplicate historical date.")
                seen_dates.add(day)
                price = _input_number(bar.get("c"), "Alpaca adjusted close", 0.000001, 10**9)
                lines.append(f"{day},{symbol},{price:.10g}")
            token = result.get("next_page_token")
            if not token:
                break
            if not isinstance(token, str) or token in seen_tokens:
                raise DeskError("Invalid or repeated Alpaca pagination token.")
            seen_tokens.add(token)
        else:
            raise DeskError("Alpaca historical download exceeded pagination limit.")
        if len(seen_dates) < MIN_RETURN_DATES + 1:
            raise DeskError(f"{symbol}: fewer than 91 daily historical bars on {feed.upper()}.")
    source = (f"Alpaca personal historical {feed.upper()} daily stock bars; adjustment=all; "
              f"requested {start.isoformat()} to {end.isoformat()}; not for public redistribution")
    result = store.save(raw="\n".join(lines) + "\n", source=source)
    return {**result, "feed": feed, "adjustment": "all", "personal_only": True}
