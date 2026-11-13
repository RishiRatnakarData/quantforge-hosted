"""Independent quality regressions: state recovery, missingness and real keyboard use."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright, expect
from smoke_final24_browser import CSP, EXTRA, FINAL, FIXTURE, HTML, login

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("QF_QUALITY_DIR", str(ROOT / "outputs/quality-review")))


async def setup(browser, width):
    page = await browser.new_page(viewport={"width": width, "height": 1000})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    async def route(r):
        if r.request.is_navigation_request():
            await r.fulfill(
                status=200,
                content_type="text/html",
                body=HTML,
                headers={"Content-Security-Policy": CSP},
            )
        else:
            await r.abort()

    await page.route("**/*", route)
    await page.goto("https://quantforge.test/#explore")
    return page, errors


async def capture(page, name):
    await page.evaluate("scrollTo(0,0)")
    await page.screenshot(path=str(OUT / (name + ".png")), full_page=True)


async def journey(browser, engine, width):
    page, errors = await setup(browser, width)
    prefix = engine + "-" + str(width)
    actions = 0

    async def click(selector):
        nonlocal actions
        actions += 1
        await page.locator(selector).click()

    await expect(page.locator("#qf27-financial-interpretation")).to_contain_text("Revenue was")
    await capture(page, prefix + "-explore")
    await click('#qf-v20-navigation [data-page="models"]')
    tab = page.locator('[data-qf-c22-phase="results"]')
    await tab.focus()
    await page.keyboard.press("ArrowRight")
    await expect(page.locator('[data-qf-c22-phase="evaluation"]')).to_be_focused()
    await expect(page.locator('[data-qf-c22-phase="evaluation"]')).to_have_attribute(
        "aria-selected", "true"
    )
    await capture(page, prefix + "-prediction-evaluation")
    await click('#qf-v20-navigation [data-page="methods"]')
    await page.locator('[data-qf-c22-method="overview"]').focus()
    await page.keyboard.press("End")
    await expect(page.locator('[data-qf-c22-method="engineering"]')).to_be_focused()
    await expect(page.locator('[data-qf-c22-method="engineering"]')).to_have_attribute(
        "aria-selected", "true"
    )
    await click('#qf-v20-navigation [data-page="portfolio"]')
    await click('[data-qf-portfolio="whatif"]')
    await expect(page.locator("#qf-b21-portfolio-export")).to_be_enabled()
    slider = page.locator("#qf-b21-weight-controls input").first
    before = int(await slider.input_value())
    await slider.focus()
    await page.keyboard.press("ArrowRight")
    await page.keyboard.press("ArrowRight")
    await expect(slider).to_be_focused()
    assert int(await slider.input_value()) == before + 2
    # A real pointer drag must retain the same native control, not lose pointer capture.
    await slider.scroll_into_view_if_needed()
    box = await slider.bounding_box()
    await page.mouse.move(box["x"] + box["width"] * 0.4, box["y"] + box["height"] / 2)
    await page.mouse.down()
    await page.mouse.move(box["x"] + box["width"] * 0.65, box["y"] + box["height"] / 2, steps=8)
    await page.mouse.up()
    assert int(await slider.input_value()) >= 55
    await page.locator("#qf-b21-amount").fill("0")
    await expect(page.locator("#qf-b21-portfolio-export")).to_be_disabled()
    await expect(page.locator("#qf-b21-whatif-stats")).to_be_empty()
    await expect(page.locator("#qf-b21-amount")).to_have_attribute("aria-invalid", "true")
    downloads = []
    page.on("download", lambda d: downloads.append(d.suggested_filename))
    await page.evaluate(
        "document.querySelector('#qf-b21-portfolio-export').dispatchEvent(new Event('click'))"
    )
    assert not downloads
    await capture(page, prefix + "-invalid-scenario")
    await page.locator("#qf-b21-amount").fill("10000")
    await expect(page.locator("#qf-b21-portfolio-export")).to_be_enabled()
    await page.evaluate(FIXTURE)
    await page.evaluate(EXTRA)
    await page.evaluate(FINAL)
    await login(page)
    await page.evaluate("QFResearch20.addAssetToCompare(QFResearch20.assetInfo('AAPL'))")
    await click('#qf-v20-navigation [data-page="compare"]')
    await click("#qf-v20-compare-run")
    await expect(page.locator("#qf-b21-compare-export")).to_be_enabled()
    await page.evaluate(
        """() => {const original=fetch;window.qfHistoryFails=false;window.fetch=async(url,options)=>qfHistoryFails&&String(url).includes('private/history?')?({ok:false,status:503,json:async()=>({code:'provider_unavailable'})}):original(url,options);} """
    )
    await page.evaluate("qfHistoryFails=true")
    await click("#qf-v20-compare-run")
    await expect(page.locator("#qf-b21-compare-state")).to_contain_text("unavailable")
    for selector in [
        "#qf-b21-risk-table table",
        "#qf-b21-risk-scatter svg",
        "#qf-b21-distribution svg",
        "#qf-b21-correlation table",
    ]:
        assert not await page.locator(selector).count(), selector
    await expect(page.locator("#qf-b21-compare-export")).to_be_disabled()
    await click('[data-qf28-compare="risk"]')
    await capture(page, prefix + "-failed-compare")
    await page.evaluate("qfHistoryFails=false")
    await click("#qf-v20-compare-run")
    await expect(page.locator("#qf-b21-compare-export")).to_be_enabled()
    await click('#qf-v20-navigation [data-page="explore"]')
    await click('[data-qf-range="30"]')
    ticks = page.locator(".qf29-price-tick")
    assert 2 <= await ticks.count() <= 5
    tick_boxes = await ticks.evaluate_all(
        "(nodes)=>nodes.map(n=>({x:n.getBoundingClientRect().x,right:n.getBoundingClientRect().right,label:n.textContent}))"
    )
    assert len({b["label"] for b in tick_boxes}) == len(tick_boxes), tick_boxes
    assert all(
        a["right"] + 4 <= b["x"] for a, b in zip(tick_boxes, tick_boxes[1:], strict=False)
    ), tick_boxes
    await click('[data-qf27-explore="financials"]')
    await page.evaluate(
        """() => {for(const c of QFPublishedSEC.companies)if(c.symbol==='MSFT')for(const row of c.annual)row.metrics.operating_income_usd=null;QFExplore27.refresh();} """
    )
    assert await page.locator("#qf-v20-financial-chart svg").count() == 1
    assert (
        "Revenue" in await page.locator("#qf-v20-financial-chart .qf29-chart-legend").inner_text()
    )
    assert (
        "Operating income"
        not in await page.locator("#qf-v20-financial-chart .qf29-chart-legend").inner_text()
    )
    await capture(page, prefix + "-missing-financial-field")
    await click('#qf-v20-navigation [data-page="methods"]')
    await click('[data-qf-c22-method="data"]')
    await expect(page.locator(".qf27-calculation")).to_contain_text("Unavailable USD B")
    assert not errors, errors
    assert await page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    await page.close()
    return {
        "engine": engine,
        "width": width,
        "counted_clicks": actions,
        "checks": [
            "tab keyboard",
            "slider keyboard and drag",
            "invalid export blocked",
            "Compare failure clears dependent results and recovers",
            "short-range axis readable",
            "missing financial series preserved",
            "Methods null not zero",
        ],
        "page_errors": errors,
    }


async def delayed_benchmark(browser):
    page, errors = await setup(browser, 1440)
    await page.evaluate(FIXTURE)
    await page.evaluate(EXTRA)
    await page.evaluate(FINAL)
    await login(page)
    await page.evaluate(
        """() => {const original=fetch,response=data=>({ok:true,status:200,json:async()=>structuredClone(data)});window.qfHeldStarted=false;window.qfHeldCompleted=false;window.qfHeld=new Promise(r=>window.qfRelease=r);window.fetch=async(url,options)=>{const p=String(url),q=new URLSearchParams(p.split('?')[1]);if(p.includes('private/history?')){const symbols=q.get('symbols').split(','),dates=QFResearchCore20.chartWindow(QFResearchCore20.syntheticPrice(symbols[0]),365).map(r=>r.date);window.qfHeldDates=dates;return response({licensed_private:true,equity_feed:'sip',symbols,dates,closes:Object.fromEntries(symbols.map(s=>[s,dates.map((_,i)=>100+i*.05)])),sessions_per_year:252,source:'Isolated private race fixture'});}if(p.includes('history-single')&&q.get('symbol')==='SPY'){window.qfHeldStarted=true;await qfHeld;window.qfHeldCompleted=true;return response({licensed_private:true,symbol:'SPY',equity_feed:'sip',ohlcv_available:false,observations:qfHeldDates.map((date,i)=>({date,close:100+i})),source:'Isolated delayed private benchmark'});}return original(url,options);};} """
    )
    await page.locator('#qf-v20-navigation [data-page="portfolio"]').click()
    await page.wait_for_function("qfHeldStarted")
    await page.locator("#qf24-switch-mode").click()
    await page.evaluate("QFResearch20.reloadPortfolio()")
    await expect(page.locator("#qf-b21-whatif-chart")).to_contain_text("SPY simulated")
    await page.evaluate("qfRelease()")
    await page.wait_for_function("qfHeldCompleted")
    await page.evaluate(
        "new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))"
    )
    await page.locator('[data-qf-portfolio="whatif"]').click()
    slider = page.locator("#qf-b21-weight-controls input").first
    await slider.focus()
    await page.keyboard.press("ArrowRight")
    await expect(page.locator("#qf-b21-whatif-chart")).not_to_contain_text("SPY observed")
    await expect(page.locator("#qf-b21-whatif-chart")).to_contain_text("SPY simulated")
    await capture(page, "delayed-private-benchmark-public-isolation")
    assert not errors, errors
    await page.close()
    return {"delayed_private_benchmark_discarded": True, "owner_data_used": False}


async def direct_routes(browser):
    results = []
    for route in ("explore", "compare", "models", "portfolio", "methods"):
        page, errors = await setup(browser, 390)
        await page.goto("https://quantforge.test/#" + route)
        await page.reload()
        await expect(page.locator("#page-" + route)).to_have_class("tabpage active")
        if route == "models":
            await expect(page.locator("#qf-c22-model-output")).to_contain_text(
                "Five-session direction experiment"
            )
        if route == "portfolio":
            await expect(page.locator("#qf-b21-overview-chart svg")).to_have_count(1)
        if route == "compare":
            await expect(page.locator("#qf-v20-compare-chips button")).to_have_count(1)
        if route == "methods":
            await expect(page.locator("#qf-c22-method-content")).to_contain_text(
                "Why QuantForge exists"
            )
        await capture(page, "direct-route-" + route)
        assert not errors, errors
        results.append({"direct_route": route, "loaded": True, "page_errors": errors})
        await page.close()
    return results


async def feed_alignment(browser):
    page, errors = await setup(browser, 390)
    await page.evaluate(FIXTURE)
    await page.evaluate(EXTRA)
    await page.evaluate(FINAL)
    await login(page)
    await page.evaluate(
        """() => {const original=fetch;window.fetch=async(url,options)=>{const r=await original(url,options),p=String(url);if(p.includes('private/history?')||p.includes('history-single')){const data=structuredClone(await r.json());data.equity_feed=p.includes('history-single')&&p.includes('SPY')?'iex':'sip';return {ok:true,status:200,json:async()=>data};}return r;};QFResearch20.addAssetToCompare(QFResearch20.assetInfo('AAPL'));}"""
    )
    await page.locator('#qf-v20-navigation [data-page="compare"]').click()
    await page.locator("#qf-v20-compare-run").click()
    await expect(page.locator("#qf-b21-compare-export")).to_be_enabled()
    await expect(page.locator("#qf-b21-compare-provenance")).to_contain_text("compatible feed")
    await expect(page.locator("#qf-b21-compare-chart")).not_to_contain_text("SPY observed")
    await capture(page, "mismatched-feed-benchmark-withheld")
    await page.locator('#qf-v20-navigation [data-page="explore"]').click()
    await page.evaluate("QFResearch20.choose('MSFT')")
    await expect(page.locator("#qf-v20-source-badge")).to_contain_text("SIP")
    await page.locator('[data-qf27-explore="market"]').click()
    await page.locator("#qf-v20-benchmark").check()
    await expect(page.locator("#qf-v20-chart-source")).to_contain_text("compatible feed")
    await expect(page.locator("#qf-v20-cursor-value")).not_to_contain_text("SPY")
    await capture(page, "explore-mismatched-feed-benchmark-withheld")

    assert not errors, errors
    await page.close()
    return {"mismatched_benchmark_feed_withheld": True, "company_history_remains_usable": True}


async def beginner_walkthrough(browser):
    page, errors = await setup(browser, 390)
    actions = []

    async def click(selector, label):
        await page.locator(selector).click()
        actions.append(label)

    async def fill(selector, value, label):
        await page.locator(selector).fill(value)
        actions.append(label)

    await click('#qf-v23-home-button', 'Open Home')
    await fill('#qf24-home-search', 'Microsoft', 'Search from Home')
    await click('#qf24-home-find', 'Research company')
    await expect(page.locator('#qf-v20-search')).to_have_value('Microsoft (MSFT)')
    await expect(page.locator('#qf-v20-company')).to_have_text('Microsoft')
    await expect(page.locator("#qf27-financial-interpretation")).to_contain_text("Revenue was")
    await click('[data-qf27-finance="cash"]', "Inspect cash generation and definition")
    await expect(page.locator("#qf29-financial-explanation")).to_contain_text(
        "Subtract cash property-and-equipment"
    )
    await click(
        '#qf-v20-navigation [data-page="compare"]', "Open Compare; current company carries over"
    )
    await fill("#qf-v20-compare-search", "Apple", "Find a second company by name")
    await click('#qf27-compare-options [data-qf27-symbol="AAPL"]', "Select Apple explicitly")
    await click("#qf-v20-compare-run", "Calculate the two-company comparison")
    await expect(page.locator("#qf-b21-finance-table")).to_contain_text("AAPL")
    await click('#qf-v20-navigation [data-page="models"]', "Open Models with the same company")
    await click('[data-qf-c22-phase="evaluation"]', "Inspect baseline and later-window evaluation")
    await expect(page.locator("#qf-c22-model-output")).to_contain_text("baseline")
    await click('#qf-v20-navigation [data-page="portfolio"]', "Open portfolio research")
    await click('[data-qf-portfolio="whatif"]', "Inspect the same two-company allocation basket")
    assert await page.locator("#qf-b21-weight-controls input").count() == 3
    await click('#qf-v20-navigation [data-page="methods"]', "Open Methods")
    await click('[data-qf-c22-method="statistical"]', "Reach worked calculations")
    assert await page.locator("math").count() > 0
    assert not errors, errors
    await page.close()
    return {
        "persona": "Beginner in finance / statistical data science background",
        "actions": actions,
        "action_count": len(actions),
        "scope": "Expert walkthrough, not a measured study with independent users. Changing weights, exports and detailed Methods use additional actions.",
    }


async def model_source_labels(browser):
    page, errors = await setup(browser, 390)
    await page.locator('#qf-v20-navigation [data-page="models"]').click()
    await page.locator('[data-qf-model="valuation"]').click()
    await expect(page.locator("#qf-c22-model-output .qf-c22-provenance")).to_contain_text(
        "Reported SEC cash flow"
    )
    await expect(page.locator("#qf-c22-model-output .qf-c22-provenance")).not_to_contain_text(
        "Synthetic price experiment"
    )
    await capture(page, "public-valuation-source-label")
    await page.evaluate(FIXTURE)
    await page.evaluate(EXTRA)
    await page.evaluate(FINAL)
    await login(page)
    await page.locator('#qf-v20-navigation [data-page="models"]').click()
    await expect(page.locator("#qf28-model-search-status")).to_contain_text(
        "Observed history ready"
    )
    await expect(page.locator("#qf28-model-search-status")).not_to_contain_text("Public")
    await page.locator('[data-qf-model="valuation"]').click()
    await expect(page.locator("#qf-c22-model-output .qf-c22-provenance")).to_contain_text(
        "Reported SEC cash flow"
    )
    await capture(page, "private-valuation-source-label")
    await page.locator("#qf24-switch-mode").click()
    await expect(page.locator("#qf28-model-search-status")).to_contain_text("Public price studies")
    assert not errors, errors
    await page.close()
    return {
        "model_source_labels": "SEC valuation distinguished from synthetic/observed price studies; mode helper updates in both directions"
    }


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    async with async_playwright() as pw:
        for engine in os.environ.get("QF_QUALITY_ENGINES", "chromium,firefox,webkit").split(","):
            browser = await getattr(pw, engine).launch()
            for width in map(
                int, os.environ.get("QF_QUALITY_WIDTHS", "320,390,768,1024,1440").split(",")
            ):
                results.append(await journey(browser, engine, width))
                print(engine, width, "independent quality PASS", flush=True)
            results.append(await beginner_walkthrough(browser))
            results.append(await feed_alignment(browser))
            results.append(await model_source_labels(browser))
            results.extend(await direct_routes(browser))
            results.append(await delayed_benchmark(browser))
            await browser.close()
    (OUT / "quality-browser-results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    asyncio.run(main())
