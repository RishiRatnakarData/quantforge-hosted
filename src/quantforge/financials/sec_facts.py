"""Extract time-filtered SEC Company Facts, preserving filing and fiscal periods."""

from __future__ import annotations

import pandas as pd

from quantforge.data.sources import ProviderError


def extract_filed_company_fact(
    companyfacts: dict,
    *,
    concept: str,
    as_of: str,
    taxonomy: str = "us-gaap",
    units: str = "USD",
    forms: tuple[str, ...] = ("10-K", "10-Q", "10-K/A", "10-Q/A"),
) -> pd.DataFrame:
    """Return fact candidates *filed by* as_of; no naive quarterly reconstruction.

    SEC may report restatements and overlapping contexts. This returns
    traceable **candidates**, not a final balance-sheet or valuation fact.
    """
    date = pd.Timestamp(as_of).normalize()
    try:
        observations = companyfacts["facts"][taxonomy][concept]["units"][units]
    except (KeyError, TypeError) as exc:
        raise ProviderError(f"Missing SEC concept {taxonomy}:{concept} [{units}]") from exc
    table = pd.DataFrame(observations)
    # Balance-sheet instants have no start; duration facts do.
    mandatory = {"end", "val", "accn", "filed", "form"}
    if not mandatory.issubset(table.columns):
        raise ProviderError("Missing SEC filing attribution fields")
    table["filed"] = pd.to_datetime(table["filed"], errors="coerce")
    table["end"] = pd.to_datetime(table["end"], errors="coerce")
    if table["filed"].isna().any() or table["end"].isna().any():
        raise ProviderError("Unparseable SEC filing or period dates")
    table = table[table["filed"].le(date) & table["form"].isin(forms)].copy()
    table["taxonomy"] = taxonomy
    table["concept"] = concept
    table["units"] = units
    return table.sort_values(["end", "filed", "accn"]).reset_index(drop=True)
