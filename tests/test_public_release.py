"""Official ECB data contract, chronology and static-site publication boundaries."""

import io
import json

import numpy as np
import pandas as pd
import pytest

from quantforge.public.analytics import evaluate_fx
from quantforge.public.ecb import CURRENCIES, decode_ecb_csv, raw_sha256, save_raw_ecb
from quantforge.public.site import build_public_site


def _fixture_csv(n=360):
    rows = []
    for date in pd.bdate_range("2023-01-02", periods=n):
        for currency, base in zip(CURRENCIES, (1.10, 0.85, 155.0, 0.96), strict=True):
            rows.append({"FREQ": "D", "CURRENCY": currency, "CURRENCY_DENOM": "EUR",
                         "EXR_TYPE": "SP00", "EXR_SUFFIX": "A",
                         "TIME_PERIOD": str(date.date()), "OBS_VALUE": base})
    return pd.DataFrame(rows).to_csv(index=False).encode()


def test_ecb_official_sdmx_dimensions_and_four_currency_panel():
    frame = decode_ecb_csv(_fixture_csv())
    assert len(frame) == 360
    assert list(frame.columns) == list(CURRENCIES)
    assert np.isclose(frame["USD"].iloc[5], 1.1)


def test_ecb_rejects_wrong_denominator_and_nonpositive():
    text = _fixture_csv().decode().replace(",EUR,SP00,", ",USD,SP00,", 1)
    with pytest.raises(ValueError, match="CURRENCY_DENOM"):
        decode_ecb_csv(text.encode())
    frame = pd.read_csv(io.BytesIO(_fixture_csv()))
    frame.loc[0, "OBS_VALUE"] = -1.1
    with pytest.raises(ValueError, match="positive"):
        decode_ecb_csv(frame.to_csv(index=False).encode())


def test_ecb_rejects_duplicate_records_and_missing_common_days():
    raw = _fixture_csv()
    duplicate = pd.read_csv(io.BytesIO(raw))
    duplicated = pd.concat([duplicate, duplicate.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate"):
        decode_ecb_csv(duplicated.to_csv(index=False).encode())
    missing = duplicate.loc[~((duplicate["CURRENCY"] == "GBP") &
                              (duplicate["TIME_PERIOD"] >= "2023-01-03"))]
    with pytest.raises(ValueError, match="Insufficient"):
        decode_ecb_csv(missing.to_csv(index=False).encode())


def test_public_source_fingerprint_and_synthetic_markers(tmp_path):
    raw = _fixture_csv()
    quotes = decode_ecb_csv(raw)
    evidence = tmp_path / "evidence"
    sha = save_raw_ecb(raw, evidence)
    assert sha == raw_sha256(raw)
    result = evaluate_fx(quotes, output=evidence, origin="ecb_reference_fx",
                         source_url="https://data-api.ecb.europa.eu/service/data/EXR/test",
                         source_sha=sha, advanced=False)
    assert result["historical_etf_holdout_2019_2025"] == "excluded_not_loaded"
    site = tmp_path / "site"
    build_public_site(fx_dir=evidence, output=site)
    text = (site / "index.html").read_text(encoding="utf-8")
    assert '"origin":"ecb_reference_fx"' in text
    assert "Source: ECB statistics" in text
    assert not list(site.glob("*.pdf"))
    assert "research paper" not in (site / "CASE_STUDY.md").read_text().lower().split("no research paper")[0]
    (evidence / "ecb_original_source.csv").write_bytes(b"changed")
    with pytest.raises(ValueError, match="raw-source"):
        build_public_site(fx_dir=evidence, output=site)


def test_publish_refuses_unknown_and_synthetic_sec(tmp_path):
    dates = pd.bdate_range("2023-01-03", periods=360)
    frame = pd.DataFrame({name: 1 + np.arange(len(dates)) * 0.0001
                          for name in CURRENCIES}, index=dates)
    evidence = tmp_path / "synthetic"
    evaluate_fx(frame, output=evidence, origin="synthetic_fx_fixture",
                source_url="offline", source_sha=None, advanced=False)
    manifest_path = evidence / "fx_manifest.json"
    original = manifest_path.read_text()
    values = json.loads(original)
    values["data_origin"] = "external_tiingo"
    manifest_path.write_text(json.dumps(values))
    with pytest.raises(ValueError, match="Tiingo"):
        build_public_site(fx_dir=evidence, output=tmp_path / "reject")
    manifest_path.write_text(original)
    sec = tmp_path / "sec"
    sec.mkdir()
    (sec / "manifest_v3.json").write_text('{"data_origin": "synthetic_demo"}')
    (sec / "financial_statement_audit.json").write_text(
        '{"status": "latest_year_complete_and_balance_reconciled"}')
    with pytest.raises(ValueError, match="refuses synthetic"):
        build_public_site(fx_dir=evidence, sec_dir=sec, output=tmp_path / "reject")
