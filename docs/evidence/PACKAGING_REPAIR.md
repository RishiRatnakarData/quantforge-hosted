# M0.1 distribution repair (2026-10-22)

## Original defect

The first `QuantForge_M0_Research_Foundation.zip` omitted `src/quantforge/data/`, despite `cli.py`, the tests, and factor/SEC modules importing it. The editable installation therefore succeeded but pytest collected six import failures and the demonstration could not start. Windows PowerShell additionally blocked the virtual environment activation script; pip consequently installed into global Python when invoked as bare `python`.

## Correction

- Restored `data/__init__.py`, `contracts.py`, `simulation.py`, `sources.py`, `storage.py`.
- Preserved the `symbol` column name in the wide-price panel so `.stack().reset_index()` produces the expected long-form returns schema.
- Added distribution checks that import required modules and assert presence of optional DuckDB/Parquet exports when DuckDB is installed.
- Added the three DuckDB/Parquet artifacts to the CI smoke-test verification.
- Updated PowerShell commands to call `.\.venv\Scripts\python.exe` directly. Activation and execution-policy changes are unnecessary.
- Bumped Python package version and output manifest release to `0.1.1` so the corrected distribution can be distinguished from the broken package.

## Validation

- `50 passed, 1 skipped` locally (the skipped integration test requires DuckDB).
- `compileall` passed.
- 330-price-day simulated CLI run succeeded; generated CSV, SQLite, JSON and HTML.
- Source wheel built successfully; all restored `quantforge.data` files confirmed in wheel.
- DuckDB/Parquet and Ruff were unavailable in this runtime and are not claimed verified. GitHub Actions has not yet run.

## Windows recovery

Extract the corrected ZIP to a **new** folder and run from the directory containing `pyproject.toml`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -c "from quantforge.data.contracts import validate_prices; print('QuantForge data modules OK')"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m quantforge demo --output outputs/demo --rows 330
Start-Process .\outputs\demo\research_dashboard.html
```

After execution inspect the manifest `storage.storage_engine` and confirm `quantforge.duckdb`, `prices.parquet` and `returns.parquet` are present before declaring the full dependency-backed run verified.
