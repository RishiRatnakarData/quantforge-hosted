import base64
import hashlib
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
src=root/'web'
html=(src/'site/site.template.html').read_text(encoding="utf-8")
nav='<div class="qf-nav-section qf-private-nav-section" role="group" aria-label="Account access"><span class="nav-caption">Your account</span><button class="nav-btn" data-page="private">Private workspace</button><button class="nav-btn qf-private-exit" data-page="overview">Public research</button></div>'
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
    <div class="controls"><span class="mini">Private portfolio · authenticated</span><strong class="tiny" id="qf-private-location" role="status" aria-live="polite">Decision Center / Research summary</strong><button class="btn sm" id="private-logout">Sign out</button></div>
    <nav class="private-nav qf-v170-nav" aria-label="Private workspace main destinations">
      <button class="active" data-private-tab="decision">Research</button>
      <button data-private-tab="home">Portfolio</button>
      <button data-private-tab="settings">Saved reports</button>
      <button data-private-tab="lab" class="qf-v170-advanced-link">Advanced research</button>
    </nav>
    <div id="qf-v93-research-ribbon" class="qf-v93-ribbon" role="status" aria-live="polite">
      <div class="qf-v93-ribbon-copy"><strong id="qf-v93-ribbon-title">Research workflow · No current assessment</strong><span class="tiny" id="qf-v93-ribbon-detail">Select companies and run research to connect your findings and reports.</span></div>
      <div class="controls"><button type="button" class="btn sm" id="qf-v93-ribbon-assess">Decision Center</button><button type="button" class="btn sm" id="qf-v93-ribbon-brief" disabled>Open briefing</button></div>
    </div>
    <section class="pane qf-v140-launch" aria-label="Private research workflow readiness">
      <div class="qf-v140-top"><div><span class="eyebrow">RESEARCH WORKFLOW</span><h3>What is ready, and what comes next?</h3></div><span id="qf-v140-progress" class="qf-v140-progress">0 / 5</span></div>
      <div id="qf-v140-status" class="tiny" role="status" aria-live="polite">Checking current research inputs.</div>
      <div id="qf-v140-steps" class="qf-v140-steps" aria-label="Research prerequisites"></div>
      <div class="controls"><button type="button" class="btn primary" id="qf-v140-next" disabled>Open next research step</button><button type="button" class="btn sm" data-private-tab="settings">Research briefing</button></div>
      <details class="qf-v140-acceptance"><summary>Live browser acceptance checklist (not yet independently verified)</summary>
      <p class="tiny">Automated tests and Cloudflare HTML verification cannot prove that authenticated provider workflows work. Complete these steps in a real browser, without sharing credentials or brokerage account data.</p>
      <ol class="tiny"><li>Sign in and complete MFA from a fresh private session.</li><li>Open Portfolio and confirm authorized holdings and market quotes load without an error.</li><li>Select 2–5 companies by name, load matching market data, and run one complete Decision Center assessment.</li><li>Confirm built-in SEC fundamentals work in standard research. If testing the optional local filing archive, inspect withheld dates in Advanced Research.</li><li>Open Research Lab and Briefing; confirm consistent candidate, model counts, and evidence status.</li><li>Save and delete a research archive note, then sign out and confirm protected data disappear. Test persistence after a separate sign-in.</li></ol>
      <p class="tiny">These are manual tests; this checklist does not automatically mark them passed.</p>
      <div class="qf-v150-acceptance" id="qf-v150-acceptance" aria-label="Owner-entered live acceptance results">
        <h4>Record actual browser checks</h4>
        <p class="tiny">Choose a result only after performing that action in this authenticated browser. These are self-attested checks, not automatic tests or proof of provider uptime. No passwords, tokens, holdings, or financial figures are recorded.</p>
        <ol id="qf-v150-checks" class="qf-v150-manual-grid">
          <li data-v150-check="mfa"><label for="qf-v150-mfa">Fresh sign-in and authenticator</label><select id="qf-v150-mfa" aria-label="MFA acceptance status"><option value="not-tested">Not tested</option><option value="passed">Passed manually</option><option value="failed">Failed / needs work</option></select></li>
          <li data-v150-check="provider"><label for="qf-v150-provider">Authorized portfolio and quotes</label><select id="qf-v150-provider"><option value="not-tested">Not tested</option><option value="passed">Passed manually</option><option value="failed">Failed / needs work</option></select></li>
          <li data-v150-check="research"><label for="qf-v150-research">Selection, prices and full research</label><select id="qf-v150-research"><option value="not-tested">Not tested</option><option value="passed">Passed manually</option><option value="failed">Failed / needs work</option></select></li>
          <li data-v150-check="sec"><label for="qf-v150-sec">SEC fundamentals; optional historical archive</label><select id="qf-v150-sec"><option value="not-tested">Not tested</option><option value="passed">Passed manually</option><option value="failed">Failed / needs work</option></select></li>
          <li data-v150-check="briefing"><label for="qf-v150-briefing">Hub / Lab / Briefing agreement</label><select id="qf-v150-briefing"><option value="not-tested">Not tested</option><option value="passed">Passed manually</option><option value="failed">Failed / needs work</option></select></li>
          <li data-v150-check="archive"><label for="qf-v150-archive">Saved-note persistence and sign-out</label><select id="qf-v150-archive"><option value="not-tested">Not tested</option><option value="passed">Passed manually</option><option value="failed">Failed / needs work</option></select></li>
        </ol>
        <p class="tiny" id="qf-v150-status" role="status" aria-live="polite">Manual verification not recorded.</p>
        <div class="controls"><button class="btn sm" id="qf-v150-download" type="button" disabled>Export redacted acceptance JSON</button><button class="btn sm" id="qf-v150-reset" type="button">Reset results</button></div>
      </div></details>
    </section>
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
      <div class="qf-v93-lab-status" id="qf-v93-lab-status" aria-live="polite"><strong>Connected research methods</strong><p class="tiny">Run an assessment in Research Hub to see which specialist methods were completed, unavailable, or failed for the chosen investments.</p></div>
      <div id="qf-v94-lab-insight" class="tiny" aria-live="polite"></div>
      <div id="qf-v96-lab-insight" class="tiny" aria-live="polite"></div>
      <div id="qf-v97-lab-insight" class="tiny" aria-live="polite"></div>
      <div id="qf-v98-lab-insight" class="tiny" aria-live="polite"></div>
      <div id="qf-v99-lab-insight" class="tiny" aria-live="polite"></div>
      <div id="qf-v100-lab-insight" class="tiny" aria-live="polite"></div>
      <div id="qf-v110-lab-insight" class="tiny" aria-live="polite"></div>
      <div id="qf-v120-lab-insight" class="tiny" aria-live="polite"></div>
      <div id="qf-v130-lab-insight" class="tiny" aria-live="polite"></div>
      <p id="qf-v140-lab-insight" class="tiny" aria-live="polite"></p>
      <div class="controls qf-v93-lab-tools"><button type="button" class="btn" data-private-tab="decision">Return to Decision Center</button><button type="button" class="btn" data-private-tab="settings">View research briefing</button></div>
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
      <div class="qf-private-start"><h2>Portfolio overview</h2><p class="qf-private-section-intro">Check your virtual holdings, then choose a research task. Detailed calculators and the plain-English guide live in their own sections.</p><div class="qf-private-paths"><button type="button" data-private-tab="ideas"><strong>Find investments</strong><small>Compare selected stocks and funds</small></button><button type="button" data-private-tab="research"><strong>Analyze market history</strong><small>Load prices for risk and strategy testing</small></button><button type="button" data-private-tab="decision"><strong>Run investment research</strong><small>Automated assessment and research brief</small></button><button type="button" data-private-tab="settings"><strong>Open research briefing</strong><small>Connected evidence, risks and methods</small></button></div></div>
      <p class="qf-private-nav-note">All holdings and transactions in this workspace are virtual. Prices are dated observations, not guarantees.</p>
      <div class="pane"><div class="three"><div class="metric"><span class="muted">Virtual portfolio value</span><strong id="private-total">—</strong></div><div class="metric"><span class="muted">Available cash</span><strong id="private-cash">—</strong></div><div class="metric"><span class="muted">Invested value</span><strong id="private-invested">—</strong></div></div><div class="section-title"><h3>Holdings</h3><button class="btn sm" data-private-tab="trade">Trade</button></div><div id="private-positions"></div></div>
      <div class="pane"><h3>Holdings by weight</h3><div id="private-concentration" class="tiny" style="margin-top:12px">Add virtual holdings to see allocation.</div></div>
    </section>
    <section class="private-view" data-private-view="decision">
      <div class="pane qf-v9-shell qf-v92-workspace" id="private-decision-os-v90">
        <span class="eyebrow">PRIVATE INVESTMENT RESEARCH</span><h2>Research your investments</h2>
        <p class="qf-v160-intro">Choose companies once. QuantForge loads available financial and market evidence, runs the eligible research models, and explains what the results mean.</p>
        <div class="qf-v170-start"><h3>Choose 2–5 investments</h3><p>Choose by company name. Every selected company will receive an individual assessment in one comparison.</p>
          <div id="qf-v170-selected" class="qf-v170-chips" role="status">No companies selected.</div>
          <button type="button" class="btn" id="qf-v170-browse">Choose companies</button></div>

        <details id="qf-v160-setup" class="qf-v160-setup"><summary>Optional: change research assumptions</summary>
        <div class="qf-v92-setup">
          <section class="qf-v92-step" aria-labelledby="qf-v92-step-one"><div class="qf-v92-stephead"><span aria-hidden="true">01</span><h3 id="qf-v92-step-one">Select investments</h3></div>
            <p class="tiny">The primary candidate below is used for the detailed legacy technical trace; all selected companies are assessed on the results screen.</p>
            <div class="field"><label for="private-v90-candidate">Company to evaluate in depth</label><select id="private-v90-candidate"><option value="">Choose an investment from your selection</option></select></div>
            <button type="button" class="btn" id="private-v90-browse">Browse companies by name</button>
            <p class="tiny" id="private-v90-selection" aria-live="polite">Choose 2–5 investments; historical comparisons require more than one security.</p>
          </section>
          <section class="qf-v92-step" aria-labelledby="qf-v92-step-two"><div class="qf-v92-stephead"><span aria-hidden="true">02</span><h3 id="qf-v92-step-two">Set your research constraints</h3></div>
            <p class="tiny">These are transparent screening assumptions, not predicted returns or individualized suitability advice.</p>
            <div class="qf-v9-fields">
              <div class="field"><label for="private-v90-risk">Risk approach</label><select id="private-v90-risk"><option value="conservative">Conservative</option><option selected value="balanced">Balanced</option><option value="growth">Growth-oriented</option></select></div>
              <div class="field"><label for="private-v90-horizon">Investment horizon</label><select id="private-v90-horizon"><option value="short">Under 1 year</option><option selected value="medium">1–5 years</option><option value="long">5+ years</option></select></div>
              <div class="field"><label for="private-v90-maxweight">Single-name portfolio ceiling</label><select id="private-v90-maxweight"><option value="0.10">10%</option><option selected value="0.20">20%</option><option value="0.35">35%</option></select></div>
              <div class="field"><label for="private-v90-maxdrawdown">Historical drawdown screen</label><select id="private-v90-maxdrawdown"><option value="0.15">15%</option><option selected value="0.25">25%</option><option value="0.40">40%</option></select></div>
              <div class="field"><label for="private-v90-days">Research history</label><select id="private-v90-days"><option value="180">6 months</option><option selected value="365">1 year</option><option value="730">2 years</option></select></div>
            </div>
          </section>
        </div>
        </details>
        <div class="qf-v92-runbar qf-v170-runbar"><div><strong>Ready to see your results?</strong><p class="tiny">One action loads available dated data and runs eligible company and portfolio models. No upload or trade required.</p></div><button type="button" class="btn primary" id="private-v90-run">Run complete research</button></div><p class="tiny" id="qf-v170-progress" role="status" aria-live="polite">Select companies, then run the research.</p>
        <div id="qf-v160-decision-center" class="qf-v160-center" aria-label="Unified evidence-based investment dashboard" aria-live="polite"><p class="tiny">Choose your investments and run the complete assessment. The dashboard will compile the eligible research automatically.</p></div>
        <details id="qf-v160-method-trace" class="qf-v160-method-trace"><summary>Open the original detailed assessment and statistical method trace</summary><div id="private-v90-report" aria-live="polite" role="status"><p class="tiny">Run your assessment to view individual model evidence, assumptions and calculations.</p></div></details>
        <div id="qf-v94-intelligence-hub" class="qf-v94-intelligence" aria-live="polite"></div>
      <div id="qf-v95-hub" class="qf-v95-host" aria-live="polite"></div>
      <div id="qf-v96-hub" class="qf-v95-host" aria-live="polite"></div>
      <div id="qf-v97-hub" class="qf-v95-host" aria-live="polite"></div>
      <div id="qf-v98-hub" class="qf-v95-host" aria-live="polite"></div>
      <section class="qf-v95-shell qf-v99-import" aria-label="Import historical SEC filing evidence">
        <span class="eyebrow">ADVANCED ONLY · LOCAL FILING REVISION ARCHIVE</span><h3>Optional deep historical filing audit</h3>
        <p>This is an expert-only research extension. The regular Decision Center uses built-in SEC data and requires no file uploads. For original-versus-later filing reconstruction, local archival evidence must be explicitly opened in this browser; the public website cannot read files from your PC automatically.</p>
        <div class="controls"><label for="qf-v99-file">Local SEC archive JSON</label><input type="file" id="qf-v99-file" accept=".json,application/json" disabled><button type="button" class="btn sm" id="qf-v99-clear">Clear imported archive</button></div>
        <p id="qf-v99-import-status" class="tiny" aria-live="polite">Sign in with MFA before importing local filing history.</p>
        <div id="qf-v99-hub-result" aria-live="polite"></div>
        <div id="qf-v100-hub-result" aria-live="polite"></div>
        <div id="qf-v130-hub-result" class="qf-v130-slot" aria-live="polite"></div><div id="qf-v120-hub-result" class="qf-v120-slot"></div><div id="qf-v110-hub-result" aria-live="polite"></div>
      </section>
      </div>
      <div id="qf-v93-legacy-compat" hidden aria-hidden="true">
      <div class="pane" id="private-decision-center-v84">
        <span class="eyebrow">PRIVATE RESEARCH · INTEGRATED ASSESSMENT</span>
        <h2 style="margin:9px 0">Investment Decision Center</h2>
        <p class="qf-private-section-intro">Bring together the analyses already run in this session. See the covered investments, what the models agree or disagree about, which evidence is missing, and the next calculation to perform. Nothing here moves money or changes your virtual portfolio.</p>
        <div class="controls"><button class="btn primary" type="button" id="private-decision-run-v84">Assess current evidence</button><span class="tiny">Generated on demand · MFA-protected</span></div>
        <div id="private-decision-result-v84" aria-live="polite" style="margin-top:15px"><p class="tiny">Choose Assess current evidence to review your completed analyses.</p></div>
      </div></div>
    </section>
    <section class="private-view" data-private-view="candidate" hidden>
      <div class="pane"><span class="eyebrow">RESEARCH METHODS · SINGLE COMPANY</span><h2>Company &amp; Factor Research</h2>
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
            <span class="eyebrow">INDEPENDENT RESEARCH FACTORS</span>
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
      <h2>Research Briefing &amp; Notes</h2><p class="qf-private-section-intro">The briefing uses the latest completed Decision Center assessment and the exact same research methods and sources. Nothing is recalculated or submitted to a brokerage when you open it.</p>
      <section class="pane qf-v93-brief-intro" aria-label="Connected research report"><div class="qf-v93-row"><div><span class="eyebrow">CONNECTED WORKFLOW</span><h3>Investment research briefing</h3><p class="tiny" id="qf-v93-brief-status">No current linked assessment. Run an automated assessment first.</p></div><button class="btn" type="button" data-private-tab="decision">Return to Decision Center</button></div>
      <p id="qf-v140-brief-insight" class="tiny" aria-live="polite"></p>
      <div id="qf-v93-briefing" aria-live="polite"><p class="tiny">Once an assessment is complete, the executive findings, conflicts, data coverage, method record, and next research actions will be available here.</p></div>
      <div id="qf-v94-intelligence-brief" class="qf-v94-intelligence" aria-live="polite"></div>
      <div id="qf-v95-brief" class="qf-v95-host" aria-live="polite"></div>
      <div id="qf-v96-brief" class="qf-v95-host" aria-live="polite"></div>
      <div id="qf-v97-brief" class="qf-v95-host" aria-live="polite"></div>
      <div id="qf-v98-brief" class="qf-v95-host" aria-live="polite"></div>
      <div id="qf-v99-brief" class="qf-v95-host" aria-live="polite"></div>
      <div id="qf-v100-brief" class="qf-v95-host" aria-live="polite"></div>
      <div id="qf-v130-brief" class="qf-v130-slot" aria-live="polite"></div><div id="qf-v120-brief" class="qf-v120-slot"></div><div id="qf-v110-brief" class="qf-v95-host" aria-live="polite"></div>
      <div class="pane" id="qf-v95-journal"><div class="section-title"><h3>Session research history</h3><button type="button" class="btn sm" id="qf-v95-journal-clear">Clear session list</button></div>
        <p class="tiny">Last eight completed assessment summaries in this authenticated browser session. No account values, holdings, or raw market prices are saved. This list is not a cloud archive and resets on refresh or logout.</p><div id="qf-v95-session-history" aria-live="polite"></div></div>
      <div class="pane qf-v96-saved" id="qf-v96-archive"><div class="section-title"><h3>Saved research archive</h3><button type="button" class="btn primary" id="qf-v96-save" disabled>Save current assessment</button></div><p class="tiny">Saved explicitly to existing MFA-protected private notes; persists across browser sessions. Stores a short conclusion and method count only—not holdings, account balances, market prices, or a full report. Deletion is permanent.</p><p class="tiny" id="qf-v96-archive-status">Owner-only archive</p><div id="qf-v96-saved-list" aria-live="polite"></div></div>
      <div class="controls"><button class="btn primary" type="button" id="qf-v93-brief-refresh" disabled>Refresh linked briefing</button><button class="btn" type="button" id="qf-v93-brief-export" disabled>Export evidence briefing (JSON)</button></div></section>
      <div class="pane" id="private-guide-card-v79">
        <div class="section-title"><h3>Optional session overview</h3><span class="mini">Private · educational decision support</span></div>
        <p class="tiny">For an overview of available work that has not yet been included in an automated Decision Center assessment, use this secondary session summary. It is separate from the linked briefing and cannot issue a candidate recommendation.</p>
        <div class="formgrid" style="margin-top:12px">
          <div class="field"><label for="private-guide-horizon-v79">When could you need this money?</label><select id="private-guide-horizon-v79"><option value="unknown">Not sure yet</option><option value="short">Within 3 years</option><option value="medium">3–10 years</option><option value="long">More than 10 years</option></select></div>
          <div class="field"><label for="private-guide-comfort-v79">How would a large temporary loss affect you?</label><select id="private-guide-comfort-v79"><option value="unknown">Not sure yet</option><option value="low">I could not comfortably absorb it</option><option value="medium">I could tolerate some loss</option><option value="high">I understand substantial losses are possible</option></select></div>
        </div>
        <div class="controls"><button class="btn primary" id="private-guide-run-v79" type="button">Summarize available session analyses</button><button class="btn" id="private-guide-export-v79" type="button" disabled>Export private report (JSON)</button></div>
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
public_disclosure="""<section class="qf-v150-data-scope" aria-labelledby="qf-v150-data-scope-title">
 <div class="section-title"><h2 id="qf-v150-data-scope-title">Research scope and evidence</h2><span class="mini">Observed · modeled · private</span></div>
 <div class="qf-v150-scope-grid">
  <div><strong>SEC-reported fundamentals</strong><p>Historical annual company facts from SEC EDGAR. Filing dates, fiscal periods and missing values are retained for source-aware comparisons.</p></div>
  <div><strong>Illustrative quantitative models</strong><p>Public portfolio returns, scenario forecasts, Monte Carlo paths and company-similarity features are modeled examples, not live market observations.</p></div>
  <div><strong>Owner-only research</strong><p>Authenticated historical prices and virtual holdings support deeper private analysis. The local multi-year SEC revision archive is not part of this public site.</p></div>
 </div>
 <p class="tiny">Historical strategy comparisons describe selected past periods, may exclude delisted issuers and distributions, and do not establish predictive investment performance.</p>
 </section>"""
