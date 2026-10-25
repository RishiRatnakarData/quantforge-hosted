"""Loopback-only investment companion. No public server or brokerage trading."""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from quantforge.desk.catalog import directory_data
from quantforge.desk.companion import CompanionStore, decision_brief
from quantforge.desk.company_models import calculate_company_dcf, compare_fundamentals
from quantforge.desk.comparison import compare_ideas
from quantforge.desk.engine import (
    DeskError,
    PaperLedger,
    money,
    portfolio_report,
    position_capacity,
)
from quantforge.desk.fundamental_ml import research_peer_group
from quantforge.desk.market import AlpacaDeskMarket, DemoDeskMarket
from quantforge.desk.portfolio_intelligence import HoldingsStore, lookthrough, rebalance_plan
from quantforge.desk.quant_portfolio import (
    HistoricalPriceStore,
    analyze_prices,
    fetch_alpaca_daily_prices,
)
from quantforge.desk.sec_research import SECResearch
from quantforge.desk.valuation import load_sec_valuation
from quantforge.live.provider import MarketDataError

HTML = Path(__file__).with_name("investment_desk.html")


def make_handler(ledger: PaperLedger, market, *, demo: bool = False, sec_dir: Path | None = None, sec_research=None):
    """Inject dependencies; no market-data calls until a user requests them."""

    companion = CompanionStore(ledger.path)
    holdings = HoldingsStore(ledger.path)
    quant_prices = HistoricalPriceStore(ledger.path)
    sec_research = sec_research if sec_research is not None else SECResearch()

    class InvestmentHandler(BaseHTTPRequestHandler):
        server_version = "QuantForgeCompanion/5.4"

        def _json(self, value: dict, status: int = 200):
            encoded = json.dumps(value, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _allowed(self) -> bool:
            # DNS rebinding mitigation; no cross-origin mutable requests.
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin", "")
            hostname = host.rsplit(":", 1)[0]
            if hostname not in ("127.0.0.1", "localhost") or not re.fullmatch(r"(?:127\.0\.0\.1|localhost):\d+", host):
                return False
            if origin and origin != "http://" + host:
                return False
            return True

        def _snapshot(self) -> dict:
            state = ledger.snapshot()
            quotes = {p["symbol"]: market.quote(p["symbol"]) for p in state["positions"]}
            return portfolio_report(state, quotes)

        def do_GET(self):  # noqa: N802
            if not self._allowed():
                return self._json({"error": "Access is restricted to the local investment desk."}, 403)
            target = urlsplit(self.path)
            params = parse_qs(target.query)
            try:
                if target.path == "/":
                    content = HTML.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    return self.wfile.write(content)
                if target.path == "/api/health":
                    return self._json({"status": "ok", "mode": "synthetic_demo" if demo else "alpaca_private",
                                       "paper_only": True, "public_display_licensed": False,
                                       "data": "fictional" if demo else "venue-specific personal-market-data"})
                if target.path == "/api/directory":
                    return self._json(directory_data())
                if target.path == "/api/profile":
                    return self._json(companion.profile())
                if target.path == "/api/watchlist":
                    return self._json({"watchlist": companion.watchlist()})
                if target.path == "/api/notes":
                    return self._json({"notes": companion.notes()})
                if target.path == "/api/compare":
                    symbols = params.get("symbols", [""])[0].split(",")
                    budget = params.get("budget", ["500"])[0]
                    return self._json(compare_ideas(symbols, budget, market, self._snapshot(), companion.profile()))
                if target.path == "/api/fundamentals":
                    return self._json(sec_research.fundamentals(params.get("symbol", [""])[0]))
                if target.path == "/api/company-dcf":
                    sym = params.get("symbol", [""])[0].upper().strip()
                    options = {k: vals[0] for k, vals in params.items()
                               if k in {"growth_pct", "margin_pct", "wacc_pct",
                                        "terminal_growth_pct", "tax_pct", "nwc_pct", "da_pct"}}
                    raw, cik = sec_research.companyfacts(sym)
                    return self._json(calculate_company_dcf(raw, ticker=sym, cik=cik,
                                                            assumptions=options))
                if target.path == "/api/company-comparables":
                    return self._json(compare_fundamentals(sec_research,
                        params.get("symbols", [""])[0].split(",")))
                if target.path == "/api/decision":
                    symbol = params.get("symbol", [""])[0]
                    budget = params.get("budget", ["0"])[0]
                    quote = market.quote(symbol)
                    return self._json(decision_brief(quote, self._snapshot(),
                                                     companion.profile(), budget))
                if target.path == "/api/quote":
                    return self._json(market.quote(params.get("symbol", [""])[0]))
                if target.path == "/api/valuation":
                    return self._json(load_sec_valuation(sec_dir))
                if target.path == "/api/portfolio":
                    return self._json(self._snapshot())
                if target.path == "/api/holdings-lookthrough":
                    return self._json(lookthrough(self._snapshot(), holdings.all()))
                if target.path == "/api/holdings-imports":
                    data = holdings.all()
                    return self._json({"funds": [dict(etf=s, as_of=d["as_of"], source=d["source"],
                        constituents=len(d["holdings"]), identified_pct=round(100 * sum(d["holdings"].values()), 2))
                        for s, d in data.items()]})
                if target.path == "/api/quant-history":
                    return self._json(quant_prices.status())
                if target.path == "/api/capacity":
                    symbol = params.get("symbol", [""])[0]
                    return self._json(position_capacity(ledger.snapshot(), self._snapshot(), symbol))
                return self._json({"error": "Not found"}, 404)
            except (DeskError, MarketDataError) as exc:
                return self._json({"error": str(exc)}, 422)

        def do_POST(self):  # noqa: N802
            if not self._allowed():
                return self._json({"error": "Cross-origin request blocked."}, 403)
            target = urlsplit(self.path)
            if target.path not in {"/api/paper-order", "/api/profile", "/api/watchlist", "/api/notes",
                                   "/api/holdings-imports", "/api/rebalance-plan",
                                   "/api/quant-import", "/api/quant-analysis",
                                   "/api/quant-alpaca-import", "/api/ml-peers"}:
                return self._json({"error": "Not found"}, 404)
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self._json({"error": "Expected application/json"}, 415)
            try:
                size = int(self.headers.get("Content-Length", "0"))
                max_bytes = (5_500_000 if target.path == "/api/quant-import" else
                             1_500_000 if target.path == "/api/holdings-imports" else 4096)
                if not 1 <= size <= max_bytes:
                    return self._json({"error": "Invalid request payload size."}, 413)
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise DeskError("Expected an object.")
                if target.path == "/api/ml-peers":
                    return self._json(research_peer_group(sec_research,
                        target=data.get("target", ""), symbols=data.get("symbols", [])))
                if target.path == "/api/quant-alpaca-import":
                    if demo:
                        raise DeskError("Alpaca historical fetch is unavailable in fictional demo mode.")
                    if not hasattr(market, "client"):
                        raise DeskError("Authenticated Alpaca market access is required.")
                    return self._json(fetch_alpaca_daily_prices(quant_prices, market.client,
                        symbols=data.get("symbols", []), feed=data.get("feed", "iex"),
                        lookback_days=400))
                if target.path == "/api/quant-import":
                    return self._json(quant_prices.save(raw=data.get("csv", ""),
                                                        source=data.get("source", "")))
                if target.path == "/api/quant-analysis":
                    return self._json(analyze_prices(quant_prices, self._snapshot(),
                        symbols=data.get("symbols"), budget=data.get("budget", 10000),
                        max_weight_pct=data.get("max_weight_pct", 60),
                        crypto_cap_pct=data.get("crypto_cap_pct", 15)))
                if target.path == "/api/holdings-imports":
                    return self._json(holdings.save(etf=data.get("etf", ""),
                        as_of=data.get("as_of", ""), source=data.get("source", ""),
                        raw=data.get("csv", "")))
                if target.path == "/api/rebalance-plan":
                    return self._json(rebalance_plan(self._snapshot(), data.get("targets")))
                if target.path == "/api/profile":
                    return self._json(companion.save_profile(data))
                if target.path == "/api/watchlist":
                    return self._json({"watchlist": companion.watch(
                        data.get("symbol", ""), remove=data.get("remove") is True)})
                if target.path == "/api/notes":
                    symbol = str(data.get("symbol", ""))
                    quote = market.quote(symbol)
                    return self._json({"saved": companion.add_note(
                        symbol=symbol, note=data.get("note", ""),
                        budget=data.get("budget"), quote=quote)})
                symbol = str(data.get("symbol", ""))
                quote = market.quote(symbol)
                expected = money(data.get("expected_price"), "previewed price")
                latest = money(quote.get("price"), "current price")
                if expected <= 0 or abs(latest / expected - 1) > 0.01:
                    raise DeskError("Market observation changed over 1% since preview. Refresh before recording.")
                result = ledger.trade(side=data.get("side"), symbol=symbol,
                                      amount=data.get("amount"), quote=quote)
                return self._json({"trade": result, "portfolio": self._snapshot()})
            except (DeskError, MarketDataError, ValueError, TypeError) as exc:
                # JSON parser errors are rendered as a generic request failure.
                if isinstance(exc, json.JSONDecodeError):
                    return self._json({"error": "Invalid JSON request."}, 422)
                return self._json({"error": str(exc)}, 422)

        def log_message(self, fmt, *args):
            # Omit request params (potentially sensitive portfolio details).
            pass

    return InvestmentHandler


def run_investment_desk(*, db: Path, demo: bool = False, port: int = 8765,
                        starting_cash: str = "10000", sec_dir: Path | None = None) -> None:
    if not 1024 <= port <= 65535:
        raise DeskError("Choose a local port between 1024 and 65535.")
    market = DemoDeskMarket() if demo else AlpacaDeskMarket()
    ledger = PaperLedger(db, initial_cash=starting_cash)
    handler = make_handler(ledger, market, demo=demo, sec_dir=sec_dir)
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"QuantForge Personal Investment Desk: http://127.0.0.1:{port}/")
        print("Mode: " + ("FICTIONAL DEMO; NO REAL PRICES" if demo else "PRIVATE ALPACA MARKET DATA"))
        print("PAPER ORDERS ONLY. Nothing is sent to a brokerage account.")
        print(f"Private SQLite portfolio: {db}")
        print("Press Ctrl+C to stop. Keep database and API keys private.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nInvestment Desk stopped.")
