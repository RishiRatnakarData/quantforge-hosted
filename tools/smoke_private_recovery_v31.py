"""Verify cold-start recovery and invalid-credential non-retry with isolated browser fixtures."""
from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright, expect
from smoke_rebuild_browser import FIXTURE

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'public/index.html').read_text(encoding='utf-8')

async def sign_in(page):
    await page.locator('#qf-v20-mode').click()
    await page.locator('#private-email').fill('fixture'+'@'+'example.invalid')
    await page.locator('#private-password').fill('fixture-password')
    await page.locator('#private-login-submit').click()

async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.launch()
        page=await browser.new_page(viewport={'width':390,'height':844})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        await page.set_content(HTML,wait_until='load')
        await page.evaluate(FIXTURE)
        # Entering the private gate performs a session check before password login.
        # Model the anonymous response explicitly instead of turning an unhandled
        # fixture route into a second, unrelated simulated network outage.
        await page.evaluate("""() => {
           const original=window.fetch;
           window.fetch=(url,options)=>String(url).includes('auth/session')
             ?Promise.resolve(new Response(JSON.stringify({signed_in:false,mfa_required:false}),{
                status:200,headers:{'content-type':'application/json'}}))
             :original(url,options);
        }""")
        await page.evaluate("""() => {
           const original=window.fetch;
           const calls={login:0,health:0};
           window.qfRecoveryCalls=calls;
           window.fetch=async(url,options={})=>{
             const p=String(url);
             if(p.includes('auth/login')){
               calls.login++;

             }
             if(p.includes('api/health')){
               calls.health++;
               if(calls.health===1)return new Response('<html>Service waking up</html>',{status:503,headers:{'content-type':'text/html'}});
               return new Response(JSON.stringify({status:'ok'}),{
                 status:200,headers:{'content-type':'application/json'}});
             }
             return original(url,options);
           };
        }""")
        await sign_in(page)
        await expect(page.locator('#qf24-mode-label')).to_contain_text('PRIVATE',timeout=8000)
        counts=await page.evaluate('window.qfRecoveryCalls')
        assert counts=={'login':1,'health':2},counts
        assert not errors,errors
        await page.close()

        page=await browser.new_page(viewport={'width':390,'height':844})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        await page.set_content(HTML,wait_until='load')
        await page.evaluate("""() => {
           window.qfRecoveryCalls={login:0,health:0};
           window.fetch=async(url)=>{
             const p=String(url);
             if(p.includes('auth/session'))return new Response(JSON.stringify({signed_in:false}),{
               status:200,headers:{'content-type':'application/json'}});
             if(p.includes('api/health')){window.qfRecoveryCalls.health++;return new Response(JSON.stringify({status:'ok'}),{headers:{'content-type':'application/json'}});}
             if(p.includes('auth/login')){window.qfRecoveryCalls.login++;
                return new Response(JSON.stringify({code:'unauthorized'}),{
                  status:401,headers:{'content-type':'application/json'}});}
             throw Error('Unexpected fixture request '+p);
           };
        }""")
        await sign_in(page)
        await expect(page.locator('#private-message')).to_contain_text('Sign-in could not be verified',timeout=5000)
        assert await page.evaluate('window.qfRecoveryCalls')=={'login':1,'health':1}
        assert not errors,errors
        await page.close()
        await browser.close()
    print('Readiness-first HTML 503 recovery and unauthorized-no-replay browser recovery PASS')

if __name__=='__main__':
    asyncio.run(main())
