"""Conservative historical stock input handling; never downloads restricted feeds."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE_URL = "https://www.kaggle.com/datasets/borismarjanovic/price-volume-data-for-all-us-stocks-etfs"
DEFAULT_STOCKS = ("AAPL", "MSFT", "NVDA", "AMZN", "WMT", "JPM", "JNJ", "XOM")
BENCHMARK = "SPY"
LAST_CC0_DATE = pd.Timestamp("2017-11-10")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_bars(frame: pd.DataFrame, *, min_sessions: int = 10) -> pd.DataFrame:
    """Require positive observed adjusted opening/closing prices and common sessions."""
    required = {"date", "symbol", "open", "close"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Missing required OHLC columns: {sorted(required - set(frame.columns))}")
    f = frame[["date", "symbol", "open", "close"]].copy()
    f["date"] = pd.to_datetime(f["date"], errors="raise").dt.normalize()
    if f["date"].isna().any():
        raise ValueError("Missing date")
    f["symbol"] = f["symbol"].astype(str).str.upper().str.strip()
    if f["symbol"].str.fullmatch(r"[A-Z0-9.\-]{1,12}").ne(True).any():
        raise ValueError("Invalid ticker format")
    for column in ("open", "close"):
        f[column] = pd.to_numeric(f[column], errors="raise")
        if not np.isfinite(f[column]).all() or (f[column] <= 0).any():
            raise ValueError(f"{column} must be strictly positive finite values")
    if f.duplicated(["date", "symbol"]).any():
        raise ValueError("Duplicate symbol/date observations")
    if BENCHMARK not in set(f["symbol"]):
        raise ValueError("An SPY benchmark series is required")
    assets = sorted(set(f["symbol"]) - {BENCHMARK})
    if not assets:
        raise ValueError("At least one non-benchmark stock is required")
    common_dates = set(f.loc[f["symbol"] == BENCHMARK, "date"])
    for ticker in assets:
        common_dates &= set(f.loc[f["symbol"] == ticker, "date"])
    if len(common_dates) < min_sessions:
        raise ValueError("Not enough common observed trading dates")
    f = f[f["date"].isin(common_dates)].sort_values(["date", "symbol"]).reset_index(drop=True)
    return f


def synthetic_bars(*, sessions: int = 600, seed: int = 42042) -> pd.DataFrame:
    """Entirely artificial data for offline tests and a clearly labeled game preview."""
    if sessions < 30:
        raise ValueError("At least 30 artificial sessions required")
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2014-01-02", periods=sessions)
    market = rng.normal(0.00025, 0.010, sessions)
    shocks = {ticker: rng.normal(0, 0.009 + i * 0.001, sessions)
              for i, ticker in enumerate((*DEFAULT_STOCKS, BENCHMARK))}
    rows = []
    for i, ticker in enumerate((*DEFAULT_STOCKS, BENCHMARK)):
        level = 45.0 + i * 17
        for idx, date in enumerate(dates):
            overnight = float(0.4 * market[idx] + 0.2 * shocks[ticker][idx])
            intraday = float(0.6 * market[idx] + 0.8 * shocks[ticker][idx])
            daily_open = level * np.exp(overnight)
            daily_close = daily_open * np.exp(intraday)
            rows.append({"date": date, "symbol": ticker, "open": daily_open, "close": daily_close})
            level = daily_close
    return validate_bars(pd.DataFrame(rows), min_sessions=sessions)


def kaggle_archive_bars(
    archive: Path, *, stocks: tuple[str, ...] = DEFAULT_STOCKS,
    start: str = "2014-01-02", end: str = "2017-11-10",
) -> pd.DataFrame:
    """Load only named CC0 dataset CSV/TXT entries from a locally obtained ZIP."""
    archive = Path(archive)
    if pd.Timestamp(end) > LAST_CC0_DATE:
        raise ValueError("The CC0 archive ends 2017-11-10; newer dates are unavailable")
    names = tuple(dict.fromkeys((*stocks, BENCHMARK)))
    data = []
    with zipfile.ZipFile(archive) as bundle:
        candidates = {name.casefold().replace("\\", "/"): name for name in bundle.namelist()}
        for ticker in names:
            folder = "etfs" if ticker == BENCHMARK else "stocks"
            suffix = f"{folder}/{ticker.lower()}.us.txt"
            matching = [original for name, original in candidates.items() if name.endswith(suffix)]
            if len(matching) != 1:
                raise ValueError(f"Could not find unique {suffix} in Kaggle archive")
            with bundle.open(matching[0]) as source:
                part = pd.read_csv(source)
            part.columns = part.columns.str.lower()
            if not {"date", "open", "close"}.issubset(part.columns):
                raise ValueError(f"Unexpected data schema for {ticker}")
            part = part.loc[:, ["date", "open", "close"]]
            part["symbol"] = ticker
            data.append(part)
    out = pd.concat(data, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"])
    out = out[out["date"].between(pd.Timestamp(start), pd.Timestamp(end))]
    return validate_bars(out, min_sessions=100)


def create_replay_data(
    *, output: Path, frame: pd.DataFrame, origin: str,
    source_path: Path | None = None, approved_redistribution: bool = False,
) -> dict:
    """Write validated daily observations and a strict publication metadata contract."""
    if origin not in {"synthetic", "cc0_kaggle_2017", "user_supplied_local", "alpaca_personal_private"}:
        raise ValueError("Unsupported stock-data origin")
    if origin == "cc0_kaggle_2017" and not approved_redistribution:
        raise ValueError("Explicitly acknowledge CC0 dataset provenance before publishing")
    if origin == "cc0_kaggle_2017" and frame["date"].max() > LAST_CC0_DATE:
        raise ValueError("CC0 market dataset cannot contain post-2017-11-10 observations")
    f = validate_bars(frame)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    csv = output / "stock_bars.csv"
    f.to_csv(csv, index=False, date_format="%Y-%m-%d", float_format="%.12g")
    manifest = {
        "schema": "quantforge.stock_bars.v1",
        "release": "4.3.0",
        "data_origin": origin,
        "data_sha256": _sha(csv),
        "source_sha256": _sha(source_path) if source_path else None,
        "source_url": SOURCE_URL if origin == "cc0_kaggle_2017" else None,
        "source_license": "CC0 (Kaggle dataset label)" if origin == "cc0_kaggle_2017" else None,
        "publication_allowed": origin == "synthetic" or (origin == "cc0_kaggle_2017" and approved_redistribution),
        "min_date": str(f["date"].min().date()),
        "max_date": str(f["date"].max().date()),
        "sessions": int(f["date"].nunique()),
        "tickers": sorted(f["symbol"].unique().tolist()),
        "price_definition": "retrospectively adjusted close/open if CC0 Kaggle; provider-defined otherwise",
        "limitations": [
            "Historical adjusted price levels are not point-in-time executable quotes",
            "Alpaca split-adjusted price-only bars omit cash dividends (not total returns)",
            "Fixed retrospective stock list has survivorship and selection bias",
            "No taxes, slippage, borrowing, fractional-share limits or market impact",
        ],
    }
    (output / "stock_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
