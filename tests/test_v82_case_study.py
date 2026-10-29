"""V8.2 SEC-only case-study contracts: math, provenance, omissions, safety."""
import csv
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/build_v82_case_study.py"
SPEC = importlib.util.spec_from_file_location("quantforge_v82_case_study", SCRIPT)
CASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CASE)


def issuer(symbol, cik):
    dates = ("2023-12-31", "2024-12-31", "2025-12-31")
    annual = []
    for idx, end in enumerate(dates):
        metrics = {
            "revenue_usd": (100 + idx * 10) * 1_000_000_000,
            "operating_income_usd": (22 + idx) * 1_000_000_000,
            "net_income_usd": 10_000_000_000,
            "operating_cash_flow_usd": 20_000_000_000,
            "capex_usd": 3_000_000_000,
            "free_cash_flow_usd": 17_000_000_000,
        }
        accession = f"{cik:010d}-25-{idx:06d}"
        sources = {key: {"accession": accession, "end": end, "filed": "2026-02-01", "tag": "TestFixture"}
                   for key in metrics if key != "free_cash_flow_usd"}
        annual.append({"fiscal_end": end, "metrics": metrics, "sources": sources})
    return {"symbol": symbol, "name": "Illustrative test issuer " + symbol,
            "cik": cik, "as_of": "2026-10-27", "annual": annual,
            "source_url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"}


def fixture():
    symbols = CASE.SYMBOLS
    base = [issuer(s, i+1) for i, s in enumerate(symbols)]
    rest = [issuer(f"T{i}", i+100) for i in range(90)]
    return {"dataset": CASE.DATASET, "companies": base + rest}


def test_original_issuer_missing_extraction_date_is_disclosed_not_fabricated():
    data = fixture()
    del data["companies"][0]["as_of"]
    selected = CASE.load_companies(data)
    assert selected[0]["cutoff"] == ""
    page = CASE.render_html(data, selected, "a" * 64)
    ledger = CASE.csv_report(selected)
    assert "MSFT: not recorded" in page
    assert "Not recorded in the source snapshot" in page
    assert "some original issuers that cutoff is unrecorded" in page
    assert "issuer_as_of" in ledger
    assert ",2023-12-31,," in ledger
    assert "MSFT: 2026-10-27" not in page


def test_invalid_nonmissing_issuer_cutoff_still_fails_closed():
    c = issuer("MSFT", 1)
    c["as_of"] = {"cutoff": "2026-10-27"}
    with pytest.raises(ValueError, match="extraction cutoff type"):
        CASE.clean_issuer(c)
    c["as_of"] = "2026-99-99"
    with pytest.raises(ValueError, match="Invalid SEC extraction cutoff"):
        CASE.clean_issuer(c)


def test_legacy_accessions_without_metric_period_end_are_disclosed_not_rejected():
    c = issuer("MSFT", 1)
    for rec in c["annual"]:
        for source in rec["sources"].values():
            source.pop("end")
    normalized = CASE.clean_issuer(c)
    assert normalized["annual"][0]["date"] == "2023-12-31"
    ledger = list(csv.DictReader(io.StringIO(CASE.csv_report([normalized]))))
    revenue = [row for row in ledger if row["metric"] == "revenue_usd"]
    assert len(revenue) == 3
    for row in revenue:
        assert row["fiscal_end"] and row["source_accession"]
        assert row["source_period_end"] == ""
        assert "unrecorded in legacy snapshot" in row["period_end_verification"]
    page = CASE.render_html(fixture(), [normalized], "a" * 64)
    assert "cannot be checked from this snapshot alone" in page


def test_midyear_legacy_microsoft_fiscal_period_2026_without_individual_source_ends():
    c = issuer("MSFT", 1)
    c.pop("as_of")
    for i, rec in enumerate(c["annual"]):
        rec["fiscal_end"] = f"{2024+i}-06-30"
        for source in rec["sources"].values():
            source.pop("end", None)
    normalized = CASE.clean_issuer(c)
    assert normalized["annual"][-1]["date"] == "2026-06-30"
    assert normalized["cutoff"] == ""
    rows = list(csv.DictReader(io.StringIO(CASE.csv_report([normalized]))))
    latest = [row for row in rows if row["fiscal_end"] == "2026-06-30"]
    assert len(latest) == len(CASE.METRICS)
    assert all(not row["source_period_end"] for row in latest)
    assert any("legacy snapshot" in row["period_end_verification"] for row in latest)


def test_explicitly_conflicting_source_period_still_fails_closed():
    c = issuer("MSFT", 1)
    c["annual"][0]["sources"]["revenue_usd"]["end"] = "2024-12-31"
    with pytest.raises(ValueError, match="Misaligned SEC source period"):
        CASE.clean_issuer(c)


