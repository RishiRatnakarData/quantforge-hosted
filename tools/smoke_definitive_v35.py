"""Final shortlist-to-assessment journey. Every owner/provider operation is an isolated fixture."""
import asyncio
import json
import os
from pathlib import Path

from browser_product_contract import navigate
from playwright.async_api import async_playwright, expect
from smoke_completion_browser import EXTEND
from smoke_consolidation_v34 import EXTRA
from smoke_final_release32 import enter, setup
from smoke_master_quality_v33 import FIXED

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('QF_DEFINITIVE_SCREENSHOTS', str(ROOT / 'outputs/definitive-v35')))
FAULTS = r'''() => {
 const original=fetch;window.qf35Failed='';window.qf35Partial='';window.qf35Held='';window.qf35Started=false;window.qf35AuthFailure='';window.qf35ReadSymbols=[];window.qf35Revocations=0;
 window.fetch=async(u,o={})=>{
  const path=String(u),q=new URLSearchParams(path.split('?')[1]||''),symbol=q.get('symbol')||(q.get('symbols')||'').split(',')[0];
  if(path.includes('auth/logout'))qf35Revocations++;
  if(path.includes('history-single'))qf35ReadSymbols.push(symbol);
  if(symbol&&symbol===qf35AuthFailure)return {ok:false,status:401,json:async()=>({code:'session_expired'})};
  if(symbol&&symbol===qf35Failed)return {ok:false,status:503,json:async()=>({code:'provider_unavailable'})};
  if(symbol===qf35Partial&&path.includes('valuation-capital'))throw new TypeError('Isolated capital-data failure');
  if(symbol===qf35Held&&path.includes('history-single')){qf35Started=true;await new Promise(resolve=>window.qf35Release=resolve);}
  return original(u,o);
 };
}'''

