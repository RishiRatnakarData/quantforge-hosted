"""Release A generated-site browser checks with *mocked* owner data.

Install Playwright and a Chromium browser to run locally; no external network,
login, provider account, or real authentication credentials are used.
This does NOT establish live Cloudflare / Render / MFA / Alpaca acceptance.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "public/index.html").read_text(encoding="utf-8")


async def assert_public(page, width: int) -> None:
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    await page.set_content(HTML, wait_until="load", timeout=25_000)
    await page.wait_for_timeout(120)
    assert await page.locator(".tabpage.active").get_attribute("id") == "page-explore"
    nav = await page.locator("#qf-v20-navigation [data-page]").all_inner_texts()
    assert nav == ["Explore", "Compare", "Models", "Portfolio", "Methods"]
    assert await page.locator("#navigation").evaluate("e => getComputedStyle(e).display") == "none"
    assert await page.locator("#qf-v20-chart svg").count() == 1
    assert "synthetic" in (await page.locator("#qf-v20-chart-source").inner_text()).lower()
    assert await page.locator("#qf-v20-financial-table tr").count() >= 3
    assert await page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

    await page.locator("#qf-v20-analyze").click()
    assert await page.locator(".qf-v20-finding").count() >= 2
    await page.locator("#qf-v20-search").fill("Apple")
    await page.locator('[data-qf-pick="AAPL"]').click()
    assert await page.locator("#qf-v20-symbol").inner_text() == "AAPL"
    assert await page.locator(".qf-v20-finding").count() == 0
    await page.locator('[data-qf-range="30"]').click()
    assert await page.locator("#qf-v20-chart svg").count() == 1
    svg = page.locator("#qf-v20-chart svg")
    await svg.focus()
    before = await page.locator("#qf-v20-cursor-value").inner_text()
    await svg.press("ArrowLeft")
    assert await page.locator("#qf-v20-cursor-value").inner_text() != before

    await page.locator('#qf-v20-navigation [data-page="compare"]').click()
    assert await page.locator(".tabpage.active").get_attribute("id") == "page-compare"
    await page.evaluate("history.back()")
    await page.wait_for_timeout(150)
    assert await page.locator(".tabpage.active").get_attribute("id") == "page-explore"
    assert not errors, errors[:2]
    print(f"Public {width}px keyboard/chart/router check PASS", flush=True)


async def assert_private_mock(page) -> None:
    await page.set_content(HTML, wait_until="load")
    await page.evaluate("""() => {
      const closes = Array.from({length: 40},(_,i)=>({
        date: new Date(Date.UTC(2026, 8, 1+i)).toISOString().slice(0,10),close:100+i*0.4
      }));
      window.fetch = async (url) => {
        const pathname=String(url);
        if (pathname.includes('history-single')) {
          const symbol=new URLSearchParams(pathname.split('?')[1]).get('symbol');
          return {ok:true,json:async()=>({schema_version:1,symbol,
            observations:closes,source:'MOCKED observed-price endpoint',
            coverage:'test fixture, not real provider acceptance',
            equity_feed:'sip',licensed_private:true,ohlcv_available:false})};
        }
        if (pathname.includes('news-research'))return {ok:false,json:async()=>({detail:'Test news unavailable'})};
        throw Error('Unexpected request '+pathname);
      };
      // Browser display-only fixture: API unit tests separately verify MFA enforcement.
      document.getElementById('private-signed').hidden=false;
    }""")
    await page.wait_for_timeout(220)
    assert "Observed" in await page.locator("#qf-v20-source-badge").inner_text()
    assert "MOCKED" in await page.locator("#qf-v20-chart-source").inner_text()
    assert "unavailable" in (await page.locator("#qf-v20-news").inner_text()).lower()
    assert await page.locator("#qf-v20-financial-table tr").count() >= 3
    await page.locator("#qf-v20-analyze").click()
    assert "observed private market risk" in await page.locator("#qf-v20-run-state").inner_text()
    assert await page.locator("#qf-v20-benchmark-wrap").is_visible()
    await page.locator("#qf-v20-search").fill("Apple")
    await page.locator('[data-qf-pick="AAPL"]').click()
    assert await page.locator("#qf-v20-symbol").inner_text() == "AAPL"
    assert await page.locator(".qf-v20-finding").count() == 0
    assert "Observed" in await page.locator("#qf-v20-source-badge").inner_text()
    print("Mocked private data and news outage PASS", flush=True)


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, executable_path=os.environ.get("QF_CHROMIUM_PATH") or None)
        try:
            for width, height in [(1440, 900), (390, 844)]:
                page = await browser.new_page(viewport={"width": width, "height": height}, accept_downloads=True)
                await assert_public(page, width)
                await page.close()
            page = await browser.new_page(viewport={"width": 1280, "height": 820})
            await assert_private_mock(page)
            await page.close()
            print("Release A Chromium smoke: public desktop/mobile, navigation/back, selection,"
                  " keyboard/chart, SEC/analysis, and mocked private provider failure PASS")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
