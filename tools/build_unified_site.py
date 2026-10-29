import base64
import hashlib
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
src=root/'web'
html=(src/'site/site.template.html').read_text(encoding="utf-8")
nav='<div class="qf-nav-section qf-private-nav-section" role="group" aria-label="Account access"><span class="nav-caption">Your account</span><button class="nav-btn" data-page="private">Private workspace</button></div>'
html=html.replace('</nav>',nav+'</nav>',1)
block='''<section class="tabpage" id="page-private">
  <div class="pagehead"><h1>Private workspace</h1><p id="private-status">Private · Sign in required</p><p class="tiny">Personal holdings, market-history analysis, and company valuation. Sign-in and authenticator verification required.</p></div>
  <div class="pane" id="private-login"><h3>Sign in</h3>
    <div class="formgrid" style="margin-top:14px">
      <div class="field"><label for="private-email">Email</label><input id="private-email" type="email" autocomplete="username" placeholder="Your private account"></div>
      <div class="field"><label for="private-password">Password</label><input id="private-password" type="password" autocomplete="current-password" placeholder="Password"></div>
    </div><div class="controls"><button class="btn primary" id="private-login-submit">Sign in</button><span class="tiny">Owner access only. Password and authenticator verification are required.</span></div>
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
    <div class="controls"><span class="mini">Private portfolio · authenticated</span><button class="btn sm" id="private-logout">Sign out</button></div>
    <nav class="private-nav" aria-label="Private workspace sections">
      <details class="private-nav-group" role="group" aria-label="Decision Center" open><summary class="private-nav-title">01 · Decision Center</summary><div class="private-nav-actions"><button class="active" data-private-tab="decision">Automated assessment</button></div></details>
      <details class="private-nav-group" role="group" aria-label="Explore Investments"><summary class="private-nav-title">02 · Explore Investments</summary><div class="private-nav-actions"><button data-private-tab="ideas">Company discovery &amp; screening</button></div></details>
      <details class="private-nav-group" role="group" aria-label="My Portfolio"><summary class="private-nav-title">03 · My Portfolio</summary><div class="private-nav-actions"><button data-private-tab="home">Holdings overview</button><button data-private-tab="trade">Virtual trades &amp; scenarios</button></div></details>
      <details class="private-nav-group" role="group" aria-label="Advanced Research Lab"><summary class="private-nav-title">04 · Advanced Research Lab</summary><div class="private-nav-actions"><button data-private-tab="lab">Research Lab overview</button><button data-private-tab="research">Market data &amp; datasets</button><button data-private-tab="candidate">Individual company &amp; factors</button><button data-private-tab="valuation">Company valuation</button><button data-private-tab="optimization">Optimization &amp; risk</button><button data-private-tab="backtest">Historical backtests</button><button data-private-tab="walkforward">Walk-forward &amp; robustness</button></div></details>
      <details class="private-nav-group" role="group" aria-label="Research Settings and History"><summary class="private-nav-title">05 · Research Settings &amp; History</summary><div class="private-nav-actions"><button data-private-tab="settings">Research preferences, guide &amp; notes</button></div></details>
    </nav>
    <div id="private-research-dataset" class="pane" hidden aria-label="Research investments">
      <div class="section-title"><h3>Research investments</h3><span class="tiny">Used in Market data, Optimization, Backtests and Walk-forward</span></div>
      <p class="tiny">Choose 2–5 investments and a time period, then load their price history. Optimization, backtesting and walk-forward testing use the same loaded observations. Changing the selection or period requires reloading and recalculating.</p>
      <div class="formgrid" style="margin-top:14px"><div class="field"><label for="private-history-selection">Selected investments (2–5)</label><input type="hidden" id="private-history-symbols" value=""><div id="private-history-selection" class="chosen-assets">Choose investments to compare.</div><button class="btn sm" type="button" id="private-browse-research">Browse investments</button></div>
      <div class="field"><label for="private-history-days">History period</label><select id="private-history-days"><option value="90">3 months</option><option value="180">6 months</option><option selected value="365">1 year</option><option value="730">2 years</option></select></div></div>
      <div class="controls"><button class="btn primary" id="private-history-load">Load market history</button><span class="tiny" id="private-history-source"></span></div>
      <div class="pane" style="background:var(--card,#f6faf8);padding:12px;margin-top:12px;border:1px solid #c9ded5;border-radius:9px">
        <p class="tiny" style="margin:0 0 8px"><strong>Selected investments:</strong> <span id="private-research-selected" aria-live="polite">None selected</span></p>
        <div class="tiny"><strong>Historical data loaded:</strong> <span id="private-research-loaded" aria-live="polite">No historical data loaded</span></div>
      </div>
      <p class="tiny" id="private-research-state" role="status" aria-live="polite">No market history loaded for the current selection.</p>
    </div>
    <section class="private-view" data-private-view="lab" hidden>
      <div class="pane qf-v9-shell"><span class="eyebrow">ADVANCED RESEARCH · METHODS LIBRARY</span><h2>Advanced Research Lab</h2>
      <p>The Decision Center runs applicable research automatically. Use this lab to inspect algorithms, change assumptions, and investigate statistical findings in greater detail.</p>
      <p class="tiny">Investment analysis is organized by purpose. Models use dated, matched observations; they do not execute orders.</p>
      <div class="qf-v9-lab-grid">
        <button type="button" data-private-tab="candidate"><strong>Company &amp; factor research</strong><small>SEC fundamentals, downside risk, market ETF beta, independent FF3 regressions</small></button>
        <button type="button" data-private-tab="valuation"><strong>Valuation &amp; scenario modeling</strong><small>Cash-flow assumptions, financial statements and observed-price ratios</small></button>
        <button type="button" data-private-tab="research"><strong>Market data &amp; price history</strong><small>Inspect aligned observations and selected investments</small></button>
        <button type="button" data-private-tab="optimization"><strong>Optimization &amp; risk</strong><small>Covariance, concentration and constrained allocations</small></button>
        <button type="button" data-private-tab="backtest"><strong>Historical backtests</strong><small>Compare buy-and-hold versus periodic rebalancing</small></button>
        <button type="button" data-private-tab="walkforward"><strong>Walk-forward &amp; robustness</strong><small>Past-only fitting, transaction costs and window sensitivity</small></button>
      </div></div>
    </section>
    <section class="private-view" data-private-view="home" hidden>
      <div class="qf-private-start"><h2>Portfolio overview</h2><p class="qf-private-section-intro">Check your virtual holdings, then choose a research task. Detailed calculators and the plain-English guide live in their own sections.</p><div class="qf-private-paths"><button type="button" data-private-tab="ideas"><strong>Find investments</strong><small>Compare selected stocks and funds</small></button><button type="button" data-private-tab="research"><strong>Analyze market history</strong><small>Load prices for risk and strategy testing</small></button><button type="button" data-private-tab="decision"><strong>Assess current evidence</strong><small>Compare findings, gaps and next steps</small></button><button type="button" data-private-tab="settings"><strong>Read my research guide</strong><small>Explain completed analyses in plain language</small></button></div></div>
      <p class="qf-private-nav-note">All holdings and transactions in this workspace are virtual. Prices are dated observations, not guarantees.</p>
      <div class="pane"><div class="three"><div class="metric"><span class="muted">Virtual portfolio value</span><strong id="private-total">—</strong></div><div class="metric"><span class="muted">Available cash</span><strong id="private-cash">—</strong></div><div class="metric"><span class="muted">Invested value</span><strong id="private-invested">—</strong></div></div><div class="section-title"><h3>Holdings</h3><button class="btn sm" data-private-tab="trade">Trade</button></div><div id="private-positions"></div></div>
      <div class="pane"><h3>Holdings by weight</h3><div id="private-concentration" class="tiny" style="margin-top:12px">Add virtual holdings to see allocation.</div></div>
    </section>
    <section class="private-view" data-private-view="decision">
      <div class="pane qf-v9-shell" id="private-decision-os-v90">
        <span class="eyebrow">PRIVATE · AUTOMATED RESEARCH</span><h2>Investment Decision Center</h2>
        <p>Choose the investments you want analyzed. QuantForge loads available observations, runs eligible models, checks your criteria and proposes an action with a full evidence trail. You can inspect all algorithms in Advanced Research Lab.</p>
        <div class="qf-v9-fields">
          <div class="field"><label for="private-v90-candidate">Investment to assess</label><select id="private-v90-candidate"><option value="">Choose an investment from your selection</option></select></div>
          <div class="field"><label for="private-v90-risk">Risk approach</label><select id="private-v90-risk"><option value="conservative">Conservative</option><option selected value="balanced">Balanced</option><option value="growth">Growth-oriented</option></select></div>
          <div class="field"><label for="private-v90-horizon">Investment horizon</label><select id="private-v90-horizon"><option value="short">Under 1 year</option><option selected value="medium">1–5 years</option><option value="long">5+ years</option></select></div>
          <div class="field"><label for="private-v90-maxweight">Single-name portfolio ceiling</label><select id="private-v90-maxweight"><option value="0.10">10%</option><option selected value="0.20">20%</option><option value="0.35">35%</option></select></div>
          <div class="field"><label for="private-v90-maxdrawdown">Historical drawdown screen</label><select id="private-v90-maxdrawdown"><option value="0.15">15%</option><option selected value="0.25">25%</option><option value="0.40">40%</option></select></div>
          <div class="field"><label for="private-v90-days">Research history period</label><select id="private-v90-days"><option value="180">6 months</option><option selected value="365">1 year</option><option value="730">2 years</option></select></div>
        </div>
        <div class="controls"><button type="button" class="btn" id="private-v90-browse">Browse companies by name</button><button type="button" class="btn primary" id="private-v90-run">Run complete research</button><span class="tiny">No automatic trading · No external AI costs</span></div>
        <p class="tiny" id="private-v90-selection" aria-live="polite">Choose 2–5 investments; historical comparisons require more than one security.</p>
        <div id="private-v90-report" aria-live="polite" role="status"><p class="tiny">Start a research run to receive a conditional investment assessment, reasons, objections and a full audit of usable models.</p></div>
      </div>
      <details class="pane qf-v9-legacy"><summary>Previously completed research review (manual)</summary>
      <div class="pane" id="private-decision-center-v84">
        <span class="eyebrow">PRIVATE RESEARCH · INTEGRATED ASSESSMENT</span>
        <h2 style="margin:9px 0">Investment Decision Center</h2>
        <p class="qf-private-section-intro">Bring together the analyses already run in this session. See the covered investments, what the models agree or disagree about, which evidence is missing, and the next calculation to perform. Nothing here moves money or changes your virtual portfolio.</p>
        <div class="controls"><button class="btn primary" type="button" id="private-decision-run-v84">Assess current evidence</button><span class="tiny">Generated on demand · MFA-protected</span></div>
        <div id="private-decision-result-v84" aria-live="polite" style="margin-top:15px"><p class="tiny">Choose Assess current evidence to review your completed analyses.</p></div>
      </div></details>
    </section>
    <section class="private-view" data-private-view="candidate" hidden>
      <div class="pane"><span class="eyebrow">RESEARCH LAB · SINGLE COMPANY</span><h2>Company &amp; Factor Research</h2>
      <p class="tiny">Expert methods and charts are collected here. The Decision Center uses eligible results automatically without requiring you to operate every model.</p>
        <section class="qf-v85-candidate" id="private-candidate-v85" aria-labelledby="private-candidate-title-v85">
          <span class="eyebrow">SINGLE-INVESTMENT RESEARCH</span><h3 id="private-candidate-title-v85">Candidate risk, valuation and portfolio scenarios</h3>
          <p class="tiny">Choose from the investments whose historical prices you actually loaded. Review SEC-derived company facts when available, observed-price valuation ratios, downside risk and a peer-relative return comparison. The selected peers are not a market-index factor model.</p>
          <div class="formgrid"><div class="field"><label for="private-candidate-select-v85">Investment to examine</label>
            <select id="private-candidate-select-v85"><option value="">Load historical observations first</option></select>
          </div></div>
          <div class="qf-v86-controls formgrid" aria-label="Benchmark, proxy, and valuation scenario choices">
            <div class="field"><label for="private-v86-benchmark">Market ETF benchmark</label><select id="private-v86-benchmark"><option value="">Choose a loaded broad-market ETF</option></select></div>
            <div class="field"><label for="private-v86-proxy1">Additional ETF proxy 1 (optional)</label><select id="private-v86-proxy1"><option value="">None</option></select></div>
            <div class="field"><label for="private-v86-proxy2">Additional ETF proxy 2 (optional)</label><select id="private-v86-proxy2"><option value="">None</option></select></div>
            <div class="field"><label for="private-v86-years">Valuation scenario horizon</label><select id="private-v86-years"><option value="1">1 year</option><option value="3">3 years</option></select></div>
          </div>
          <p class="tiny">Market beta requires SPY, VTI, VOO or IVV within your loaded investment history. Other eligible ETF selections are <strong>proxies</strong>, not Fama–French factors. No external benchmark is fetched behind the scenes.</p>
          <div class="controls"><button type="button" class="btn primary" id="private-candidate-run-v85">Analyze this investment</button><span class="tiny">On demand · private session · no trade</span></div>
          <div id="private-candidate-output-v85" aria-live="polite" role="status" class="qf-v85-output"><p class="tiny">Load market history, then choose a candidate to examine.</p></div>
          <div id="private-v86-output" aria-live="polite" class="qf-v86-output"></div>
          <section class="qf-v87-study" aria-labelledby="private-v87-title">
            <span class="eyebrow">INDEPENDENT RESEARCH FACTORS · V8.7</span>
            <h3 id="private-v87-title">Fama–French three-factor model validation</h3>
            <p class="tiny">Import the official <strong>daily</strong> three-factor CSV (not monthly) from the <a href="https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html" target="_blank" rel="noopener noreferrer">Kenneth French Data Library</a>. Download the daily CSV ZIP, extract the CSV, then choose it here. The file is read inside this authenticated browser session only; it is not uploaded or stored. Source authenticity is not automatically verified.</p>
            <div class="formgrid"><div class="field"><label for="private-v87-factor-file">Extracted daily FF3 research-factor CSV</label><input type="file" id="private-v87-factor-file" accept=".csv,.txt,text/csv,text/plain" /></div></div>
            <p class="tiny" id="private-v87-factor-status" role="status" aria-live="polite">No independently sourced factor file imported.</p>
            <div class="controls"><button type="button" class="btn primary" id="private-v87-factor-run">Estimate and validate factor exposures</button><button type="button" class="btn sm" id="private-v87-factor-clear">Clear imported factors</button></div>
            <div id="private-v87-factor-output" role="status" aria-live="polite"></div>
          </section>
        </section>
      </div>
    </section>
    <section class="private-view" data-private-view="trade" hidden>
      <p class="qf-private-section-intro">Check an observed quote, test the impact of a proposed purchase, or record a virtual transaction. Portfolio cash management is here too.</p>
      <div class="pane"><h3>Prices and virtual trades</h3><p class="tiny">Request the latest available stock, ETF, or supported cryptocurrency observation, then record a simulated trade if desired. Prices are source- and time-stamped; no brokerage order is sent.</p>
      <div class="formgrid" style="margin-top:12px"><div class="field"><label for="private-selected-asset">Investment</label><input type="hidden" id="private-symbol" value=""><div class="selected-asset" id="private-selected-asset">No investment selected</div><button class="btn sm" type="button" id="private-browse-trade">Browse investments</button></div>
      <div class="field"><label for="private-side">Action</label><select id="private-side"><option value="buy">Buy with USD budget</option><option value="sell">Sell units</option></select></div>
      <div class="field"><label for="private-amount">USD budget / units</label><input type="number" min="0.00000001" step="any" id="private-amount" value="100"></div></div>
      <div class="controls"><button class="btn" id="private-quote-submit">Get market price</button><button class="btn primary" id="private-trade-submit">Record virtual trade</button></div><p id="private-quote" class="tiny" style="margin-top:12px">No quote loaded.</p></div>

      <div class="pane" id="private-allocation-card-v74">
        <h3>Proposed purchase impact</h3>
        <p class="tiny">Check how a hypothetical cash-funded purchase changes your current virtual portfolio weights, using available market observations. This calculation neither records a virtual trade nor places a brokerage order.</p>
        <div class="formgrid" style="margin-top:14px">
          <div class="field"><label for="private-allocation-symbol-v74">Investment</label><select id="private-allocation-symbol-v74"><option value="">Choose an investment</option></select></div>
          <div class="field"><label for="private-allocation-budget-v74">Proposed spending (USD)</label><input id="private-allocation-budget-v74" type="number" min="1" step="1" value="250"></div>
        </div>
        <p id="private-allocation-selection-v74" class="tiny">Choose from screened investments or current virtual holdings.</p>
        <div class="controls"><button class="btn" type="button" id="private-allocation-choices-v74">Refresh choices</button><button class="btn primary" type="button" id="private-allocation-run-v74">Calculate impact</button><button class="btn" type="button" id="private-allocation-export-v74" disabled>Export research JSON</button></div>
        <div id="private-allocation-results-v74" aria-live="polite" style="margin-top:15px"></div>
      </div>
      <div class="pane"><h3>Virtual cash balance</h3><p class="tiny">Add or withdraw simulated cash, or reset virtual holdings and transaction history. These changes do not move actual money. Saved research notes are preserved after a portfolio reset.</p>
      <div class="formgrid" style="margin-top:14px"><div class="field"><label for="private-capital-action">Change</label><select id="private-capital-action"><option value="deposit">Add virtual cash</option><option value="withdraw">Withdraw virtual cash</option><option value="reset">Start a new virtual portfolio</option></select></div><div class="field"><label for="private-capital-amount">Amount ($)</label><input id="private-capital-amount" type="number" min="1" max="1000000" step="1" value="10000"></div></div>
      <div class="controls"><button class="btn" id="private-capital-submit">Update virtual balance</button></div></div>
    </section>
    <section class="private-view" data-private-view="ideas" hidden>
      <div class="pane"><span class="eyebrow">HISTORICAL PRICE AND FINANCIAL DATA</span><h2 style="margin:7px 0 9px">Investment screening</h2>
        <p class="muted">Compare selected stocks and ETFs using historical momentum, volatility, drawdown, and available SEC fundamentals. Scores rank candidates under the selected criteria; they do not estimate future returns or recommend trades.</p>
        <div class="section-title" style="margin-top:18px"><h3>Screening list</h3><span class="tiny" id="ideas-count"></span></div>
        <div id="ideas-selected" class="chosen-assets" aria-live="polite"></div>
        <div class="controls"><button class="btn sm" type="button" id="ideas-browse">Browse investments</button><button class="btn sm" type="button" id="ideas-reset">Reset list</button></div>
        <div class="formgrid" style="margin-top:17px">
          <div class="field"><label for="ideas-lens">Research perspective</label><select id="ideas-lens"><option value="balanced">Balanced: momentum and downside</option><option value="growth">Growth: recent trends emphasized</option><option value="defensive">Risk-aware: volatility and drawdown emphasized</option></select></div>
          <div class="field"><label for="ideas-period">Historical observation window</label><select id="ideas-period"><option value="365" selected>1 year</option><option value="730">2 years</option></select></div>
        </div>
        <label class="inline-checkbox"><input id="ideas-sec" type="checkbox" checked> Include available SEC business fundamentals (slower)</label>
        <div class="controls"><button class="btn primary" id="ideas-run" type="button">Compare selected investments</button></div>
        <p class="tiny" role="status" aria-live="polite" id="ideas-status">Choose companies by name or use the starting shortlist.</p>
        <div id="ideas-brief" class="decision-brief" hidden>
          <div class="section-title"><div><span class="eyebrow">HISTORICAL DECISION SUPPORT</span><h3>Screening summary</h3></div><button class="btn sm" type="button" id="ideas-brief-export" disabled>Download research brief (JSON)</button></div>
          <p class="tiny">Summarizes comparative measures, overlap with existing holdings, and unresolved risks. Historical ranks are not trade recommendations.</p>
          <div id="ideas-brief-output" aria-live="polite"></div>
        </div>
        <div id="ideas-results" aria-live="polite"></div>
      </div>
      <div class="pane"><h3>Reading the scores</h3><p class="tiny" style="margin-top:9px">A higher research score indicates a more favorable balance of <strong>past</strong> momentum and realized risk under the selected lens. It is not an estimated probability of profit, expected return, or price target. SEC results describe past business finances separately; ETFs generally do not have comparable company income statements. Reassess against valuation, diversification, fees, tax impact, investment horizon, and the risk of loss before any real-money decision. IEX-only bars are not consolidated market-wide prices.</p></div>
    </section>
    <section class="private-view" data-private-view="research" hidden>
      <div class="pane"><h3>Historical prices and risk</h3><p class="tiny">Load daily stock, ETF, or supported USD cryptocurrency prices from the private Alpaca connection. Equity prices are price-only, excluding dividends; cryptocurrency trades seven days a week.</p>
      <p class="tiny">Check the Research investments panel above for selected symbols, loaded observations, and date coverage.</p>
      <div id="private-history-chart" class="private-chart" style="margin-top:15px">Load a historical series to begin.</div><div id="private-risk-results"></div>
      </div>
    </section>
    <section class="private-view" data-private-view="optimization" hidden>
      <div class="pane"><h3>Optimize an allocation</h3><p class="tiny">Use the loaded historical returns to calculate long-only weights subject to concentration limits. Review correlations and risk contributions before interpreting the proposed allocation. Results do not alter your virtual holdings.</p>
        <div class="formgrid" style="margin-top:15px">
          <div class="field"><label for="private-opt-objective">Allocation method</label><select id="private-opt-objective"><option value="minimum">Minimum historical volatility</option><option value="inverse">Inverse-volatility allocation</option><option value="tilt">Historical return tilt</option></select></div>
          <div class="field"><label for="private-opt-cap">Maximum weight per investment</label><select id="private-opt-cap"><option value="0.35">35%</option><option value="0.40">40%</option><option value="0.50">50%</option><option selected value="0.60">60%</option><option value="0.75">75%</option><option value="1.00">100%</option></select></div>
        </div>
        <div class="controls"><button class="btn primary" id="private-opt-run" type="button">Calculate allocations</button><button class="btn" id="private-opt-export" type="button" disabled>Export allocations CSV</button></div>
        <div id="private-opt-output" style="margin-top:16px" aria-live="polite">Select 2–5 investments in Market data, load their history, then calculate an allocation.</div>
      </div>
      <div class="pane"><h3>Risk diagnostics</h3><p class="tiny">Risk estimates use historical returns and a 20% diagonal covariance shrinkage. Correlations, drawdowns, and tail-loss statistics describe the selected sample; they do not predict future outcomes.</p><div id="private-opt-risk" style="margin-top:15px">Risk diagnostics appear after an allocation is calculated.</div></div>
    </section>
    <section class="private-view" data-private-view="backtest" hidden>
      <div class="pane"><h3>Buy-and-hold vs. rebalancing</h3><p class="tiny">Compare equal-weight buy-and-hold and monthly rebalancing on the loaded historical price series, after modeled transaction fees. These are retrospective calculations, not an executable trading record.</p>
      <div class="formgrid" style="margin-top:14px"><div class="field"><label for="private-test-capital">Starting virtual capital ($)</label><input id="private-test-capital" type="number" min="100" max="1000000" step="100" value="10000"></div>
      <div class="field"><label for="private-test-fee">Fee per rebalance (basis points)</label><input id="private-test-fee" type="number" min="0" max="100" step="1" value="5"></div></div>
      <div class="controls"><button class="btn primary" id="private-backtest-run">Run backtest</button></div>
      <div id="private-backtest-output" style="margin-top:15px"></div></div>
    </section>
    <section class="private-view" data-private-view="walkforward" hidden>
      <div class="pane"><h3>Walk-forward strategy comparison</h3><p class="tiny">Fit portfolio weights on earlier prices and evaluate on subsequent periods, refitting at each boundary. Compare against equal-weight rebalancing using the same transaction-fee assumptions. No brokerage orders.</p>
        <div class="formgrid" style="margin-top:14px">
          <div class="field"><label for="private-wf-train">Training window</label><select id="private-wf-train"><option value="63">63 observations</option><option selected value="126">126 observations</option><option value="252">252 observations</option></select></div>
          <div class="field"><label for="private-wf-step">Out-of-sample test window</label><select id="private-wf-step"><option selected value="21">21 observations</option><option value="42">42 observations</option></select></div>
          <div class="field"><label for="private-wf-mode">Allocation rule</label><select id="private-wf-mode"><option value="minimum">Minimum historical volatility</option><option value="inverse">Inverse volatility</option><option value="tilt">Historical-return tilt</option></select></div>
          <div class="field"><label for="private-wf-cap">Maximum position weight</label><select id="private-wf-cap"><option value="0.35">35%</option><option value="0.40">40%</option><option value="0.50">50%</option><option selected value="0.60">60%</option><option value="0.75">75%</option><option value="1.00">100%</option></select></div>
          <div class="field"><label for="private-wf-fee">Fee per turnover (bps)</label><input id="private-wf-fee" type="number" min="0" max="100" value="5" step="1"></div>
          <div class="field"><label for="private-wf-capital">Research capital ($)</label><input id="private-wf-capital" type="number" min="100" max="1000000" value="10000"></div>
        </div>
        <div class="controls"><button class="btn primary" type="button" id="private-wf-run">Run walk-forward test</button><button class="btn" id="private-wf-export" type="button" disabled>Export test windows CSV</button></div>
        <div id="private-wf-output" style="margin-top:15px" aria-live="polite">Load price history in Market data to begin.</div>
        <div id="private-wf-diagnostics" class="pane" hidden style="margin-top:14px"><h3>Performance and risk diagnostics</h3><div id="private-wf-diagnostics-content"></div>
          <div class="controls"><button class="btn" type="button" id="private-wf-robustness" disabled>Check transaction-cost sensitivity</button><button class="btn" type="button" id="private-wf-report" disabled>Download research report (JSON)</button></div>
          <div id="private-wf-robustness-output" aria-live="polite"></div>
          <div class="pane" style="margin-top:16px"><h3>Benchmark and sensitivity checks</h3>
          <p class="tiny">Compare a passive benchmark, alternative weight rules, larger fees, and leave-one-window-out sensitivity on matched evaluation dates. Select a longer history in Research investments and reload if the analysis has too few test windows.</p>
          <div class="controls"><button class="btn" type="button" id="private-wf-v68-run" disabled>Check strategy robustness</button><button class="btn" type="button" id="private-wf-v68-export" disabled>Download robustness report (JSON)</button></div>
          <div id="private-wf-v68-output" aria-live="polite">Run Walk-forward first, then check robustness.</div></div></div>
        <p class="tiny">Model uses price-only historical returns; no dividends, borrow costs, slippage, taxes, or corporate-action simulations. Backtests remain subject to selection bias and do not establish future performance.</p>
      </div>
    </section>
    <section class="private-view" data-private-view="valuation" hidden>
      <div class="pane"><h3>SEC-based valuation scenarios</h3><p class="tiny">Start with company cash-flow disclosures and vary growth, discount, and terminal-value assumptions. Alpaca prices are separate market observations, not accounting data. Scenario values are not price targets.</p>
      <div class="formgrid" style="margin-top:14px"><div class="field"><label for="private-valuation-company">Company</label><input id="private-valuation-company" type="hidden"><div class="selected-asset" id="private-valuation-selected">No company selected</div><button class="btn sm" id="private-browse-valuation" type="button">Browse companies</button></div>
      <div class="field"><label for="private-valuation-growth">Annual FCF growth (%)</label><input id="private-valuation-growth" type="number" min="-30" max="40" value="4"></div>
      <div class="field"><label for="private-valuation-wacc">Discount rate (%)</label><input id="private-valuation-wacc" type="number" min="2" max="30" value="10"></div>
      <div class="field"><label for="private-valuation-terminal">Terminal growth (%)</label><input id="private-valuation-terminal" type="number" min="-5" max="8" value="2"></div></div>
      <div class="controls"><button class="btn primary" id="private-valuation-run">Run scenario</button></div><div id="private-valuation-output" style="margin-top:15px"></div><div id="private-value-card-v73" style="margin-top:18px;border-top:1px solid #d8e6df;padding-top:14px">
          <h3>Market price and financial context</h3>
          <p class="tiny">SEC-reported shares and annual cash flows are compared with the latest available Alpaca market observation. Ratios depend on disclosure dates and quote coverage; they are not fair-value estimates.</p>
          <div class="controls"><button type="button" class="btn" id="private-value-run-v73">Compare observed market price</button></div>
          <div id="private-value-output-v73" aria-live="polite" style="margin-top:12px"></div>
        </div></div>
      <div class="pane"><h3>Multi-year cash-flow scenarios</h3>
        <p class="tiny">Projections use the selected company’s reported SEC annual baseline and hypothetical revenue growth, FCF-margin, and discount-rate assumptions. Conservative and optimistic cases vary growth by 4 percentage points and FCF margin by 3 points. Reported statements remain unchanged.</p>
        <div class="formgrid" style="margin-top:14px">
          <div class="field"><label for="private-fc-years">Projection horizon</label><select id="private-fc-years"><option value="3">3 years</option><option selected value="5">5 years</option><option value="7">7 years</option></select></div>
          <div class="field"><label for="private-fc-growth">Base annual revenue growth (%)</label><input id="private-fc-growth" type="number" min="-30" max="40" value="6" step="0.5"></div>
          <div class="field"><label for="private-fc-margin">Base FCF proxy / revenue (%)</label><input id="private-fc-margin" type="number" min="-25" max="60" value="12" step="0.5"></div>
          <div class="field"><label for="private-fc-discount">Discount rate (%)</label><input id="private-fc-discount" type="number" min="2" max="30" value="10" step="0.5"></div>
          <div class="field"><label for="private-fc-terminal">Terminal growth (%)</label><input id="private-fc-terminal" type="number" min="-5" max="8" value="2" step="0.5"></div>
        </div>
        <div class="controls"><button class="btn primary" id="private-fc-run" type="button">Forecast selected company</button></div>
        <div id="private-fc-output" style="margin-top:15px" aria-live="polite">Load SEC statements for a selected company first.</div>
        <div id="private-fc-diagnostics" class="pane" hidden style="margin-top:14px"><h3>Valuation sensitivity</h3><div id="private-fc-diagnostics-content"></div>
          <div class="controls"><button class="btn" type="button" id="private-fc-report" disabled>Download financial research report (JSON)</button></div></div>
      </div>
      <div class="pane"><h3>Company comparison</h3><div id="private-peers"></div></div>
    </section>
    <section class="private-view" data-private-view="settings" hidden>
      <h2>Research guide and notes</h2><p class="qf-private-section-intro">Generate an evidence-based explanation of the analyses you have actually run. The report separates observations, limitations and next research steps; it does not decide whether to buy or sell.</p>
      <div class="pane" id="private-guide-card-v79">
        <div class="section-title"><h3>Research guide: what the evidence says</h3><span class="mini">Private · educational decision support</span></div>
        <p class="tiny">New to investing? Generate a plain-language review of your virtual portfolio, loaded market data, portfolio model, walk-forward results, and SEC company research. The guide uses only analyses currently available in this signed-in session. It never places trades or sends your information to an external AI provider.</p>
        <div class="formgrid" style="margin-top:12px">
          <div class="field"><label for="private-guide-horizon-v79">When could you need this money?</label><select id="private-guide-horizon-v79"><option value="unknown">Not sure yet</option><option value="short">Within 3 years</option><option value="medium">3–10 years</option><option value="long">More than 10 years</option></select></div>
          <div class="field"><label for="private-guide-comfort-v79">How would a large temporary loss affect you?</label><select id="private-guide-comfort-v79"><option value="unknown">Not sure yet</option><option value="low">I could not comfortably absorb it</option><option value="medium">I could tolerate some loss</option><option value="high">I understand substantial losses are possible</option></select></div>
        </div>
        <div class="controls"><button class="btn primary" id="private-guide-run-v79" type="button">Explain my current research</button><button class="btn" id="private-guide-export-v79" type="button" disabled>Export private report (JSON)</button></div>
        <div id="private-guide-result-v79" aria-live="polite" style="margin-top:14px"><p class="tiny">Click Explain my current research when signed in. Results stay in this browser session until cleared.</p></div>
        <details class="lab-details"><summary>Finance terms · plain-English reference</summary><div class="tiny" style="padding-top:10px"><p><strong>Volatility:</strong> how much prices moved up and down in the observed period.</p><p><strong>Drawdown:</strong> how far a portfolio fell from a prior high.</p><p><strong>Backtest:</strong> a calculation using past prices, not proof of future success.</p><p><strong>Walk-forward:</strong> a backtest that repeatedly fits on earlier data and checks later observations.</p><p><strong>Cash flow:</strong> money reported moving through a company; this is not the same as stock-price return.</p><p><strong>Concentration:</strong> how dependent your portfolio value is on one holding.</p><p><strong>SEC filing:</strong> a company disclosure filed with the US securities regulator.</p><p><strong>FCF proxy:</strong> operating cash flow minus cash spent on property and equipment; not a stock-price target.</p><p><strong>Discount rate:</strong> a model assumption about the value of future cash flow in today’s dollars.</p><p><strong>Correlation:</strong> how two observed return series moved together; historical correlation can change.</p></div></details>
        <details class="lab-details"><summary>Before acting: a research checklist</summary><div class="tiny" style="padding-top:10px"><ol><li>Can I explain what the company or fund owns and how it makes money?</li><li>Are my financial figures reported, current, and comparable across periods?</li><li>What do the historical risk and walk-forward results disagree about?</li><li>How would this change concentration or cash in my portfolio?</li><li>What information is still missing, and would a possible loss affect money I need soon?</li></ol><p>Use the analysis links in your generated report to answer each question. This is a review tool, not a buy/sell signal.</p></div></details>
        <p class="tiny">This is a rule-based research explanation, not a generative AI chatbot, investment recommendation, or personalized suitability determination. Nothing is sent to an AI service.</p>
      </div>

      <div class="pane"><h3>Saved research notes</h3><div class="field" style="margin-top:12px"><label for="private-note">Private note</label><textarea id="private-note" maxlength="2000" rows="3" placeholder="Write a research note..."></textarea></div>
      <div class="controls"><button class="btn" id="private-note-submit">Save note</button></div><div id="private-notes"></div><p class="tiny">Watchlist: <span id="private-watchlist">None</span></p></div>
    </section>
  </div>
  <div id="private-asset-browser" class="private-picker" hidden role="dialog" aria-modal="true" aria-labelledby="asset-browser-title">
    <div class="picker-shell">
      <div class="picker-header"><div><h2 id="asset-browser-title">Choose an investment</h2><p class="tiny">Search by company or fund name; ticker symbols are optional.</p></div><button class="btn sm" id="asset-browser-close" type="button" aria-label="Close investment browser">Close</button></div>
      <div class="controls picker-controls"><button class="btn sm" data-asset-category="popular" type="button">Popular</button><button class="btn sm" data-asset-category="all" type="button">All stocks &amp; ETFs</button><button class="btn sm" data-asset-category="crypto" type="button">Supported crypto</button></div>
      <div class="field"><label for="asset-browser-search">Search by name (optional)</label><input id="asset-browser-search" maxlength="60" autocomplete="off" placeholder="Optional name search"></div>
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
qfv9_css="""
/* V9 private operating system: public site remains visually unchanged. */
#private-signed .qf-v9-shell h2{margin:8px 0 10px;font-size:24px}
#private-signed .qf-v9-shell>p{font-size:13px;line-height:1.75;color:#435f50}
#private-signed .qf-v9-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:19px 0}
#private-signed .qf-v9-fields .field{min-width:0}
#private-signed .qf-v9-result{border:1px solid #c9dfd2;background:#f5faf6;border-radius:11px;padding:17px 20px;margin:18px 0}
#private-signed .qf-v9-result h3{margin:7px 0 10px;color:#174c3a;font-size:21px}
#private-signed .qf-v9-grid,#private-signed .qf-v9-lab-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;margin:14px 0}
#private-signed .qf-v9-evidence{border:1px solid #d5e5dc;border-radius:9px;padding:13px 15px;min-width:0;background:#fff}
#private-signed .qf-v9-evidence p{font-size:12px;color:#456557;line-height:1.5}
#private-signed .qf-v9-lab-grid button{border:1px solid #d4e2d9;border-radius:10px;background:#f9fcfa;padding:15px;display:flex;flex-direction:column;gap:7px;text-align:left;cursor:pointer}
#private-signed .qf-v9-lab-grid small{color:#4c6759;font-size:12px;line-height:1.5}
#private-signed .qf-v9-legacy{margin-top:16px}
#private-signed .qf-v9-legacy summary{cursor:pointer;font-weight:700;color:#1b5d45}
#private-signed .private-nav{grid-template-columns:repeat(5,minmax(0,1fr))}
#private-signed .private-nav-group{min-width:0}
#private-signed .private-nav .private-nav-group button{white-space:normal}
@media(min-width:1220px){#private-signed>.private-nav{display:flex;flex-direction:column}#private-signed>.private-nav>.private-nav-group{width:100%}}
@media(max-width:1200px){#private-signed .private-nav{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:700px){#private-signed .private-nav{grid-template-columns:1fr 1fr}#private-signed .qf-v9-fields,#private-signed .qf-v9-grid,#private-signed .qf-v9-lab-grid{grid-template-columns:1fr}}
@media(max-width:450px){#private-signed .private-nav{grid-template-columns:1fr}}
"""
html=html.replace('</style>',qfv9_css+'</style>',1)
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
     or len(symbols) != len(set(symbols)) or not set(ISSUERS).issubset(symbols)
     or any(not isinstance(c, dict) or not re.fullmatch(r'[A-Z0-9.\-]{1,15}', str(c.get('symbol', '')))
            or not isinstance(c.get('cik'), int) or c['cik'] <= 0
            or (c['symbol'] in ISSUERS and c['cik'] != ISSUERS[c['symbol']][0])
            or c.get('source_url') != f"https://data.sec.gov/api/xbrl/companyfacts/CIK{c['cik']:010d}.json"
            or not isinstance(c.get('annual'), list) or len(c['annual']) < 2
            or not all(isinstance(y,dict) and isinstance(y.get('fiscal_end'),str)
                       and isinstance(y.get('metrics'),dict) for y in c['annual'])
            for c in public_companies)):
  raise ValueError('SEC snapshot validation failed; core issuers and any additional company records must be validated')
snapshot_js=json.dumps(snapshot, separators=(',',':'), ensure_ascii=True).replace('<', r'\u003c').replace('>', r'\u003e').replace('&', r'\u0026')
for slot, file in [('/* QF_MODEL */','model.js'),('/* QF_APP */','app.js'),('/* QF_PRIVATE */','private.js')]:
 text=(src/'site'/file).read_text(encoding="utf-8")
 if file=='private.js':
  # Bundled alongside the existing private script: still only three CSP-protected scripts.
  text=(src/'site/private_ideas_v70.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_allocation_v74.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_value_v73.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_decision_v72.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_guide_v79.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_decision_center_v84.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_candidate_v85.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_factor_scenarios_v86.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_french_factors_v87.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_research_os_v90.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_optimizer.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_multimarket.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_forecast_v65.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_walkforward_v65.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_diagnostics_v66.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_integrity_v67.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_robustness_v68.js').read_text(encoding='utf-8')+'\n'+text
 if file=='app.js':
  assert text.count('/* QF_SEC_DATA */ null')==1
  # Bundle pure SEC analytics in the existing public app script. CSP remains 3 hashes.
  analytics=(src/'site/sec_analytics.js').read_text(encoding='utf-8')
  evidence=(src/'site/public_evidence_v76.js').read_text(encoding='utf-8')
  lab=(src/'site/public_lab_v77.js').read_text(encoding='utf-8')
  visuals=(src/'site/sec_visuals_v81.js').read_text(encoding='utf-8')
  text=analytics+'\n'+evidence+'\n'+lab+'\n'+visuals+'\n'+text.replace('/* QF_SEC_DATA */ null', snapshot_js)
 text=text.replace('</script','<\\/script')
 html=html.replace(slot,text)
(root/'public/index.html').write_text(html, encoding="utf-8")
scripts=re.findall(r'<script>(.*?)</script>',html,re.DOTALL)
assert len(scripts)==3
hashes=["'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in scripts]
csp="default-src 'none'; script-src "+' '.join(hashes)+"; style-src 'unsafe-inline'; connect-src 'self'; img-src data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
(root/'public/_headers').write_text("/*\n  Content-Security-Policy: "+csp+"\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n", encoding="utf-8")
print('Built',root/'public/index.html',len(html),'bytes',len(scripts),'protected scripts')
