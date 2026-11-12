"""Completed shared-engine acceptance. All owner activity uses isolated offline fixtures."""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import math
import os
from pathlib import Path

from browser_product_contract import pick_compare
from playwright.async_api import async_playwright, expect
from smoke_rebuild_browser import FIXTURE, HTML

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('QF_SCREENSHOT_DIR', str(ROOT / 'outputs/rebuild-review')))
CSP = next(line.strip().split(': ', 1)[1] for line in (ROOT / 'public/_headers').read_text(encoding='utf-8').splitlines() if 'Content-Security-Policy:' in line)
EXTEND = r'''() => {
 const original=window.fetch;
 window.fetch=async(url,options={})=>{
  const path=String(url),response=(data,ok=true,status=200)=>({ok,status,json:async()=>data});
  if(path.includes('private/news-research')){const symbol=new URLSearchParams(path.split('?')[1]).get('symbols');return response({rows:[{symbol,articles:50,tone:'Neutral',topics:['Earnings'],headlines:Array.from({length:50},(_,i)=>({headline:'OFFLINE fixture: dated earnings context '+i,created_at:'2026-10-09T15:00:00Z',source:'MOCK news',url:'https://example.invalid/headline',tone:'Neutral'}))}]});}
  if(path.includes('private/sec/company')){const symbol=new URLSearchParams(path.split('?')[1]).get('symbol');return response(window.QFPublishedSEC.companies.find(c=>c.symbol===symbol)||{symbol,annual:[]});}
  if(path.includes('private/valuation-capital')){const symbol=new URLSearchParams(path.split('?')[1]).get('symbol');return response({symbol,shares:{value:1000000000,periodEnd:'2026-06-30',tag:'EntityCommonStockSharesOutstanding'},source:'MOCK SEC capital fixture',debtCashSamePeriod:false});}
  if(path.includes('private/valuation-snapshot')||path.includes('private/capital')){
   window.qfMockRequests.push(path);const body=JSON.parse(options.body);
   if(body.expected_version!==window.qfMockVersion)return response({detail:'Version conflict'},false,409);
   const account=window.qfMockOwner;
   if(path.includes('private/capital-preview')){const delta=Number(body.amount)*(body.action==='deposit'?1:-1);return response({preview:{action:body.action,amount:Number(body.amount),cash_before:account.cash,cash_after:account.cash+delta,contributions_after:account.initial_cash+delta},version:qfMockVersion});}
   if(path.includes('private/capital')){const delta=Number(body.amount)*(body.action==='deposit'?1:-1);account.cash+=delta;account.initial_cash+=delta;}
   else{const marks=account.valuations||(account.valuations=[]),value=account.cash+Object.values(account.holdings).reduce((sum,q)=>sum+q*300,0);marks.push({at:new Date(Date.UTC(2026,9,1+marks.length)).toISOString(),value,cash:account.cash,net_contributions:account.initial_cash,pnl:value-account.initial_cash,source:'MOCK server-verified mark'});}
   window.qfMockVersion++;return response({portfolio:account,version:window.qfMockVersion,paper_only:true});
  }
  return original(url,options);
 };
}'''


def factor_csv():
    dates = []
    current = dt.date(2024, 10, 14)
    while len(dates) < 520:
        if current.weekday() < 5:
            dates.append(current)
        current += dt.timedelta(days=1)
    rows = [',Mkt-RF,SMB,HML,RF']
    rows += [f'{day:%Y%m%d},{0.7 * math.sin(i * .17):.5f},'
             f'{0.5 * math.cos(i * .13):.5f},{0.4 * math.sin(i * .29):.5f},0.01'
             for i, day in enumerate(dates)]
    return '\n'.join(rows).encode()


def revision_fixture():
    snapshot = json.loads((ROOT / 'web/site/sec_snapshot.json').read_text(encoding='utf-8'))
    issuers = []
    for company in snapshot['companies']:
        if company['symbol'] not in ('MSFT', 'AAPL', 'NVDA'):
            continue
        periods = []
        for year in (2023, 2024, 2025):
            facts = {}
            for key, value, tag in [
                ('revenue_usd', 1000 + (year - 2023) * 100, 'RevenueFromContractWithCustomerExcludingAssessedTax'),
                ('operating_cash_flow_usd', 300, 'NetCashProvidedByUsedInOperatingActivities'),
                ('capex_usd', 100, 'PaymentsToAcquirePropertyPlantAndEquipment'),
            ]:
                facts[key] = [{'start': f'{year}-01-01', 'filed': f'{year + 1}-03-01',
                               'accession': f'{company["cik"]:010d}-{str(year + 1)[2:]}-000001',
                               'tag': tag, 'tag_priority': 0, 'value': value}]
            periods.append({'fiscal_end': f'{year}-12-31', 'revisions': facts})
        issuers.append({'symbol': company['symbol'], 'cik': company['cik'], 'annual': periods})
    return json.dumps({'schema': 'quantforge.sec.filing-revisions.v9.8',
                       'as_of': '2026-10-09', 'companies': issuers}).encode()


