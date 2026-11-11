"""Bounded headline evidence, qualifier handling and duplicate suppression."""
from cloud.news_intelligence_v180 import _tone, analyze_news


def test_qualified_and_negated_financial_headlines():
    for headline, expected in [
        ('Company beats estimates and raises guidance', 'Positive'),
        ('Company cuts guidance after weak demand', 'Negative'),
        ('Company does not face weak demand', 'Positive'),
        ('Company may raise guidance after product launch', 'Uncertain'),
        ('Reportedly strong growth could reverse', 'Uncertain'),
        ('Company announces annual meeting date', 'Mixed / neutral'),
    ]:
        assert _tone(headline)[0] == expected


def test_analyzed_sample_is_inspectable_and_distribution_counts_reconcile(monkeypatch):
    monkeypatch.delenv('QF_FINBERT_LOCAL_DIR', raising=False)
    items = [{'id': i, 'headline': f'Company earnings growth update number {i}',
              'symbols': ['MSFT'], 'created_at': '2026-11-05T12:00:00Z',
              'source': 'MOCK', 'url': 'https://example.invalid/story'} for i in range(60)]
    items.insert(1, {**items[0], 'id': 'duplicate-provider-id'})
    result = analyze_news(items, ['MSFT'], as_of='2026-11-06T12:00:00Z')
    row = result['rows'][0]
    assert result['articles_analyzed'] == row['articles'] == len(row['headlines']) == 50
    assert sum(row['topic_counts'].values()) == sum(row['tone_counts'].values()) == 50
    assert row['coverage']['first'] == row['coverage']['last'] == '2026-11-05T12:00:00Z'
    assert all('topic' in h and 'tone' in h for h in row['headlines'])
