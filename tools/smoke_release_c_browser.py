"""Release C source-only Chromium journeys: Models/Methods, selection, source integrity.

Public runs deterministic synthetic examples. Owner-only history uses mocks; this is
NOT signed-in MFA, real Alpaca permission, live Render or Cloudflare acceptance.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'public/index.html').read_text(encoding='utf-8')


async def public(page, width: int) -> None:
    errors = []
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    await page.set_content(HTML, wait_until='load')
    await page.locator('#qf-v20-navigation [data-page="models"]').click()
    assert await page.locator('.tabpage.active').get_attribute('id') == 'page-models'
    assert await page.locator('#page-models [data-qf-model]').count() == 4
    assert await page.locator('#page-models [data-qf-c22-phase]').count() == 3
    assert 'Synthetic' in await page.locator('#qf-c22-model-output').inner_text()
    assert 'Brier score' in await page.locator('#qf-c22-model-output').inner_text()
    await page.locator('[data-qf-c22-phase="evaluation"]').click()
    assert await page.get_by_role('heading',name='Chronological held-out evaluation',exact=True).locator('..').locator('tbody tr').count() == 3
    assert 'calibration' in (await page.locator('#qf-c22-model-output').inner_text()).lower()
    await page.locator('[data-qf-c22-phase="method"]').click()
    assert 'L2-regularized' in await page.locator('#qf-c22-model-output').inner_text()
    await page.locator('#page-models [data-qf-model="risk"]').click()
    assert 'rolling volatility' in (await page.locator('#qf-c22-model-output').inner_text()).lower()
    assert await page.locator('#qf-c22-model-output svg').count() >= 1
    await page.locator('[data-qf-c22-phase="evaluation"]').click()
    assert 'Moving-block bootstrap' in await page.locator('#qf-c22-model-output').inner_text()
    await page.locator('#page-models [data-qf-model="valuation"]').click()
    assert 'Cash-flow scenario sensitivity' in await page.locator('#qf-c22-model-output').inner_text()
    assert await page.locator('#qf-c22-model-output tbody tr').count() == 3
    await page.locator('[data-qf-c22-phase="evaluation"]').click()
    assert await page.locator('#qf-c22-model-output tbody tr').count() == 4
    await page.locator('#page-models [data-qf-model="strategy"]').click()
    assert await page.locator('#qf-c22-model-output svg').count() >= 1
    assert 'Buy and hold' in await page.locator('#qf-c22-model-output').inner_text()
    assert await page.locator('#page-models details:visible').count() == 0
    await page.locator('#qf-v20-navigation [data-page="methods"]').click()
    assert await page.locator('.tabpage.active').get_attribute('id') == 'page-methods'
    assert await page.locator('#page-methods [data-qf-c22-method]').count() == 4
    assert 'Why QuantForge exists' in await page.locator('#qf-c22-method-content').inner_text()
    await page.locator('[data-qf-c22-method="data"]').click()
    assert '94 issuers' in await page.locator('#qf-c22-method-content').inner_text()
    assert 'tools/build_public_sec_snapshot.py' in await page.locator('#qf-c22-method-content').inner_text() or await page.locator('#qf-c22-method-content a').count() >= 3
    await page.locator('[data-qf-c22-method="statistical"]').click()
    assert 'TF-IDF' not in await page.locator('#qf-c22-method-content').inner_text()
    assert 'Brier' in await page.locator('#qf-c22-method-content').inner_text()
    await page.locator('[data-qf-c22-method="engineering"]').click()
    assert 'MFA' in await page.locator('#qf-c22-method-content').inner_text()
    assert await page.locator('#page-methods details:visible').count() == 0
    await page.locator('#qf-v20-navigation [data-page="explore"]').click()
    await page.locator('#qf-v20-search').fill('Apple')
    await page.locator('#qf-v20-search-results [data-qf27-symbol="AAPL"]').click()
    await page.locator('#qf-v20-navigation [data-page="models"]').click()
    assert 'Apple (AAPL)' in await page.locator('#qf-v20-model-selected').inner_text()
    assert 'Synthetic' in await page.locator('#qf-c22-model-output').inner_text()
    assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors, errors[:4]
    print(f'Release C public {width}px Models/Methods/selection/no-accordion PASS', flush=True)


async def private_mock(page) -> None:
    errors = []
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    await page.set_content(HTML, wait_until='load')
    await page.evaluate('''() => {
      window.qfTestCalls=[];
      const dates=[];const start=Date.UTC(2024,0,2);
      for(let i=0;dates.length<250;i++){
        const d=new Date(start+i*86400000);if(d.getUTCDay()===0||d.getUTCDay()===6)continue;
        dates.push(d.toISOString().slice(0,10));
      }
      window.fetch=async url=>{
        const path=String(url);window.qfTestCalls.push(path);
        const q=new URLSearchParams(path.split('?')[1]||'');
        if(path.includes('private/history-single')){
          const symbol=q.get('symbol');
          return {ok:true,json:async()=>({licensed_private:true,symbol,ohlcv_available:false,
             observations:dates.map((d,i)=>({date:d,close:150*Math.exp(i*.0004+.02*Math.sin(i/9))})),
             source:'MOCKED entitled observed close history',sessions_per_year:252})};
        }
        if(String(url).includes('private/assets'))return {ok:true,json:async()=>({licensed_private:true,items:[{symbol:'AAPL',name:'Apple',asset_class:'us_equity'}]})};
        if(path.includes('private/news-research'))return {ok:false,json:async()=>({detail:'Mocked news outage'})};
        if(path.includes('private/state'))return {ok:false,json:async()=>({detail:'Mocked portfolio database offline'})};
        throw Error('Unexpected private test request '+path);
      };
      document.getElementById('private-signed').hidden=false;
    }''')
    await page.wait_for_timeout(250)
    await page.locator('#qf-v20-navigation [data-page="models"]').click()
    assert 'Authenticated historical market observations' in await page.locator('#qf-c22-model-output').inner_text()
    assert 'synthetic' not in (await page.locator('#qf-c22-model-output').inner_text()).lower()
    await page.locator('#page-models [data-qf-model="risk"]').click()
    assert 'Risk needs' not in await page.locator('#qf-c22-model-output').inner_text()
    await page.evaluate('''() => {
      window.fetch=async url=>{
        if(String(url).includes('history-single'))return {ok:false,json:async()=>({detail:'Deliberate owner price provider outage'})};
        if(String(url).includes('private/assets'))return {ok:true,json:async()=>({licensed_private:true,items:[{symbol:'AAPL',name:'Apple',asset_class:'us_equity'}]})};
        if(String(url).includes('news'))return {ok:false,json:async()=>({detail:'News outage'})};
        if(String(url).includes('private/state'))return {ok:false,json:async()=>({detail:'Portfolio outage'})};
        throw Error('Unexpected '+url);
      };
    }''')
    await page.locator('#qf-v20-navigation [data-page="explore"]').click()
    await page.locator('#qf-v20-search').fill('Apple')
    await page.locator('#qf-v20-search-results [data-qf27-symbol="AAPL"]').click()
    await page.wait_for_timeout(190)
    await page.locator('#qf-v20-navigation [data-page="models"]').click()
    assert 'Not enough eligible evidence' in await page.locator('#qf-c22-model-output').inner_text()
    assert 'Synthetic' not in await page.locator('#qf-c22-model-output').inner_text()
    assert await page.locator('#qf-v20-financial-kpis').count() == 1
    assert not errors, errors[:4]
    print('Release C mocked MFA private price vs provider outage isolation PASS', flush=True)


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, executable_path=os.getenv('QF_CHROMIUM_PATH') or None)
        try:
            for width in (1440, 390):
                page = await browser.new_page(viewport={'width': width, 'height': 900})
                await public(page, width)
                if width == 1440 and os.getenv('QF_RELEASE_C_SCREENSHOT'):
                    await page.screenshot(path=os.environ['QF_RELEASE_C_SCREENSHOT'], full_page=False)
                await page.close()
            page = await browser.new_page(viewport={'width': 1280, 'height': 820})
            await private_mock(page)
            await page.close()
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
