"""Guided research acceptance. All private IO is isolated fixture state."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright, expect
from smoke_rebuild_browser import FIXTURE

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('QF_SCREENSHOT_DIR',str(ROOT/'outputs/guided-research')))
HTML=(ROOT/'public/index.html').read_text(encoding='utf-8')
CSP=next(line.strip().split(': ',1)[1] for line in (ROOT/'public/_headers').read_text().splitlines() if 'Content-Security-Policy:' in line)

async def login(page):
    await page.locator('#qf-v20-mode').click()
    await page.locator('#private-email').fill('fixture'+'@'+'example.invalid')
    await page.locator('#private-password').fill('isolated-fixture')
    await page.locator('#private-login-submit').click()
    await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE')

async def run():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[]
    async with async_playwright() as pw:
        for engine in os.environ.get('QF_TEST_BROWSERS','chromium,firefox,webkit').split(','):
            browser=await getattr(pw,engine).launch()
            for width in (320,390,768,1024,1440):
                page=await browser.new_page(viewport={'width':width,'height':1000})
                errors=[]
                page.on('pageerror',lambda e, errors=errors:errors.append(str(e)))
                await page.route('**/*',lambda route:route.fulfill(status=200,content_type='text/html',body=HTML,headers={'Content-Security-Policy':CSP}) if route.request.resource_type=='document' else route.abort())
                await page.goto('https://guided.invalid/#explore/news')
                assert await page.evaluate('location.hash')=='#explore'
                assert await page.locator('#qf-v20-news, [data-qf27-explore="context"]').count()==0
                await page.locator('[data-qf27-finance="health"]').click()
                await expect(page.locator('#qf-v20-financial-chart')).to_contain_text('Current ratio')
                await expect(page.locator('#qf-v20-financial-chart')).to_contain_text('0001193125-26-323660')
                await page.screenshot(path=str(OUT/f'{engine}-{width}-balance-sheet.png'),full_page=True)
                await page.locator('#qf27-analyze').click()
                await expect(page.locator('#qf30-guide')).to_contain_text('Separate price from valuation')
                await page.locator('[data-qf30-action="compare"]').evaluate('(e)=>e.closest("details").open=true')
                await page.locator('[data-qf30-action="compare"]').click()
                await expect(page.locator('#qf-v20-compare-chips')).to_contain_text('MSFT')
                await page.evaluate(FIXTURE)
                await login(page)
                await page.locator('[data-qf27-explore="research"]').click()
                await page.locator('#qf30-interest').fill('Fixture thesis: investigate cash generation <script>')
                await page.locator('#qf30-more-prompts summary').click()
                await page.locator('#qf30-concerns').fill('Capital spending and missing segment evidence')
                await page.locator('#qf30-review').fill('2027-01-15')
                await page.locator('#qf30-save').click()
                await expect(page.locator('#qf30-journal-status')).to_contain_text('Thesis saved')
                original=await page.evaluate('structuredClone(qfMockOwner.notes[0])')
                await page.locator('[data-qf-v23-edit="0"]').click()
                await expect(page.locator('#qf30-revision-context')).to_contain_text('current financial period')
                await expect(page.locator('#qf30-revision-context')).to_contain_text('Recorded revenue')
                await page.locator('#qf30-change').fill('Negative FCF in two later reports would change my view')
                await page.locator('#qf30-save').click()
                await expect(page.locator('#qf-v23-note-list')).to_contain_text('revision 2')
                assert await page.evaluate('qfMockOwner.notes.length')==2
                assert await page.evaluate('qfMockOwner.notes[1]')==original
                assert await page.locator('#qf-v23-note-list script').count()==0
                await page.screenshot(path=str(OUT/f'{engine}-{width}-thesis-fixture.png'),full_page=True)
                saved=await page.evaluate('({owner:structuredClone(qfMockOwner),version:qfMockVersion})')
                await page.reload()
                await page.evaluate(FIXTURE)
                await page.evaluate('(s)=>{qfMockOwner=s.owner;qfMockVersion=s.version}',saved)
                await login(page)
                await page.locator('[data-qf27-explore="research"]').click()
                await expect(page.locator('#qf-v23-note-list')).to_contain_text('revision 2')
                await expect(page.locator('#qf-v23-note-list')).to_contain_text('revision 1')
                await page.evaluate('''async()=>{while(qfMockOwner.notes.length<100)qfMockOwner.notes.push({text:'preserved original',at:'2026-01-01',symbol:'AAPL'});await QFPrivateBridgeV23.refresh();window.qfBeforeFull=JSON.stringify(qfMockOwner.notes);}''')
                await page.locator('#qf30-interest').fill('Must not discard any saved record')
                await page.locator('#qf30-save').click()
                await expect(page.locator('#qf30-journal-status')).to_contain_text('full')
                assert await page.evaluate('JSON.stringify(qfMockOwner.notes)===qfBeforeFull')
                assert not await page.evaluate('qfMockRequests.some(p=>p.includes("news"))')
                await page.evaluate("QFResearch20.chooseAsset({symbol:'TEST',name:'Long-name unsupported research instrument with no compatible SEC company statements',asset_class:'us_equity',tradable:true})")
                await page.locator('[data-qf27-explore="financials"]').click()
                await page.locator('[data-qf27-finance="health"]').click()
                await expect(page.locator('#qf27-financial-interpretation')).to_contain_text('No compatible')
                await expect(page.locator('#qf-v20-financial-chart')).to_contain_text('Unavailable')
                assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')

                await page.locator('#qf24-switch-mode').click()
                assert 'Fixture thesis' not in await page.locator('body').inner_text()
                assert await page.locator('[data-qf27-explore="research"]').is_hidden()
                await page.locator('#qf24-switch-mode').click()
                await page.locator('#qf-v20-navigation [data-page="portfolio"]').click()
                await expect(page.locator('#qf-b21-owner-account')).to_be_visible()
                await page.locator('#qf24-switch-mode').click()
                await expect(page.locator('#qf-b21-owner-account')).to_be_hidden()
                await page.locator('#qf24-switch-mode').click()
                await expect(page.locator('#qf-b21-owner-account')).to_be_visible()
                await expect(page.locator('#qf-b21-owner-account-table')).to_contain_text('MSFT')
                await page.locator('#qf24-switch-mode').click()
                await page.locator('#qf-v20-navigation [data-page="methods"]').click()
                await page.locator('[data-qf-c22-method="statistical"]').click()
                assert await page.locator('[data-qf27-method="nlp"]').count()==0
                assert await page.locator('#qf27-lab-output math').count()>0
                assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert not errors,errors
                results.append({'browser':engine,'width':width,'pass':True})
                print(engine,width,'health / thesis revision / reload / full archive / isolation PASS',flush=True)
                await page.close()
            await browser.close()
    (OUT/'verification.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    asyncio.run(run())
