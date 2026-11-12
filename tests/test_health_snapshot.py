import copy

import pytest

from tools.build_health_snapshot import normalize


def sample():
    return {'cik':1,'facts':{'us-gaap':{'Assets':{'units':{'USD':[
        {'end':'2025-12-31','filed':'2026-02-01','form':'10-K','val':100,'accn':'original'},
        {'end':'2025-12-31','filed':'2026-04-01','form':'10-K/A','val':110,'accn':'amended'},
        {'end':'2025-12-31','filed':'2026-08-01','form':'10-K/A','val':999,'accn':'future'},
        {'start':'2025-01-01','end':'2025-12-31','filed':'2026-03-01','form':'10-K','val':500,'accn':'duration'},
    ]}}}}}


def test_instant_fact_cutoff_and_amendment_selection():
    raw=sample()
    row=normalize(raw,1,'2025-12-31','2026-05-01')
    assert row['metrics']['assets_usd']==110
    assert row['sources']['assets_usd']['accession']=='amended'
    assert row['metrics']['cash_usd'] is None
    assert normalize(raw,1,'2025-12-31','2026-03-01')['metrics']['assets_usd']==100
    assert normalize(raw,1,'2024-12-31','2026-05-01')['metrics']['assets_usd'] is None


@pytest.mark.parametrize('value',[True,float('nan'),float('inf'),'100',None])
def test_ineligible_value_is_missing(value):
    raw=sample()
    raw['facts']['us-gaap']['Assets']['units']['USD']=[{'end':'2025-12-31','filed':'2026-02-01','form':'10-K','val':value}]
    assert normalize(raw,1,'2025-12-31','2026-05-01')['metrics']['assets_usd'] is None


def test_identity_negative_equity_and_no_quarter_construction():
    raw=copy.deepcopy(sample())
    with pytest.raises(ValueError,match='CIK'):
        normalize(raw,2,'2025-12-31','2026-05-01')
    raw['facts']['us-gaap']['StockholdersEquity']={'units':{'USD':[{'end':'2025-12-31','filed':'2026-02-01','form':'10-K','val':-20}]}}
    raw['facts']['us-gaap']['Assets']['units']['USD']=[{'end':'2025-12-31','filed':'2026-02-01','form':'10-Q','val':80}]
    row=normalize(raw,1,'2025-12-31','2026-05-01')
    assert row['metrics']['assets_usd'] is None
    assert row['metrics']['equity_usd']==-20
