"""Offline product acceptance and screenshot matrix. Never uses live credentials or services."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from browser_product_contract import PRODUCT_TRADES, pick_compare, virtual_buy
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('QF_SCREENSHOT_DIR', str(ROOT / 'outputs/rebuild-review')))
HTML = (ROOT / 'public/index.html').read_text(encoding='utf-8')
FIXTURE = r'''() => {
 const dates=[];
 for(let i=0;dates.length<520;i++){const d=new Date(Date.UTC(2024,9,14+i));if(d.getUTCDay()!==0&&d.getUTCDay()!==6)dates.push(d.toISOString().slice(0,10));}
 window.qfMockRequests=[];window.qfMockVersion=2;
 window.qfMockOwner={cash:2500,initial_cash:2500,holdings:{MSFT:1},watchlist:[],notes:[],trades:[]};
 const levels=s=>dates.map((_,i)=>100*Math.exp(i*.0003+.08*Math.sin(i/(13+s.length))+.02*Math.cos(i/3)));
 window.fetch=async(url,options={})=>{
  const p=String(url);window.qfMockRequests.push(p);const q=new URLSearchParams(p.split('?')[1]||'');
  const response=(data,ok=true,status=200)=>({ok,status,json:async()=>data});
  if(p.includes('/api/health'))return response({status:'ok'});
  if(p.includes('auth/login'))return response({signed_in:true});
  if(p.includes('auth/logout'))return response({signed_in:false});
  if(p.includes('private/state'))return response({portfolio:window.qfMockOwner,version:window.qfMockVersion});
  if(p.includes('private/quotes'))return response({quotes:(q.get('symbols')||'').split(',').map(s=>({symbol:s,price:300,synthetic:false,venue:'MOCK',timestamp:new Date().toISOString()}))});
  if(p.includes('private/history-single')){const s=q.get('symbol'),values=levels(s);return response({symbol:s,licensed_private:true,observations:dates.map((date,i)=>({date,close:values[i]})),ohlcv_available:false,source:'MOCK historical provider fixture',coverage:'offline fixture, no live entitlement verified',sessions_per_year:252});}
  if(p.includes('private/history?')){const symbols=q.get('symbols').split(',');return response({symbols,dates,closes:Object.fromEntries(symbols.map(s=>[s,levels(s)])),source:'MOCK historical provider fixture',licensed_private:true,sessions_per_year:252});}
  if(p.includes('private/news-research'))return response({detail:'No news entitlement'},false,422);
  if(p.includes('private/notes')){const input=JSON.parse(options.body);if(input.expected_version!==window.qfMockVersion)return response({detail:'Version changed'},false,409);window.qfMockOwner.notes=input.notes;window.qfMockVersion++;return response({portfolio:window.qfMockOwner,version:window.qfMockVersion});}
  if(p.includes('private/trade')){const input=JSON.parse(options.body);if(input.expected_version!==window.qfMockVersion)return response({detail:'Version changed'},false,409);window.qfMockOwner.holdings[input.symbol]=2;window.qfMockOwner.cash-=Number(input.amount);window.qfMockOwner.trades.unshift({symbol:input.symbol,side:input.side,units:2,at:'2026-10-09'});window.qfMockVersion++;return response({portfolio:window.qfMockOwner,version:window.qfMockVersion,paper_only:true});}
  if(p.includes('private/assets'))return response({licensed_private:true,total:4,items:[{symbol:'AAPL',name:'Apple',asset_class:'us_equity'},{symbol:'NVDA',name:'NVIDIA',asset_class:'us_equity'},{symbol:'MSFT',name:'Microsoft',asset_class:'us_equity'},{symbol:'TEST',name:'Offline Test Company',asset_class:'us_equity'}]});
  throw Error('Unexpected mocked route '+p);
 };
}'''


async def capture(page, name):
    await page.evaluate('document.fonts.ready')
    await page.evaluate("window.scrollTo({top:0,left:0,behavior:'instant'})")
    await page.screenshot(path=str(OUT / (name + '.png')), full_page=True)
    assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), name


async def matrix(page, prefix):
    for route in ('explore', 'compare', 'models', 'portfolio', 'methods'):
        await page.locator(f'#qf-v20-navigation [data-page="{route}"]').click()
        if route == 'explore':
            await page.locator('#qf27-analyze').click()
        if route == 'compare':
            # Exact covered names; synthetic public and mocked private histories stay separate.
            for symbol in ('AAPL', 'NVDA'):
                await pick_compare(page, symbol)
            await page.locator('#qf-v20-compare-run').click()
            await page.wait_for_function("document.querySelector('#qf-b21-compare-chart svg')")
        if route == 'models':
            for category in ('prediction', 'risk', 'valuation', 'strategy'):
                await page.locator(f'#page-models [data-qf-model="{category}"]').click()
                for phase in ('results', 'evaluation', 'method'):
                    await page.locator(f'[data-qf-c22-phase="{phase}"]').click()
                    if phase == 'method':
                        assert await page.locator('#qf-c22-model-output math').count() > 0
                    if category == 'strategy' and phase == 'results':
                        await page.locator('#qf24-walkforward-run').click()
                        await page.wait_for_function("document.querySelector('#qf24-walkforward-output table')")
                        assert 'disjoint test windows' in await page.locator('#qf24-walkforward-output').inner_text()
                    await capture(page, f'{prefix}-models-{category}-{phase}')
        elif route == 'methods':
            for view in ('overview', 'data', 'statistical', 'engineering'):
                await page.locator(f'[data-qf-c22-method="{view}"]').click()
                if view == 'statistical':
                    assert await page.locator('#qf-c22-method-content math').count() >= 1
                await capture(page, f'{prefix}-methods-{view}')
            assert await page.locator('#qf-c22-method-content a[href*="github.com"]').count() == 0
        elif route == 'portfolio':
            for view in ('overview', 'whatif', 'analysis'):
                await page.locator(f'[data-qf-portfolio="{view}"]').click()
                await capture(page, f'{prefix}-portfolio-{view}')
            await page.locator('[data-qf-portfolio="whatif"]').click()
            slider = page.locator('[data-qf-b21-weight]').first
            await slider.fill('35')
            await slider.dispatch_event('input')
            assert '100%' in await page.locator('#qf-b21-weights-total').inner_text()
            await page.locator('#qf-b21-lower-risk').click()
            assert await page.locator('#qf-b21-optimizer-output').inner_text()
        else:
            await capture(page, f'{prefix}-{route}')


async def journey(browser, width):
    page = await browser.new_page(viewport={'width': width, 'height': 900 if width == 1440 else 844})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    # No request from this suite is permitted to reach a real provider or account.
    await page.route('**/*', lambda route: route.abort())
    await page.set_content(HTML, wait_until='load')
    await matrix(page, f'public-{width}')
    await page.locator('#qf-v23-home-button').click()
    assert await page.locator('#qf-v23-landing').is_visible()
    assert await page.locator('#qf24-home-find').is_visible()
    assert await page.locator('#qf-v23-open-research').count() == 0
    assert await page.locator('#qf-v23-landing svg, #qf31-home-chart').count() == 0
    assert await page.locator('#qf32-home-options').count() == 1
    await capture(page, f'public-{width}-home')
    await page.locator('#qf24-home-search').fill('Microsoft')
    await page.locator('#qf24-home-find').click()
    assert await page.locator('#qf-v20-company').inner_text() == 'Microsoft'
    await page.locator('#qf-v20-mode').click()
    await page.evaluate("""() => { window.fetch=async(url)=>String(url).includes('/api/health')?{ok:true,json:async()=>({status:'ok'})}:({ok:false,status:422,json:async()=>({detail:[{loc:['body','password'],msg:'invalid',input:'DO-NOT-ECHO'}]})}); }""")
    await page.locator('#private-email').fill('fixture' + '@' + 'example.invalid')
    await page.locator('#private-password').fill('offline-password')
    await page.locator('#private-login-submit').click()
    await page.wait_for_function("document.querySelector('#private-message').textContent.includes('Check the email')")
    assert 'object Object' not in await page.locator('#private-message').inner_text()
    assert 'DO-NOT-ECHO' not in await page.locator('#private-message').inner_text()
    await capture(page, f'error-{width}-structured-validation')
    await page.evaluate(FIXTURE)
    await page.evaluate(PRODUCT_TRADES)
    await page.locator('#private-password').fill('offline-password')
    await page.locator('#private-login-submit').click()
    await page.wait_for_function('window.QFPrivateBridgeV23.ready()')
    assert 'PRIVATE' in await page.locator('#qf24-mode-label').inner_text()
    assert 'CRYPTO' not in await page.locator('#qf-v20-source-badge').inner_text()
    await page.locator('#qf-v20-search').fill('Offline')
    await page.locator('#qf-v20-search-results [data-qf27-symbol="TEST"]').click()
    assert 'not covered' in await page.locator('#qf-v20-sector').inner_text()
    await page.locator('#qf27-analyze').click()
    assert 'no coverage' in await page.locator('#qf-v20-coverage').inner_text()
    await capture(page, f'private-{width}-non-sec-asset')
    await page.evaluate("window.QFResearch20.choose('MSFT')")
    await page.wait_for_function("window.QFResearch20.context().origin==='market'")
    assert 'FEED NOT SUPPLIED' in await page.locator('#qf-v20-source-badge').inner_text()
    await matrix(page, f'private-{width}')
    await page.locator('#qf-v20-navigation [data-page="explore"]').click()
    await page.locator('[data-qf27-explore="research"]').click()
    assert await page.locator('#qf24-notes').is_visible()
    assert not await page.locator('#qf-v23-owner-panel').is_visible()
    await page.locator('#qf-v23-note').fill('OFFLINE-PRIVATE-NOTE')
    await page.locator('#qf-v23-save').click()
    await page.wait_for_function("document.querySelector('#qf-v23-note-list').textContent.includes('OFFLINE-PRIVATE-NOTE')")
    await page.locator('#qf27-analyze').click()
    await page.locator('[data-qf27-explore="research"]').click()
    await page.locator('#qf24-save-brief').click()
    await page.wait_for_function("window.qfMockOwner.notes.length===2")
    await page.evaluate('''async () => {
      window.qfMockOwner.notes.push({symbol:'MSFT',at:'2026-10-09',text:'QF96|'+JSON.stringify({v:1,date:'2026-10-09',symbol:'MSFT',action:'Review risks',readiness:'limited',covered:3,universe:['MSFT','AAPL'],policy:'research only'})});
      await window.QFPrivateBridgeV23.refresh();
      window.dispatchEvent(new Event('qf:research-context'));
    }''')
    assert 'Saved historical assessment' in await page.locator('#qf-v23-note-list').inner_text()
    await capture(page, f'private-{width}-saved-research')
    await page.locator('#qf24-switch-mode').click()
    assert await page.locator('#qf24-notes').is_hidden()
    assert 'OFFLINE-PRIVATE-NOTE' not in await page.locator('body').inner_text()
    assert await page.evaluate("window.QFResearch20.context().origin==='synthetic'")
    before = await page.evaluate('window.qfMockRequests.length')
    await page.locator('#qf27-analyze').click()
    assert await page.evaluate('window.qfMockRequests.length') == before
    await page.locator('#qf24-switch-mode').click()
    await page.locator('#qf-v20-navigation [data-page="portfolio"]').click()
    await page.locator('[data-qf-portfolio="overview"]').click()
    await virtual_buy(page, 'TEST', 120)
    await page.wait_for_function('window.qfMockVersion===5')
    await page.locator('#qf-v20-mode').click()
    await page.locator('#qf-v23-signout').click()
    await page.wait_for_function('!window.QFPrivateBridgeV23.ready()')
    assert await page.locator('#qf24-notes').is_hidden()
    assert 'OFFLINE-PRIVATE-NOTE' not in await page.locator('body').inner_text()
    assert not errors, errors
    print(f'{width}px public/private route matrix, structured auth error, non-SEC search, contextual notes/briefs, versioned virtual trade, mode isolation and logout PASS', flush=True)
    await page.close()


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            for width in (1440, 390):
                await journey(browser, width)
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
