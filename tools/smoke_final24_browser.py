"""Final 24-issue workflow acceptance. Compiled CSP; no real account or network."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright, expect
from smoke_product_v27 import EXTRA, FIXTURE

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "public/index.html").read_text(encoding="utf-8")
CSP = next(
    line.strip().split(": ", 1)[1]
    for line in (ROOT / "public/_headers").read_text().splitlines()
    if "Content-Security-Policy:" in line
)
OUT = Path(os.environ.get("QF_SCREENSHOT_DIR", str(ROOT / "outputs/final24")))
FINAL = r"""() => {
 const original=fetch;window.qfFundingPosts=0;
 window.fetch=async(url,options={})=>{
  const path=String(url),response=(data,status=200)=>({ok:status<400,status,json:async()=>structuredClone(data)});
  if(path.includes('private/trade-preview')&&window.qfRejectPreview){const code=window.qfRejectPreview;window.qfRejectPreview=null;return response({code,detail:{secret:'MUST-NOT-ECHO'}},code==='account_changed'?409:422);}
  if(path.includes('private/assets')&&new URLSearchParams(path.split('?')[1]).get('query')==='TEST')return response({licensed_private:true,items:[{symbol:'TEST',name:'Offline Synthetic Investment With A Deliberately Long Issuer And Fund Name For Component Reflow Verification',asset_class:'us_equity',tradable:true,exchange:'MOCK'}]});
  if(path.includes('private/capital')){
   const body=JSON.parse(options.body);if(body.expected_version!==qfMockVersion)return response({code:'account_changed'},409);
   const amount=Math.round(Number(body.amount)*100)/100,delta=body.action==='deposit'?amount:-amount;
   if(body.action==='withdraw'&&amount>qfMockOwner.cash)return response({code:'withdraw_cash'},422);
   const preview={action:body.action,amount,cash_before:qfMockOwner.cash,cash_after:qfMockOwner.cash+delta,contributions_after:qfMockOwner.initial_cash+delta,cash_impact:delta};
   if(path.includes('capital-preview'))return response({preview,version:qfMockVersion});
   window.qfFundingPosts++;qfMockOwner.cash=preview.cash_after;qfMockOwner.initial_cash=preview.contributions_after;qfMockOwner.capital_events.unshift({action:body.action,amount,at:new Date().toISOString(),request_id:body.request_id});qfMockVersion++;
   if(window.qfLoseFunding){window.qfLoseFunding=false;throw new TypeError('Offline interrupted funding response');}
   return response({portfolio:qfMockOwner,version:qfMockVersion,paper_only:true});
  }
  const result=await original(url,options);
  if(path.endsWith('private/trade')&&result.ok){for(const [symbol,units] of Object.entries(qfMockOwner.holdings))if(units===0)delete qfMockOwner.holdings[symbol];const data=await result.json();data.portfolio=structuredClone(qfMockOwner);return response(data);}
  return result;
 };
}"""


async def capture(page, name, component=None):
    await page.evaluate("window.scrollTo(0,0)")
    await page.screenshot(path=str(OUT / (name + ".png")), full_page=True)
    if component:
        await page.locator(component).screenshot(path=str(OUT / (name + "-component.png")))
    assert await page.evaluate("document.documentElement.scrollWidth<=innerWidth"), name


async def login(page):
    await page.locator("#qf-v20-mode").click()
    await page.locator("#private-email").fill("offline" + "@" + "example.invalid")
    await page.locator("#private-password").fill("offline-fixture")
    await page.locator("#private-login-submit").click()
    await expect(page.locator("#qf24-mode-label")).to_contain_text("PRIVATE")


async def journey(browser, engine, width):
    page = await browser.new_page(viewport={"width": width, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(error.stack))

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
    await expect(page.locator("#qf-v23-landing")).to_be_visible()
    await page.locator('#qf-v20-navigation [data-page="explore"]').click()
    await expect(page.locator("#qf27-explore-financials")).to_be_visible()
    await page.locator('#qf-v20-navigation [data-page="models"]').click()
    await page.locator("#qf28-model-search").fill("Apple")
    await page.locator('#qf28-model-search-options [data-qf27-symbol="AAPL"]').click()
    assert await page.evaluate("QFResearch20.context().symbol") == "AAPL"
    await page.locator('[data-qf-c22-phase="evaluation"]').click()
    await capture(page, f"{engine}-{width}-model-selection-evaluation")
    await page.locator('#qf-v20-navigation [data-page="methods"]').click()
    await page.locator('[data-qf-c22-method="data"]').click()
    await expect(page.locator("#qf28-quality")).to_contain_text("94 issuers")
    await capture(page, f"{engine}-{width}-sec-quality")
    await page.locator('[data-qf-c22-method="statistical"]').click()
    assert await page.locator('[data-qf27-method="nlp"]').count()==0
    await expect(page.locator('#qf27-lab-output')).to_contain_text('Calculation')
    await page.locator('#qf-v20-navigation [data-page="portfolio"]').click()
    await page.locator('[data-qf-portfolio="whatif"]').click()
    before_basket = set(await page.evaluate("QFResearch20.context().universe"))
    await page.locator("#qf28-scenario-search").fill("Adobe")
    await page.locator('#qf28-scenario-search-options [data-qf27-symbol="ADBE"]').click()
    await expect(page.locator('[data-qf-b21-weight="ADBE"]')).to_be_visible()
    assert set(await page.evaluate("QFResearch20.context().universe")) == before_basket | {"ADBE"}
    await page.locator("#qf28-scenario-search").fill("Adobe")
    await page.locator('#qf28-scenario-search-options [data-qf27-symbol="ADBE"]').click()
    await expect(page.locator("#qf28-scenario-search-status")).to_contain_text("already")
    await page.locator("#qf28-scenario-search").fill("AMD")
    await page.locator('#qf28-scenario-search-options [data-qf27-symbol="AMD"]').click()
    await page.locator("#qf28-scenario-search").fill("AMAT")
    await page.locator('#qf28-scenario-search-options [data-qf27-symbol="AMAT"]').click()
    await expect(page.locator("#qf28-scenario-search-status")).to_contain_text("Five investments")
    assert len(await page.evaluate("QFResearch20.context().universe")) == 5
    await expect(page.locator("#qf-b21-weights-total")).to_contain_text("100%")
    await capture(page, f"{engine}-{width}-shared-scenario-selection")
    await page.evaluate(FIXTURE)
    await page.evaluate(EXTRA)
    await page.evaluate(FINAL)
    await login(page)
    await expect(page.locator("#qf27-explore-market")).to_be_visible()
    await page.locator('#qf-v20-navigation [data-page="models"]').click()
    await page.locator("#qf28-model-search").fill("TEST")
    await page.locator('#qf28-model-search-options [data-qf27-symbol="TEST"]').click()
    await expect(page.locator("#qf-v20-model-selected")).to_contain_text("Deliberately Long")
    await capture(page, f"{engine}-{width}-long-provider-name")
    await page.locator('#qf-v20-navigation [data-page="explore"]').click()
    await expect(page.locator("#qf27-explore-market")).to_be_visible()
    await page.locator('[data-qf27-explore="financials"]').click()
    await expect(page.locator("#qf-v20-coverage")).to_contain_text("no coverage")
    await page.locator('#qf-v20-navigation [data-page="portfolio"]').click()
    await page.locator('[data-qf-portfolio="overview"]').click()
    await page.evaluate(
        """async()=>{qfMockOwner.trades=Array.from({length:80},(_,i)=>({symbol:'MSFT',side:i%2?'sell':'buy',units:.01,price:300,fee:0,gross:3,cash_impact:i%2?3:-3,venue:'MOCK',observed_at:new Date(Date.UTC(2026,9,1,0,i)).toISOString(),at:new Date(Date.UTC(2026,9,1,0,i)).toISOString()}));qfMockOwner.capital_events=Array.from({length:100},(_,i)=>({action:i%2?'withdraw':'deposit',amount:10,at:new Date(Date.UTC(2026,9,2,0,i)).toISOString()}));qfMockVersion++;await QFPrivateBridgeV23.refresh();dispatchEvent(new Event('qf:owner-state'));}"""
    )
    await expect(page.locator("#qf27-ledger-page")).to_contain_text("180 saved records")
    await page.locator("#qf27-ledger-filter").select_option("funding")
    await page.locator("#qf27-ledger-next").click()
    await page.locator("#qf27-ledger-next").click()
    await capture(page, f"{engine}-{width}-large-filtered-ledger", "#qf24-transaction-ledger")
    await page.locator("#qf27-buy").click()
    await page.locator("#qf27-trade-query").fill("Microsoft")
    await expect(page.locator("#qf27-trade-options")).to_contain_text("Leveraged")
    await page.locator('#qf27-trade-options [data-qf27-symbol="MSFT"]').click()
    await page.evaluate("window.qfRejectPreview='quote_stale'")
    await page.locator("#qf27-preview").click()
    await expect(page.locator("#qf27-trade-status")).to_contain_text("too old")
    assert await page.evaluate("qfTradePosts") == 0
    assert "MUST-NOT-ECHO" not in await page.locator("body").inner_text()
    await capture(page, f"{engine}-{width}-stale-quote-rejection", ".qf27-trade-shell")
    await page.evaluate("window.qfRejectPreview='account_changed'")
    await page.locator("#qf27-preview").click()
    await expect(page.locator("#qf27-trade-status")).to_contain_text("new preview")
    await page.locator("#qf27-preview").click()
    await expect(page.locator("#qf27-confirm")).to_be_visible()
    await page.locator("#qf27-confirm").dblclick()
    await expect(page.locator("#qf27-trade-status")).to_contain_text("recorded")
    await expect(page.locator("#qf27-ledger-filter")).to_have_value("all")
    await expect(page.locator("#qf27-ledger-page")).to_contain_text("Page 1")
    await expect(
        page.locator("#qf24-transaction-ledger tbody tr").first.locator("td").nth(1)
    ).to_have_text("buy")
    assert await page.evaluate("qfTradePosts") == 1
    await page.locator("#qf27-refresh").click()
    await expect(page.locator("#qf27-trade-status")).to_contain_text("refreshed")
    await capture(
        page, f"{engine}-{width}-newest-buy-visible-after-refresh", "#qf24-transaction-ledger"
    )
    await page.locator("#qf27-sell").click()
    await page.locator('#qf27-trade-options [data-qf27-symbol="MSFT"]').click()
    await page.locator("#qf28-sell-max").click()
    assert await page.locator("#qf27-trade-amount").input_value() == await page.locator(
        "#qf27-trade-amount"
    ).get_attribute("max")
    await page.locator("#qf27-preview").click()
    await page.locator("#qf27-confirm").click()
    await expect(page.locator("#qf27-trade-status")).to_contain_text("sell recorded")
    assert "MSFT" not in await page.evaluate("QFPrivateBridgeV23.snapshot().holdings")
    await capture(page, f"{engine}-{width}-full-owned-sale", ".qf27-trade-shell")
    await page.locator("#qf28-fund").click()
    await page.locator("#qf25-capital-amount").fill("25.37")
    await page.locator("#qf25-capital-submit").click()
    await expect(page.locator("#qf28-funding-preview")).to_contain_text("Net contributions after")
    assert await page.evaluate("qfFundingPosts") == 0
    await capture(page, f"{engine}-{width}-funding-preview", "#qf28-funding")
    await page.locator("#qf28-funding-confirm").dblclick()
    await expect(page.locator("#qf28-funding-status")).to_contain_text("recorded")
    assert await page.evaluate("qfFundingPosts") == 1
    await page.locator("#qf25-capital-amount").fill("10")
    await page.locator("#qf25-capital-submit").click()
    await page.evaluate("window.qfLoseFunding=true")
    await page.locator("#qf28-funding-confirm").click()
    await expect(page.locator("#qf28-funding-status")).to_contain_text("interrupted")
    assert (
        await page.locator("#qf27-buy").is_disabled()
        and await page.locator("#qf25-capital-submit").is_disabled()
    )
    await page.locator("#qf27-refresh").click()
    await expect(page.locator("#qf28-funding-status")).to_contain_text("refreshed")
    assert await page.evaluate("qfFundingPosts") == 2
    await capture(page, f"{engine}-{width}-funding-reconciliation", "#qf28-funding")
    await page.locator("#qf25-capital-action").select_option("withdraw")
    await page.locator("#qf25-capital-amount").fill("1000000")
    await page.locator("#qf25-capital-submit").click()
    await expect(page.locator("#qf28-funding-status")).to_contain_text("exceeds available")
    assert await page.evaluate("qfFundingPosts") == 2
    saved = await page.evaluate("({state:qfMockOwner,version:qfMockVersion})")
    await page.add_init_script(
        "("
        + FIXTURE
        + ")();("
        + EXTRA
        + ")();("
        + FINAL
        + ")();window.qfMockOwner="
        + json.dumps(saved["state"])
        + ";window.qfMockVersion="
        + str(saved["version"])
        + ";"
    )
    await page.reload()
    await login(page)
    await page.locator('#qf-v20-navigation [data-page="portfolio"]').click()
    assert await page.evaluate("QFPrivateBridgeV23.snapshot().cash") == saved["state"]["cash"]
    await capture(page, f"{engine}-{width}-isolated-reload-persistence")
    await page.locator("#qf24-switch-mode").click()
    assert not await page.evaluate('document.querySelector("#qf24-transactions").offsetWidth')
    assert await page.evaluate("QFPrivateBridgeV23.ready()") is True
    assert "Quote: MOCK" not in await page.locator("body").inner_text()
    assert not errors, errors
    print(
        f"{engine} {width}px final24 account/ledger/funding/reload/source/picker/Methods PASS",
        flush=True,
    )
    await page.close()


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        for engine in os.environ.get("QF_TEST_BROWSERS", "chromium,firefox,webkit").split(","):
            browser = await getattr(pw, engine).launch()
            try:
                for width in [
                    int(x) for x in os.environ.get("QF_FINAL_WIDTHS", "1440,390").split(",")
                ]:
                    await journey(browser, engine, width)
            finally:
                await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
