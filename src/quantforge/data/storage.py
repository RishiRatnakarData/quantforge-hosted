"""SQLite/CSV baseline plus DuckDB/Parquet exports when those modules exist."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd


def sha256_file(path: str | Path) -> str:
    """Hash bytes without loading an entire provider-owned dataset into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: str | Path, content: dict) -> None:
    """Write an auditable UTF-8 JSON record; never quietly stringify errors."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(content, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def write_analytics(output: Path, prices: pd.DataFrame, returns: pd.DataFrame) -> dict:
    """Persist normalized price/return tables; record actual storage capabilities."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    price_table = prices[["date", "symbol", "adjusted_close"]].copy()
    return_table = returns[["date", "symbol", "simple_return"]].copy()
    for frame in (price_table, return_table):
        frame["date"] = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
    price_table.to_csv(output / "prices.csv", index=False, float_format="%.12g")
    return_table.to_csv(output / "returns.csv", index=False, float_format="%.12g")
    with sqlite3.connect(output / "quantforge.sqlite") as connection:
        price_table.to_sql("market_prices", connection, if_exists="replace", index=False)
        return_table.to_sql("market_returns", connection, if_exists="replace", index=False)
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_market_prices_date_symbol ON market_prices(date, symbol)")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_market_returns_date_symbol ON market_returns(date, symbol)")
    # DuckDB and PyArrow are part of the declared runtime dependencies. The
    # SQLite path permits a minimal offline test environment without them;
    # a full Windows install must verify DuckDB and Parquet were actually written.
    try:
        import duckdb
    except ImportError:
        return {"storage_engine": "sqlite_csv_only", "parquet_files": []}
    with duckdb.connect(str(output / "quantforge.duckdb")) as connection:
        connection.register("incoming_prices", price_table)
        connection.register("incoming_returns", return_table)
        connection.execute("CREATE OR REPLACE TABLE market_prices AS SELECT * FROM incoming_prices")
        connection.execute("CREATE OR REPLACE TABLE market_returns AS SELECT * FROM incoming_returns")
        # COPY destinations are SQL literals, not dynamically interpolated identifiers.
        for table, filename in (("market_prices", "prices.parquet"), ("market_returns", "returns.parquet")):
            safe_path = str((output / filename).resolve()).replace("'", "''")
            connection.execute(f"COPY {table} TO '{safe_path}' (FORMAT PARQUET)")
    return {"storage_engine": "duckdb_parquet_and_sqlite", "parquet_files": ["prices.parquet", "returns.parquet"]}
