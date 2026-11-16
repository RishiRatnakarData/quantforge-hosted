"""Final release regressions. All authentication and account state are isolated fixtures."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright, expect
from smoke_rebuild_browser import FIXTURE

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'public/index.html').read_text(encoding='utf-8')
CSP=next(s.split(': ',1)[1] for s in (ROOT/'public/_headers').read_text().splitlines() if 'Content-Security-Policy:' in s)
OUT=ROOT/'outputs/final-release32'

async def setup(browser,width=390):
    page=await browser.new_page(viewport={'width':width,'height':950})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    await page.route('**/*',lambda r:r.fulfill(status=200,content_type='text/html',body=HTML,headers={'Content-Security-Policy':CSP}) if r.request.resource_type=='document' else r.abort())
    await page.goto('https://final-release.invalid/')
    await page.evaluate(FIXTURE)
    await page.evaluate("""() => {const original=fetch;window.fetch=(u,o)=>String(u).includes('auth/session')?Promise.resolve({ok:true,json:async()=>({signed_in:false})}):original(u,o)}""")
    return page,errors

async def enter(page):
    await page.locator('#qf-v20-mode').click()
    await expect(page.locator('#private-message')).to_contain_text('Sign in to continue')
    await page.locator('#private-email').fill('isolated'+'@'+'example.invalid')
    await page.locator('#private-password').fill('fixture-only')

async def recovery(browser):
    # Simulate a 100-second startup using the browser clock, not a real host spin-up.
    page,errors=await setup(browser)
    await enter(page)
    await page.clock.install()
    await page.evaluate("""() => {const original=fetch,start=Date.now();window.recovery32={health:0,login:0};window.fetch=async(u,o)=>{
      if(String(u).includes('/api/health')){recovery32.health++;return {ok:Date.now()-start>=95000,status:503,json:async()=>({status:'ok'})};}
      if(String(u).includes('auth/login'))recovery32.login++;
      return original(u,o);
    }}""")
    await page.locator('#private-login-submit').click()
    await page.clock.run_for(100500)
    await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE')
    assert await page.evaluate('recovery32.login')==1
    assert await page.evaluate('recovery32.health')>=13
    assert not errors,errors
    await page.close()
    # An uncertain login response is NEVER automatically replayed, even after health succeeds.
    page,errors=await setup(browser)
    await enter(page)
    await page.evaluate("""() => {const original=fetch;window.loginPosts=0;window.fetch=async(u,o)=>{if(String(u).includes('auth/login')){loginPosts++;throw Error('timeout after possible completion');}return original(u,o)}}""")
    await page.locator('#private-login-submit').click()
    await expect(page.locator('#private-message')).to_contain_text('Could not reach')
    await page.wait_for_timeout(300)
    assert await page.evaluate('loginPosts')==1
    assert not errors,errors
    await page.close()
    # Signing out while health is pending cancels login before credential submission.
    page,errors=await setup(browser)
    await enter(page)
    await page.evaluate("""() => {const original=fetch;window.loginPosts=0;window.fetch=(u,o)=>{if(String(u).includes('/api/health'))return new Promise(resolve=>window.finishWake=()=>resolve({ok:true,json:async()=>({status:'ok'})}));if(String(u).includes('auth/login'))loginPosts++;return original(u,o)}}""")
    await page.locator('#private-login-submit').click()
    await page.wait_for_function('Boolean(window.finishWake)')
    await page.evaluate('QFPrivateBridgeV23.signOut()')
    await page.evaluate('finishWake()')
    await expect(page.locator('#private-login-submit')).to_be_enabled()
    assert await page.evaluate('loginPosts')==0
    assert not await page.evaluate('QFPrivateBridgeV23.ready()')
    assert not errors,errors
    await page.close()
    # Hosting verification is distinct from a sleeping service and must not be hammered.
    page,errors=await setup(browser)
    await enter(page)
    await page.evaluate("""() => {const original=fetch;window.challengeCalls={health:0,login:0};window.fetch=(u,o)=>{if(String(u).includes('/api/health')){challengeCalls.health++;return Promise.resolve(new Response(JSON.stringify({code:'hosting_verification'}),{status:503}));}if(String(u).includes('auth/login'))challengeCalls.login++;return original(u,o)}}""")
    await page.locator('#private-login-submit').click()
    await expect(page.locator('#private-message')).to_contain_text('verification page')
    assert await page.evaluate('challengeCalls')=={'health':1,'login':0}
    assert not errors,errors
    await page.close()
    # A persistent outage stops at its deadline without ever sending credentials.
    page,errors=await setup(browser)
    await enter(page)
    await page.clock.install()
    await page.evaluate("""() => {const original=fetch;window.loginPosts=0;window.fetch=async(u,o)=>{if(String(u).includes('/api/health'))return {ok:false,status:503};if(String(u).includes('auth/login'))loginPosts++;return original(u,o)}}""")
    await page.locator('#private-login-submit').click()
    await page.clock.run_for(121000)
    await expect(page.locator('#private-message')).to_contain_text('still unavailable')
    assert await page.evaluate('loginPosts')==0
    await expect(page.locator('#private-login-submit')).to_be_enabled()
    assert not errors,errors
    await page.close()


    # An unmarked hosting rate limit waits before another readiness GET, then submits login once.
    page,errors=await setup(browser)
    await enter(page)
    await page.clock.install()
    await page.evaluate("""() => {const original=fetch;window.rateCalls={health:0,login:0};window.fetch=(u,o)=>{
      if(String(u).includes('/api/health')){rateCalls.health++;return Promise.resolve(rateCalls.health===1?{ok:false,status:503,json:async()=>({code:'hosting_rate_limited',retry_after_seconds:30})}:{ok:true,status:200,json:async()=>({status:'ok'})});}
      if(String(u).includes('auth/login'))rateCalls.login++;return original(u,o);
    }}""")
    await page.locator('#private-login-submit').click()
    await expect(page.locator('#private-message')).to_contain_text('requested a pause')
    await page.clock.run_for(29000)
    assert await page.evaluate('rateCalls')=={'health':1,'login':0}
    await page.clock.run_for(4000)
    await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE')
    assert await page.evaluate('rateCalls')=={'health':2,'login':1}
    assert not errors,errors
    await page.close()
    # Persistent rate limits stop after three reads and never transmit credentials.
    page,errors=await setup(browser)
    await enter(page)
    await page.clock.install()
    await page.evaluate("""() => {const original=fetch;window.rateCalls={health:0,login:0};window.fetch=(u,o)=>{
      if(String(u).includes('/api/health')){rateCalls.health++;return Promise.resolve({ok:false,status:503,json:async()=>({code:'hosting_rate_limited',retry_after_seconds:30})});}
      if(String(u).includes('auth/login'))rateCalls.login++;return original(u,o);
    }}""")
    await page.locator('#private-login-submit').click()
    await page.clock.run_for(121000)
    await expect(page.locator('#private-message')).to_contain_text('still unavailable')
    assert await page.evaluate('rateCalls')=={'health':3,'login':0},await page.evaluate('rateCalls')
    assert not errors,errors
    await page.close()
    # A provider pause longer than the remaining deadline must not be shortened.
    page,errors=await setup(browser)
    await enter(page)
    await page.clock.install()
    await page.evaluate("""() => {const original=fetch;window.rateCalls={health:0,login:0};window.fetch=(u,o)=>{
      if(String(u).includes('/api/health')){rateCalls.health++;return Promise.resolve({ok:false,status:503,json:async()=>({code:'hosting_rate_limited',retry_after_seconds:180})});}
      if(String(u).includes('auth/login'))rateCalls.login++;return original(u,o);
    }}""")
    await page.locator('#private-login-submit').click()
    await page.clock.run_for(121000)
    await expect(page.locator('#private-message')).to_contain_text('still unavailable')
    assert await page.evaluate('rateCalls')=={'health':1,'login':0}
    assert not errors,errors
    await page.close()

async def journey(browser,engine,width):
    page,errors=await setup(browser,width)
    await expect(page.locator('#qf-v23-landing')).to_be_visible()
    assert await page.locator('#qf-v23-landing svg, #qf31-home-chart, #qf-v23-landing details').count()==0
    await page.locator('#qf24-home-search').fill('NVIDIA')
    await page.locator('#qf32-home-options [data-qf27-symbol="NVDA"]').click()
    await expect(page.locator('#qf-v20-company')).to_have_text('NVIDIA')
    await page.locator('#qf-v20-navigation [data-page="models"]').click()
    assert await page.evaluate('QFResearch20.context().symbol')=='NVDA'
    await page.locator('#qf-v23-home-button').click()
    await page.locator('#qf24-home-search').fill('Microsoft')
    await page.locator('#qf24-home-find').click()
    await expect(page.locator('#qf-v20-company')).to_have_text('Microsoft')
    await enter(page)
    await page.locator('#private-login-submit').click()
    await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE')
    await page.wait_for_function("QFResearch20.context().origin==='market'")
    await page.locator('[data-qf27-explore="brief"]').click()
    await expect(page.locator('#qf32-summary')).to_be_visible()
    await expect(page.locator('#qf32-summary')).to_contain_text('Brier')
    await expect(page.locator('#qf32-summary')).to_contain_text('Already held')
    await page.locator('#qf32-horizon').select_option('long')
    await page.locator('#qf32-drawdown').select_option('0.15')
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    await page.screenshot(path=str(OUT/f'{engine}-{width}-summary-fixture.png'),full_page=True)
    await page.locator('#qf32-summary [data-qf30-action="prediction"]').click()
    await expect(page.locator('#page-models')).to_be_visible()
    assert await page.locator('[data-qf-c22-phase]').count()==3
    await expect(page.locator('[data-qf-c22-phase="evaluation"]')).to_have_attribute('aria-selected','true')
    await page.locator('#qf-v20-navigation [data-page="explore"]').click()
    await page.locator('#qf24-switch-mode').click()
    await expect(page.locator('#qf32-summary')).to_be_hidden()
    assert await page.locator('#qf32-summary').inner_text()==''
    await page.locator('#qf24-switch-mode').click()
    await page.wait_for_function("QFResearch20.context().origin==='market'")
    await page.evaluate('QFPrivateBridgeV23.signOut()')
    assert await page.locator('#qf32-summary').inner_text()==''
    assert not errors,errors
    await page.close()
    return {'browser':engine,'width':width,'direct_picker':True,'continuity':True,'private_summary':True,'isolation':True}

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[]
    async with async_playwright() as pw:
        for engine in ('chromium','firefox','webkit'):
            browser=await getattr(pw,engine).launch()
            await recovery(browser)
            for width in (320,390,768,1024,1440):
                results.append(await journey(browser,engine,width))
                print(engine,width,'Home picker, private synthesis and isolation PASS',flush=True)
            await browser.close()
    (OUT/'critical-verification.json').write_text(json.dumps({'fixtures_only':True,'simulated_recovery':'100-second success; bounded persistent outage; uncertain login never replayed','journeys':results},indent=2))

if __name__=='__main__':
    asyncio.run(main())
