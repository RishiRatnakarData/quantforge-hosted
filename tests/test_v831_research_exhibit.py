"""V8.3.1 research question, data-derived conclusions and case-study navigation."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('qf_v831_research_builder', ROOT / 'tools/build_v82_case_study.py')
assert SPEC and SPEC.loader
CASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CASE)


def rows():
    return [
        {'symbol': 'AAA', 'growth': 12.0, 'operating_margin': 30.0, 'fcf_margin': 15.0},
        {'symbol': 'BBB', 'growth': 25.0, 'operating_margin': 15.0, 'fcf_margin': 3.0},
        {'symbol': 'CCC', 'growth': -3.0, 'operating_margin': 2.0, 'fcf_margin': -5.0},
        {'symbol': 'DDD', 'growth': None, 'operating_margin': 18.0, 'fcf_margin': None},
    ]


def test_conclusion_is_computed_and_distinguishes_growth_from_margin():
    cards, conclusion = CASE.research_brief(rows())
    assert 'BBB' in cards and '+25.0%' in cards
    assert 'AAA' in cards and '+30.0%' in cards
    assert '2 / 3' in cards
    assert 'BBB' in conclusion and 'AAA' in conclusion
    assert 'growth alone does not reproduce' in conclusion
    assert 'No inferential significance' in conclusion


def test_missing_values_do_not_create_unsupported_findings():
    empty=[{'symbol':'AAA','growth':None,'operating_margin':None,'fcf_margin':None}]
    cards, conclusion=CASE.research_brief(empty)
    assert 'Unavailable' in cards
    assert 'Not reported' in cards
    assert '0 / 0' in cards
    assert 'do not support a complete' in conclusion


def test_research_title_and_interpretation_are_not_prediction():
    assert 'revenue growth' in CASE.CASE_STUDY_TITLE.lower() or 'growing' in CASE.CASE_STUDY_TITLE.lower()
    source=(ROOT/'tools/build_v82_case_study.py').read_text(encoding='utf-8')
    assert 'Conclusion and interpretation' in source
    assert 'company with the highest latest annual revenue growth' in source
    assert 'The sample is small and deliberately selected.' in source


def test_public_methods_links_to_dedicated_study_and_exploratory_scatter():
    template=(ROOT/'web/site/site.template.html').read_text(encoding='utf-8')
    assert 'id="qf-v82-case-study"' in template
    assert template.count('href="research-case-study.html"')>=2
    assert 'Read complete case study' in template
    assert 'switch between a focused axis range and the full distribution' in template
    assert 'QF V8.3.1 / Case-study and readable SEC scatter' in template
