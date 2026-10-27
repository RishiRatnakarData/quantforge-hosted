import base64
import hashlib
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
src=root/'web'
html=(src/'site/site.template.html').read_text(encoding="utf-8")
nav='<button class="nav-btn" data-page="private">My workspace</button>'
html=html.replace('</nav>',nav+'</nav>',1)
block='''<section class="tabpage" id="page-private">
  <div class="pagehead"><h1>My workspace</h1><p id="private-status">Private · Sign in required</p></div>
  <div class="pane" id="private-login"><h3>Sign in</h3>
    <div class="formgrid" style="margin-top:14px">
      <div class="field"><label for="private-email">Email</label><input id="private-email" type="email" autocomplete="username" placeholder="Your private account"></div>
      <div class="field"><label for="private-password">Password</label><input id="private-password" type="password" autocomplete="current-password" placeholder="Password"></div>
    </div><div class="controls"><button class="btn primary" id="private-login-submit">Sign in</button><span class="tiny">Only the authorized owner account can sign in.</span></div>
  </div>
  <div id="private-mfa" class="pane" hidden>
    <h3 id="private-mfa-title">Authenticator verification</h3>
    <p id="private-mfa-instructions" class="tiny">Enter a six-digit code from your authenticator app.</p>
    <div id="private-mfa-setup-actions" hidden>
      <button class="btn" id="private-mfa-start">Start authenticator setup</button>
    </div>
    <div id="private-mfa-qr-wrap" hidden>
      <img id="private-mfa-qr" width="210" height="210" alt="Authenticator enrollment QR code" style="background:white;padding:8px;margin:12px 0" />
      <p class="tiny">Scan the code with an authenticator app. Keep the authenticator and its recovery options secure.</p>
    </div>
    <div class="field" style="max-width:220px;margin:14px 0">
      <label for="private-mfa-code">Six-digit code</label>
      <input id="private-mfa-code" type="text" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="000000" />
    </div>
    <div class="controls"><button class="btn primary" id="private-mfa-submit">Verify authenticator</button>
      <button class="btn" id="private-mfa-logout">Sign out</button></div>
  </div>
  <div id="private-signed" hidden>
    <div class="controls"><span class="mini">Personal research · authenticated</span><button class="btn sm" id="private-logout">Sign out</button></div>
    <nav class="private-nav" aria-label="Private workspace sections"><button class="active" data-private-tab="home">Portfolio</button><button data-private-tab="trade">Virtual trading</button><button data-private-tab="ideas">Investment ideas</button><button data-private-tab="research">Market research</button><button data-private-tab="optimization">Optimization</button><button data-private-tab="backtest">Backtesting</button><button data-private-tab="walkforward">Walk-forward</button><button data-private-tab="valuation">Valuation &amp; peers</button><button data-private-tab="settings">Settings &amp; notes</button></nav>
    <div id="private-research-dataset" class="pane" hidden aria-label="Research investments">
      <div class="section-title"><h3>Research investments</h3><span class="tiny">Shared by Market research, Optimization, Backtesting and Walk-forward</span></div>
      <p class="tiny">Choose 2–5 investments by name, choose a historical period, and load the prices once. All four research views use that same loaded dataset.</p>
      <div class="formgrid" style="margin-top:14px"><div class="field"><label for="private-history-selection">Selected investments (2–5)</label><input type="hidden" id="private-history-symbols" value=""><div id="private-history-selection" class="chosen-assets">Choose investments to compare.</div><button class="btn sm" type="button" id="private-browse-research">Browse investments</button></div>
      <div class="field"><label for="private-history-days">Period</label><select id="private-history-days"><option value="90">3 months</option><option value="180">6 months</option><option selected value="365">1 year</option><option value="730">2 years</option></select></div></div>
      <div class="controls"><button class="btn primary" id="private-history-load">Load market history</button><span class="tiny" id="private-history-source"></span></div>
      <div class="pane" style="background:var(--card,#f6faf8);padding:12px;margin-top:12px;border:1px solid #c9ded5;border-radius:9px">
        <p class="tiny" style="margin:0 0 8px"><strong>Selected investments:</strong> <span id="private-research-selected" aria-live="polite">None selected</span></p>
        <div class="tiny"><strong>Loaded for analysis:</strong> <span id="private-research-loaded" aria-live="polite">No historical data loaded</span></div>
      </div>
      <p class="tiny" id="private-research-state" role="status" aria-live="polite">Select investments, then load history to activate the analysis tools.</p>
    </div>
    <section class="private-view" data-private-view="home">
      <div class="pane"><div class="three"><div class="metric"><span class="muted">Virtual total</span><strong id="private-total">—</strong></div><div class="metric"><span class="muted">Available cash</span><strong id="private-cash">—</strong></div><div class="metric"><span class="muted">Invested value</span><strong id="private-invested">—</strong></div></div><div class="section-title"><h3>Holdings</h3><button class="btn sm" data-private-tab="trade">Trade</button></div><div id="private-positions"></div></div>
      <div class="pane"><h3>Portfolio concentration</h3><div id="private-concentration" class="tiny" style="margin-top:12px">Add virtual holdings to see allocation.</div></div>
    </section>
    <section class="private-view" data-private-view="trade" hidden>
      <div class="pane"><h3>Market observation &amp; virtual trade</h3><p class="tiny">Stocks, ETFs, and supported crypto pairs. Market observations are private and read-only; no brokerage orders are placed.</p>
      <div class="formgrid" style="margin-top:12px"><div class="field"><label for="private-selected-asset">Investment</label><input type="hidden" id="private-symbol" value=""><div class="selected-asset" id="private-selected-asset">No investment selected</div><button class="btn sm" type="button" id="private-browse-trade">Browse investments</button></div>
      <div class="field"><label for="private-side">Action</label><select id="private-side"><option value="buy">Buy with USD budget</option><option value="sell">Sell units</option></select></div>
      <div class="field"><label for="private-amount">USD budget / units</label><input type="number" min="0.00000001" step="any" id="private-amount" value="100"></div></div>
      <div class="controls"><button class="btn" id="private-quote-submit">Get market price</button><button class="btn primary" id="private-trade-submit">Record virtual trade</button></div><p id="private-quote" class="tiny" style="margin-top:12px">No quote loaded.</p></div>
    </section>
    <section class="private-view" data-private-view="ideas" hidden>
      <div class="pane"><span class="eyebrow">PERSONAL RESEARCH · OBSERVED DATA</span><h2 style="margin:7px 0 9px">Investment ideas</h2>
        <p class="muted">A plain-language research shortlist built from private historical market observations and, where available, SEC company filings. The ranking is a transparent screening heuristic, <strong>not</strong> a return forecast, buy signal, or individualized advice.</p>
        <div class="section-title" style="margin-top:18px"><h3>Companies to examine</h3><span class="tiny" id="ideas-count"></span></div>
        <div id="ideas-selected" class="chosen-assets" aria-live="polite"></div>
        <div class="controls"><button class="btn sm" type="button" id="ideas-browse">Browse investments</button><button class="btn sm" type="button" id="ideas-reset">Restore starting shortlist</button></div>
        <div class="formgrid" style="margin-top:17px">
          <div class="field"><label for="ideas-lens">Research perspective</label><select id="ideas-lens"><option value="balanced">Balanced: momentum and downside</option><option value="growth">Growth: recent trends emphasized</option><option value="defensive">Risk-aware: volatility and drawdown emphasized</option></select></div>
          <div class="field"><label for="ideas-period">Historical observation window</label><select id="ideas-period"><option value="365" selected>1 year</option><option value="730">2 years</option></select></div>
        </div>
        <label class="inline-checkbox"><input id="ideas-sec" type="checkbox" checked> Include available SEC business fundamentals (slower)</label>
        <div class="controls"><button class="btn primary" id="ideas-run" type="button">Compare selected investments</button></div>
        <p class="tiny" role="status" aria-live="polite" id="ideas-status">Choose companies by name or use the starting shortlist.</p>
        <div id="ideas-brief" class="decision-brief" hidden>
          <div class="section-title"><div><span class="eyebrow">HISTORICAL DECISION SUPPORT</span><h3>Investment decision brief</h3></div><button class="btn sm" type="button" id="ideas-brief-export" disabled>Download research brief (JSON)</button></div>
          <p class="tiny">A concise comparison of what deserves further research, portfolio overlap, and what the data cannot establish. Not a buy/sell instruction.</p>
          <div id="ideas-brief-output" aria-live="polite"></div>
        </div>
        <div id="ideas-results" aria-live="polite"></div>
      </div>
      <div class="pane"><h3>How to interpret this</h3><p class="tiny" style="margin-top:9px">A higher research score indicates a more favorable balance of <strong>past</strong> momentum and realized risk under the selected lens. It is not an estimated probability of profit, expected return, or price target. SEC results describe past business finances separately; ETFs generally do not have comparable company income statements. Reassess against valuation, diversification, fees, tax impact, investment horizon, and the risk of loss before any real-money decision. IEX-only bars are not consolidated market-wide prices.</p></div>
    </section>
    <section class="private-view" data-private-view="research" hidden>
      <div class="pane"><h3>Historical market research</h3><p class="tiny">Historical daily stocks, ETFs, and supported USD cryptocurrencies from the private Alpaca connection. Stock prices exclude dividends; crypto trades every day.</p>
      <p class="tiny">The investments and date range currently loaded for this analysis are shown in Research investments above.</p>
      <div id="private-history-chart" class="private-chart" style="margin-top:15px">Load a historical series to begin.</div><div id="private-risk-results"></div>
      </div>
    </section>
    <section class="private-view" data-private-view="optimization" hidden>
      <div class="pane"><h3>Portfolio optimization</h3>
        <p class="tiny">Use the historical prices selected in Market research to explore constrained, long-only allocations. The research calculation stays separate from your virtual positions. Nothing is traded or saved to your portfolio.</p>
        <div class="formgrid" style="margin-top:15px">
          <div class="field"><label for="private-opt-objective">Allocation method</label><select id="private-opt-objective"><option value="minimum">Minimum historical volatility</option><option value="inverse">Inverse-volatility allocation</option><option value="tilt">Historical return tilt</option></select></div>
          <div class="field"><label for="private-opt-cap">Maximum weight per investment</label><select id="private-opt-cap"><option value="0.35">35%</option><option value="0.40">40%</option><option value="0.50">50%</option><option selected value="0.60">60%</option><option value="0.75">75%</option><option value="1.00">100%</option></select></div>
        </div>
        <div class="controls"><button class="btn primary" id="private-opt-run" type="button">Calculate allocations</button><button class="btn" id="private-opt-export" type="button" disabled>Export allocations CSV</button></div>
        <div id="private-opt-output" style="margin-top:16px" aria-live="polite">Select 2–5 investments in Market research, load their history, then calculate an allocation.</div>
      </div>
      <div class="pane"><h3>Risk diagnostics</h3><p class="tiny">Empirical covariance uses 20% diagonal shrinkage. Historical correlations, contribution to variance, drawdowns, and tail losses are descriptive, not forecasts.</p><div id="private-opt-risk" style="margin-top:15px">Risk diagnostics appear after an allocation is calculated.</div></div>
    </section>
    <section class="private-view" data-private-view="backtest" hidden>
      <div class="pane"><h3>Historical strategy simulator</h3><p class="tiny">Equal-weight buy-and-hold versus monthly rebalancing, using the symbols and daily history selected in Market research. Includes hypothetical transaction fees; no forward-looking optimization.</p>
      <div class="formgrid" style="margin-top:14px"><div class="field"><label for="private-test-capital">Starting virtual capital ($)</label><input id="private-test-capital" type="number" min="100" max="1000000" step="100" value="10000"></div>
      <div class="field"><label for="private-test-fee">Fee per rebalance (basis points)</label><input id="private-test-fee" type="number" min="0" max="100" step="1" value="5"></div></div>
      <div class="controls"><button class="btn primary" id="private-backtest-run">Run backtest</button></div>
      <div id="private-backtest-output" style="margin-top:15px"></div></div>
    </section>
    <section class="private-view" data-private-view="walkforward" hidden>
      <div class="pane"><h3>Walk-forward strategy validation</h3>
        <p class="tiny">Fit portfolio weights using previous historical observations, then evaluate the allocation on later dates. Refit at every test-window boundary. Compare against equal-weight rebalancing using the same transaction-fee assumptions. No brokerage orders.</p>
        <div class="formgrid" style="margin-top:14px">
          <div class="field"><label for="private-wf-train">Training window</label><select id="private-wf-train"><option value="63">63 observations</option><option selected value="126">126 observations</option><option value="252">252 observations</option></select></div>
          <div class="field"><label for="private-wf-step">Out-of-sample test window</label><select id="private-wf-step"><option selected value="21">21 observations</option><option value="42">42 observations</option></select></div>
          <div class="field"><label for="private-wf-mode">Allocation rule</label><select id="private-wf-mode"><option value="minimum">Minimum historical volatility</option><option value="inverse">Inverse volatility</option><option value="tilt">Historical-return tilt</option></select></div>
          <div class="field"><label for="private-wf-cap">Maximum position weight</label><select id="private-wf-cap"><option value="0.35">35%</option><option value="0.40">40%</option><option value="0.50">50%</option><option selected value="0.60">60%</option><option value="0.75">75%</option><option value="1.00">100%</option></select></div>
          <div class="field"><label for="private-wf-fee">Fee per turnover (bps)</label><input id="private-wf-fee" type="number" min="0" max="100" value="5" step="1"></div>
          <div class="field"><label for="private-wf-capital">Research capital ($)</label><input id="private-wf-capital" type="number" min="100" max="1000000" value="10000"></div>
        </div>
        <div class="controls"><button class="btn primary" type="button" id="private-wf-run">Run walk-forward test</button><button class="btn" id="private-wf-export" type="button" disabled>Export test windows CSV</button></div>
        <div id="private-wf-output" style="margin-top:15px" aria-live="polite">Load historical investments in Market research to begin.</div>
        <div id="private-wf-diagnostics" class="pane" hidden style="margin-top:14px"><h3>Evaluation diagnostics</h3><div id="private-wf-diagnostics-content"></div>
          <div class="controls"><button class="btn" type="button" id="private-wf-robustness" disabled>Check transaction-cost sensitivity</button><button class="btn" type="button" id="private-wf-report" disabled>Download research report (JSON)</button></div>
          <div id="private-wf-robustness-output" aria-live="polite"></div>
          <div class="pane" style="margin-top:16px"><h3>Strategy robustness and benchmarks</h3>
          <p class="tiny">Compare a passive buy-and-hold benchmark, alternative allocation methods, higher fees, and leaving out each evaluation window. All allocation-rule comparisons hold the evaluation dates fixed. For longer tests, select 2 years in Research investments and reload history first.</p>
          <div class="controls"><button class="btn" type="button" id="private-wf-v68-run" disabled>Check strategy robustness</button><button class="btn" type="button" id="private-wf-v68-export" disabled>Download robustness report (JSON)</button></div>
          <div id="private-wf-v68-output" aria-live="polite">Run Walk-forward first, then check robustness.</div></div></div>
        <p class="tiny">Model uses price-only historical returns; no dividends, borrow costs, slippage, taxes, or corporate-action simulations. Backtests remain subject to selection bias and do not establish future performance.</p>
      </div>
    </section>
    <section class="private-view" data-private-view="valuation" hidden>
      <div class="pane"><h3>Financial valuation scenarios</h3><p class="tiny">Historical company financials from SEC filings, with editable forecast assumptions. Alpaca supplies market prices, not audited accounting statements.</p>
      <div class="formgrid" style="margin-top:14px"><div class="field"><label for="private-valuation-company">Company</label><input id="private-valuation-company" type="hidden"><div class="selected-asset" id="private-valuation-selected">No company selected</div><button class="btn sm" id="private-browse-valuation" type="button">Browse companies</button></div>
      <div class="field"><label for="private-valuation-growth">Annual FCF growth (%)</label><input id="private-valuation-growth" type="number" min="-30" max="40" value="4"></div>
      <div class="field"><label for="private-valuation-wacc">Discount rate (%)</label><input id="private-valuation-wacc" type="number" min="2" max="30" value="10"></div>
      <div class="field"><label for="private-valuation-terminal">Terminal growth (%)</label><input id="private-valuation-terminal" type="number" min="-5" max="8" value="2"></div></div>
      <div class="controls"><button class="btn primary" id="private-valuation-run">Run scenario</button></div><div id="private-valuation-output" style="margin-top:15px"></div></div>
      <div class="pane"><h3>Multi-year SEC financial projections</h3>
        <p class="tiny">Choose a company above and load its SEC annual disclosures first. Enter hypothetical annual revenue growth and free-cash-flow margin; projections never overwrite reported financials. Scenarios differ by ±4 percentage points of growth and ±3 points of FCF margin.</p>
        <div class="formgrid" style="margin-top:14px">
          <div class="field"><label for="private-fc-years">Projection horizon</label><select id="private-fc-years"><option value="3">3 years</option><option selected value="5">5 years</option><option value="7">7 years</option></select></div>
          <div class="field"><label for="private-fc-growth">Base annual revenue growth (%)</label><input id="private-fc-growth" type="number" min="-30" max="40" value="6" step="0.5"></div>
          <div class="field"><label for="private-fc-margin">Base FCF proxy / revenue (%)</label><input id="private-fc-margin" type="number" min="-25" max="60" value="12" step="0.5"></div>
          <div class="field"><label for="private-fc-discount">Discount rate (%)</label><input id="private-fc-discount" type="number" min="2" max="30" value="10" step="0.5"></div>
          <div class="field"><label for="private-fc-terminal">Terminal growth (%)</label><input id="private-fc-terminal" type="number" min="-5" max="8" value="2" step="0.5"></div>
        </div>
        <div class="controls"><button class="btn primary" id="private-fc-run" type="button">Forecast selected company</button></div>
        <div id="private-fc-output" style="margin-top:15px" aria-live="polite">Load SEC statements for a selected company first.</div>
        <div id="private-fc-diagnostics" class="pane" hidden style="margin-top:14px"><h3>Forecast assumption sensitivity</h3><div id="private-fc-diagnostics-content"></div>
          <div class="controls"><button class="btn" type="button" id="private-fc-report" disabled>Download financial research report (JSON)</button></div></div>
      </div>
      <div class="pane"><h3>Selected company comparison</h3><div id="private-peers"></div></div>
    </section>
    <section class="private-view" data-private-view="settings" hidden>
      <div class="pane"><h3>Virtual account balance</h3><p class="tiny">Change your simulation budget without any bank transfer or brokerage order. Deposits and withdrawals affect only uninvested cash. Reset clears virtual positions and trades but preserves notes.</p>
      <div class="formgrid" style="margin-top:14px"><div class="field"><label for="private-capital-action">Change</label><select id="private-capital-action"><option value="deposit">Add virtual cash</option><option value="withdraw">Withdraw virtual cash</option><option value="reset">Start a new virtual portfolio</option></select></div><div class="field"><label for="private-capital-amount">Amount ($)</label><input id="private-capital-amount" type="number" min="1" max="1000000" step="1" value="10000"></div></div>
      <div class="controls"><button class="btn" id="private-capital-submit">Update virtual balance</button></div></div>
      <div class="pane"><h3>Research notes</h3><div class="field" style="margin-top:12px"><label for="private-note">Private note</label><textarea id="private-note" maxlength="2000" rows="3" placeholder="Write a research note..."></textarea></div>
      <div class="controls"><button class="btn" id="private-note-submit">Save note</button></div><div id="private-notes"></div><p class="tiny">Watchlist: <span id="private-watchlist">None</span></p></div>
    </section>
  </div>
  <div id="private-asset-browser" class="private-picker" hidden role="dialog" aria-modal="true" aria-labelledby="asset-browser-title">
    <div class="picker-shell">
      <div class="picker-header"><div><h2 id="asset-browser-title">Choose an investment</h2><p class="tiny">Browse by name. No ticker knowledge required.</p></div><button class="btn sm" id="asset-browser-close" type="button" aria-label="Close investment browser">Close</button></div>
      <div class="controls picker-controls"><button class="btn sm" data-asset-category="popular" type="button">Popular</button><button class="btn sm" data-asset-category="all" type="button">All stocks &amp; ETFs</button><button class="btn sm" data-asset-category="crypto" type="button">Supported crypto</button></div>
      <div class="field"><label for="asset-browser-search">Filter by company name (optional)</label><input id="asset-browser-search" maxlength="60" autocomplete="off" placeholder="Optional name search"></div>
      <div class="picker-letters" id="asset-browser-letters" aria-label="Browse by first letter"></div>
      <div id="asset-browser-status" class="tiny" role="status" aria-live="polite">Select a category.</div>
      <div id="asset-browser-results" class="picker-results"></div>
      <div class="controls"><button class="btn sm" type="button" id="asset-browser-prev">Previous</button><span class="tiny" id="asset-browser-page"></span><button class="btn sm" type="button" id="asset-browser-next">Next</button></div>
    </div>
  </div>
  <p id="private-message" class="tiny" role="status" aria-live="polite"></p>
</section>'''
html=html.replace('<div class="footerline">',block+'\n<div class="footerline">',1)
html=html.replace('<script>/* QF_APP */</script>', '<script>/* QF_APP */</script>\n<script>/* QF_PRIVATE */</script>')
html=html.replace('All figures are fictional; none are market observations.','All demo figures are fictional; the private workspace uses a separate data source.')
html=html.replace('Methods are simplified client-side implementations for review.', 'Public analysis uses separate simplified client-side calculations; private positions use the authenticated API.')
html=html.replace('.navtop{display:none}', '#private-research-dataset[hidden],#private-signed[hidden],#private-login[hidden],#private-mfa[hidden],#private-mfa-qr-wrap[hidden],#private-mfa-setup-actions[hidden]{display:none!important}#private-message{margin-top:8px}.navtop{display:none}')
html=html.replace('body></html>','body></html>')
# Ensure all app scripts stay CSP-protected; no external JS libraries.
snapshot_path=src/'site/sec_snapshot.json'
snapshot=json.loads(snapshot_path.read_text(encoding="utf-8")) if snapshot_path.exists() else None
if snapshot is not None:
 from build_public_sec_snapshot import ISSUERS
 public_companies = snapshot.get('companies', [])
 symbols = [c.get('symbol') for c in public_companies if isinstance(c, dict)]
 if (snapshot.get('dataset') != 'SEC EDGAR Company Facts, annual 10-K US-GAAP'
     or len(symbols) != len(ISSUERS) or set(symbols) != set(ISSUERS)
     or any(c.get('cik') != ISSUERS[c['symbol']][0] or
            c.get('source_url') != f"https://data.sec.gov/api/xbrl/companyfacts/CIK{c['cik']:010d}.json"
            or not isinstance(c.get('annual'), list) or len(c['annual']) < 2
            for c in public_companies)):
  raise ValueError('SEC snapshot validation failed; regenerate the 12-company file from the official source')
