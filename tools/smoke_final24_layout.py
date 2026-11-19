"""Component-aware visual matrix. Never authenticates to an external service."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from browser_product_contract import navigate, pick_compare
from playwright.async_api import async_playwright
from smoke_final24_browser import CSP, EXTRA, FINAL, FIXTURE, HTML, login

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("QF_LAYOUT_SCREENSHOT_DIR", str(ROOT / "outputs/final24-layout")))


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        cases = [
            (int(width), 1, "100")
            for width in os.environ.get("QF_LAYOUT_WIDTHS", "320,390,768,1024,1440").split(",")
        ] + [(720, 2, "200-equivalent")]
        for width, density, zoom in cases:
            page = await browser.new_page(
                viewport={"width": width, "height": 1000}, device_scale_factor=density
            )
            errors = []
            page.on("pageerror", lambda error, errors=errors: errors.append(error.stack))

            async def route(request):
                if request.request.is_navigation_request():
                    await request.fulfill(
                        status=200,
                        content_type="text/html",
                        body=HTML,
                        headers={"Content-Security-Policy": CSP},
                    )
                else:
                    await request.abort()

            await page.route("**/*", route)
            await page.goto("https://quantforge.test/")
            for private in (False, True):
                mode = "private" if private else "public"
                prefix = f"{mode}-{width}-{zoom}"
                if private:
                    await page.evaluate(FIXTURE)
                    await page.evaluate(EXTRA)
                    await page.evaluate(FINAL)
                    await login(page)

                async def check(name, page=page, prefix=prefix, errors=errors):
                    await page.evaluate("window.scrollTo(0,0)")
                    await page.screenshot(
                        path=str(OUT / (prefix + "-" + name + ".png")), full_page=True
                    )
                    finding = await page.evaluate(
                        """()=>({pageOverflow:document.documentElement.scrollWidth-innerWidth,clippedControls:[...document.querySelectorAll('.tabpage.active button,.tabpage.active h1,.tabpage.active h2,.tabpage.active h3')].filter(e=>e.getBoundingClientRect().width>0&&e.scrollWidth>e.clientWidth+2).map(e=>({id:e.id,text:e.textContent.slice(0,80)})),smallChartText:[...document.querySelectorAll('.tabpage.active svg text')].filter(e=>e.getBoundingClientRect().width>0&&e.getBoundingClientRect().height<10).map(e=>({text:e.textContent,size:e.getBoundingClientRect().height})),tableRegions:[...document.querySelectorAll('.tabpage.active .table-wrap')].filter(e=>e.querySelector('table')).every(e=>e.tabIndex===0&&e.getAttribute('role')==='region')})"""
                    )
                    assert await page.locator('input[type="file"]:visible').count() == 0
                    finding.update(await page.evaluate("""()=>{
                      const rgb=s=>(s.match(/[0-9.]+/g)||[]).slice(0,3).map(Number),lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4);}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
                      return {oversizedPriceCharts:[...document.querySelectorAll('.tabpage.active .qf-b21-chart svg,.tabpage.active .qf-b21-chart-sm svg')].filter(e=>e.getBoundingClientRect().height>640).map(e=>e.parentElement.id),lowContrastSelections:[...document.querySelectorAll('.qf27-lab-selector button[aria-pressed=true]')].filter(e=>{if(!e.getBoundingClientRect().width)return false;const s=getComputedStyle(e),a=lum(rgb(s.color)),b=lum(rgb(s.backgroundColor));return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)<4.5;}).map(e=>e.textContent)};
                    }"""))
                    results.append({"case": prefix, "view": name, **finding, "errors": errors[:]})

                await navigate(page, 'explore')
                await page.locator("#qf-v20-search").fill("Microsoft")
                await page.locator('#qf-v20-search-results [data-qf27-symbol="MSFT"]').click()
                await check("picker-selected")
                for view in ("financials", "market", "brief", "research"):
                    if view in ("market", "research") and not private:
                        continue
                    await page.locator(f'[data-qf27-explore="{view}"]').click()
                    if view == "brief":
                        await page.locator("#qf27-analyze").click()
                    if view == "financials":
                        for finance in ("performance", "margin", "cash", "health", "sources"):
                            await page.locator(f'[data-qf27-finance="{finance}"]').click()
                            await check("explore-" + finance)
                    else:
                        await check("explore-" + view)
                        if view == "brief" and private:
                            await page.locator('#qf33-evidence-tab').click()
                            await check("explore-supporting-evidence")
                            await page.locator('#qf33-assessment-tab').click()

                await navigate(page, 'compare')
                await pick_compare(page, "AAPL")
                await page.locator("#qf-v20-compare-run").click()
                await page.wait_for_function('document.querySelector("#qf-b21-compare-chart svg")')
                assert await page.locator('#qf-v20-compare-output > section').count() == 0
                for view in ("financial", "market", "risk"):
                    await page.locator(f'[data-qf28-compare="{view}"]').click()
                    await check("compare-" + view)
                await navigate(page, 'models')
                for category in ("prediction", "risk", "valuation", "strategy"):
                    await page.locator(f'#page-models [data-qf-model="{category}"]').click()
                    for phase in ("results", "evaluation", "method"):
                        await page.locator(f'[data-qf-c22-phase="{phase}"]').click()
                        await check("model-" + category + "-" + phase)
                await navigate(page, 'portfolio')
                for view in ("overview", "whatif", "analysis"):
                    await page.locator(f'[data-qf-portfolio="{view}"]').click()
                    if not private and view == "overview":
                        # A transient narrow/hidden pane must not bake a 210px chart
                        # into a wide screen and magnify its labels after navigation.
                        await page.locator('#qf-b21-overview-chart').evaluate("e=>e.style.width='1px'")
                        await page.evaluate('QFResearch20.reloadPortfolio()')
                        chart_width=await page.locator('#qf-b21-overview-chart svg').get_attribute('viewBox')
                        if width>=720:
                            assert float(chart_width.split()[2])>210,chart_width
                        await page.locator('#qf-b21-overview-chart').evaluate("e=>e.style.removeProperty('width')")
                        await page.evaluate('QFResearch20.reloadPortfolio()')
                    await check("portfolio-" + view)
                await navigate(page, 'methods')
                for view in ("overview", "data", "statistical", "engineering"):
                    await page.locator(f'[data-qf-c22-method="{view}"]').click()
                    await check("methods-" + view)
                await page.locator('[data-qf-c22-method="statistical"]').click()
                for method in (
                    "regression",
                    "portfolio",
                    "tails",
                    "logistic",
                    "dcf",
                    "walk",
                ):
                    await page.locator(f'[data-qf27-method="{method}"]').click()
                    await check("worked-" + method)
                if private:
                    await page.locator("#qf-v20-mode").click()
                    await check("account-dialog")
                    await page.locator("#qf-v23-close").click()
                print(
                    prefix + " all named views captured and inspected by component probes",
                    flush=True,
                )
            await page.close()
        await browser.close()
    (OUT / "component-results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    failures = [
        r
        for r in results
        if r["pageOverflow"] > 0
        or r["clippedControls"]
        or r["smallChartText"]
        or not r["tableRegions"]
        or r["oversizedPriceCharts"]
        or r["lowContrastSelections"]
        or r["errors"]
    ]
    (OUT / "component-failures.json").write_text(
        json.dumps(failures, indent=2) + "\n", encoding="utf-8"
    )
    assert not failures, json.dumps(failures[:10], indent=2)
    print(
        f"{len(results)} component-aware view checks PASS; 200-equivalent is 720 CSS px at 2x density, not native browser zoom.",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
