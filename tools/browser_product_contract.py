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