snapshot_js=json.dumps(snapshot, separators=(',',':'), ensure_ascii=True).replace('<', r'\u003c').replace('>', r'\u003e').replace('&', r'\u0026')
for slot, file in [('/* QF_MODEL */','model.js'),('/* QF_APP */','app.js'),('/* QF_PRIVATE */','private.js')]:
 text=(src/'site'/file).read_text(encoding="utf-8")
 if file=='private.js':
  # Bundled alongside the existing private script: still only three CSP-protected scripts.
  text=(src/'site/private_ideas_v70.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_decision_v72.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_optimizer.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_multimarket.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_forecast_v65.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_walkforward_v65.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_diagnostics_v66.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_integrity_v67.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_robustness_v68.js').read_text(encoding='utf-8')+'\n'+text
 if file=='app.js':
  assert text.count('/* QF_SEC_DATA */ null')==1
  # Bundle pure SEC analytics in the existing public app script. CSP remains 3 hashes.
  analytics=(src/'site/sec_analytics.js').read_text(encoding='utf-8')
  text=analytics+'\n'+text.replace('/* QF_SEC_DATA */ null', snapshot_js)
 text=text.replace('</script','<\\/script')
 html=html.replace(slot,text)
(root/'public/index.html').write_text(html, encoding="utf-8")
scripts=re.findall(r'<script>(.*?)</script>',html,re.DOTALL)
assert len(scripts)==3
hashes=["'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in scripts]
csp="default-src 'none'; script-src "+' '.join(hashes)+"; style-src 'unsafe-inline'; connect-src 'self'; img-src data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
(root/'public/_headers').write_text("/*\n  Content-Security-Policy: "+csp+"\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n", encoding="utf-8")
print('Built',root/'public/index.html',len(html),'bytes',len(scripts),'protected scripts')
