"""Release B: offline Chromium UX, math and unavailable-provider acceptance.
Does not authenticate to real MFA, Alpaca, Supabase or Cloudflare.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from browser_product_contract import navigate, pick_compare
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'public/index.html').read_text(encoding='utf-8')


async def public(page, width: int) -> None:
    errors = []
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    await page.set_content(HTML, wait_until='load')
    await navigate(page, 'compare')
    assert await page.locator('.tabpage.active').get_attribute('id') == 'page-compare'
    assert await page.locator('#qf-v20-compare-chips button').count() == 1
    await pick_compare(page, 'AAPL')
    assert await page.locator('#qf-v20-compare-chips button').count() == 2
    await page.locator('#qf-v20-compare-run').click()
    assert await page.locator('#qf-b21-compare-chart svg').count() == 1
    assert 'simulated' in (await page.locator('#qf-b21-compare-provenance').inner_text()).lower()
    assert await page.locator('#qf-b21-risk-table tbody tr').count() == 2
    assert await page.locator('#qf-b21-finance-table tbody tr').count() == 2
    assert await page.locator('#qf-b21-correlation tbody tr').count() == 2
    assert not await page.locator('#qf-b21-compare-export').is_disabled()
    await page.locator('[data-qf-b21-sort="growth"]').click()
    await page.locator('[data-qf28-compare="market"]').click()
    await page.locator('#qf-b21-compare-chart svg').focus()
    before = await page.locator('#qf-b21-compare-chart-cursor').inner_text()
    await page.locator('#qf-b21-compare-chart svg').press('ArrowLeft')
    assert await page.locator('#qf-b21-compare-chart-cursor').inner_text() != before
    await navigate(page, 'portfolio')
    assert await page.locator('#qf-b21-overview-chart svg').count() == 1
    assert await page.locator('#page-portfolio details').count() == 0
    await page.locator('[data-qf-portfolio="whatif"]').click()
    assert await page.locator('#qf-b21-weight-controls input[type="range"]').count() == 3
    first = page.locator('#qf-b21-weight-controls input[type="range"]').first
    await first.fill('60')
    assert 'Total 100%' in await page.locator('#qf-b21-weights-total').inner_text()
    weights = await page.locator('#qf-b21-weight-controls input[type="range"]').evaluate_all(
        'els => els.map(e=>Number(e.value))')
    assert sum(weights) == 100, weights
    assert await page.locator('#qf-b21-whatif-chart svg').count() == 1
    assert await page.locator('#qf-b21-portfolio-export').is_enabled()
    await page.locator('#qf-b21-lower-risk').click()
    assert 'minimum-variance experiment' in (await page.locator('#qf-b21-optimizer-output').inner_text()).lower()
    await page.locator('#qf-b21-apply-optimizer').click()
    assert await page.locator('#qf-b21-whatif-chart svg').count() == 1
    await page.locator('[data-qf-portfolio="analysis"]').click()
    assert await page.locator('#qf-b21-analysis-corr tbody tr').count() == 2
    assert 'Worst observed sample day' in await page.locator('#qf-b21-analysis-stress').inner_text()
    assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    # Any edited universe must invalidate previously calculated prices and leave SEC available.
    await navigate(page, 'compare')
    await pick_compare(page, 'NVDA')
    assert await page.locator('#qf-b21-compare-export').is_disabled()
    assert await page.locator('#qf-b21-finance-table tbody tr').count() == 0  # stale SEC rows invalidated
    assert 'Selection changed' in await page.locator('#qf-b21-compare-state').inner_text()
    assert not errors, errors[:3]
    print(f'Release B public {width}px compare/chart/portfolio/keyboard/stale acceptance PASS', flush=True)


async def private_mock(page) -> None:
    errors = []
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    await page.set_content(HTML, wait_until='load')
    await page.evaluate('''() => {
      const dates=Array.from({length:95},(_,i)=>new Date(Date.UTC(2026,5,1+i)).toISOString().slice(0,10));
      window.qfTestRequests=[];
      window.fetch=async url=>{
        const path=String(url);window.qfTestRequests.push(path);
        if(path.includes('/api/health'))return {ok:true,json:async()=>({status:'ok'})};
        if(path.includes('auth/login'))return {ok:true,json:async()=>({signed_in:true})};
        if(path.includes('private/assets'))return {ok:true,json:async()=>({licensed_private:true,items:QFPublishedSEC.companies.filter(c=>['MSFT','AAPL','NVDA'].includes(c.symbol)).map(c=>({symbol:c.symbol,name:c.name,asset_class:'us_equity'}))})};
        const params=new URLSearchParams((path.split('?')[1]||''));
        if(path.includes('private/history?')){
          const symbols=params.get('symbols').split(',');
          return {ok:true,json:async()=>({licensed_private:true,symbols,dates,
            closes:Object.fromEntries(symbols.map((s,j)=>[s,dates.map((_,i)=>101+j*18+i*0.28+Math.sin(i*.3+j)*2)])),
            sessions_per_year:252,source:'MOCKED Alpaca owner history',coverage:'test fixture; not a production feed'})};
        }
        if(path.includes('private/history-single')){
          const symbol=params.get('symbol');
          return {ok:true,json:async()=>({licensed_private:true,symbol,ohlcv_available:false,observations:dates.map((d,i)=>({date:d,close:100+i*0.3})),source:'MOCKED owner observation',coverage:'test data'})};
        }
        if(path.includes('private/state')){
          return {ok:true,json:async()=>({version:4,portfolio:{cash:1537.8,initial_cash:2500,holdings:{MSFT:2.5,AAPL:1.5}}})};
        }
        if(path.includes('private/quotes?')){
          const symbols=params.get('symbols').split(',');
          return {ok:true,json:async()=>({quotes:symbols.map((symbol,i)=>({symbol,price:300+i*20,
            timestamp:new Date().toISOString(),synthetic:false}))})};
        }
        if(path.includes('news-research'))return {ok:false,json:async()=>({detail:'Test news endpoint unavailable'})};
        throw Error('Unexpected private test route '+path);
      };
    }''')
    await page.locator('#qf-v20-mode').click()
    await page.locator('#private-email').fill('offline' + '@' + 'example.invalid')
    await page.locator('#private-password').fill('offline-fixture-password')
    await page.locator('#private-login-submit').click()
    await page.wait_for_function('window.QFPrivateBridgeV23.ready()')
    await page.wait_for_timeout(190)
    await navigate(page, 'compare')
    await pick_compare(page, 'AAPL')
    await page.locator('#qf-v20-compare-run').click()
    await page.wait_for_timeout(160)
    assert await page.locator('#qf-b21-compare-chart svg').count() == 1
    assert 'MOCKED Alpaca' in await page.locator('#qf-b21-compare-provenance').inner_text()
    assert 'synthetic' not in (await page.locator('#qf-b21-compare-provenance').inner_text()).lower()
    await navigate(page, 'portfolio')
    await page.wait_for_timeout(180)
    assert await page.locator('#qf-b21-owner-account').is_visible()
    assert '1,537.80' in await page.locator('#qf-b21-owner-account-table').inner_text(), await page.locator('#qf-b21-owner-account-table').inner_text()
    assert 'Cumulative paper P&L' in await page.locator('#qf27-account-summary').inner_text()
    assert not errors, errors[:3]
    print('Release B mocked authenticated history/state and isolated news failures PASS', flush=True)
    # Force an outage and a selection change; do not use public synthetic prices as fallback.
    await page.evaluate('''() => {
      window.fetch=async url=>{
       if(String(url).includes('private/assets'))return {ok:true,json:async()=>({licensed_private:true,items:[{symbol:'NVDA',name:'NVIDIA',asset_class:'us_equity'}]})};
       if(String(url).includes('private/history?'))return {ok:false,json:async()=>({detail:'Deliberate provider outage'})};
       if(String(url).includes('private/state'))return {ok:false,json:async()=>({detail:'Test database offline'})};
       if(String(url).includes('history-single'))return {ok:false,json:async()=>({detail:'Test price feed offline'})};
       if(String(url).includes('news'))return {ok:false,json:async()=>({detail:'Test news offline'})};
       throw Error('Unexpected '+url);
      };
    }''')
    await navigate(page, 'compare')
    await pick_compare(page, 'NVDA')
    await page.locator('#qf-v20-compare-run').click()
    assert 'History unavailable' in await page.locator('#qf-b21-compare-state').inner_text()
    assert await page.locator('#qf-b21-compare-chart svg').count() == 0
    assert await page.locator('#qf-b21-finance-table tbody tr').count() == 3
    assert not errors, errors[:3]
    print('Release B private outage: withhold price/chart, retain independent SEC metrics PASS',flush=True)


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=os.getenv('QF_CHROMIUM_PATH') or None)
        try:
            for width in (1440, 390):
                page = await browser.new_page(viewport={'width':width,'height':900},accept_downloads=True)
                await public(page,width)
                await page.close()
            page=await browser.new_page(viewport={'width':1280,'height':820},accept_downloads=True)
            await private_mock(page)
            await page.close()
        finally:
            await browser.close()

if __name__=='__main__':
    asyncio.run(main())