async def private_journey(browser, engine, width):
    page, errors = await setup(browser, width)
    await page.evaluate(EXTEND)
    await page.evaluate(FIXED)
    await page.evaluate(EXTRA)
    await page.evaluate(FAULTS)
    await enter(page)
    await page.locator('#private-login-submit').click()
    await expect(page.locator('#qf37-research-home')).to_be_visible()
    assert await page.locator('#qf-v20-navigation [data-page]').all_text_contents() == ['Explore', 'Compare', 'Models', 'Portfolio', 'Methods']
    assert await page.locator('#qf34-workspace-nav, #qf37-secondary').count() == 0
    assert await page.locator('#qf37-research-home .qf34-shortlist').count() == 0
    assert await page.locator('#qf37-research-home [data-qf34-workspace="research"]').count() == 1
    assert await page.evaluate('qf34UniverseReads') == 0
    reads_before_selection = await page.evaluate('qf34CompanyReads')
    await page.locator('#qf37-research-home [data-qf34-workspace="research"]').click()
    await expect(page.locator('#qf37-company-search')).to_be_focused()
    await expect(page.locator('#qf37-research-home')).to_be_visible()
    await expect(page.locator('#qf37-selection-status')).to_contain_text('select the matching listing')
    assert await page.evaluate('qf34CompanyReads') == reads_before_selection
    home_bounds = await page.locator('#qf37-research-home').bounding_box()
    content_bounds = await page.locator('#page-explore').bounding_box()
    assert home_bounds['width'] >= content_bounds['width'] - 4
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    await page.screenshot(path=str(OUT / f'{engine}-{page.viewport_size["width"]}-research-home.png'), full_page=True)
    if width == 390:
        await page.locator('#qf37-company-search').fill('Microsoft')
        await expect(page.locator('#qf37-company-options [data-qf27-symbol="MSFT"]')).to_be_visible()
        await page.locator('#qf37-company-search').press('ArrowDown')
        await page.locator('#qf37-company-search').press('Enter')
        await expect(page.locator('#qf37-research-home')).to_be_hidden()
        await expect(page.locator('#qf-v20-symbol')).to_have_text('MSFT')
        await expect(page.locator('#qf32-summary')).to_contain_text('Investment research summary', timeout=30000)
        await expect(page.locator('#qf-v20-run-state')).to_contain_text('Calculated for', timeout=30000)
        before_unsupported = await page.evaluate('qf34CompanyReads')
        await page.evaluate("QFWorkspace34.research('BTC/USD')")
        await expect(page.locator('#qf37-research-home')).to_be_visible()
        await expect(page.locator('#qf37-selection-status')).to_contain_text('BTC/USD')
        assert await page.evaluate('QFResearch20.context().symbol') == 'MSFT'
        assert await page.evaluate('qf34CompanyReads') == before_unsupported
        await navigate(page, 'portfolio')
        await expect(page.locator('#page-portfolio')).to_be_visible()
        await navigate(page, 'explore')
        await expect(page.locator('#qf37-research-home')).to_be_visible()
        assert await page.evaluate('qf34Writes') == 0
    await page.locator('[data-qf34-workspace="discovery"]:visible').click()
    await expect(page.locator('#qf34-briefing')).to_be_visible()
    await expect(page.locator('#qf34-universe-status')).to_contain_text('Financial screen ready.')
    assert await page.locator('[data-qf35-select]:checked').count() == 3
    assert not await page.locator('#qf35-assumptions').get_attribute('open')
    for i in range(3):
        await page.locator('[data-qf35-select]').nth(i).uncheck()
    await expect(page.locator('#qf35-analyze-shortlist')).to_be_disabled()
    assert await page.locator('[data-qf35-select]').count() == 5
    for i in range(5):
        await page.locator('[data-qf35-select]').nth(i).check()
    assert await page.locator('[data-qf35-select]:checked').count() == 5
    for i in [3, 4]:
        await page.locator('[data-qf35-select]').nth(i).uncheck()
    await page.locator('[data-qf35-select]').first.focus()
    await page.keyboard.press('Space')
    assert await page.locator('[data-qf35-select]:checked').count() == 2
    await page.keyboard.press('Space')
    assert await page.locator('[data-qf35-select]:checked').count() == 3

    await expect(page.locator('#qf35-opportunities')).to_contain_text('Companies worth investigating')
    await expect(page.locator('#qf36-order-description')).to_contain_text('cash-flow proxy margin')
    assert await page.locator('#qf36-history').get_attribute('open') is None
    assert await page.locator('input[type="file"]:visible').count() == 0
    await page.locator('#qf35-filters > summary').click()
    for order, label in [('growth', 'annual revenue growth'), ('margin', 'operating margin'), ('cashMargin', 'cash-flow proxy margin')]:
        await page.locator('#qf34-order').select_option(order)
        await expect(page.locator('#qf36-order-description')).to_contain_text(label)
        expected = await page.evaluate("order => QFDecision34.screen({snapshot:QFPublishedSEC,health:QFHealthSnapshot30,eligible:{schema:'quantforge.research-universe.v34',licensed_private:true,items:QFPublishedSEC.companies.map(c=>({symbol:c.symbol}))},filters:{minGrowth:0,order}}).shortlist.map(r=>r.symbol)", order)
        assert await page.locator('[data-qf35-select]').evaluate_all('(els)=>els.map(e=>e.dataset.qf35Select)') == expected
    await page.locator('#qf34-min-growth').fill('20')
    await page.locator('#qf34-min-growth').dispatch_event('change')
    await expect(page.locator('#qf35-opportunities')).to_contain_text('20.0% minimum')
    await page.locator('#qf34-min-growth').fill('0')
    await page.locator('#qf34-min-growth').dispatch_event('change')
    await page.locator('#qf35-filters > summary').click()
    await page.locator('#qf36-selection-why > summary').click()
    await expect(page.locator('#qf36-selection-why')).to_contain_text('550 days')
    await expect(page.locator('#qf36-selection-why')).to_contain_text('not the best five investments')
    await page.locator('#qf36-selection-why > summary').click()

    symbol_before = await page.evaluate('QFResearch20.context().symbol')
    picks = await page.locator('[data-qf35-select]:checked').evaluate_all('(els)=>els.map(e=>e.dataset.qf35Select)')
    await page.evaluate('(symbol)=>window.qf35Failed=symbol', picks[1])
    await page.evaluate('(symbol)=>window.qf35Partial=symbol', picks[0])
    await page.locator('#qf35-analyze-shortlist').dblclick()
    try:
        await page.wait_for_function("() => document.querySelectorAll('.qf35-result').length===3&&[...document.querySelectorAll('.qf35-result')].every(e=>/Complete coverage|Partial coverage|Outdated evidence|Provider unavailable|Research failed/.test(e.textContent))", timeout=90000)
    except Exception:
        print(engine, width, 'isolated fixture timeout diagnostics', await page.locator('.qf35-result').all_text_contents(), errors, flush=True)
        raise
    await expect(page.locator('#qf35-analyze-shortlist')).to_be_enabled(timeout=60000)
    states = await page.locator('.qf35-result').all_text_contents()
    assert len(states) == 3
    assert 'Provider unavailable' in states[1], states
    assert 'Provider unavailable' in states[0]
    assert 'Complete coverage' in states[2] or 'Partial coverage' in states[2] or 'Outdated evidence' in states[2]
    assert await page.locator('.qf34-shortlist .qf35-result').count() == 0
    assert await page.locator('#qf36-results .qf35-result').count() == 3
    await expect(page.locator('#qf36-results')).to_contain_text('Research coverage')
    await expect(page.locator('#qf36-results')).to_contain_text('Research disposition')
    assert await page.evaluate('QFResearch20.context().symbol') == symbol_before
    assert '[object Object]' not in await page.locator('#qf34-briefing').inner_text()
    assert await page.evaluate('qf34Writes') == 0
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    await page.screenshot(path=str(OUT / f'{engine}-{width}-batch-partial.png'), full_page=True)
    await page.evaluate('window.qf35Failed="";window.qf35Partial=""')
    if width == 390:
        for i in range(5):
            await page.locator('[data-qf35-select]').nth(i).check()
        await page.locator('#qf35-analyze-shortlist').click()
        await expect(page.locator('#qf35-analyze-shortlist')).to_be_enabled(timeout=90000)
        assert await page.locator('#qf36-results .qf35-result').count() == 5
        assert await page.evaluate('qf34Writes') == 0
        await page.screenshot(path=str(OUT / f'{engine}-{width}-five-results.png'), full_page=True)
    await page.locator('[data-qf34-symbol="'+picks[0]+'"]:visible').first.click()
    await expect(page.locator('#qf32-summary')).to_contain_text('Investment research summary', timeout=30000)
    await expect(page.locator('#qf35-company-details')).not_to_have_attribute('open', '')
    assert await page.locator('.qf35-primary-evidence li').count() <= 6
    await page.locator('#qf35-company-details > summary').click()
    await expect(page.locator('#qf35-company-details')).to_contain_text('Coverage of this company assessment')
    await page.screenshot(path=str(OUT / f'{engine}-{width}-assessment-detail.png'), full_page=True)
    await page.locator('[data-qf34-workspace="discovery"]:visible').click()
    await page.locator('#qf35-assumptions > summary').click()
    await page.locator('[data-qf34-rule="maxWeight"]').fill('20')
    await page.locator('#qf34-rules button[type="submit"]').click()
    assert await page.evaluate('QFWorkspace34.rules().maxWeight') == .2
    assert await page.locator('.qf35-result').count() == 0
    await page.locator('#qf35-assumptions > summary').click()
    await page.evaluate('(symbol)=>window.qf35Held=symbol', picks[0])
    await page.locator('#qf35-analyze-shortlist').click()
    await page.wait_for_function('() => qf35Started')
    await page.locator('#qf24-switch-mode').click()
    await page.evaluate('qf35Release()')
    await expect(page.locator('#qf34-briefing')).to_be_hidden()
    await expect(page.locator('#qf34-briefing')).to_be_empty()
    await expect(page.locator('#qf37-company-options')).to_be_empty()
    await expect(page.locator('#qf37-selection-status')).to_be_empty()
    assert await page.evaluate('qf34Writes') == 0
    assert not errors, errors
    await page.close()
    return {'engine': engine, 'width': width, 'independentSelection': True, 'partialFailurePreserved': True, 'cancelledOnPublic': True, 'writes': 0}

