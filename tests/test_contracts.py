import numpy as np
import pandas as pd
import pytest

from quantforge.data.contracts import (
    DataContractError,
    make_complete_panel,
    simple_returns,
    validate_basis,
    validate_prices,
)


def test_prices_normalization(price_frame):
    out = validate_prices(price_frame.sample(frac=1, random_state=3))
    assert list(out.columns) == ["date", "symbol", "adjusted_close"]
    assert out.iloc[0]["symbol"] == "AAA"
    assert len(out) == len(price_frame)


@pytest.mark.parametrize("column", ["date", "symbol", "adjusted_close"])
def test_missing_required_field_rejected(price_frame, column):
    with pytest.raises(DataContractError):
        validate_prices(price_frame.drop(columns=column))


def test_duplicate_rejected(price_frame):
    with pytest.raises(DataContractError, match="Duplicate"):
        validate_prices(pd.concat([price_frame, price_frame.iloc[[0]]]))


@pytest.mark.parametrize("bad", [-1, 0, float("nan"), float("inf")])
def test_invalid_price_rejected(price_frame, bad):
    price_frame.loc[0, "adjusted_close"] = bad
    with pytest.raises(DataContractError):
        validate_prices(price_frame)


def test_missing_cross_section_fails(price_frame):
    with pytest.raises(DataContractError, match="missing"):
        make_complete_panel(price_frame.iloc[1:])


def test_correct_simple_returns(price_frame):
    panel = make_complete_panel(price_frame)
    result = simple_returns(panel)
    assert len(result) == 89
    assert np.isclose(result["BBB"].iloc[0], 0.003)
    assert np.isclose(result["CCC"].iloc[-1], 0.0045)


def test_no_backfill_or_future_data(price_frame):
    frame = price_frame.copy()
    frame.loc[10, "adjusted_close"] = np.nan
    with pytest.raises(DataContractError):
        make_complete_panel(frame)


def test_price_basis_validation():
    assert validate_basis("dividend_adjusted_close") == "dividend_adjusted_close"
    with pytest.raises(DataContractError):
        validate_basis("mystery")
