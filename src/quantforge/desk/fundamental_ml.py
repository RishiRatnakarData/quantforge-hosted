"""Exploratory SEC fundamental peers; unsupervised descriptions, not stock forecasts.

Rows come only from identified 10-K reports via SECResearch. Training and
feature scaling are intentionally restricted to the selected peer universe.
"""

from __future__ import annotations

import datetime as dt
import math
import re
import time
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler

from quantforge.desk.engine import DeskError

FIELDS = (
    ("revenue_growth_pct", "Revenue growth", "%"),
    ("operating_margin_pct", "Operating margin", "%"),
    ("net_margin_pct", "Net margin", "%"),
    ("fcf_margin_pct", "Free cash flow / revenue", "%"),
    ("long_term_debt_assets_pct", "Long-term debt / assets", "%"),
)
STOCK_SYMBOL = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")
MAX_PEERS = 16


def _features(fundamentals: dict) -> dict[str, float | None]:
    rev = fundamentals.get("revenue_usd")
    assets = fundamentals.get("total_assets_usd")
    fcf = fundamentals.get("free_cash_flow_usd")
    debt = fundamentals.get("long_term_debt_usd")
    values = {
        "revenue_growth_pct": fundamentals.get("revenue_growth_pct"),
        "operating_margin_pct": fundamentals.get("operating_margin_pct"),
        "net_margin_pct": fundamentals.get("net_margin_pct"),
        "fcf_margin_pct": 100 * fcf / rev if isinstance(rev, (int, float)) and rev > 0 and isinstance(fcf, (int, float)) else None,
        "long_term_debt_assets_pct": 100 * debt / assets if isinstance(assets, (int, float)) and assets > 0 and isinstance(debt, (int, float)) else None,
    }
    for k, v in values.items():
        if not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > 10000:
            values[k] = None
        else:
            values[k] = round(float(v), 5)
    return values


def _prepare_symbol_list(target: str, symbols: list[str]) -> list[str]:
    target = str(target).strip().upper()
    if not STOCK_SYMBOL.fullmatch(target):
        raise DeskError("Select a valid U.S. company ticker for SEC peer analysis.")
    if not isinstance(symbols, list):
        raise DeskError("Select a list of peer-company symbols.")
    normalized = [target]
    for symbol in symbols:
        value = str(symbol).strip().upper()
        if not STOCK_SYMBOL.fullmatch(value):
            raise DeskError("Peer list contains an invalid stock ticker.")
        if value not in normalized:
            normalized.append(value)
    if not 6 <= len(normalized) <= MAX_PEERS:
        raise DeskError("Select 6–16 different companies, including the research target.")
    return normalized


