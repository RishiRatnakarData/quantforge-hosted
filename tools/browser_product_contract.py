"""Shared browser actions for the approved picker and transaction workflow."""
from playwright.async_api import expect


async def pick_compare(page, symbol):
    await page.locator('#qf-v20-compare-search').fill(symbol)
    await page.locator(f'#qf27-compare-options [data-qf27-symbol="{symbol}"]').click()


async def virtual_buy(page, symbol, amount):
    await page.locator('#qf27-buy').click()
    await page.locator('#qf27-trade-query').fill(symbol)
    await page.locator(f'#qf27-trade-options [data-qf27-symbol="{symbol}"]').click()
    await page.locator('#qf27-trade-amount').fill(str(amount))
    await page.locator('#qf27-preview').click()
    await expect(page.locator('#qf27-preview-result')).to_contain_text('Resulting cash')
    await page.locator('#qf27-confirm').click()
    await expect(page.locator('#qf27-trade-status')).to_contain_text('recorded')


PRODUCT_TRADES = r'''() => {
 const original=fetch;
 window.fetch=async(url,options={})=>{
  const path=String(url),response=(data,status=200)=>({ok:status<400,status,json:async()=>structuredClone(data)});
  if(!path.includes('private/trade'))return original(url,options);
  const input=JSON.parse(options.body);if(input.expected_version!==qfMockVersion)return response({detail:'Version conflict'},409);
  const buy=input.side==='buy',units=buy?Math.floor(Number(input.amount)/(300*1.0005)*1e8)/1e8:Number(input.amount),gross=Math.round(units*300*100)/100,fee=Math.round(gross*.0005*100)/100,impact=buy?-gross-fee:gross-fee;
  if(!buy&&units>Number(qfMockOwner.holdings[input.symbol]||0))return response({detail:'Too many units'},422);
  const preview={symbol:input.symbol,side:input.side,units,gross,fee,price:300,cash_before:qfMockOwner.cash,cash_after:Math.round((qfMockOwner.cash+impact)*100)/100,cash_impact:impact,venue:'MOCK',observed_at:new Date().toISOString()};
  if(path.includes('trade-preview'))return response({preview,version:qfMockVersion});
  qfMockOwner.cash=preview.cash_after;qfMockOwner.holdings[input.symbol]=(qfMockOwner.holdings[input.symbol]||0)+(buy?units:-units);qfMockOwner.trades.unshift({...preview,at:new Date().toISOString()});qfMockVersion++;
  return response({portfolio:qfMockOwner,version:qfMockVersion,paper_only:true});
 };
}'''


async def navigate(page, route):
    """Use the same visible persistent navigation in both data modes."""
    control = page.locator(f'#qf-v20-navigation [data-page="{route}"]')
    await expect(control).to_be_visible()
    await control.click()
    await expect(page.locator(f'#page-{route}')).to_be_visible()
    await expect(control).to_have_attribute('aria-current', 'page')


async def open_company_research(page):
    """Open Explore, then explicitly enter its Private company workflow."""
    await navigate(page, 'explore')
    if await page.locator('body').evaluate("e=>e.classList.contains('qf37-private')"):
        await expect(page.locator('#qf37-research-home')).to_be_visible()
        symbol = await page.evaluate('QFResearch20.context().symbol')
        await page.locator('#qf37-company-search').fill(symbol)
        await page.locator(f'#qf37-company-options [data-qf27-symbol="{symbol}"]').click()
        await expect(page.locator('#qf37-research-home')).to_be_hidden()


async def audit_shared_navigation(page, mode, engine, width, out):
    """Rendered visibility, operation, focus, active state and history in each mode."""
    routes = ['explore', 'compare', 'models', 'portfolio', 'methods']
    controls = page.locator('#qf-v20-navigation [data-page]')
    assert await controls.all_text_contents() == ['Explore', 'Compare', 'Models', 'Portfolio', 'Methods']
    saved = await page.evaluate('JSON.stringify({owner:qfMockOwner,version:qfMockVersion})')
    rows = []
    for route in routes:
        await navigate(page, route)
        assert await page.locator('#qf-v20-navigation [aria-current="page"]').count() == 1
        assert await page.locator('#qf-v20-navigation .active').count() == 1
        for i in range(5):
            control = controls.nth(i)
            await expect(control).to_be_visible()
            await expect(control).to_be_enabled()
            await expect(control).to_be_in_viewport()
            bounds = await control.evaluate('e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {text:e.textContent.trim(),font:s.font,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,display:s.display,visibility:s.visibility,opacity:Number(s.opacity),left:r.left,right:r.right,width:r.width,height:r.height,viewport:innerWidth,clipped:e.scrollWidth>e.clientWidth+2}}')
            assert bounds['display'] != 'none' and bounds['visibility'] == 'visible' and bounds['opacity'] > 0, bounds
            assert bounds['height'] >= 44 and bounds['left'] >= 0 and bounds['right'] <= bounds['viewport'] + 1, bounds
            assert not bounds['clipped'], bounds
        assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        if width <= 800:
            nav_rows = await controls.evaluate_all('(nodes)=>nodes.map(e=>Math.round(e.getBoundingClientRect().top))')
            if width <= 420:
                assert len(set(nav_rows)) == 2 and nav_rows[:3] == [nav_rows[0]] * 3 and nav_rows[3:] == [nav_rows[3]] * 2, nav_rows
                assert await page.locator('.side').evaluate('e=>e.getBoundingClientRect().height') <= 180
            else:
                assert max(nav_rows) - min(nav_rows) <= 1, nav_rows
                assert await page.locator('.side').evaluate('e=>e.getBoundingClientRect().height') <= 160
        if mode == 'private' and route == 'explore':
            await expect(page.locator('#qf37-research-home')).to_be_visible()
        if mode == 'private' and route == 'portfolio':
            await expect(page.locator('#qf24-transactions')).to_be_visible()
        await page.screenshot(path=str(out / f'{engine}-{width}-{mode}-nav-{route}.png'))
        rows.append({'route':route,'allFiveVisible':True,'correctActiveState':True,'pageVisible':True})
    await controls.first.focus()
    for i in range(5):
        await expect(controls.nth(i)).to_be_focused()
        if i < 4:
            await page.keyboard.press('Tab')
    await navigate(page, 'compare')
    await navigate(page, 'models')
    await page.go_back()
    await expect(page.locator('#page-compare')).to_be_visible()
    await expect(page.locator('#qf-v20-navigation [data-page="compare"]')).to_have_attribute('aria-current', 'page')
    await page.go_forward()
    await expect(page.locator('#page-models')).to_be_visible()
    await expect(page.locator('#qf-v20-navigation [data-page="models"]')).to_have_attribute('aria-current', 'page')
    for origin in ['explore', 'compare', 'models']:
        await navigate(page, origin)
        await navigate(page, 'portfolio')
        if mode == 'private':
            await expect(page.locator('#qf24-transactions')).to_be_visible()
        await navigate(page, 'explore')
        if mode == 'private':
            await expect(page.locator('#qf37-research-home')).to_be_visible()
    assert await page.evaluate('JSON.stringify({owner:qfMockOwner,version:qfMockVersion})') == saved
    assert await page.locator('#qf34-workspace-nav, #qf37-secondary').count() == 0
    return {'engine':engine,'width':width,'mode':mode,'routes':rows,'keyboardOrder':True,'backForward':True,'ownerUnchanged':True,'portfolioEntryFromExploreCompareModels':True}
