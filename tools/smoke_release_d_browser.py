"""Release D UI acceptance. Mocked MFA/provider; no live owner service verification."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from browser_product_contract import PRODUCT_TRADES, navigate, open_company_research, virtual_buy
from playwright.async_api import async_playwright

HTML = (Path(__file__).resolve().parents[1] / 'public/index.html').read_text(encoding='utf-8')

MOCK = r'''() => {
  const dates=Array.from({length:85},(_,i)=>new Date(Date.UTC(2026,0,1+i)).toISOString().slice(0,10));
  window.qfMockRequests=[];window.qfMockVersion=2;
  window.qfMockOwner={cash:2500,initial_cash:2500,holdings:{MSFT:1},watchlist:[],notes:[],trades:[]};
  window.fetch=async (url,options={})=>{
    const p=String(url);window.qfMockRequests.push(p);
    const q=new URLSearchParams(p.split('?')[1]||'');
    const response=(data,ok=true)=>({ok,json:async()=>data});
    if(p.includes('/api/health'))return response({status:'ok'});
    if(p.includes('auth/login'))return response({signed_in:true});
    if(p.includes('auth/logout'))return response({signed_in:false});
    if(p.includes('private/state'))return response({portfolio:window.qfMockOwner,version:window.qfMockVersion});
    if(p.includes('private/quotes')){const ss=q.get('symbols')?.split(',')||[];
      return response({quotes:ss.map(s=>({symbol:s,price:300,venue:'MOCK',timestamp:new Date().toISOString()}))});}
    if(p.includes('private/history-single')){const s=q.get('symbol');return response({symbol:s,licensed_private:true,
       observations:dates.map((date,i)=>({date,close:200+i*.5})),ohlcv_available:false,
       source:'MOCK owner history',coverage:'test fixture',sessions_per_year:252});}
    if(p.includes('private/history?')){const symbols=q.get('symbols')?.split(',')||[];
      return response({symbols,dates,closes:Object.fromEntries(symbols.map(s=>[s,dates.map((_,i)=>100+i*.5)])),
       source:'MOCK owner history',licensed_private:true,sessions_per_year:252});}
    if(p.includes('private/news-research'))return response({detail:'No news entitlement'},false);
    if(p.includes('private/notes')){
      const input=JSON.parse(options.body);if(input.expected_version!==window.qfMockVersion)return response({detail:'Version changed'},false);
      window.qfMockOwner.notes=input.notes;window.qfMockVersion++;
      return response({portfolio:window.qfMockOwner,version:window.qfMockVersion});}
    if(p.includes('private/trade')){
      const input=JSON.parse(options.body);if(input.expected_version!==window.qfMockVersion)return response({detail:'Version changed'},false);
      window.qfMockOwner.holdings[input.symbol]=2;window.qfMockOwner.cash-=Number(input.amount);
      window.qfMockVersion++;return response({portfolio:window.qfMockOwner,version:window.qfMockVersion,paper_only:true});}
    if(p.includes('private/assets'))return response({licensed_private:true,total:1,items:[{symbol:'MSFT',name:'Microsoft',asset_class:'us_equity'}]});
    throw Error('Unexpected route '+p);
  };
}'''


async def run_page(browser, width: int) -> None:
    page = await browser.new_page(viewport={'width': width, 'height': 900}, accept_downloads=True)
    errors: list[str] = []
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    try:
        await page.set_content(HTML, wait_until='load')
        assert await page.locator('#qf-v20-navigation [data-page]').count() == 5
        await page.locator('#qf-v23-home-button').click()
        assert await page.locator('#qf-v23-landing').is_visible()
        await page.locator('#qf24-home-search').fill('Microsoft')
        await page.locator('#qf24-home-find').click()
        assert await page.locator('#qf-v20-search').is_visible()
        assert await page.locator('#qf-v20-company').inner_text() == 'Microsoft'
        assert await page.locator('#qf-v20-symbol').inner_text() == 'MSFT'
        assert await page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        assert not errors, errors[:3]
        if width == 1440:
            await page.screenshot(path=os.getenv('QF_D23_PUBLIC_SCREENSHOT', '/tmp/qf_d23_public.png'))
        # Real account always requires MFA. This mock skips it only inside an isolated browser test.
        await page.evaluate(MOCK)
        await page.evaluate(PRODUCT_TRADES)
        await page.locator('#qf-v20-mode').click()
        assert await page.locator('#private-login').is_visible()
        await page.locator('#private-email').fill('test' + '@' + 'example.invalid')
        await page.locator('#private-password').fill('offline-test-not-a-real-password')
        await page.locator('#private-login-submit').click()
        await page.wait_for_function("window.QFPrivateBridgeV23 && window.QFPrivateBridgeV23.ready()")
        assert await page.locator('.tabpage.active').get_attribute('id') == 'page-explore'
        assert not await page.locator('#private-signed').is_visible()
        assert await page.locator('#qf-v20-mode').inner_text() == 'Account'
        await page.evaluate("window.QFNavigate20('private')")
        assert await page.locator('.tabpage.active').get_attribute('id') == 'page-explore'
        await open_company_research(page)
        await page.locator('#qf27-analyze').click()
        assert await page.locator('[data-qf27-explore="research"]').is_visible()
        await page.locator('[data-qf27-explore="research"]').click()
        assert not await page.locator('#qf-v23-owner-panel').is_visible()
        assert await page.locator('#qf24-notes').is_visible()
        assert await page.locator('#qf-v23-note-company').inner_text() == 'Microsoft (MSFT)'
        await page.locator('#qf-v23-note').fill('A concise sample research note.')
        await page.locator('#qf-v23-save').click()
        await page.locator('#qf24-note-status').get_by_text('Research note saved.', exact=True).wait_for()
        assert await page.locator('#qf-v23-note-list .qf-v23-note-entry').count() == 1
        await navigate(page, 'portfolio')
        await page.locator('[data-qf-portfolio="overview"]').click()
        await virtual_buy(page, 'MSFT', 120)
        assert '$2,380.00' in await page.locator('#qf27-account-summary').inner_text()
        if width == 1440:
            await page.screenshot(path=os.getenv('QF_D23_PRIVATE_SCREENSHOT', '/tmp/qf_d23_private.png'))
        await page.locator('#qf-v20-mode').click()
        await page.locator('#qf-v23-signout').click()
        await page.wait_for_function("!window.QFPrivateBridgeV23.ready()")
        assert not await page.locator('#qf-v23-owner-panel').is_visible()
        assert await page.locator('#qf-v20-mode').inner_text() == 'Sign in'
        assert not await page.locator('[data-qf27-explore="research"]').is_visible()
        assert not errors, errors[:5]
        print(f'Release D {width}px home / MFA-mock / notes / virtual trades / signout PASS', flush=True)
    finally:
        await page.close()


async def main() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, executable_path=os.getenv('QF_CHROMIUM_PATH') or None)
        try:
            for width in (1440, 390):
                await run_page(browser, width)
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
