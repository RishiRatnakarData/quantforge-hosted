"""Actual HTTPS-root Home acceptance using isolated published SEC data only."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'public/index.html').read_text(encoding='utf-8')
CSP=next(line.strip().split(': ',1)[1] for line in (ROOT/'public/_headers').read_text().splitlines() if 'Content-Security-Policy:' in line)
OUT=ROOT/'outputs'/'home-v31'

async def visit(browser,width):
    page=await browser.new_page(viewport={'width':width,'height':880 if width>700 else 950})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    await page.route('**/*',lambda route:route.fulfill(status=200,content_type='text/html',body=HTML,headers={'Content-Security-Policy':CSP}) if route.request.resource_type=='document' else route.abort())
    await page.goto('https://quantforge-preview.invalid/')
    await page.wait_for_timeout(350)
    diagnostic=await page.evaluate("""() => ({url:location.href,hash:location.hash,
      protocol:location.protocol,route:document.querySelector('.tabpage.active')?.id,
      shell:window.QFUnifiedPrivate23?.state(),secLoaded:Boolean(window.QFPublishedSEC),
      landingHidden:document.querySelector('#qf-v23-landing')?.hidden})""")
    print('Home startup diagnostic',diagnostic,'errors',errors[:4],flush=True)
    assert await page.locator('#qf-v23-landing').is_visible(),(diagnostic,errors[:4])
    assert await page.locator('#qf-v23-explore-content').is_hidden()
    assert await page.locator('#qf-v23-landing svg, #qf31-home-chart').count()==0
    assert await page.locator('.qf31-home-steps button[data-qf33-home]').count()==5
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    await page.screenshot(path=str(OUT/f'home-{width}.png'),full_page=True)
    await page.locator('#qf24-home-search').fill('Microsoft')
    await page.locator('#qf24-home-find').click()
    assert await page.locator('#qf-v23-explore-content').is_visible()
    assert 'Microsoft' in await page.locator('#qf-v20-search').input_value()
    assert await page.locator('#qf-v20-company').inner_text()=='Microsoft'
    await page.locator('#qf-v23-home-button').click()
    assert await page.locator('#qf-v23-landing').is_visible()
    await page.locator('#qf-v20-navigation [data-page="compare"]').click()
    assert await page.locator('#page-compare').is_visible()
    assert await page.locator('#qf-v23-landing').is_hidden()
    assert not errors,errors
    await page.close()
    return {'width':width,'home':True,'search':True,'navigation':True,'no_browser_errors':True}

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as pw:
        browser=await pw.chromium.launch()
        results=[]
        for width in (320,390,768,1024,1440):
            results.append(await visit(browser,width))
        await browser.close()
    (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print('Fresh HTTPS-root Home and navigation: five widths PASS')

if __name__=='__main__':
    asyncio.run(main())
