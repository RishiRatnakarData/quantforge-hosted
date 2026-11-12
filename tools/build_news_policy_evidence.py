"""Build sanitized, synthetic teaching evidence from the actual headline implementation."""
from __future__ import annotations

import inspect
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cloud.news_intelligence_v180 import _tone, summarize_tone  # noqa: E402


def build_evidence():
    examples = [
        ("Company beats estimates and raises guidance", "Positive", "Directional financial words."),
        ("Company shares fall after product recall", "Negative", "Directional negative vocabulary."),
        ("Company board schedules annual meeting", "Mixed / neutral", "No dictionary direction."),
        ("Company may report strong growth", "Uncertain", "Qualifier overrides favorable words."),
        ("Company growth is not strong", "Mixed / neutral", "Opposing lexical contributions cancel; scope is limited."),
        ("Company says no loss was recorded", "Positive", "Negated loss; not evidence of future returns."),
        ("Company cuts avoidable overhead costs", "Uncertain", "A cost cut can help profitability; the dictionary treats cut as negative."),
        ("Company publishes record of annual meeting", "Mixed / neutral", "Record is a positive dictionary word even when it means a document."),
        ("Company might face a lawsuit", "Uncertain", "Qualified legal language."),
        ("Company reports layoffs and weak demand", "Negative", "Negative vocabulary; magnitude is unknown."),
    ]
    rows = [{"headline": headline, "expected": expected, "observed": _tone(headline)[0], "note": note}
            for headline, expected, note in examples]
    counts = [{}, {"Positive": 1}, {"Positive": 1, "Mixed / neutral": 49},
              {"Positive": 25, "Negative": 25}, {"Positive": 30, "Negative": 10, "Mixed / neutral": 10},
              {"Negative": 1, "Uncertain": 49}]
    return {"scope": "Synthetic teaching fixtures, not provider news or an accuracy benchmark",
            "aggregates": [{"counts": c, "result": summarize_tone(Counter(c))} for c in counts],
            "examples": rows, "agreement": sum(row["expected"] == row["observed"] for row in rows),
            "code_excerpt": inspect.getsource(summarize_tone)}


if __name__ == '__main__':
    payload = json.dumps(build_evidence(), ensure_ascii=False, sort_keys=True)
    (ROOT/'web/site/news_policy_examples_v28.js').write_text('window.QFNewsPolicyEvidence28 = '+payload+';\n', encoding='utf-8')
    print('Generated deterministic synthetic headline-policy and lexical error evidence.')