def test_invalid_recorded_source_period_type_fails_closed():
    c = issuer("MSFT", 1)
    c["annual"][0]["sources"]["revenue_usd"]["end"] = {"invalid": True}
    with pytest.raises(ValueError, match="Invalid recorded SEC source period"):
        CASE.clean_issuer(c)


def test_revenue_growth_and_margin_are_reported_ratios():
    assert CASE.yoy(120, 100) == pytest.approx(20.0)
    assert CASE.yoy(80, 100) == pytest.approx(-20.0)
    assert CASE.percentage(20, 100) == pytest.approx(20.0)
    assert CASE.percentage(-20, 100) == pytest.approx(-20.0)


def test_missing_zero_or_nonfinite_values_are_withheld():
    assert CASE.yoy(0, 0) is None
    assert CASE.percentage(10, 0) is None
    assert CASE.percentage(None, 100) is None
    assert CASE.yoy(float("inf"), 100) is None
    assert CASE.percentage(True, 100) is None


def test_four_issuers_selected_in_declared_order_from_94_company_catalog():
    selected = CASE.load_companies(fixture())
    assert [item["symbol"] for item in selected] == list(CASE.SYMBOLS)
    assert len(selected[0]["annual"]) == 3


def test_duplicate_or_missing_issuer_fails_closed():
    data = fixture()
    data["companies"][4]["symbol"] = "AMD"
    with pytest.raises(ValueError, match="duplicate"):
        CASE.load_companies(data)
    data = fixture()
    data["companies"] = data["companies"][:93]
    with pytest.raises(ValueError, match="94"):
        CASE.load_companies(data)


def test_cash_flow_proxy_requires_audited_inputs_and_exact_reconciliation():
    c = issuer("AMD", 2)
    c["annual"][0]["metrics"]["free_cash_flow_usd"] = 88_000_000_000
    with pytest.raises(ValueError, match="does not reconcile"):
        CASE.clean_issuer(c)
    c = issuer("AMD", 2)
    c["annual"][0]["sources"].pop("capex_usd")
    with pytest.raises(ValueError, match="Unattributed"):
        CASE.clean_issuer(c)


def test_untrusted_issuer_name_escaped_and_csv_injection_prevented():
    data = fixture()
    data["companies"][0]["name"] = '=HYPERLINK("evil")<script>alert(1)</script>'
    selected = CASE.load_companies(data)
    page = CASE.render_html(data, selected, "a" * 64)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page
    ledger = CASE.csv_report(selected)
    assert "'\"" not in ledger  # neutralize formula prefix rather than quote a formula
    assert "'=HYPERLINK" in ledger


def test_report_has_no_market_returns_or_personalized_claim():
    data = fixture()
    selected = CASE.load_companies(data)
    page = CASE.render_html(data, selected, "a" * 64)
    assert "Historical disclosures only" in page
    assert "point-in-time" in page
    assert "not adjusted stock-price histories" in page
    assert "source_accession" in CASE.csv_report(selected)
    assert "<script" not in page.lower()


def test_reproducible_artifacts_and_snapshot_immutable(tmp_path):
    repo = tmp_path
    (repo / "web/site").mkdir(parents=True)
    (repo / "web/site/sec_snapshot.json").write_text(json.dumps(fixture()), encoding="utf-8")
    before = (repo / "web/site/sec_snapshot.json").read_bytes()
    CASE.write_outputs(repo)
    first = (repo / "public/research-case-study.html").read_bytes()
    CASE.write_outputs(repo)
    assert first == (repo / "public/research-case-study.html").read_bytes()
    assert before == (repo / "web/site/sec_snapshot.json").read_bytes()


def test_actual_public_snapshot_when_installed():
    data = json.loads((ROOT / "web/site/sec_snapshot.json").read_text(encoding="utf-8"))
    selected = CASE.load_companies(data)
    assert len(selected) == 4
    assert (ROOT / "public/research-case-study.html").is_file()
    assert (ROOT / "public/research-case-study.csv").is_file()
    assert "QF V8.2 PUBLIC RESEARCH CASE STUDY" in (ROOT / "web/site/site.template.html").read_text(encoding="utf-8")


def test_committed_public_case_study_matches_exact_sec_snapshot_bytes():
    import hashlib

    path = ROOT / "web/site/sec_snapshot.json"
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    companies = CASE.load_companies(data)
    digest = hashlib.sha256(raw).hexdigest()
    assert (ROOT / "public/research-case-study.html").read_text(encoding="utf-8") == CASE.render_html(data, companies, digest)
    assert (ROOT / "public/research-case-study.csv").read_text(encoding="utf-8") == CASE.csv_report(companies)


def test_full_public_site_static_boundary_and_case_study_link():
    audit_script = ROOT / "tools/audit_v82_readiness.py"
    result = subprocess.run(
        [sys.executable, str(audit_script), "--repo", str(ROOT)],
        capture_output=True, text=True, check=True,
    )
    assert "static readiness PASS" in result.stdout
