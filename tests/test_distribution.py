"""Release regression: every source module needed by the CLI must be present."""

import os
from unittest import SkipTest

REQUIRED_MODULES = (
    "quantforge.data.contracts",
    "quantforge.data.simulation",
    "quantforge.data.sources",
    "quantforge.data.storage",
    "quantforge.data.tiingo",
    "quantforge.cli",
    "quantforge.portfolio.advanced",
    "quantforge.risk.conditional_coverage",
    "quantforge.risk.garch",
    "quantforge.risk.stress",
    "quantforge.research.study",
    "quantforge.research.v2",
    "quantforge.regimes.markov",
    "quantforge.forecasting.advanced",
    "quantforge.derivatives.black_scholes",
    "quantforge.simulation.portfolio_mc",
)


def test_required_source_modules_exist_and_import():
    for name in REQUIRED_MODULES:
        module = __import__(name, fromlist=["__name__"])
        assert os.path.isfile(module.__file__)


def test_duckdb_parquet_export_when_dependency_available(tmp_path):
    try:
        import duckdb
    except ImportError as exc:
        raise SkipTest("duckdb is not installed in this environment") from exc
    from quantforge.cli import main

    output = tmp_path / "duckdb_run"
    assert main(["demo", "--rows", "80", "--lookback", "30", "--output", str(output)]) == 0
    for filename in ("quantforge.duckdb", "prices.parquet", "returns.parquet"):
        assert (output / filename).stat().st_size > 100
    with duckdb.connect(str(output / "quantforge.duckdb"), read_only=True) as connection:
        assert connection.execute("SELECT COUNT(*) FROM market_returns").fetchone()[0] == 79 * 4