html=html.replace('<div class="qf-evidence-shortcut">',public_disclosure+'<div class="qf-evidence-shortcut">',1)

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

/* Consolidated private navigation and decision-center emphasis. */
#private-signed>.private-nav{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;align-items:start;margin:15px 0 14px}
#private-signed>.private-nav>.private-nav-group{min-width:0;width:auto;border:1px solid #d5e4de;border-radius:11px;background:#fbfdfb;padding:9px 11px}
#private-signed .private-nav-title{cursor:pointer;font-weight:740;font-size:12px;line-height:1.5}
#private-signed .private-nav-actions{display:grid;gap:4px;margin-top:8px}
#private-signed .private-nav-actions button{width:100%;text-align:left;min-height:34px;border-radius:7px}
#private-signed .qf-v160-center{margin-top:16px}
#private-signed .qf-v160-gray{background:#edf1f2;color:#43535c;border-color:#cfd7db}
#private-signed .qf-v160-signal .qf-v160-light{white-space:normal;text-align:center}
#private-signed .qf-v160-hero p{max-width:70ch}
#private-signed .qf-v140-launch{margin-top:13px}
@media(max-width:1080px){#private-signed>.private-nav{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:580px){#private-signed>.private-nav{grid-template-columns:1fr}}

#private-signed .private-nav .private-nav-group button{white-space:normal}
@media(min-width:1220px){#private-signed>.private-nav{display:flex;flex-direction:column}#private-signed>.private-nav>.private-nav-group{width:100%}}
@media(max-width:1200px){#private-signed .private-nav{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:700px){#private-signed .private-nav{grid-template-columns:1fr 1fr}#private-signed .qf-v9-fields,#private-signed .qf-v9-grid,#private-signed .qf-v9-lab-grid{grid-template-columns:1fr}}
@media(max-width:450px){#private-signed .private-nav{grid-template-columns:1fr}}

/* V9.2 private Decision Center: clear visual hierarchy and responsive readable comparison. */
#private-signed .qf-v92-workspace{max-width:1200px;margin-inline:auto}
#private-signed .qf-v92-setup{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.4fr);gap:15px;margin-top:20px}
#private-signed .qf-v92-step{border:1px solid #d6e3df;border-radius:13px;background:#fbfdfc;padding:18px;min-width:0}
#private-signed .qf-v92-stephead{display:flex;align-items:center;gap:12px;margin-bottom:8px}
#private-signed .qf-v92-stephead span{background:#164f46;color:white;border-radius:9px;min-width:36px;height:36px;display:grid;place-items:center;font-weight:700}
#private-signed .qf-v92-stephead h3{font-size:17px;margin:0;color:#193d36}
#private-signed .qf-v92-step>.field{margin:15px 0}
#private-signed .qf-v92-step .qf-v9-fields{grid-template-columns:repeat(2,minmax(0,1fr));margin:12px 0 0;gap:11px}
#private-signed .qf-v92-step .qf-v9-fields label{font-size:12px}
#private-signed .qf-v92-runbar{display:flex;align-items:center;justify-content:space-between;gap:15px;padding:17px 19px;margin:14px 0;border-radius:12px;background:#eaf3ef;border:1px solid #b9d4c8}
#private-signed .qf-v92-runbar p{margin:5px 0 0}
#private-signed .qf-v92-report{margin-top:21px}
#private-signed .qf-v92-hero{background:#f3f8f6;border:1px solid #bed8ce;border-left:5px solid #145b4c;border-radius:13px;padding:21px 24px}
#private-signed .qf-v92-hero h3{font-size:clamp(19px,2.1vw,27px);margin:14px 0 9px;line-height:1.25;color:#143b32}
#private-signed .qf-v92-hero p{max-width:850px;line-height:1.65}
#private-signed .qf-v92-row{display:flex;align-items:center;justify-content:space-between;gap:9px;flex-wrap:wrap}
#private-signed .qf-v92-readiness{display:inline-block;border:1px solid #b4ccc3;background:white;border-radius:50px;padding:5px 10px;font-size:11px;font-weight:650;color:#234f43}
#private-signed .qf-v92-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:14px 0 21px}
#private-signed .qf-v92-metrics>div{background:white;border:1px solid #d4e3dd;border-radius:11px;padding:14px;display:flex;flex-direction:column;gap:5px;min-width:0}
#private-signed .qf-v92-metrics strong{font-size:24px;color:#153f36;font-variant-numeric:tabular-nums}
#private-signed .qf-v92-metrics span{font-size:11px;color:#526a60;line-height:1.5}
#private-signed .qf-v92-twin{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px;margin:0 0 23px}
#private-signed .qf-v92-panel{background:white;border:1px solid #d5e4de;border-radius:12px;padding:17px}
#private-signed .qf-v92-panel h4,#private-signed .qf-v92-heading h4{margin:0;color:#183e33;font-size:17px}
#private-signed .qf-v92-panel .qf-v92-list{margin:12px 0 0}
#private-signed .qf-v92-list{padding-left:18px;font-size:13px;line-height:1.7}
#private-signed .qf-v92-list li+li{margin-top:7px}
#private-signed .qf-v92-core>section{margin-top:20px}
#private-signed .qf-v92-heading{display:flex;align-items:baseline;justify-content:space-between;gap:15px;flex-wrap:wrap;margin-bottom:11px}
#private-signed .qf-v92-evidence-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
#private-signed .qf-v92-evidence{border:1px solid #d5e4de;background:#fff;border-radius:11px;padding:14px;min-width:0}
#private-signed .qf-v92-evidence p{font-size:12px;line-height:1.6;color:#3a564c;margin:10px 0}
#private-signed .qf-v92-evidence strong{font-size:13px}
#private-signed .qf-v92-tag{font-size:10px;border-radius:30px;padding:4px 7px;background:#eff3f1;color:#3b5049;border:1px solid #d5e2dc;white-space:nowrap}
#private-signed .qf-v92-state-supports,#private-signed .qf-v92-state-available{background:#e7f5ee;color:#225b41;border-color:#c4dfcd}
#private-signed .qf-v92-state-cautions{background:#fff3e3;color:#8a4a14;border-color:#eed4a7}
#private-signed .qf-v92-table{width:100%;font-size:12px;table-layout:auto}
#private-signed .qf-v92-table caption{text-align:left;font-size:11px;color:#4b675a;margin:0 0 8px}
#private-signed .qf-v92-table th,#private-signed .qf-v92-table td{vertical-align:middle}
#private-signed .qf-v92-bar{display:inline-block;width:90px;max-width:48%;height:9px;background:#e7eae8;border-radius:10px;overflow:hidden;vertical-align:middle;margin-right:8px}
#private-signed .qf-v92-bar>span{display:block;height:100%;background:#ad7c41;border-radius:10px}
#private-signed .qf-v92-barvalue{font-variant-numeric:tabular-nums;white-space:nowrap}
#private-signed .qf-v92-more{border:1px solid #d5e4de;border-radius:11px;margin-top:10px;padding:13px 17px;background:#fff}
#private-signed .qf-v92-more summary{cursor:pointer;font-weight:650;color:#235a49}
#private-signed .qf-v92-more[open] summary{margin-bottom:12px}
#private-signed .qf-v92-actions{margin-top:20px}
@media(max-width:900px){#private-signed .qf-v92-setup{grid-template-columns:1fr}}
@media(max-width:650px){#private-signed .qf-v92-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}#private-signed .qf-v92-twin,#private-signed .qf-v92-evidence-grid{grid-template-columns:1fr}#private-signed .qf-v92-runbar{flex-direction:column;align-items:stretch}}
@media(max-width:430px){#private-signed .qf-v92-step .qf-v9-fields{grid-template-columns:1fr}}

/* V9.3 connected private research hub, reusable briefing and small-screen navigation */
#private-signed #qf-v93-legacy-compat[hidden]{display:none!important}
#private-signed .qf-v93-ribbon{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;margin:12px 0 18px;padding:14px 17px;background:#eff6f2;border:1px solid #c9ded4;border-radius:12px}
#private-signed .qf-v93-ribbon-copy{display:flex;flex-direction:column;gap:4px;min-width:0;flex:1}
#private-signed .qf-v93-ribbon-copy strong{color:#16463b;font-size:13px}
#private-signed .qf-v93-ribbon .controls{margin:0}
#private-signed .qf-v93-lab-status{margin:16px 0;padding:16px;border:1px solid #c9ded4;background:#f6faf8;border-radius:12px}
#private-signed .qf-v93-lab-status p{margin:7px 0 0}
#private-signed .qf-v93-lab-tags{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px;margin-top:12px}
#private-signed .qf-v93-lab-tag{background:white;border:1px solid #d3e4db;border-radius:9px;padding:10px;display:flex;flex-direction:column;gap:5px;font-size:12px}
#private-signed .qf-v93-lab-tag small{color:#517064;line-height:1.4}
#private-signed .qf-v93-brief-intro{max-width:1200px;margin-inline:auto;border-color:#cbded4}
#private-signed .qf-v93-row{display:flex;align-items:start;justify-content:space-between;gap:14px;flex-wrap:wrap}
#private-signed .qf-v93-report-top{border:1px solid #cfdfd6;border-radius:13px;background:#f5faf7;padding:21px;margin:16px 0}
#private-signed .qf-v93-report-top h4{font-size:23px;margin:7px 0;color:#16493c}
#private-signed .qf-v93-report-top p{line-height:1.65}
#private-signed .qf-v93-brief-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:16px 0}
#private-signed .qf-v93-brief-section{border:1px solid #d6e5dd;background:white;border-radius:12px;padding:17px;min-width:0}
#private-signed .qf-v93-brief-section h4{margin:0 0 8px;font-size:16px;color:#1a4d40}
#private-signed .qf-v93-brief-section ul{margin:8px 0;padding-left:17px;line-height:1.6;font-size:13px}
#private-signed .qf-v93-method{padding:9px 0;border-bottom:1px solid #edf2ef;line-height:1.5;font-size:12px}
#private-signed .qf-v93-method:last-child{border-bottom:0}
#private-signed .qf-v93-method small{display:block;margin-top:4px;color:#526a5f}
#private-signed .qf-v93-actions{margin:14px 0;display:flex;flex-wrap:wrap;gap:8px}
#private-signed .qf-v93-related{margin:15px 0;border:1px solid #ccddd4;border-radius:12px;padding:14px;background:#fbfdfc}
#private-signed .qf-v93-related p{font-size:12px;color:#416253}
#private-signed .qf-v93-related .controls{margin:7px 0 0}
@media(max-width:750px){#private-signed .qf-v93-brief-grid{grid-template-columns:1fr}#private-signed .qf-v93-ribbon{align-items:stretch}#private-signed .qf-v93-ribbon .controls{flex-wrap:wrap}}
/* V9.8: evidence-quality audit complements the V9.7 historic replay. */
#private-signed .qf-v98-shell{border-left:4px solid #53786d}
#private-signed .qf-v98-shell .table-wrap{overflow-x:auto;margin:13px 0}
#private-signed .qf-v98-shell .qf-v95-table td{max-width:270px;overflow-wrap:anywhere}
#private-signed .qf-v99-import{margin-top:20px;border-left:4px solid #567e92}
#private-signed .qf-v99-import input[type=file]{max-width:100%;min-width:200px}
#private-signed .qf-v99-shell .table-wrap{overflow-x:auto}
#private-signed .qf-v99-shell td{max-width:260px;overflow-wrap:anywhere}

/* V13.0: integrated research integrity console, legible on narrow screens. */
#private-signed .qf-v130-console{border-left:4px solid #315f79;background:#f8fbfc;margin:16px 0}
#private-signed .qf-v130-gates{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin:14px 0}
#private-signed .qf-v130-gate{border:1px solid #cbdde4;border-radius:10px;background:white;padding:12px;min-width:0}
#private-signed .qf-v130-gate strong{display:block;color:#244b60;font-size:13px;overflow-wrap:anywhere}
#private-signed .qf-v130-state{display:inline-block;border:1px solid #bacbd4;border-radius:12px;padding:2px 8px;margin:6px 0;color:#344d5c;font-size:11px}
#private-signed .qf-v130-gate p{font-size:12px;line-height:1.5;margin:5px 0;color:#485b67}
#private-signed .qf-v130-console details{margin-top:12px}
#private-signed .qf-v130-console details summary{cursor:pointer;font-weight:650}
#private-signed .qf-v110-panel{margin-top:16px;border-left:4px solid #205e76;background:#fbfdfe}
#private-signed .qf-v110-panel .table-wrap{overflow-x:auto;margin:12px 0}
#private-signed .qf-v110-panel p{font-size:12px;line-height:1.6}
#private-signed .qf-v110-panel th{white-space:normal}
/* V9.4 cross-security evidence and policy stability; same shared research run */
#private-signed .qf-v95-host{max-width:1200px;margin:20px auto}
#private-signed .qf-v95-shell{border:1px solid #ccdcd6;background:#f7faf8;border-radius:14px;padding:18px}
#private-signed .qf-v95-heading h3{margin:7px 0;font-size:20px;color:#174f43}
#private-signed .qf-v95-heading p{font-size:12px;line-height:1.55;color:#486458}
#private-signed .qf-v95-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:15px}
#private-signed .qf-v95-panel{min-width:0;background:#fff;border:1px solid #d5e3dc;border-radius:12px;padding:16px}
#private-signed .qf-v95-panel h4{font-size:15px;color:#174f43;margin:0 0 12px}
#private-signed .qf-v95-panel p{font-size:12px;line-height:1.65;color:#435c50}
#private-signed .qf-v95-table{width:100%;font-size:11px;white-space:normal}
#private-signed .qf-v95-table th,#private-signed .qf-v95-table td{padding:7px;vertical-align:top;font-variant-numeric:tabular-nums}
#private-signed .qf-v95-journal-row{padding:9px 6px;border-bottom:1px solid #dbe6e0;font-size:12px}
@media(max-width:850px){#private-signed .qf-v95-grid{grid-template-columns:1fr}}
#private-signed .qf-v94-intelligence{max-width:1200px;margin:18px auto}
#private-signed .qf-v94-head{display:flex;justify-content:space-between;align-items:start;flex-wrap:wrap;gap:12px;margin-bottom:12px}
#private-signed .qf-v94-head h3{font-size:21px;margin:4px 0 5px;color:#16463b}
#private-signed .qf-v94-head p{font-size:12px;max-width:780px;line-height:1.6;color:#476254;margin:3px 0}
#private-signed .qf-v94-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:12px 0}
#private-signed .qf-v94-card{background:white;border:1px solid #d0dfd7;padding:18px;border-radius:12px;min-width:0}
#private-signed .qf-v94-card h4{color:#174c3e;font-size:16px;margin:0 0 8px}
#private-signed .qf-v94-card p{font-size:12px;line-height:1.65;color:#475d52}
#private-signed .qf-v94-table{width:100%;font-size:12px;white-space:normal}
#private-signed .qf-v94-table td,#private-signed .qf-v94-table th{padding:9px;vertical-align:top}
#private-signed .qf-v94-table td{font-variant-numeric:tabular-nums}
#private-signed .qf-v94-table td:first-child{font-weight:600}
#private-signed .qf-v94-neutral{color:#6b6658;font-size:12px}
@media(max-width:780px){#private-signed .qf-v94-grid{grid-template-columns:1fr}}

"""
qfv9_css += """
/* V14.0: one guided workflow; detailed secondary research stays accessible on demand. */
#private-signed .qf-v140-launch{max-width:1200px;margin:12px auto 20px;padding:17px 19px;border:1px solid #bfdbd3;background:#f7fbf9;border-radius:13px}
#private-signed .qf-v140-launch[hidden]{display:none!important}
#private-signed .qf-v140-top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
#private-signed .qf-v140-top h3{margin:5px 0 8px;color:#174e41;font-size:18px}
#private-signed .qf-v140-progress{font-weight:650;white-space:nowrap;color:#2a6555;font-size:13px}
#private-signed .qf-v140-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin:12px 0}
#private-signed .qf-v140-step{border:1px solid #d5e5df;background:#fff;border-radius:9px;padding:10px;display:flex;flex-direction:column;gap:4px;min-width:0}
#private-signed .qf-v140-step strong{font-size:12px;line-height:1.4;color:#194d40}
#private-signed .qf-v140-step>span:first-child{font-size:17px;color:#21604c}
#private-signed .qf-v140-acceptance{margin-top:15px;border-top:1px solid #d7e5df;padding-top:11px}
#private-signed .qf-v140-acceptance summary{cursor:pointer;font-weight:600;color:#235b4b;font-size:13px}
#private-signed .qf-v140-acceptance li{margin-bottom:7px}
#private-signed .qf-v140-details{margin:20px 0;border:1px solid #cbdcd3;border-radius:12px;padding:13px 17px;background:#fafcfb}
#private-signed .qf-v140-details summary{cursor:pointer;color:#215444;font-weight:650;line-height:1.6}
#private-signed .qf-v140-details[open] summary{margin-bottom:12px}
#private-signed .qf-v140-details .qf-v95-host{max-width:none}
#private-signed #qf-v140-lab-insight,#private-signed #qf-v140-brief-insight{border-left:3px solid #437b68;padding:7px 12px;background:#f5faf7;margin:12px 0}
@media(max-width:550px){#private-signed .qf-v140-steps{grid-template-columns:1fr}#private-signed .qf-v140-launch{padding:13px}}
"""
html=html.replace('</style>',qfv9_css+'\n/* V15.0: clear research provenance and legible manual release acceptance */\n.qf-v150-data-scope{margin:14px 0 24px;padding:20px;border:1px solid var(--line);background:#f9fcfa;border-radius:13px}\n.qf-v150-data-scope h2{font-size:21px;margin:0}\n.qf-v150-scope-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px;margin:15px 0}\n.qf-v150-scope-grid>div{background:white;border:1px solid #d0e2d8;border-radius:9px;padding:15px;min-width:0}\n.qf-v150-scope-grid strong{font-size:13px;color:#204e40}\n.qf-v150-scope-grid p{font-size:12px;color:#52695f;line-height:1.55;margin:8px 0 0}\n#private-signed .qf-v150-acceptance{margin-top:15px;padding:12px;border:1px solid #d0e2d8;border-radius:10px;background:#fff}\n#private-signed .qf-v150-acceptance h4{margin:0 0 8px;font-size:15px}\n#private-signed .qf-v150-manual-grid{margin:11px 0;padding-left:22px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}\n#private-signed .qf-v150-manual-grid li{font-size:12px;min-width:0;padding-right:6px}\n#private-signed .qf-v150-manual-grid label{display:block;margin-bottom:5px;color:#315549}\n#private-signed .qf-v150-manual-grid select{width:100%;padding:8px;border:1px solid #bcd4c8;border-radius:7px;background:#fff;color:#264d40}\n@media(max-width:760px){.qf-v150-scope-grid,#private-signed .qf-v150-manual-grid{grid-template-columns:1fr}}\n'+'</style>',1)
html=html.replace('</style>','\n/* V16.0 private decision center: purely descriptive research visualizations. */\n#private-signed #qf-v93-research-ribbon{display:none}\n#private-signed .qf-v160-intro{font-size:14px;line-height:1.65;max-width:900px;color:#465d55}\n#private-signed .qf-v160-center{margin:20px 0 18px;min-width:0}\n#private-signed .qf-v160-hero{border:1px solid #c9dbd2;border-radius:16px;background:linear-gradient(120deg,#f7fbf9,#fff);padding:20px}\n#private-signed .qf-v160-title{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}\n#private-signed .qf-v160-title h3{font-size:23px;line-height:1.35;margin:4px 0;color:#173b34}\n#private-signed .qf-v160-title p{color:#49635a;font-size:12px;margin:4px 0}\n#private-signed .qf-v160-light{display:inline-flex;align-items:center;gap:7px;border-radius:22px;padding:6px 11px;font-size:12px;font-weight:700;border:1px solid #c5d5cd;background:#f3f6f4;color:#38584d}\n#private-signed .qf-v160-light::before{content:"";width:10px;height:10px;display:block;border-radius:50%;background:#909b95}\n#private-signed .qf-v160-green{background:#e8f7ee;color:#145735;border-color:#a9d7b8}\n#private-signed .qf-v160-green::before{background:#238449}\n#private-signed .qf-v160-amber{background:#fff6e4;color:#855b15;border-color:#e7c789}\n#private-signed .qf-v160-amber::before{background:#cb8d23}\n#private-signed .qf-v160-red{background:#fcebec;color:#8d333b;border-color:#e1acb0}\n#private-signed .qf-v160-red::before{background:#cf454b}\n#private-signed .qf-v160-topline{display:grid;grid-template-columns:minmax(160px,220px) 1fr;gap:18px;align-items:center;margin:18px 0}\n#private-signed .qf-v160-dial{--score:0;display:flex;flex-direction:column;align-items:center;justify-content:center;width:158px;height:158px;border-radius:50%;background:conic-gradient(#368a68 calc(var(--score) * 1%),#e5efea 0);position:relative;margin:auto}\n#private-signed .qf-v160-dial::before{content:"";position:absolute;inset:12px;background:#fff;border-radius:50%}\n#private-signed .qf-v160-dial span{z-index:1;font-size:33px;font-weight:700;color:#184c3d;font-variant-numeric:tabular-nums}\n#private-signed .qf-v160-dial small{z-index:1;font-size:10px;text-align:center;color:#456256;max-width:95px}\n#private-signed .qf-v160-action{border-left:4px solid #b3c9bf;padding:10px 14px;background:#fff;border-radius:8px}\n#private-signed .qf-v160-action strong{font-size:17px;display:block;color:#193f34;margin:4px 0}\n#private-signed .qf-v160-action p{font-size:13px;line-height:1.6;color:#425d52;margin:5px 0}\n#private-signed .qf-v160-meter{height:11px;border-radius:30px;background:#e9eee9;overflow:hidden;margin:8px 0}\n#private-signed .qf-v160-meter>span{display:block;height:100%;background:#3b8768;border-radius:30px}\n#private-signed .qf-v160-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:14px 0}\n#private-signed .qf-v160-signal{background:#fff;border:1px solid #d3e1d8;border-radius:12px;padding:13px 15px;min-width:0}\n#private-signed .qf-v160-signal strong{font-size:13px;color:#20463a;display:block;margin-bottom:7px}\n#private-signed .qf-v160-signal p{font-size:12px;line-height:1.5;margin:7px 0;color:#51645c;overflow-wrap:anywhere}\n#private-signed .qf-v160-signal small{font-size:11px;color:#61766b}\n#private-signed .qf-v160-compare{border:1px solid #d6e3dc;border-radius:12px;background:white;padding:15px;margin:12px 0}\n#private-signed .qf-v160-compare h4{font-size:15px;margin:0 0 10px;color:#254f40}\n#private-signed .qf-v160-compare-row{display:grid;grid-template-columns:minmax(95px,1fr) minmax(105px,2fr) 90px;align-items:center;gap:12px;padding:7px 0;font-size:12px;border-bottom:1px solid #f0f3f0}\n#private-signed .qf-v160-bar{height:10px;background:#e9eeeb;border-radius:9px;overflow:hidden}\n#private-signed .qf-v160-bar>span{height:100%;display:block;background:#708b7e;border-radius:9px}\n#private-signed .qf-v160-findings{display:grid;grid-template-columns:1fr 1fr;gap:14px}\n#private-signed .qf-v160-findings ul{padding-left:18px;margin:6px 0}\n#private-signed .qf-v160-findings li{font-size:12px;line-height:1.55;margin-bottom:7px}\n#private-signed .qf-v160-method-trace,#private-signed .qf-v160-setup{margin:12px 0;padding:14px 17px;border:1px solid #d4e2d9;border-radius:10px;background:#fafcfb}\n#private-signed .qf-v160-setup summary,#private-signed .qf-v160-method-trace summary{cursor:pointer;font-weight:700;color:#2b5748;font-size:13px}\n#private-signed .qf-v160-setup[open] summary,#private-signed .qf-v160-method-trace[open] summary{margin-bottom:13px}\n#private-signed .qf-v160-archive-details{border:1px solid #dae5dd;border-radius:12px;padding:12px 16px;margin:14px 0;background:#fafcfb}\n#private-signed .qf-v160-archive-details summary{font-weight:600;cursor:pointer;font-size:13px}\n#private-signed .qf-v160-archive-details .qf-v99-import{margin:14px 0}\n@media(max-width:780px){#private-signed .qf-v160-topline{grid-template-columns:1fr}#private-signed .qf-v160-grid,#private-signed .qf-v160-findings{grid-template-columns:1fr}#private-signed .qf-v160-hero{padding:14px}#private-signed .qf-v160-compare-row{gap:6px;grid-template-columns:100px 1fr 68px}}\n'+'</style>',1)
html=html.replace('</style>', """
/* Decision eligibility is the prominent visual status; alignment is deliberately neutral. */
#page-private:has(#private-signed:not([hidden]))>.pagehead{display:none}
#private-signed .qf-v160-topline{display:block}
#private-signed .qf-v160-action{padding:18px 19px;background:#fff;border-left:5px solid #b6c7bc}
#private-signed .qf-v160-decision-red{border-left-color:#b73e45;background:#fff9f9}
#private-signed .qf-v160-decision-amber{border-left-color:#c28b30;background:#fffdf7}
#private-signed .qf-v160-decision-gray{border-left-color:#93a6a0;background:#fafcfb}
#private-signed .qf-v160-decision-green{border-left-color:#237a55;background:#f7fcf9}
#private-signed .qf-v160-scoreline{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px;padding:12px 16px;margin:12px 0;border:1px solid #dbe6df;border-radius:9px;background:#f7f9f7;color:#37554b}
#private-signed .qf-v160-scoreline strong{font-size:14px}
#private-signed .qf-v160-scoreline span{font-size:12px}
#private-signed .qf-v160-blockers{padding:14px 17px;border:1px solid #dca5a7;border-radius:9px;background:#fff8f8;margin:13px 0;color:#812f38}
#private-signed .qf-v160-blockers ul{padding-left:19px;font-size:12px;margin:9px 0 0}
#private-signed .qf-v160-dial{display:none} /* Retired misleading green circle. */
#private-signed #qf-private-location{font-size:12px;color:#315b4b}
@media(max-width:780px){#private-signed #qf-private-location{order:3;flex-basis:100%}}
</style>""", 1)
html=html.replace('</style>', """
/* Simple private landing page; advanced methods remain accessible from a single link. */
#private-signed>.private-nav.qf-v170-nav{display:flex;flex-wrap:wrap;gap:8px;position:static;border:0;margin:12px 0 18px;padding:0;align-items:center}
#private-signed .qf-v170-nav button{font-size:14px;border:1px solid #d1e1d9;background:white;color:#2a5348;border-radius:10px;min-height:42px;padding:10px 18px}
#private-signed .qf-v170-nav button.active{background:#1d665a;color:white;border-color:#1d665a}
#private-signed .qf-v170-nav .qf-v170-advanced-link{margin-left:auto;background:transparent;border-color:transparent;text-decoration:underline}
#private-signed .qf-v170-nav .qf-v170-advanced-link.active{background:#1d665a;text-decoration:none}
#private-signed .qf-v170-start{border:1px solid #cbded5;background:#f8fbf9;border-radius:14px;padding:19px;margin:20px 0 14px}
#private-signed .qf-v170-start h3{font-size:19px;margin:0 0 6px}
#private-signed .qf-v170-start p{font-size:13px;color:#567367;margin:0 0 12px}
#private-signed .qf-v170-chips{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
#private-signed .qf-v170-chip{display:inline-block;background:#e1f0e8;color:#194d3c;border:1px solid #c6e3d5;border-radius:20px;padding:6px 12px;font-size:13px;font-weight:650}
#private-signed .qf-v170-chip small{font-weight:normal}
#private-signed .qf-v170-runbar{margin:13px 0 17px}
#private-signed .qf-v170-results{display:block;margin:0}
#private-signed .qf-v170-head h3{font-size:25px;line-height:1.3;margin:8px 0}
#private-signed .qf-v170-head p,#private-signed .qf-v170-overview p{font-size:14px;color:#476358;line-height:1.65}
#private-signed .qf-v170-overview{border-radius:12px;padding:19px;background:#eff7f3;border:1px solid #cae4d4;margin:18px 0}
#private-signed .qf-v170-overview strong{font-size:18px;color:#1a4b3c}
#private-signed .qf-v170-overview p{margin-top:6px}
#private-signed .qf-v170-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(265px,1fr));gap:13px}
#private-signed .qf-v170-company{border:1px solid #d4e1dc;border-left:5px solid #b7c6c0;background:white;border-radius:13px;padding:17px;min-width:0}
#private-signed .qf-v170-company.qf-v170-green{border-left-color:#268458}
#private-signed .qf-v170-company.qf-v170-amber{border-left-color:#c59a43}
#private-signed .qf-v170-company.qf-v170-red{border-left-color:#ce5b5c}
#private-signed .qf-v170-company-title{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:6px;margin-bottom:11px}
#private-signed .qf-v170-company h4{margin:0;font-size:17px;color:#193d33}
#private-signed .qf-v170-company h4 small{font-size:11px;color:#668075}
#private-signed .qf-v170-company p{font-size:13px;line-height:1.6;color:#465e54;margin:8px 0;overflow-wrap:anywhere}
#private-signed .qf-v170-company .qf-v170-verdict{font-size:14px;display:block}
#private-signed .qf-v170-pill{font-size:11px;border-radius:18px;padding:4px 9px;background:#ebf0ec;color:#4d655a}
#private-signed .qf-v170-pill.qf-v170-green{background:#e3f4e9;color:#1f6b42}
#private-signed .qf-v170-pill.qf-v170-red{background:#fae8e8;color:#94393c}
#private-signed .qf-v170-pill.qf-v170-amber{background:#fff2dd;color:#805b14}
#private-signed .qf-v170-chart{border:1px solid #d4e4dc;padding:20px;border-radius:13px;margin:17px 0}
#private-signed .qf-v170-chart h4{font-size:18px;margin:0 0 7px}
#private-signed .qf-v170-chart p{font-size:13px;color:#567266}
#private-signed .qf-v170-bar-row{display:grid;grid-template-columns:minmax(80px,1fr) minmax(85px,2fr) 50px;align-items:center;gap:10px;padding:10px 0;font-size:13px}
#private-signed .qf-v170-bar{height:13px;background:#eaf1ec;border-radius:9px;overflow:hidden}
#private-signed .qf-v170-bar>span{display:block;height:100%;background:#aa7861;border-radius:9px}
#private-signed .qf-v170-footer{font-size:12px;color:#61766c;margin-top:16px}
#private-signed .qf-v170-empty{padding:18px;border:1px solid #d8e5de;border-radius:11px;color:#51685f}
/* The primary screen must not repeat the old extensive technical panels. */
#private-signed [data-private-view=decision] #qf-v94-intelligence-hub,
#private-signed [data-private-view=decision] #qf-v95-hub,
#private-signed [data-private-view=decision] #qf-v96-hub,
#private-signed [data-private-view=decision] #qf-v97-hub,
#private-signed [data-private-view=decision] #qf-v98-hub,
#private-signed [data-private-view=decision] #qf-v160-method-trace{display:none!important}
@media(max-width:680px){#private-signed .qf-v170-nav .qf-v170-advanced-link{margin-left:0}#private-signed .qf-v170-company{padding:13px}#private-signed .qf-v170-bar-row{grid-template-columns:85px 1fr 45px}}
</style>""",1)
html=html.replace('.navtop{display:none}',  '#private-research-dataset[hidden],#private-signed[hidden],#private-login[hidden],#private-mfa[hidden],#private-mfa-qr-wrap[hidden],#private-mfa-setup-actions[hidden]{display:none!important}#private-message{margin-top:8px}.navtop{display:none}')
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
  text=(src/'site/private_ideas_v70.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_allocation_v74.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_value_v73.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_decision_v72.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_guide_v79.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_decision_center_v84.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_candidate_v85.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_factor_scenarios_v86.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_french_factors_v87.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_research_orchestrator_v91.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_research_os_v90.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_decision_review_v92.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_research_brief_v93.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_investment_intelligence_v94.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_portfolio_validation_v95.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_research_intelligence_v96.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_pit_validation_v97.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_sec_coverage_v98.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_archived_sec_v99.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_archive_quality_v100.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_historical_panel_v110.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_robustness_v120.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_historical_attribution_v130.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_decision_integrity_v130.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_workflow_v140.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_release_acceptance_v150.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_unified_decision_v160.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_simple_research_v170.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_optimizer.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_multimarket.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_forecast_v65.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_walkforward_v65.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_diagnostics_v66.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_integrity_v67.js').read_text(encoding='utf-8')+'\n'+(src/'site/private_robustness_v68.js').read_text(encoding='utf-8')+'\n'+text
 if file=='app.js':
  assert text.count('/* QF_SEC_DATA */ null')==1
  # Bundle pure SEC analytics in the existing public app script. CSP remains 3 hashes.
  analytics=(src/'site/sec_analytics.js').read_text(encoding='utf-8')+'\n'+(src/'site/sec_peer_model.js').read_text(encoding='utf-8')
  evidence=(src/'site/public_evidence_v76.js').read_text(encoding='utf-8')
  lab=(src/'site/public_lab_v77.js').read_text(encoding='utf-8')
  visuals=(src/'site/sec_visuals_v81.js').read_text(encoding='utf-8')
  text=analytics+'\n'+evidence+'\n'+lab+'\n'+visuals+'\n'+text.replace('/* QF_SEC_DATA */ null', snapshot_js)
 text=text.replace('</script','<\\/script')
 html=html.replace(slot,text)
(root/'public/index.html').write_text(html, encoding="utf-8", newline="\n")
scripts=re.findall(r'<script>(.*?)</script>',html,re.DOTALL)
assert len(scripts)==3
hashes=["'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in scripts]
csp="default-src 'none'; script-src "+' '.join(hashes)+"; style-src 'unsafe-inline'; connect-src 'self'; img-src data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
(root/'public/_headers').write_text("/*\n  Content-Security-Policy: "+csp+"\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n", encoding="utf-8", newline="\n")
print('Built',root/'public/index.html',len(html),'bytes',len(scripts),'protected scripts')
