"""Isolated HTTPS/CSP session lifecycle regressions; never uses real accounts."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright, expect
from smoke_rebuild_browser import FIXTURE

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'public/index.html').read_text(encoding='utf-8')
CSP = next(line.split(': ', 1)[1] for line in (ROOT / 'public/_headers').read_text().splitlines()
           if 'Content-Security-Policy:' in line)
OUT = ROOT / 'outputs/session-lifecycle'
KEY = 'qf-restore-verified-private-v1'


async def setup(browser, mode):
    context = await browser.new_context(viewport={'width': 390, 'height': 950})
    page = await context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    await page.route('**/*', lambda route: route.fulfill(
        status=200, content_type='text/html', body=HTML,
        headers={'Content-Security-Policy': CSP})
        if route.request.resource_type == 'document' else route.abort())
    script = '(' + FIXTURE + ')();' + r'''
    (() => {
      const original=window.fetch, mode=MODE;
      const response=(body,status=200)=>Promise.resolve(new Response(JSON.stringify(body),{
        status,headers:{'content-type':'application/json'}}));
      window.lifecycle={session:0,health:0,login:0,verify:0,logout:0};
      if(mode.startsWith('restore'))localStorage.setItem(KEY,'yes');
      window.fetch=(url,options={})=>{
        const p=String(url),calls=window.lifecycle;
        if(p.includes('auth/session')){
          calls.session++;
          if(mode==='restore-outage' && calls.session===1)return response({},503);
          if(mode==='restore-expired')return response({signed_in:false,mfa_required:false});
          if(mode==='restore-aal1')return response({signed_in:false,mfa_required:true});
          return response({signed_in:mode.startsWith('restore'),mfa_required:false});
        }
        if(p.includes('/api/health')){calls.health++;return response({status:'ok'});}
        if(p.includes('auth/login')){
          calls.login++;
          return response({signed_in:mode!=='mfa-race',mfa_required:mode==='mfa-race'});
        }
        if(p.includes('auth/mfa/factors'))return response({factor_id:'11111111-1111-4111-8111-111111111111'});
        if(p.includes('auth/mfa/verify')){
          calls.verify++;
          return new Promise(resolve=>window.finishVerification=()=>resolve(new Response(
            JSON.stringify({signed_in:true,mfa_required:false}),{status:200})));
        }
        if(p.includes('auth/logout')){calls.logout++;return response({signed_in:false},mode==='logout-outage'?503:200);}
        return original(url,options);
      };
    })();
    '''.replace('MODE', json.dumps(mode)).replace('KEY', json.dumps(KEY))
    await page.add_init_script(script=script)
    await page.goto('https://session-lifecycle.invalid/')
    return context, page, errors


async def login(page):
    await page.locator('#qf-v20-mode').click()
    # Wait for the initial anonymous check before selecting the trusted-device option.
    await expect(page.locator('#private-message')).to_contain_text('Sign in to continue')
    await page.locator('#qf31-remember-session').check()
    await page.locator('#private-email').fill('fixture@example.com')
    await page.locator('#private-password').fill('isolated-fixture-password')
    await page.locator('#private-login-submit').click()


async def lifecycle(browser, engine):
    # Transient session failure retains preference and resumes through the MFA gate.
    context, page, errors = await setup(browser, 'restore-outage')
    await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE')
    assert await page.evaluate('lifecycle') == {
        'session': 2, 'health': 1, 'login': 0, 'verify': 0, 'logout': 0}
    assert await page.evaluate(f'localStorage.getItem({json.dumps(KEY)})') == 'yes'
    assert not errors, errors
    await context.close()

    # A failed network sign-out clears content and leaves a visible, honest notice.
    context, page, errors = await setup(browser, 'logout-outage')
    await login(page)
    await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE')
    await page.evaluate('QFPrivateBridgeV23.signOut()')
    await expect(page.locator('#qf31-session-notice')).to_be_visible()
    await expect(page.locator('#qf31-session-notice')).to_contain_text('could not be confirmed')
    assert not await page.evaluate('QFPrivateBridgeV23.ready()')
    assert await page.evaluate(f'localStorage.getItem({json.dumps(KEY)})') is None
    assert not errors, errors
    await context.close()

    # A password-only restored session still requires authenticator verification.
    context, page, errors = await setup(browser, 'restore-aal1')
    await page.locator('#qf-v20-mode').click()
    await expect(page.locator('#private-mfa')).to_be_visible()
    assert not await page.evaluate('QFPrivateBridgeV23.ready()')
    assert not any('private/state' in path for path in await page.evaluate('qfMockRequests'))
    assert not errors, errors
    await context.close()

    # An actually expired session clears the preference, without health polling.
    context, page, errors = await setup(browser, 'restore-expired')
    await page.wait_for_function('lifecycle.session===1')
    await page.wait_for_function(f'localStorage.getItem({json.dumps(KEY)})===null')
    assert not await page.evaluate('QFPrivateBridgeV23.ready()')
    assert await page.evaluate('lifecycle.health') == 0
    assert not errors, errors
    await context.close()

    # Opt-in persists across a new document, with no secret browser storage.
    context, page, errors = await setup(browser, 'login')
    await login(page)
    await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE')
    assert await page.evaluate('Object.entries(localStorage)') == [[KEY, 'yes']]
    await page.add_init_script(script="""(() => {
       const previous=window.fetch;
       window.fetch=(url,opts)=>String(url).includes('auth/session')
         ?Promise.resolve(new Response(JSON.stringify({signed_in:true,mfa_required:false}),{status:200}))
         :previous(url,opts);
    })();""")
    await page.reload()
    await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE')
    await page.screenshot(path=str(OUT / f'{engine}-restored-fixture.png'), full_page=True)
    await page.evaluate('QFPrivateBridgeV23.signOut()')
    assert not await page.evaluate('QFPrivateBridgeV23.ready()')
    assert await page.evaluate(f'localStorage.getItem({json.dumps(KEY)})') is None
    await page.reload()
    await expect(page.locator('#qf24-mode-label')).to_contain_text('PUBLIC')
    assert await page.evaluate('lifecycle.session') == 0
    assert not await page.evaluate('QFPrivateBridgeV23.ready()')
    assert not errors, errors
    await context.close()

    # Late MFA success cannot reveal account content or win the race with sign-out.
    context, page, errors = await setup(browser, 'mfa-race')
    await login(page)
    await expect(page.locator('#private-mfa')).to_be_visible()
    await page.locator('#private-mfa-code').fill('123456')
    await page.locator('#private-mfa-submit').click()
    await page.wait_for_function('lifecycle.verify===1')
    await page.evaluate('window.signoutDone=QFPrivateBridgeV23.signOut();void 0')
    assert not await page.evaluate('QFPrivateBridgeV23.ready()')
    await page.evaluate('finishVerification()')
    await page.evaluate('signoutDone')
    assert await page.evaluate('lifecycle.logout') == 1
    assert not await page.evaluate('QFPrivateBridgeV23.ready()')
    assert not any('private/state' in path for path in await page.evaluate('qfMockRequests'))
    assert await page.evaluate(f'localStorage.getItem({json.dumps(KEY)})') is None
    assert not errors, errors
    await context.close()
    print(engine, 'session outage / expiry / MFA / opt-in reload / logout race PASS', flush=True)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        for engine in ('chromium', 'firefox', 'webkit'):
            browser = await getattr(pw, engine).launch()
            try:
                await lifecycle(browser, engine)
            finally:
                await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
