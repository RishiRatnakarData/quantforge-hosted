"""Private consolidation acceptance. Isolated accounts and provider fixtures only."""

import asyncio
import json
import os
from pathlib import Path

from browser_product_contract import audit_shared_navigation, navigate, open_company_research
from playwright.async_api import async_playwright, expect
from smoke_completion_browser import EXTEND
from smoke_final_release32 import enter, setup
from smoke_master_quality_v33 import FIXED

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("QF_CONSOLIDATION_SCREENSHOTS", str(ROOT / "outputs/consolidation-v34")))
EXTRA = r"""() => {
 const original=fetch;window.qf34Writes=0;window.qf34UniverseReads=0;window.qf34CompanyReads=0;
 window.fetch=async(u,o={})=>{
  const path=String(u);
  if(o.method&&o.method!=='GET'&&!path.includes('auth/')){qf34Writes++;throw Error('No account mutation is permitted in this acceptance journey.');}
  if(path.includes('private/research-universe')){qf34UniverseReads++;return {ok:true,status:200,json:async()=>({schema:'quantforge.research-universe.v34',licensed_private:true,items:QFPublishedSEC.companies.map(c=>({symbol:c.symbol,name:c.name})),excluded:[],financial_cutoff:QFPublishedSEC.as_of,eligibility_checked_at:new Date().toISOString(),scope:'ISOLATED covered-universe fixture',limitations:'Not the whole market.'})};}
  if(path.includes('private/sec/company')){qf34CompanyReads++;await new Promise(r=>setTimeout(r,150));}
  return original(u,o);
 };
}"""


async def run():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    navigation_results = []
    async with async_playwright() as pw:
        for engine in ("chromium", "firefox", "webkit"):
            browser = await getattr(pw, engine).launch()
            for width in (320, 390, 768, 1024, 1440, 1920):
                page, errors = await setup(browser, width)
                await page.evaluate(EXTEND)
                await page.evaluate(FIXED)
                await page.evaluate(EXTRA)
                navigation_results.append(await audit_shared_navigation(page, 'public', engine, width, OUT))
                await enter(page)
                await page.locator("#private-login-submit").click()
                await expect(page.locator('#qf37-research-home')).to_be_visible()
                navigation_results.append(await audit_shared_navigation(page, 'private', engine, width, OUT))
                await page.locator('#qf37-research-home .qf37-advanced > summary').click()
                await page.locator('#qf37-research-home [data-qf34-configure]').click()
                await expect(page.locator('[data-qf34-rule="maxWeight"]')).to_be_focused()
                await page.locator('#qf35-assumptions > summary').click()
                await expect(page.locator("#qf34-briefing")).to_be_visible()
                await expect(page.locator("#qf34-universe-status")).to_contain_text(
                    "Financial screen ready."
                )
                assert 0 < await page.locator(".qf34-shortlist article").count() <= 5
                assert await page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                assert "[object Object]" not in await page.locator("#qf34-briefing").inner_text()
                assert await page.evaluate("qf34UniverseReads") == 1
                await page.screenshot(
                    path=str(OUT / f"{engine}-{width}-briefing.png"), full_page=True
                )
                await page.locator('#qf35-assumptions > summary').click()
                await page.locator('[data-qf34-rule="maxWeight"]').fill("15")
                await page.locator('#qf34-rules button[type="submit"]').click()
                assert await page.evaluate("QFWorkspace34.rules().maxWeight") == 0.15
                await open_company_research(page)
                await expect(page.locator("#qf27-analyze")).to_be_visible()
                await page.wait_for_function("QFResearch20.context().origin==='market'")
                await page.locator("#qf27-analyze").click()
                await expect(page.locator("#qf32-summary")).to_contain_text(
                    "Loaded held-position correlations: AAPL", timeout=30000
                )
                await expect(page.locator(".qf34-rule-trace")).to_contain_text("Maximum single-name weight")
                await page.screenshot(
                    path=str(OUT / f"{engine}-{width}-assessment.png"), full_page=True
                )
                # Rapid identical calculations share one provider read. No duplicate API fan-out.
                assert await page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                # Settle the preceding analysis before measuring a new concurrent pair.
                # Joining an already pending read correctly creates no additional request.
                await page.evaluate("QFDeepUI25.execute('company')")
                before = await page.evaluate("qf34CompanyReads")
                await page.evaluate(
                    "Promise.all([QFDeepUI25.execute('company'),QFDeepUI25.execute('company')])"
                )
                after = await page.evaluate("qf34CompanyReads")
                assert after == before + 1, {"engine": engine, "width": width, "before": before, "after": after}
                await page.locator('[data-qf34-workspace="discovery"]:visible').first.click()
                await page.locator("#qf36-history > summary").click()
                await expect(page.locator("#qf34-reviewed")).to_contain_text("MSFT")
                await navigate(page, 'portfolio')
                await expect(page.locator("#page-portfolio")).to_be_visible()
                assert await page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                await page.locator("#qf24-switch-mode").click()
                assert await page.locator("#qf34-workspace-nav, #qf37-secondary").count() == 0
                assert await page.evaluate("Object.keys(QFWorkspace34.rules()).length") == 0
                await open_company_research(page)
                await expect(page.locator("#qf-v23-explore-content")).to_be_visible()
                assert await page.evaluate("qf34Writes") == 0
                assert not errors, errors
                results.append(
                    {
                        "engine": engine,
                        "width": width,
                        "writes": 0,
                        "researchHome": True,
                        "exactUniverse": True,
                        "canonicalAssessment": True,
                        "ruleReset": True,
                    }
                )
                await page.close()
            await browser.close()
    (OUT / "navigation-results.json").write_text(json.dumps(navigation_results, indent=2))
    (OUT / "results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps({"journeys": len(results), "writes": 0, "passed": True}))


if __name__ == "__main__":
    asyncio.run(run())
