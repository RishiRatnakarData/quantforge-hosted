"""Clearly fictional Microsoft-shaped SEC fixture for OFFLINE QA ONLY."""

from __future__ import annotations

from quantforge.financials.annual import ANNUAL, BALANCE, SHARE_TAGS


def synthetic_companyfacts() -> dict:
    """Synthetic accounting relationships; no numbers are Microsoft disclosures."""
    data: dict = {"cik": 789019, "entityName": "SYNTHETIC DEMO — NOT MICROSOFT FINANCIALS", "facts": {"us-gaap": {}}}
    years = [2023, 2024, 2025, 2026]
    measurements = {
        "revenue": [180_000, 210_000, 245_000, 280_000],
        "operating_income": [75_000, 90_000, 110_000, 125_000],
        "pretax_income": [76_000, 91_000, 111_000, 126_000],
        "tax_expense": [14_000, 17_000, 20_000, 24_000],
        "net_income": [62_000, 74_000, 91_000, 102_000],
        "gross_profit": [120_000, 144_000, 170_000, 190_000],
        "operating_cash_flow": [88_000, 105_000, 122_000, 146_000],
        "capex": [35_000, 45_000, 60_000, 83_000],
        "depreciation_amortization": [19_000, 22_000, 28_000, 33_000],
        "cash": [25_000, 27_000, 29_000, 31_000],
        "short_term_investments": [65_000, 67_000, 60_000, 59_000],
        "receivables": [41_000, 48_000, 58_000, 69_000],
        "inventory": [3_000, 3_200, 3_400, 3_800],
        "payables": [22_000, 25_000, 27_000, 29_000],
        "deferred_revenue": [46_000, 49_000, 56_000, 62_000],
        "debt_current": [3_000, 4_000, 5_000, 6_000],
        "debt_long_term": [44_000, 43_000, 42_000, 41_000],
        "assets": [380_000, 420_000, 480_000, 570_000],
        "current_assets": [165_000, 175_000, 190_000, 220_000],
        "current_liabilities": [100_000, 110_000, 120_000, 140_000],
        "ppe_net": [98_000, 112_000, 140_000, 160_000],
        "liabilities": [190_000, 208_000, 228_000, 265_000],
        "stockholders_equity": [190_000, 212_000, 252_000, 305_000],
        "diluted_shares": [7_500, 7_490, 7_480, 7_465],
    }
    for field, tag_choices in {**ANNUAL, **BALANCE, "diluted_shares": SHARE_TAGS}.items():
        tag = tag_choices[0]
        units = "shares" if field == "diluted_shares" else "USD"
        rows = []
        for i, year in enumerate(years):
            row = {
                "end": f"{year}-06-30", "filed": f"{year}-08-01",
                "form": "10-K", "accn": f"FAKE-DEMO-{year}",
                "val": int(measurements[field][i] * 1_000_000),
                "fy": year, "fp": "FY",
            }
            if field in ANNUAL or field == "diluted_shares":
                row["start"] = f"{year - 1}-07-01"
            rows.append(row)
        data["facts"]["us-gaap"][tag] = {"units": {units: rows}}
    return data
