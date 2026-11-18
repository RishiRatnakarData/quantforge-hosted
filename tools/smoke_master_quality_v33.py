"""Current candidate acceptance with controlled fixtures; never contacts an owner API."""
import asyncio
import json
import os
from pathlib import Path

from browser_product_contract import navigate
from playwright.async_api import async_playwright, expect
from smoke_completion_browser import EXTEND
from smoke_final_release32 import enter, setup

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('QF_MASTER_SCREENSHOT_DIR', str(ROOT/'outputs/master-quality-review')))
FIXED = r'''() => {
 const original=fetch;
 const dates=[];let d=new Date('2026-11-13T00:00:00Z');
 while(dates.length<520){if(d.getUTCDay()!==0&&d.getUTCDay()!==6)dates.unshift(d.toISOString().slice(0,10));d.setUTCDate(d.getUTCDate()-1);}
 qfMockOwner.holdings={MSFT:1,AAPL:2};qfMockOwner.initial_cash=3250;qfMockOwner.basis_accounting={version:1,positions:{MSFT:{units:1,total_basis:250},AAPL:{units:2,total_basis:550}},realized_pnl:50,realized_complete:false};window.previewOnlyCalls=0;window.forbiddenTradeCalls=0;
 window.fetch=async(url,options={})=>{
  const path=String(url);
  if(path.includes('private/trade-preview')){previewOnlyCalls++;return {ok:false,status:422,json:async()=>({code:'quote_stale',observation:{observed_at:'2026-11-13T20:00:00Z',age_seconds:240000,max_age_seconds:900,source:'Controlled stale provider fixture'}})};}
  if(path.includes('private/trade')&&!path.includes('preview')){forbiddenTradeCalls++;throw Error('A test must not submit a transaction.');}
  const r=await original(url,options);
  if(path.includes('private/history')){const data=await r.json();if(data.observations)data.observations=data.observations.map((x,i)=>({...x,date:dates[i]}));else data.dates=dates;data.source='CONTROLLED CURRENT-DATE FIXTURE — no live market observations';return {ok:r.ok,status:r.status,json:async()=>data};}
  return r;
 };
 const label=document.createElement('p');label.textContent='ISOLATED FIXTURE · NO OWNER RECORDS · NOT A LIVE FINANCIAL ASSESSMENT';label.style.cssText='background:#242a30;color:white;padding:12px;font-size:13px;position:relative;z-index:9999';document.body.prepend(label);
}'''


async def run():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    async with async_playwright() as pw:
        for engine in ('chromium', 'firefox', 'webkit'):
            browser = await getattr(pw, engine).launch()
            for width in (390, 1440):
                page, errors = await setup(browser, width)
                await page.evaluate(EXTEND)
                await page.evaluate(FIXED)
                await page.locator('#qf-v23-home-button').click()
                await expect(page.locator('.qf33-home-proof')).to_be_visible()
                await page.screenshot(path=str(OUT/f'{engine}-{width}-home.png'), full_page=True)
                await page.locator('.qf33-home-proof [data-qf33-home="methods"]').click()
                await expect(page.locator('#page-methods')).to_be_visible()
                await enter(page)
                await page.locator('#private-login-submit').click()
                await page.wait_for_function("QFPrivateBridgeV23.ready()&&QFResearch20.context().origin==='market'")
                await page.locator('[data-qf34-workspace="research"]:visible').click()
                await page.locator('[data-qf27-explore="brief"]').click()
                await page.locator('#qf27-analyze').click()
                await expect(page.locator('#qf32-summary')).to_contain_text('Price / annual cash-flow proxy:', timeout=30000)
                await expect(page.locator('#qf32-summary')).to_contain_text('Loaded held-position correlations: AAPL')
                await expect(page.locator('#qf32-summary')).to_contain_text('0.80 review flag')
                assert await page.evaluate("Boolean(document.querySelector('#qf32-summary').compareDocumentPosition(document.querySelector('#qf-v20-findings')) & Node.DOCUMENT_POSITION_FOLLOWING)")
                await expect(page.locator('#qf-v20-analyze')).to_be_hidden()
                assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                await page.screenshot(path=str(OUT/f'{engine}-{width}-private-assessment.png'), full_page=True)
                await page.locator('#qf33-evidence-tab').focus()
                await page.keyboard.press('End')
                await expect(page.locator('#qf33-evidence-details')).to_be_visible()
                await expect(page.locator('#qf32-summary')).to_be_hidden()
                await page.screenshot(path=str(OUT/f'{engine}-{width}-supporting-evidence.png'), full_page=True)
                await page.keyboard.press('Home')
                await expect(page.locator('#qf32-summary')).to_be_visible()

                await navigate(page, 'portfolio')
                await page.locator('[data-qf-portfolio="overview"]').click()
                await expect(page.locator('#qf27-account-summary')).to_contain_text('Unrealized P&L')
                await expect(page.locator('#qf27-account-summary')).to_contain_text('Tracked realized P&L')
                await page.locator('#qf27-trade-query').fill('AAPL')
                await page.locator('#qf27-trade-options [data-qf27-symbol="AAPL"]').click()
                await page.locator('#qf27-preview').click()
                await expect(page.locator('#qf27-trade-status')).to_contain_text('Controlled stale provider fixture')
                await expect(page.locator('#qf27-trade-status')).to_contain_text('15-minute')
                await expect(page.locator('#qf27-confirm')).to_be_hidden()
                assert await page.evaluate('previewOnlyCalls===1&&forbiddenTradeCalls===0')
                await page.locator('#qf27-trade-status').scroll_into_view_if_needed()
                await page.screenshot(path=str(OUT/f'{engine}-{width}-stale-preview.png'), full_page=True)
                await navigate(page, 'explore')
                await page.locator('#qf24-switch-mode').click()
                assert await page.locator('#qf32-summary').inner_text() == ''
                assert not errors, errors
                results.append({'browser':engine,'width':width,'fixtures_only':True,'matched_valuation':True,'held_correlation':True,'summary_before_details':True,'stale_preview_refused':True,'transaction_posts':0,'public_isolation':True})
                await page.close()
            await browser.close()
    (OUT/'verification.json').write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2), flush=True)

if __name__ == '__main__':
    asyncio.run(run())