async def auth_rejection(browser, engine):
    page, errors = await setup(browser, 390)
    for fixture in [EXTEND, FIXED, EXTRA, FAULTS]:
        await page.evaluate(fixture)
    await enter(page)
    await page.locator('#private-login-submit').click()
    await expect(page.locator('#qf37-research-home')).to_be_visible()
    assert await page.locator('#qf-v20-navigation [data-page]').all_text_contents() == ['Explore', 'Compare', 'Models', 'Portfolio', 'Methods']
    assert await page.locator('#qf34-workspace-nav, #qf37-secondary').count() == 0
    assert await page.locator('#qf37-research-home .qf34-shortlist').count() == 0
    assert await page.locator('#qf37-research-home [data-qf34-workspace="research"]').count() == 1
    assert await page.evaluate('qf34UniverseReads') == 0
    reads_before_selection = await page.evaluate('qf34CompanyReads')
    await page.locator('#qf37-research-home [data-qf34-workspace="research"]').click()
    await expect(page.locator('#qf37-company-search')).to_be_focused()
    await expect(page.locator('#qf37-research-home')).to_be_visible()
    await expect(page.locator('#qf37-selection-status')).to_contain_text('select the matching listing')
    assert await page.evaluate('qf34CompanyReads') == reads_before_selection
    home_bounds = await page.locator('#qf37-research-home').bounding_box()
    content_bounds = await page.locator('#page-explore').bounding_box()
    assert home_bounds['width'] >= content_bounds['width'] - 4
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    await page.screenshot(path=str(OUT / f'{engine}-{page.viewport_size["width"]}-research-home.png'), full_page=True)
    await page.locator('[data-qf34-workspace="discovery"]:visible').click()
    await expect(page.locator('#qf34-universe-status')).to_contain_text('Financial screen ready.')
    picks = await page.locator('[data-qf35-select]:checked').evaluate_all('(els)=>els.map(e=>e.dataset.qf35Select)')
    await page.evaluate('(symbol)=>{qf35AuthFailure=symbol;qf35ReadSymbols=[];}', picks[1])
    await page.locator('#qf35-analyze-shortlist').click()
    await page.wait_for_function('() => !QFPrivateBridgeV23.ready()', timeout=90000)
    await expect(page.locator('#qf34-briefing')).to_be_empty()
    await expect(page.locator('#qf37-company-options')).to_be_empty()
    await expect(page.locator('#qf37-selection-status')).to_be_empty()
    assert await page.locator('.qf35-result').count() == 0
    assert await page.evaluate('QFPrivateBridgeV23.snapshot()') is None
    await expect(page.locator('#private-positions')).to_be_empty()
    await expect(page.locator('#private-notes')).to_be_empty()
    await expect(page.locator('#qf31-session-notice')).to_contain_text('authorization could not be verified')
    assert picks[2] not in await page.evaluate('qf35ReadSymbols')
    assert await page.evaluate('qf35Revocations') == 0
    assert await page.evaluate('qf34Writes') == 0
    assert not errors, errors
    await page.close()
    print(engine, 'mid-batch authorization rejection clears all results and stops later companies PASS', flush=True)
    return {'engine': engine, 'authRejected': True, 'privateCleared': True, 'laterCompanyPrevented': True, 'writes': 0}

async def run():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    async with async_playwright() as pw:
        for engine in os.environ.get('QF_TEST_BROWSERS', 'chromium,firefox,webkit').split(','):
            browser = await getattr(pw, engine).launch()
            for width in [int(x) for x in os.environ.get('QF_DEFINITIVE_WIDTHS', '320,390,768,1024,1440').split(',')]:
                rows.append(await private_journey(browser, engine, width))
                print(engine, width, 'isolated shortlist / partial failure / assessment / rules / cancellation PASS', flush=True)
            rows.append(await auth_rejection(browser, engine))
            await browser.close()
    (OUT / 'results.json').write_text(json.dumps(rows, indent=2))

if __name__ == '__main__':
    asyncio.run(run())
