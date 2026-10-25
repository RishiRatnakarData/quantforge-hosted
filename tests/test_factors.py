import zipfile

import numpy as np
import pandas as pd
import pytest

from quantforge.data.contracts import DataContractError
from quantforge.factors.french import (
    descriptive_factor_regression,
    read_french_five_factor_daily_archive,
)


def test_parse_daily_factor_zip_and_scale(tmp_path):
    csv = "Created by Kenneth French\n,Mkt-RF,SMB,HML,RMW,CMA,RF\n20200102,0.50,-0.10,0.02,0.01,0.03,0.01\n20200103,-0.20,0.05,0.01,-0.03,0.04,0.01\n\nAnnual Factors:\n1990,2,1,1,1,1,1"
    file = tmp_path / "factors.zip"
    with zipfile.ZipFile(file, "w") as archive:
        archive.writestr("F-F_Research_Data_5_Factors_2x3_daily.csv", csv)
    frame = read_french_five_factor_daily_archive(file)
    assert len(frame) == 2
    assert frame.iloc[0]["market_excess"] == pytest.approx(0.005)
    assert frame.iloc[0]["RF"] == pytest.approx(0.0001)


def test_parser_rejects_missing_value_sentinel(tmp_path):
    csv = ",Mkt-RF,SMB,HML,RMW,CMA,RF\n20200102,-99.99,1,1,1,1,1"
    path = tmp_path / "missing.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("daily.csv", csv)
    with pytest.raises(DataContractError):
        read_french_five_factor_daily_archive(path)


def test_factor_regression_recovers_known_betas():
    rng = np.random.default_rng(123)
    n = 180
    dates = pd.bdate_range("2020-01-01", periods=n)
    matrix = rng.normal(0, 0.015, size=(n, 5))
    coefs = np.array([1.2, 0.3, -0.2, 0.1, 0.5])
    rf = np.full(n, 0.0001)
    target = 0.0002 + matrix @ coefs + rf
    factors = pd.DataFrame(matrix, columns=["market_excess", "SMB", "HML", "RMW", "CMA"])
    factors["date"] = dates
    factors["RF"] = rf
    result = descriptive_factor_regression(pd.Series(target, index=dates), factors)
    assert result["observations"] == n
    assert result["alpha_daily"] == pytest.approx(0.0002, abs=1e-10)
    assert result["beta_market"] == pytest.approx(1.2, abs=1e-10)
    assert result["beta_CMA"] == pytest.approx(0.5, abs=1e-10)
    assert result["r_squared"] == pytest.approx(1, abs=1e-10)


def test_factor_date_overlap_required():
    dates = pd.bdate_range("2020-01-01", periods=40)
    asset = pd.Series([0.01] * 40, index=dates)
    factors = pd.DataFrame({"date": dates + pd.DateOffset(days=400)})
    for key in ["market_excess", "SMB", "HML", "RMW", "CMA", "RF"]:
        factors[key] = 0
    with pytest.raises(DataContractError):
        descriptive_factor_regression(asset, factors)
