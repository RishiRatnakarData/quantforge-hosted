"""Exact neutral-majority regression and descriptive, not predictive, aggregation."""

import datetime as dt
from collections import Counter

import pytest

from cloud.news_intelligence_v180 import analyze_news, summarize_tone


@pytest.mark.parametrize(
    ("counts", "label"),
    [
        ({}, "No recent news"),
        ({"Positive": 1}, "Limited sample"),
        ({"Negative": 3}, "Limited sample"),
        ({"Positive": 1, "Mixed / neutral": 49}, "Mostly neutral"),
        ({"Negative": 1, "Uncertain": 49}, "Ambiguous coverage"),
        ({"Positive": 25, "Negative": 25}, "Conflicting coverage"),
        ({"Positive": 30, "Negative": 10, "Mixed / neutral": 10}, "Mostly positive"),
        ({"Negative": 30, "Positive": 10, "Mixed / neutral": 10}, "Mostly negative"),
        ({"Positive": 20, "Negative": 5, "Uncertain": 25}, "Mixed / neutral"),
    ],
)
def test_all_labels_consider_sample_size_and_full_distribution(counts, label):
    result = summarize_tone(Counter(counts))
    assert result["label"] == label
    assert result["sample_size"] == sum(counts.values())
    assert sum(result["shares"].values()) == pytest.approx(1 if counts else 0)
    assert "not calibrated" in result["policy"]


def test_actual_fifty_headlines_one_positive_forty_nine_neutral(monkeypatch):
    monkeypatch.delenv("QF_FINBERT_LOCAL_DIR", raising=False)
    records = [
        {
            "headline": "Issuer board notice schedule " + str(i),
            "created_at": "2026-11-10T15:00:00Z",
            "symbols": ["MSFT"],
            "source": "Synthetic test source",
        }
        for i in range(50)
    ]
    records[0]["headline"] = "Issuer reports strong growth"
    result = analyze_news(
        records, ["MSFT"], as_of=dt.datetime(2026, 11, 11, tzinfo=dt.UTC).isoformat()
    )
    row = result["rows"][0]
    assert row["articles"] == len(row["headlines"]) == 50
    assert (row["positive"], row["neutral"], row["negative"]) == (1, 49, 0)
    assert row["tone"] == "Mostly neutral"
    assert row["tone_summary"]["shares"]["Positive"] == 0.02


def test_malformed_and_future_records_cannot_create_available_sentiment():
    row = analyze_news(
        [
            None,
            {},
            {
                "headline": "Future strong profits",
                "symbols": ["MSFT"],
                "created_at": "2027-01-01T12:00:00Z",
            },
        ],
        ["MSFT"],
        as_of="2026-11-11T12:00:00Z",
    )["rows"][0]
    assert row["tone"] == "No recent news" and row["tone_summary"]["sample_size"] == 0


def test_public_teaching_evidence_is_exactly_reproducible_from_real_implementation():
    import json
    from pathlib import Path

    from tools.build_news_policy_evidence import build_evidence

    path = Path(__file__).resolve().parents[1] / "web/site/news_policy_examples_v28.js"
    value = (
        path.read_text(encoding="utf-8")
        .removeprefix("window.QFNewsPolicyEvidence28 = ")
        .rstrip()
        .removesuffix(";")
    )
    observed = json.loads(value)
    assert observed == build_evidence()
    assert observed["agreement"] < len(observed["examples"])  # visible errors must not disappear
    assert observed["aggregates"][2]["result"]["label"] == "Mostly neutral"
