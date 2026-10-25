"""Mocked eight-ETF handoff integration; never interpreted as actual market data."""

import json

import numpy as np
import pandas as pd

from quantforge.cli import main


def test_v02_handoff_cli_from_mocked_source(tmp_path):
    rng = np.random.default_rng(401)
    symbols = ["SPY", "IWM", "EFA", "EEM", "IEF", "TLT", "GLD", "LQD"]
    days = pd.bdate_range("2010-01-04", periods=550)
    moves = rng.normal(.00015, .008, (550, 8))
    values = 100 * np.exp(np.cumsum(moves, axis=0))
    prices = (pd.DataFrame(values, index=days, columns=symbols)
              .rename_axis("date").stack().rename("adjusted_close")
              .rename_axis(index=["date", "symbol"]).reset_index())
    path = tmp_path / "prices.csv"
    prices.to_csv(path, index=False)
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(json.dumps({
        "provider": "Tiingo EOD", "price_basis": "dividend_adjusted_close",
        "calendar_audit": {"pass": True}, "symbol_universe": symbols,
        "snapshots": [{"symbol": s} for s in symbols],
    }))
    out = tmp_path / "research"
    # V4 prevents further generation of persistent data-derived outputs under
    # Tiingo Starter licensing; legacy V1 scientific engine is tested via
    # deterministic in-memory simulation elsewhere in the suite.
    assert main(["v1-risk", "--input-prices", str(path), "--source-manifest",
                 str(manifest_path), "--output", str(out)]) == 2
    assert not out.exists()
