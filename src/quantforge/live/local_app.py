"""Private read-only investment desk; binds only to the local machine.

Historical bars live in a TemporaryDirectory deleted when the server exits.
The browser loads a private HTML replay, and optional quotes are fetched only
on deliberate clicks via a localhost endpoint. Credentials never reach JS.
"""

from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlsplit

import pandas as pd

from quantforge.live.provider import AlpacaClient, MarketDataError, valid_symbol
from quantforge.simulator.marketdata import create_replay_data, validate_bars
from quantforge.simulator.website import build_stock_site


def prepare_private_site(*, client: AlpacaClient, root: Path, symbols: list[str],
                         start: str, end: str, sec_dir: Path | None = None) -> dict:
    """Build transient local research site, never a public or persistent artifact."""
    requested = list(dict.fromkeys([*(valid_symbol(symbol) for symbol in symbols), "SPY"]))
    if not 2 <= len(requested) <= 16:
        raise MarketDataError("Choose between one and 15 stocks; SPY is added automatically.")
    batches = [client.history(symbol, start, end) for symbol in requested]
    frame = validate_bars(pd.DataFrame([record for rows in batches for record in rows]),
                          min_sessions=30)
    data_dir = root / "private-market-data"
    create_replay_data(output=data_dir, frame=frame, origin="alpaca_personal_private")
    result = build_stock_site(stock_dir=data_dir, output=root / "website",
                              sec_dir=sec_dir, local_only=True)
    return {"site": root / "website", "observations": result["observations"],
            "tickers": requested, "until": str(frame["date"].max().date())}


def serve_personal_desk(*, symbols: list[str], start: str, end: str,
                        sec_dir: Path | None = None, port: int = 8765) -> None:
    if not 1024 <= port <= 65535:
        raise MarketDataError("Port must be between 1024 and 65535.")
    client = AlpacaClient.from_environment()
    with TemporaryDirectory(prefix="quantforge_personal_") as directory:
        result = prepare_private_site(client=client, root=Path(directory),
                                      symbols=symbols, start=start, end=end,
                                      sec_dir=sec_dir)
        site_dir = result["site"]

        class LocalHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(site_dir), **kwargs)

            def do_GET(self):  # noqa: N802
                request = urlsplit(self.path)
                if request.path != "/api/quote":
                    return super().do_GET()
                query = parse_qs(request.query)
                symbol = query.get("symbol", [""])[0]
                try:
                    answer = client.quote(symbol)
                    status = 200
                except MarketDataError as exc:
                    status, answer = 422, {"error": str(exc)}
                payload = json.dumps(answer, allow_nan=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        with ThreadingHTTPServer(("127.0.0.1", port), LocalHandler) as server:
            print(f"PRIVATE QuantForge Investment Desk: http://127.0.0.1:{port}/")
            print(f"Observed sessions: {result['observations']} | symbols: {', '.join(result['tickers'])}")
            print(f"Latest historical bar: {result['until']}")
            print("Alpaca IEX trades: click 'Get Latest IEX Trade' in Stock Explorer.")
            print("Private market data stays in temporary local files until Ctrl+C.")
            print("Do not publish browser exports, screenshots containing prices, or temporary site files.")
            try:
                server.serve_forever(poll_interval=0.4)
            except KeyboardInterrupt:
                print("\nPrivate session ended; temporary market files will be deleted.")