def analyze_fundamentals(records: list[dict], target: str) -> dict:
    """Produce deterministic peer proximity and limited sample-relative outlier diagnostics.

    No return labels, future-price targets, probability of success, or implied
    investment advice. Robust scale and median imputation are fit within the
    selected sample only; missing values and coverage are disclosed.
    """
    target = str(target).strip().upper()
    data = {r["symbol"]: r for r in records}
    if target not in data:
        raise DeskError("The target company has insufficient annual SEC facts.")
    if len(data) < 6:
        raise DeskError("At least six distinct companies with usable SEC financials are required.")

    symbols = sorted(data)
    processed = [_features(data[s]) for s in symbols]
    keys = [k for k, _, _ in FIELDS]
    raw = np.array([[row[k] if row[k] is not None else np.nan for k in keys] for row in processed], dtype=float)
    # A missing company may have at most one of the five signals unavailable.
    # Do not hide broad financial-data gaps with imputation.
    valid_counts = np.sum(np.isfinite(raw), axis=1)
    if np.any(valid_counts < 4):
        raise DeskError("Insufficient financial-feature coverage; exclude companies missing two or more metrics.")
    if np.any(np.sum(np.isfinite(raw), axis=0) < 4):
        raise DeskError("At least four reporting companies per financial metric are required.")
    imputer = SimpleImputer(strategy="median")
    imputed = imputer.fit_transform(raw)
    scaler = RobustScaler(with_centering=True, with_scaling=True)
    z = scaler.fit_transform(imputed)
    if not np.isfinite(z).all():
        raise DeskError("Peer feature scaling produced invalid values.")
    varying = np.var(z, axis=0) > 1e-12
    if int(np.count_nonzero(varying)) < 3:
        raise DeskError("Peer group has fewer than three varying financial metrics.")
    z = z[:, varying]
    target_idx = symbols.index(target)
    distances = np.linalg.norm(z - z[target_idx], axis=1)
    peers_order = sorted((i for i in range(len(symbols)) if i != target_idx),
                         key=lambda i: (float(distances[i]), symbols[i]))
    closest = peers_order[:5]

    # Small-sample diagnostic: compare closest peer under each leave-one-feature-out
    # metric set (not cross-validated prediction accuracy).
    stable = 0
    trials = 0
    for j in range(z.shape[1]):
        if z.shape[1] <= 3:
            continue
        reduced = np.delete(z, j, axis=1)
        alternate = np.linalg.norm(reduced - reduced[target_idx], axis=1)
        ordered = sorted((i for i in range(len(symbols)) if i != target_idx),
                         key=lambda i: (float(alternate[i]), symbols[i]))
        trials += 1
        if ordered[0] == closest[0]:
            stable += 1

    anomaly = {"available": False, "reason": "At least 12 valid companies are needed for an exploratory outlier ranking."}
    if len(symbols) >= 12:
        # The rank is *only* relative to the selected group; no class labels and
        # no external evaluation mean no calibrated accuracy or probability.
        forest = IsolationForest(n_estimators=256, contamination="auto",
                                 max_samples=min(256, len(symbols)), random_state=341)
        scores = forest.fit(z).score_samples(z)  # Smaller is more unusual.
        ranks = sorted(range(len(symbols)), key=lambda i: (float(scores[i]), symbols[i]))
        anomaly = {
            "available": True,
            "model": "IsolationForest (unsupervised, 256 trees, random seed 341)",
            "unusualness_rank": ranks.index(target_idx) + 1,
            "out_of": len(symbols),
            "interpretation": "Rank 1 is the most unusual within these selected companies. Not a fraud, distress or return forecast.",
        }

    feature_table = []
    for k, label, unit in FIELDS:
        j = keys.index(k)
        target_val = processed[target_idx][k]
        observed = [float(raw[i, j]) for i in range(len(symbols))
                    if i != target_idx and np.isfinite(raw[i, j])]
        feature_table.append({
            "name": label, "key": k, "unit": unit,
            "target": target_val,
            "peer_median": round(float(np.median(observed)), 3),
            "target_imputed": not np.isfinite(raw[target_idx, j]),
            "missing_company_count": int(np.count_nonzero(~np.isfinite(raw[:, j]))),
            "used_for_distance": bool(varying[j]),
        })
    peers = [dict(symbol=symbols[i], company_name=data[symbols[i]].get("company_name", symbols[i]),
                  fiscal_end=data[symbols[i]].get("fiscal_end"),
                  distance=round(float(distances[i]), 4),
                  imputed_fields=[keys[j] for j in range(len(keys)) if not np.isfinite(raw[i, j])])
             for i in closest]
    ends = [data[s].get("fiscal_end") for s in symbols]
    return {
        "target": target,
        "target_name": data[target].get("company_name", target),
        "sample_size": len(symbols),
        "peers": peers,
        "financial_features": feature_table,
        "imputed_values": int(np.count_nonzero(~np.isfinite(raw))),
        "target_imputed_fields": [keys[j] for j in range(len(keys)) if not np.isfinite(raw[target_idx, j])],
        "neighbor_stability": {"same_closest_peer": stable, "feature_drop_checks": trials},
        "anomaly": anomaly,
        "fiscal_end_range": [min(ends), max(ends)],
        "source": "SEC EDGAR 10-K Company Facts (annual); issuer and fiscal periods in peer list",
        "method": "Within-selected-sample median imputation (max 1 missing metric per company); RobustScaler median/IQR; Euclidean nearest peers; optional IsolationForest.",
        "limitations": "Exploratory within the selected peer set. Not a predicted return, fair value, trading signal or validated anomaly classification. Company fiscal years differ. Similarity depends on group and feature selection. Financial sectors can have different accounting conventions. Do not publish private research exports.",
    }


def research_peer_group(sec_research: Any, *, target: str, symbols: list[str]) -> dict:
    universe = _prepare_symbol_list(target, symbols)
    accepted: list[dict] = []
    skipped: list[dict] = []
    seen_ciks: set[int] = set()
    for ticker in universe:
        try:
            row = sec_research.fundamentals(ticker)
            cik = row.get("cik")
            if cik in seen_ciks:
                skipped.append({"symbol": ticker, "reason": "Duplicate issuer (share class)"})
                continue
            if int(row.get("revenue_usd") or 0) <= 0:
                skipped.append({"symbol": ticker, "reason": "No positive annual revenue"})
                continue
            feats = _features(row)
            if sum(v is not None for v in feats.values()) < 4:
                skipped.append({"symbol": ticker, "reason": "More than one required SEC financial metric missing"})
                continue
            accepted.append(row)
            if isinstance(cik, int):
                seen_ciks.add(cik)
        except (DeskError, KeyError, ValueError, TypeError) as exc:
            skipped.append({"symbol": ticker, "reason": str(exc)[:180]})
        # Be civil to the SEC's fair-access API during a multi-company request.
        if sec_research.__class__.__name__ == "SECResearch":
            time.sleep(0.13)
    result = analyze_fundamentals(accepted, target)
    result["excluded_companies"] = skipped
    result["included_companies"] = [dict(symbol=x["symbol"], name=x.get("company_name", x["symbol"]),
                                          fiscal_end=x.get("fiscal_end"),
                                          filing_date=x.get("revenue_filing_date")) for x in accepted]
    result["requested_count"] = len(universe)
    result["analysis_as_of"] = dt.date.today().isoformat()
    return result
