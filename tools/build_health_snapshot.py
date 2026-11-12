"""Normalize cached SEC instant facts. No requests; no invented missing values."""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

FIELDS = {
    'cash_usd': ('CashAndCashEquivalentsAtCarryingValue',),
    'assets_usd': ('Assets',),
    'liabilities_usd': ('Liabilities',),
    'current_assets_usd': ('AssetsCurrent',),
    'current_liabilities_usd': ('LiabilitiesCurrent',),
    'equity_usd': ('StockholdersEquity',),
    'long_term_debt_current_usd': ('LongTermDebtCurrent',),
    'long_term_debt_noncurrent_usd': ('LongTermDebtNoncurrent',),
}

def normalize(raw: dict, cik: int, period: str, cutoff: str) -> dict:
    if raw.get('cik') != cik:
        raise ValueError('SEC CIK mismatch')
    dt.date.fromisoformat(period)
    dt.date.fromisoformat(cutoff)
    gaap=raw.get('facts',{}).get('us-gaap',{})
    row={'fiscal_end':period,'cutoff':cutoff,'metrics':{},'sources':{}}
    for key,tags in FIELDS.items():
        eligible=[]
        for tag in tags:
            for fact in gaap.get(tag,{}).get('units',{}).get('USD',[]):
                value=fact.get('val')
                if (fact.get('end') != period or fact.get('start') or fact.get('form') not in ('10-K','10-K/A')
                    or not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value)
                    or abs(value)>=1e15):
                    continue
                try:
                    filed=dt.date.fromisoformat(fact.get('filed',''))
                except (TypeError,ValueError):
                    continue
                if not dt.date.fromisoformat(period)<=filed<=dt.date.fromisoformat(cutoff):
                    continue
                eligible.append((fact['filed'],fact.get('accn',''),tag,fact))
        chosen=max(eligible,key=lambda t:t[:3]) if eligible else None
        row['metrics'][key]=chosen[3]['val'] if chosen else None
        if chosen:
            row['sources'][key]={'filed':chosen[0],'accession':chosen[1],'tag':chosen[2]}
    return row

def build(root: Path) -> dict:
    snapshot=json.loads((root/'web/site/sec_snapshot.json').read_text(encoding='utf-8'))
    result={'method':'Instant USD facts at published fiscal ends; 10-K/10-K/A; latest filing <= issuer cutoff. No quarterly/TTM construction. Debt fields are components, not complete total debt.','companies':{}}
    for company in snapshot['companies']:
        cache=root/f"data/sec_companyfacts_cache/CIK{company['cik']:010d}.json"
        if not cache.is_file():
            continue
        raw=json.loads(cache.read_text(encoding='utf-8'))
        cutoff=company.get('as_of') or snapshot['as_of']
        rows=[normalize(raw,company['cik'],r['fiscal_end'],cutoff) for r in company['annual']]
        result['companies'][company['symbol']]={'source_url':company['source_url'],'cik':company['cik'],'cutoff':cutoff,'annual':rows}
    return result

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    out=root/'web/site/sec_health_snapshot.json'
    out.write_text(json.dumps(build(root),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('Wrote cached SEC health facts:',out)
