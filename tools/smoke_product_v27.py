"""Product-stage acceptance under the compiled CSP; every owner service is mocked."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from browser_product_contract import navigate
from playwright.async_api import async_playwright, expect
from smoke_rebuild_browser import FIXTURE

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'public/index.html').read_text(encoding='utf-8')
CSP=next(line.strip().split(': ',1)[1] for line in (ROOT/'public/_headers').read_text().splitlines() if 'Content-Security-Policy:' in line)
OUT=Path(os.environ.get('QF_SCREENSHOT_DIR',str(ROOT/'outputs/product-v27')))
EXTRA=r'''() => {
 const original=fetch;window.qfTradePosts=0;window.qfStaleReads=false;window.qfOldState=structuredClone(qfMockOwner);
 window.fetch=async(url,options={})=>{
  const path=String(url),response=(value,status=200)=>({ok:status<400,status,json:async()=>structuredClone(value)});
  if(path.includes('private/assets')&&new URLSearchParams(path.split('?')[1]).get('category')==='crypto')return response({licensed_private:true,items:[{symbol:'BTC/USD',name:'Bitcoin',asset_class:'crypto',tradable:true}]});
  if(path.includes('private/assets'))return response({licensed_private:true,total:3,items:[{symbol:'MSFU',name:'Direxion Daily Microsoft Bull ETF',asset_class:'us_equity',exchange:'NASDAQ',instrument_type:'ETF / fund',tradable:true},{symbol:'MSFT',name:'Microsoft Corporation',asset_class:'us_equity',exchange:'NASDAQ',instrument_type:'equity listing',tradable:true},{symbol:'AAPL',name:'Apple',asset_class:'us_equity',tradable:true},{symbol:'TEST',name:'Offline Test Company',asset_class:'us_equity',tradable:true}]});
  if(path.includes('private/state')&&window.qfStaleReads)return response({portfolio:qfOldState,version:2});
  if(path.includes('private/trade-preview')||path.includes('private/trade')){
   const body=JSON.parse(options.body),buy=body.side==='buy',units=buy?Math.floor(Number(body.amount)/(300*1.0005)*1e8)/1e8:Number(body.amount),gross=Math.round(units*300*100)/100,fee=Math.round(gross*.0005*100)/100,impact=buy?-gross-fee:gross-fee;
   if(body.expected_version!==qfMockVersion)return response({detail:'Version conflict'},409);
   if(!buy&&units>Number(qfMockOwner.holdings[body.symbol]||0))return response({detail:'No owned position'},422);
   const preview={symbol:body.symbol,side:body.side,units,gross,fee,price:300,cash_before:qfMockOwner.cash,cash_after:Math.round((qfMockOwner.cash+impact)*100)/100,cash_impact:impact,venue:'MOCK',observed_at:new Date().toISOString()};
   if(path.includes('trade-preview'))return response({preview,version:qfMockVersion});
   window.qfTradePosts++;qfMockOwner.cash=preview.cash_after;qfMockOwner.holdings[body.symbol]=(qfMockOwner.holdings[body.symbol]||0)+(buy?units:-units);qfMockOwner.trades.unshift({...preview,at:new Date().toISOString(),request_id:body.request_id});qfMockVersion++;if(window.qfLoseResponse){window.qfLoseResponse=false;throw new TypeError('Mock interrupted response');}
   return response({portfolio:qfMockOwner,version:qfMockVersion,paper_only:true});
  }
  if(path.includes('private/news-research'))return response({method:'MOCK lexical fixture',rows:[{symbol:'MSFT',articles:24,topics:['Earnings','Products'],headlines:Array.from({length:24},(_,i)=>({headline:'MOCK headline '+i+' about earnings and operations',created_at:'2026-11-'+String(1+Math.floor(i/4)).padStart(2,'0')+'T12:00:00Z',source:'Offline fixture',url:'https://example.invalid/'+i,topic:i%2?'Earnings':'Products',tone:i%3===0?'Negative':i%3===1?'Positive':'Uncertain'}))}]});
  return original(url,options);
 };
}'''

async def capture(page,name):
    await page.evaluate('window.scrollTo(0,0)')
    await page.screenshot(path=str(OUT/(name+'.png')),full_page=True)
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),name

async def journey(browser,engine,width):
    page=await browser.new_page(viewport={'width':width,'height':900})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    async def route(request):
        if request.request.is_navigation_request() and request.request.url=='https://quantforge.test/':
            await request.fulfill(status=200,content_type='text/html',body=HTML,headers={'Content-Security-Policy':CSP})
        else:
            await request.abort()
    await page.route('**/*',route)
    await page.goto('https://quantforge.test/')
    await expect(page.locator('#qf-v23-landing')).to_be_visible()
    await navigate(page, 'explore')
    await expect(page.locator('#qf27-explore-financials')).to_be_visible()
    assert await page.locator('#qf-v20-chart').is_hidden()
    await expect(page.locator('#qf-v20-financial-chart svg')).to_be_visible()
    await capture(page,f'{engine}-{width}-public-financial-primary')
    for view in ('performance','margin','cash','sources'):
        await page.locator(f'[data-qf27-finance="{view}"]').click()
    await capture(page,f'{engine}-{width}-public-financial-sources')
    await page.locator('#qf-v20-search').fill('Microsoft')
    await page.locator('#qf-v20-search-results [data-qf27-symbol="MSFT"]').click()
    await page.locator('#qf27-analyze').click()
    await expect(page.locator('#qf-v20-findings')).to_contain_text('Why it matters')
    await capture(page,f'{engine}-{width}-public-brief')
    assert await page.locator('[data-qf27-explore="context"]').count()==0
    await page.locator('[data-qf27-explore="financials"]').click()
    await page.locator('[data-qf27-finance="sources"]').click()
    await expect(page.locator('#qf-v20-financial-table')).to_contain_text('Accession')
    await navigate(page, 'compare')
    basket_before=await page.locator('#qf-v20-compare-chips').inner_text()
    await page.locator('#qf27-peer-scope').select_option('all')
    expected_percent=await page.evaluate("()=>{const r=QFPublicSECPeers.compare(QFPublishedSEC,'MSFT',{sectorOnly:false});return r.peers[0].values[r.indices[0]].toFixed(3)+'%';}")
    await expect(page.locator('#qf25-peers')).to_contain_text(expected_percent)
    assert basket_before==await page.locator('#qf-v20-compare-chips').inner_text()
    await expect(page.locator('#qf25-peers')).to_contain_text('percentage points')
    if width < 740:
        exhibit = page.locator('#qf25-peers .qf24-figure svg').first
        assert await exhibit.evaluate('(svg)=>svg.viewBox.baseVal.width < 400')
        assert await exhibit.locator('text').first.evaluate('(t)=>t.getBoundingClientRect().height >= 12')
    await capture(page,f'{engine}-{width}-peer-scope')
    await navigate(page, 'methods')
    for view in ('overview','data','engineering'):
        await page.locator(f'[data-qf-c22-method="{view}"]').click()
        await capture(page,f'{engine}-{width}-methods-{view}')
    await page.locator('[data-qf-c22-method="overview"]').click()
    async with page.expect_download() as download:
        await page.locator('#qf27-case-csv').click()
    assert (await download.value).suggested_filename.endswith('.csv')
    await page.locator('[data-qf-c22-method="statistical"]').click()
    for method in ('returns','regression','portfolio','tails','drawdown','uncertainty','logistic','brier','ratios','dcf','walk'):
        await page.locator(f'[data-qf27-method="{method}"]').click()
        assert await page.locator('#qf27-lab-output math').count() >= 1
        await capture(page,f'{engine}-{width}-method-{method}')
    await page.locator('[data-qf27-method="portfolio"]').click()
    await page.locator('#qf27-lab-value').fill('60')
    await page.locator('#qf27-lab-rho').fill('-1')
    await page.locator('#qf27-lab-calculate').click()
    assert 'NaN' not in await page.locator('#qf27-lab-output').inner_text()
    await page.locator('[data-qf27-method="portfolio"]').focus()
    await page.keyboard.press('ArrowRight')
    await expect(page.locator('[data-qf27-method="tails"]')).to_have_attribute('aria-pressed','true')
    await page.keyboard.press('Home')
    await expect(page.locator('[data-qf27-method="returns"]')).to_have_attribute('aria-pressed','true')
    await navigate(page, 'explore')
    await page.evaluate(FIXTURE)
    await page.evaluate(EXTRA)
    await page.locator('#qf-v20-mode').click()
    await page.locator('#private-email').fill('offline'+'@'+'example.invalid')
    await page.locator('#private-password').fill('offline-fixture')
    await page.locator('#private-login-submit').click()
    await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE')
    await page.locator('[data-qf34-workspace="research"]:visible').click()
    await page.evaluate("""() => {
      const original=fetch;let first=true;
      window.fetch=async(url,options={})=>{
        if(String(url).includes('private/assets')&&new URLSearchParams(String(url).split('?')[1]).get('query')==='Microsoft'&&first){
          first=false;return await new Promise(resolve=>{window.qfResolveOldAsset=()=>resolve({ok:true,status:200,json:async()=>({licensed_private:true,items:[{symbol:'MSFT',name:'Microsoft Corporation',asset_class:'us_equity'}]})});});
        }
        return original(url,options);
      };
    }""")
    await page.locator('#qf-v20-search').fill('Microsoft')
    await expect(page.locator('#qf-v20-search-results')).to_contain_text('Searching authenticated')
    await page.locator('#qf-v20-search').fill('Apple')
    await expect(page.locator('#qf-v20-search-results [data-qf27-symbol="AAPL"]')).to_be_visible()
    await page.evaluate('window.qfResolveOldAsset()')
    assert await page.locator('#qf-v20-search-results [data-qf27-symbol="MSFT"]').count()==0
    await page.locator('#qf-v20-search-results [data-qf27-symbol="AAPL"]').click()
    await expect(page.locator('#qf-v20-symbol')).to_have_text('AAPL')
    await page.locator('#qf-v20-search').fill('Microsoft')
    await page.locator('#qf-v20-search-results [data-qf27-symbol="MSFT"]').click()
    assert await page.locator('#qf-v20-news').count()==0
    assert await page.locator('[data-qf27-explore="context"]').count()==0
    await navigate(page, 'portfolio')
    await page.locator('[data-qf-portfolio="overview"]').click()
    await page.evaluate("async()=>{qfMockOwner.holdings['BTC/USD']=.25;qfMockVersion++;await QFPrivateBridgeV23.refresh();window.dispatchEvent(new Event('qf:owner-state'));}")
    await page.locator('#qf27-sell').click()
    await expect(page.locator('#qf27-trade-options [data-qf27-symbol="MSFT"]')).to_have_count(1)
    assert await page.locator('#qf27-trade-options [data-qf27-symbol="TEST"]').count()==0
    await expect(page.locator('#qf27-trade-options [data-qf27-symbol="BTC/USD"]')).to_have_count(1)
    await page.locator('#qf27-trade-options [data-qf27-symbol="MSFT"]').click()
    await page.locator('#qf27-trade-amount').fill('2')
    await page.locator('#qf27-preview').click()
    await expect(page.locator('#qf27-trade-status')).to_contain_text('exceeds')
    await page.locator('#qf27-buy').click()
    await page.locator('#qf27-trade-query').fill('Microsoft')
    await expect(page.locator('#qf27-trade-options [role="option"]').first).to_contain_text('Microsoft Corporation')
    await page.locator('#qf27-trade-options [data-qf27-symbol="MSFT"]').click()
    await page.locator('#qf27-preview').click()
    await expect(page.locator('#qf27-preview-result')).to_contain_text('Resulting cash')
    await capture(page,f'{engine}-{width}-buy-preview')
    # Reproduce the old failure: accepted POST must not be overwritten by an older GET.
    await page.evaluate('window.qfStaleReads=true')
    await page.locator('#qf27-confirm').dblclick()
    await expect(page.locator('#qf27-trade-status')).to_contain_text('recorded')
    await expect(page.locator('#qf24-transaction-ledger')).to_contain_text('buy')
    assert await page.evaluate('qfTradePosts')==1
    assert await page.evaluate('QFPrivateBridgeV23.snapshot().trades.length')==1
    await capture(page,f'{engine}-{width}-accepted-buy')
    await page.evaluate('window.qfLoseResponse=true')
    await page.locator('#qf27-preview').click()
    await expect(page.locator('#qf27-confirm')).to_be_visible()
    await page.locator('#qf27-confirm').click()
    await expect(page.locator('#qf27-trade-status')).to_contain_text('may have recorded')
    assert await page.evaluate('qfTradePosts') == 2
    assert await page.locator('#qf27-preview').is_disabled()
    await page.locator('#qf27-refresh').click()
    await expect(page.locator('#qf27-trade-status')).to_contain_text('older account')
    assert await page.evaluate('QFPrivateBridgeV23.snapshot().trades.length') == 1
    await page.evaluate('window.qfStaleReads=false')
    await page.locator('#qf27-refresh').click()
    await expect(page.locator('#qf27-trade-status')).to_contain_text('refreshed')
    assert await page.evaluate('QFPrivateBridgeV23.snapshot().trades.length') == 2
    await capture(page,f'{engine}-{width}-reconciled-lost-response')
    await page.locator('#qf-v20-mode').click()
    await capture(page,f'{engine}-{width}-account-overview')
    await page.locator('#qf-v23-close').click()
    await navigate(page, 'methods')
    await page.locator('[data-qf-c22-method="statistical"]').click()
    await page.locator('[data-qf27-method="uncertainty"]').click()
    await expect(page.locator('#qf27-lab-output')).to_contain_text('Private observed')
    await page.locator('#qf24-switch-mode').click()
    await expect(page.locator('#qf27-lab-output')).to_contain_text('Explicitly synthetic')
    assert 'MOCK headline' not in await page.locator('body').inner_text()
    assert 'Microsoft Corporation (MSFT)' not in await page.locator('#qf24-transaction-ledger').inner_text()
    await page.locator('#qf24-switch-mode').click()
    await page.evaluate("""() => {
      const original=fetch;
      window.qfPendingRefresh=QFPrivateBridgeV23.snapshot();
      window.fetch=async(url,options={})=>{
        if(String(url).includes('private/state'))return await new Promise(resolve=>{window.qfResolveLate=()=>resolve({ok:true,status:200,json:async()=>({portfolio:qfMockOwner,version:qfMockVersion})});});
        return original(url,options);
      };
      window.qfLateRefresh=QFPrivateBridgeV23.refresh().catch(error=>String(error.message));
    }""")
    await page.locator('#qf-v20-mode').click()
    await page.locator('#qf-v23-signout').click()
    await page.evaluate('window.qfResolveLate()')
    await page.evaluate('window.qfLateRefresh')
    assert await page.evaluate('QFPrivateBridgeV23.snapshot()') is None
    assert await page.locator('#qf24-transactions').is_hidden()
    assert not errors,errors
    print(f'{engine} {width}px source modes/picker/peers/retired-news/preview/owned-sell/accepted receipt/isolation PASS',flush=True)
    await page.close()

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as pw:
        for engine in os.environ.get('QF_TEST_BROWSERS','chromium,firefox,webkit').split(','):
            browser=await getattr(pw,engine).launch()
            try:
                for width in (1440,390):
                    await journey(browser,engine,width)
            finally:
                await browser.close()

if __name__=='__main__':
    asyncio.run(main())
