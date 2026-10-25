import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from quantforge.data.contracts import make_complete_panel, simple_returns


def test_sql_return_calculation_matches_pandas(price_frame):
    frame = price_frame.copy()
    frame["date"] = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
    with sqlite3.connect(":memory:") as connection:
        frame.to_sql("market_prices", connection, index=False)
        sql = (Path(__file__).resolve().parents[1] / "sql" / "returns.sql").read_text()
        actual = pd.read_sql_query(sql, connection).dropna(subset=["simple_return"])
    expected = simple_returns(make_complete_panel(price_frame))
    expected_long = expected.rename_axis("date").stack().rename("simple_return").reset_index()
    actual["date"] = pd.to_datetime(actual["date"])
    actual = actual.sort_values(["date", "symbol"]).reset_index(drop=True)
    expected_long = expected_long.sort_values(["date", "symbol"]).reset_index(drop=True)
    assert np.allclose(actual["simple_return"], expected_long["simple_return"], atol=1e-12)
