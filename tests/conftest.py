import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def price_frame():
    dates = pd.bdate_range("2021-01-04", periods=90)
    values = []
    for i, date in enumerate(dates):
        for j, ticker in enumerate(("AAA", "BBB", "CCC", "DDD")):
            values.append(
                {"date": date, "symbol": ticker, "adjusted_close": 100 * (1 + 0.0015 * (j + 1)) ** i}
            )
    return pd.DataFrame(values)


@pytest.fixture
def return_frame():
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2021-01-04", periods=170)
    return pd.DataFrame(rng.normal(0, 0.011, (170, 4)), index=dates, columns=list("ABCD"))