async def capture(page, name):
    await page.evaluate("window.scrollTo({top:0,left:0,behavior:'instant'})")
    await page.screenshot(path=str(OUT / (name + '.png')), full_page=True)
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'), name


async def journey(browser, engine, width):
    page = await browser.new_page(viewport={'width': width, 'height': 900 if width == 1440 else 844})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    async def isolate(route):
        if route.request.is_navigation_request() and route.request.url == 'https://quantforge.test/':
            await route.fulfill(status=200, content_type='text/html', body=HTML,
                                headers={'Content-Security-Policy': CSP})
        else:
            await route.abort()
    await page.route('**/*', isolate)
    await page.goto('https://quantforge.test/', wait_until='load')
    for mode in ('public', 'private'):
        if mode == 'private':
            await page.evaluate(FIXTURE)
            await page.evaluate(EXTEND)
            await page.locator('#qf-v20-mode').click()
            await page.locator('#private-email').fill('offline' + '@' + 'example.invalid')
            await page.locator('#private-password').fill('offline-fixture-password')
            await page.locator('#private-login-submit').click()
            await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE')
            await expect(page.locator('#qf-v20-source-badge')).to_contain_text('Observed')
            assert await page.locator('#qf-v20-news').count() == 0
        prefix = f'v25-{engine}-{mode}-{width}'
        await page.locator('#qf-v20-navigation [data-page="explore"]').click()
        await page.locator('#qf27-analyze').click()
        await page.locator('#qf25-company table').first.wait_for()
        assert 'undefined' not in await page.locator('#qf25-company').inner_text()
        await capture(page, prefix + '-connected-research')
        await page.locator('#qf-v20-navigation [data-page="compare"]').click()
        for symbol in ('AAPL', 'NVDA'):
            await pick_compare(page, symbol)
        await page.locator('[data-qf28-compare="financial"]').click()
        await page.locator('#qf25-peers svg').first.wait_for()
        assert 'shared ratios' in await page.locator('#qf25-peers').inner_text()
        await capture(page, prefix + '-financial-peers')
        await page.locator('#qf-v20-navigation [data-page="models"]').click()
        await page.locator('[data-qf-model="strategy"]').click()
        await page.locator('[data-qf25-run="strategy"]').click()
        await page.locator('#qf25-strategy svg[data-qf25-chart]').wait_for()
        chart = page.locator('#qf25-strategy svg[data-qf25-chart]').first
        await chart.focus()
        await page.keyboard.press('Home')
        assert '2025' in await page.locator('#qf25-strategy').inner_text()
        assert 'Leave-one-window-out' in await page.locator('#qf25-strategy').inner_text()
        await capture(page, prefix + '-strategy-robustness')
        await page.locator('[data-qf-model="valuation"]').click()
        await page.locator('#qf25-forecast-run').click()
        await page.locator('#qf25-forecast table').wait_for()
        assert 'Year 5' in await page.locator('#qf25-forecast').inner_text()
        await page.locator('[data-qf25-run="valuation"]').click()
        if mode == 'private':
            await page.locator('#qf25-valuation table').wait_for()
            await expect(page.locator('#qf25-valuation')).to_contain_text('300,000,000,000')
        else:
            await expect(page.locator('#qf25-valuation')).to_contain_text('authenticated quotes')
        await capture(page, prefix + '-revenue-scenarios')
        await page.locator('#qf-v20-navigation [data-page="methods"]').click()
        await page.locator('[data-qf-c22-method="data"]').click()
        await page.locator('#qf25-factor-file').set_input_files({'name': 'offline-ff3.csv', 'mimeType': 'text/csv', 'buffer': factor_csv()})
        await expect(page.locator('#qf25-import-status')).to_contain_text('Parsed independent')
        await page.locator('#qf25-archive-file').set_input_files({'name': 'offline-revisions.json', 'mimeType': 'application/json', 'buffer': revision_fixture()})
        await expect(page.locator('#qf25-import-status')).to_contain_text('Validated revision')
        await page.locator('[data-qf25-run="data"]').click()
        await page.locator('#qf25-data table').first.wait_for()
        assert 'undefined' not in await page.locator('#qf25-data').inner_text()
        assert 'Revision archive replay' in await page.locator('#qf25-data').inner_text()
        await capture(page, prefix + '-filing-revision-audit')
        await page.locator('#qf-v20-navigation [data-page="models"]').click()
        await page.locator('[data-qf-model="risk"]').click()
        await page.locator('[data-qf25-run="factors"]').click()
        await page.locator('#qf25-factors table').wait_for()
        assert 'holdout RMSE' in await page.locator('#qf25-factors').inner_text()
        assert 'undefined' not in await page.locator('#qf25-factors').inner_text()
        await capture(page, prefix + '-proxy-and-independent-factors')
        await page.locator('#qf-v20-navigation [data-page="portfolio"]').click()
        await page.locator('[data-qf-portfolio="analysis"]').click()
        await page.locator('[data-qf25-run="portfolio"]').click()
        await page.locator('#qf25-portfolio svg').first.wait_for()
        assert '1,800 seeded paths' in await page.locator('#qf25-portfolio').inner_text()
        await capture(page, prefix + '-allocation-scenarios')
        if mode == 'private':
            await page.locator('[data-qf-portfolio="overview"]').click()
            await page.locator('#qf25-record-mark').click()
            await expect(page.locator('#qf25-account-chart')).to_contain_text('1 recorded marks')
            await page.locator('#qf28-fund').click()
            await page.locator('#qf25-capital-amount').fill('500')
            await page.locator('#qf25-capital-submit').click()
            await page.locator('#qf28-funding-confirm').click()
            await expect(page.locator('#qf27-account-summary')).to_contain_text('$3,000.00')
            await page.locator('#qf25-record-mark').click()
            await expect(page.locator('#qf25-account-chart')).to_contain_text('2 recorded marks')
            assert 'paper P&L $0.00' in await page.locator('#qf25-account-chart').inner_text()
            await capture(page, prefix + '-recorded-account-history')
            await page.locator('#qf-v20-navigation [data-page="explore"]').click()
            await page.locator('[data-qf27-explore="research"]').click()
            await page.locator('#qf-v23-note').fill('Original offline note')
            await page.locator('#qf-v23-save').click()
            await expect(page.locator('#qf-v23-note-list')).to_contain_text('Original offline note')
            await page.locator('[data-qf-v23-edit="0"]').click()
            await page.locator('#qf-v23-note').fill('Edited offline note')
            await page.locator('#qf-v23-save').click()
            await expect(page.locator('#qf-v23-note-list')).to_contain_text('Edited offline note')
            assert await page.evaluate('window.qfMockOwner.notes.length') == 2
            await expect(page.locator('#qf-v23-note-list')).to_contain_text('Original offline note')
            await page.locator('#qf-v20-navigation [data-page="compare"]').click()
            await page.locator('#qf-v20-compare-search').fill('Offline')
            await expect(page.locator('#qf27-compare-options [data-qf27-symbol="TEST"]')).to_have_count(1)
            await pick_compare(page, 'TEST')
            assert 'TEST' in await page.locator('#qf-v20-compare-chips').inner_text()
            await page.locator('#qf24-switch-mode').click()
            assert 'TEST' not in await page.locator('#qf-v20-compare-chips').inner_text()
            assert 'Edited offline note' not in await page.locator('body').inner_text()
            assert 'Server-verified valuation recorded.' not in await page.locator('body').inner_text()
        # A career reviewer can trace each claim without private source access.
        await page.locator('#qf-v20-navigation [data-page="methods"]').click()
        await page.locator('[data-qf-c22-method="overview"]').click()
        await page.locator('#qf-c22-method-content [data-qf26-tour="engineering"]').click()
        await expect(page.locator('.qf26-pipeline li')).to_have_count(4)
        await expect(page.locator('[data-qf26-discipline]')).to_have_count(7)
        for discipline in ('data', 'analysis', 'ml', 'statistics', 'finance', 'optimization', 'software'):
            await page.locator(f'[data-qf26-discipline="{discipline}"]').click()
            await expect(page.locator('#qf26-evidence-detail')).to_contain_text('Reproducible checks')
            assert await page.locator('#qf26-evidence-detail code').count() >= 2
        await page.locator('[data-qf26-discipline="statistics"]').click()
        await capture(page, prefix + '-technical-evidence')
        await page.locator('[data-qf26-open="statistics"]').click()
        chart = page.locator('#qf-c22-model-output svg[data-qf26-chart]').first
        await chart.focus()
        await page.keyboard.press('Home')
        start = await page.locator('#qf-c22-model-output .qf26-readout').first.inner_text()
        await page.keyboard.press('End')
        assert start != await page.locator('#qf-c22-model-output .qf26-readout').first.inner_text()
        await expect(page.locator('#qf-c22-model-output .qf26-readout').first).to_contain_text('%')
        assert await page.locator('#qf-c22-model-output svg[data-qf26-chart]').count() == 2
        await capture(page, prefix + '-risk-scaled-plots')
        assert not errors, errors[:5]
    await page.close()
    print(f'{engine} {width}px deep engines / optional evidence / snapshot funding accounting / note editing / mode isolation PASS', flush=True)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    engines = os.environ.get('QF_TEST_BROWSERS', 'chromium,firefox,webkit').split(',')
    async with async_playwright() as pw:
        for engine in engines:
            browser = await getattr(pw, engine).launch(headless=True)
            try:
                for width in (1440, 390):
                    await journey(browser, engine, width)
            finally:
                await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
