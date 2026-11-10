/* Interview-readable evidence and accessible plots. No IO, storage or account data. */
(function (root) {
  'use strict';
  const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const finite = Number.isFinite;
  const percent = value => finite(value) ? (value * 100).toFixed(1) + '%' : 'Unavailable';
  const number = value => finite(value) ? value.toLocaleString('en-US', {maximumFractionDigits: 2}) : 'Unavailable';
  const catalog = [
    {id: 'data', name: 'Data engineering', question: 'Can a financial figure be traced back to a filing?',
      method: 'Validate SEC Company Facts by issuer, fiscal period, unit and accession. Preserve missing values and negative cash flow, then derive compatible annual ratios. The deterministic published snapshot is separate from an optional historical revision archive.',
      evaluation: 'Issuer/CIK checks, period and unit fixtures, missingness cases and deterministic snapshot validation. A current snapshot is not evidence that a restatement was known at an earlier decision date.',
      example: 'Inspect the selected company’s annual revenue and filing record below. This separates the period being measured from the date the information was filed.',
      files: ['tools/build_public_sec_snapshot.py', 'web/site/sec_analytics.js'], tests: ['tests/test_public_sec_snapshot.py', 'web/tests/sec_analytics.test.cjs'], route: 'explore', formula: null},
    {id: 'analysis', name: 'Analysis & communication', question: 'How do companies differ on comparable evidence?',
      method: 'Intersect actual observation dates before normalizing market series to 100. Keep SEC growth, margin and cash-flow comparisons separate from price returns. Show financial missingness and industry differences instead of assigning a best-stock score.',
      evaluation: 'Common-date alignment, unique 2–5-name baskets, CSV safety, missing-value handling and consistent accounting definitions. Synthetic public paths demonstrate the workflow; they cannot establish actual company price risk.',
      example: 'Explore provides source-backed findings; Compare adds normalized paths, financial contrasts, distributions, risk/return and correlations using the same basket.',
      files: ['web/site/research_app_v20.js', 'web/site/research_compare_portfolio_v21.js'], tests: ['web/tests/research_compare_portfolio_v21.test.cjs', 'tools/smoke_release_b_browser.py'], route: 'compare', formula: 'risk'},
    {id: 'ml', name: 'Statistical machine learning', question: 'Does a direction model improve on a simple base rate?',
      method: 'The L2-regularized logistic classifier uses past returns and volatility. Five-session labels must mature before entering training. Expanding historical frequency is the baseline; later, non-overlapping test windows supply accuracy, Brier score and calibration bins.',
      evaluation: 'Chronological feature/label tests, sample counts, held-out baseline comparisons and signal withholding. A lower Brier score measures squared probability error in this sample; it does not establish profitable trading or a future dollar price.',
      example: 'Models → Prediction → Evaluation shows actual test windows, class balance and calibration counts for the current inputs. Public results are experiments on explicitly synthetic prices.',
      files: ['web/site/private_predictive_ml_v180.js', 'web/site/research_models_methods_ui_v22.js'], tests: ['web/tests/private_predictive_ml_v180.test.cjs', 'tools/smoke_release_c_browser.py'], route: 'models', model: 'prediction', formula: 'prediction'},
    {id: 'statistics', name: 'Statistics & uncertainty', question: 'How stable are historical downside estimates?',
      method: 'Compute simple daily returns, sample volatility, running-peak drawdown and empirical one-session VaR/Expected Shortfall. Compare early and late samples; circular moving blocks resample nearby observations together for volatility sensitivity.',
      evaluation: 'Numerical return/tail fixtures, invalid histories, short samples and deterministic resampling. Blocks retain some local dependence but do not create a calibrated future loss bound or solve regime change.',
      example: 'Models → Risk plots every dated drawdown and rolling volatility. Evaluation reports the 300-resample historical sensitivity range only when at least 180 returns are available.',
      files: ['web/site/research_models_core_v22.js'], tests: ['web/tests/research_models_core_v22.test.cjs'], route: 'models', model: 'risk', formula: 'risk'},
    {id: 'finance', name: 'Financial modeling', question: 'Which assumptions drive a discounted cash-flow scenario?',
      method: 'Start with reported operating cash flow less PP&E purchases. Discount five assumed annual cash flows and a terminal amount. Require a positive starting proxy and a discount rate above terminal growth. Separate sourced observed-price ratios from hypothetical cash-flow values.',
      evaluation: 'Present-value identities, bounded rates, nonpositive cash-flow withholding and discount/terminal sensitivity. This proxy is not audited FCFF, enterprise value, equity value or a per-share price target.',
      example: 'Models → Valuation exposes the annual/terminal contribution and sensitivity matrix. Change an assumption and explain why the value changes before interpreting its size.',
      files: ['web/site/research_models_core_v22.js', 'cloud/valuation_market_v73.py'], tests: ['web/tests/research_models_core_v22.test.cjs', 'tests/test_valuation_snapshots.py'], route: 'models', model: 'valuation', formula: 'valuation'},
    {id: 'optimization', name: 'Optimization & backtesting', question: 'Does a fitted allocation survive later dates and costs?',
      method: 'Use aligned returns and constrained covariance minimization. The rolling study trains on 126 earlier closes, evaluates 21 later sessions and repeats with long-only weights capped at 60%. Fit and passive benchmark pay modeled turnover costs on identical dates.',
      evaluation: 'Weight/cash constraints, chronology, fees and benchmark accounting; fixed diagnostic cases and leave-one-window-out comparisons. In-sample minimum variance is distinct from rolling evaluation; both remain sensitive to the selected universe and window.',
      example: 'Portfolio → What If? shows concentration and fitted risk. Models → Strategy Testing shows rolling wealth, train/test windows, weights, costs and robustness evidence.',
      files: ['web/site/private_optimizer.js', 'web/site/private_walkforward_v65.js'], tests: ['web/tests/private_optimizer.test.cjs', 'web/tests/private_research_v65.test.cjs'], route: 'models', model: 'strategy', formula: 'portfolio'},
    {id: 'nlp', name: 'NLP & text analytics', question: 'What topics and language appear in dated news?',
      method: 'Tokenize provider headlines; use sparse TF-IDF vectors and cosine similarity for shared vocabulary. A lexical dictionary with negation handling labels tone. Display original dates and sources so the text summary can be checked.',
      evaluation: 'Tokenization, topic similarity, negation and endpoint fixtures. Tone can miss irony, context and the company being discussed. Topic similarity and lexical tone are not causal findings or return forecasts; no paid language model is required.',
      example: 'Private Explore places entitled dated headlines beside the selected company. A news outage disables that panel without removing SEC financials or eligible prices.',
      files: ['cloud/news_intelligence_v180.py', 'cloud/api.py'], tests: ['tests/test_news_intelligence_v180.py', 'tools/smoke_completion_browser.py'], route: 'explore', formula: 'nlp'},
    {id: 'software', name: 'Software & cloud engineering', question: 'How can one interface protect two different data modes?',
      method: 'Native JavaScript shares selection and result views while source adapters stay separate. Cloudflare serves a deterministic three-script CSP bundle; its same-origin proxy calls FastAPI. Server-side owner/MFA checks precede Supabase state and entitled provider requests.',
      evaluation: 'Owner denial, MFA, origin/action controls, version conflicts, safe errors, privacy/CSP checks and isolated browser journeys. CI does not prove live entitlement or owner persistence. Public requests cannot acquire private state.',
      example: 'Recorded virtual-account marks separate net contributions from P&L. The server validates complete fresh quotes before a version-checked write; tests do not modify the real owner account.',
      files: ['cloud/api.py', 'functions/api/[[path]].js', 'tools/build_unified_site.py'], tests: ['tests/test_hosted_web.py', 'tests/test_valuation_snapshots.py', 'tools/smoke_completion_browser.py'], route: 'methods', formula: null}
  ];
  let chosen = 'data';
  const reference = (label, files) => '<div class="qf26-references"><strong>' + label + '</strong>' + files.map(file => '<code>' + safe(file) + '</code>').join('') + '</div>';
  function detail(ctx) {
    const item = catalog.find(row => row.id === chosen);
    let trace = '';
    if (item.id === 'data') {
      const evidence = ctx?.financial?.evidence?.find(row => row.metric === 'revenue_usd');
      trace = evidence ? '<div class="qf26-trace"><strong>' + safe(ctx.symbol) + ' · annual revenue $' + number(evidence.value / 1e9) + 'B</strong><p>Fiscal end ' + safe(evidence.fiscal_end) + ' · filed ' + safe(evidence.filed || 'unavailable') + '</p><p>Accession <code>' + safe(evidence.accession || 'unavailable') + '</code></p></div>' : '<p>No compatible reported revenue is available for the selected company; no figure is inferred.</p>';
    }
    return '<h3>' + safe(item.question) + '</h3><p>' + safe(item.method) + '</p>' + (item.formula ? root.QFExhibits24.formula(item.formula) : '') + '<h4>How it is evaluated</h4><p>' + safe(item.evaluation) + '</p>' + trace + '<h4>Inspect it in the application</h4><p>' + safe(item.example) + '</p><button type="button" class="btn primary" data-qf26-open="' + safe(item.id) + '">Open ' + safe(item.model ? 'Models · ' + item.model : item.route) + '</button>' + reference('Implementation', item.files) + reference('Reproducible checks', item.tests) + '<p class="qf26-caption">These exact repository paths are provided for code review. Repository access is restricted; the explanation and live demonstrations are available here.</p>';
  }
  function methods(view, ctx) {
    if (view === 'overview') return '<section class="pane qf26-tour"><h2>A research project you can inspect</h2><p>QuantForge connects reported company financials, statistical experiments and hypothetical portfolios in one source-aware workflow. It demonstrates applied data science and software engineering without claiming institutional finance expertise or proven forecasting skill.</p><div class="qf26-tour-grid">' + [['1', 'Follow a financial figure', 'Explore', 'Check a fiscal period and accession, then explain growth and cash generation.', 'explore'], ['2', 'Challenge a model', 'Models', 'Compare the baseline, later test windows, calibration and withheld results.', 'models'], ['3', 'Inspect the implementation', 'Engineering', 'Trace a technique to its source, tests and design trade-offs.', 'engineering']].map(([n,title,label,description,route]) => '<div><span class="qf26-step">' + n + '</span><h3>' + title + '</h3><p>' + description + '</p><button type="button" class="btn" data-qf26-tour="' + route + '">' + label + '</button></div>').join('') + '</div><p class="qf26-caption">The project was built to learn financial research and demonstrate statistical data science. Synthetic market examples test the product; private market results require authorized data. Neither is a claim of investment performance.</p></section>';
    if (view !== 'engineering') return '';
    return '<section class="pane qf26-architecture"><h2>From source to explanation</h2><p>One shared interface; distinct public and authenticated data paths. Each stage can withhold an ineligible result without fabricating a replacement.</p><ol class="qf26-pipeline"><li><strong>Sources</strong><span>SEC filings · synthetic public paths · entitled private history/news</span></li><li><strong>Validation</strong><span>Units and dates · missingness · exact-date alignment · owner/MFA</span></li><li><strong>Computation</strong><span>Pure numerical engines · chronological evaluation · constrained scenarios</span></li><li><strong>Evidence</strong><span>Source + scope + dates · baseline and limits · readable charts and findings</span></li></ol><div class="qf24-trust-grid"><div><h3>Public delivery</h3><p>Deterministic static HTML and three hashed scripts on Cloudflare Pages. Historical SEC data and labeled simulations are redistributable here. No credentials or personal holdings enter this artifact.</p></div><div><h3>Private services</h3><p>Browser → same-origin Pages proxy → FastAPI → Supabase / Alpaca. Owner identity and authenticator verification gate access; credentials remain server-side. Version-checked virtual writes reject stale state.</p></div></div><h3>Deliberate trade-offs</h3><p>Native modules retain tested calculations without a framework rewrite. Native MathML renders equations without a third-party script. Price-only histories remain line charts; candles and volume are withheld without genuine OHLCV. Optional filing/factor inputs stay in session memory.</p></section><section class="pane"><h2>Technical evidence by discipline</h2><p>Select a discipline to inspect the question, implementation, evaluation and exact source/test references. Every demonstration uses the current research context.</p><div class="qf26-disciplines" role="group" aria-label="Technical evidence disciplines">' + catalog.map(item => '<button type="button" class="btn" data-qf26-discipline="' + item.id + '" aria-pressed="' + (item.id === chosen) + '">' + item.name + '</button>').join('') + '</div><div id="qf26-evidence-detail" class="qf26-evidence-detail" aria-live="polite">' + detail(ctx) + '</div></section>';
  }

  let sequence = 0;
  const plots = new Map();
  function curve(title, dates, lines, options = {}) {
    if (!Array.isArray(dates) || dates.length < 2 || !lines.length || lines.some(line => line.values.length !== dates.length || line.values.some(value => !finite(value)))) return '<p>Chart unavailable: aligned finite observations are required.</p>';
    const id = 'qf26-chart-' + (++sequence), width = Math.max(300, Math.min(850, (root.innerWidth || 1200) - ((root.innerWidth || 1200) >= 800 ? 355 : 68))), height = 310;
    const left = 62, right = width - 16, top = 25, bottom = 252;
    const values = lines.flatMap(line => line.values), low = Math.min(...values), high = Math.max(...values), pad = (high - low || Math.abs(low) || 1) * .08;
    const min = low - pad, span = high - low + 2 * pad;
    const x = i => left + (right - left) * i / (dates.length - 1), y = value => bottom - (value - min) / span * (bottom - top);
    const fmt = options.format === 'percent' ? percent : number;
    const path = values => values.map((value, i) => (i ? 'L' : 'M') + x(i).toFixed(2) + ' ' + y(value).toFixed(2)).join(' ');
    plots.set(id, {dates, lines, fmt, width, left, right, index: dates.length - 1, x});
    if (plots.size > 64) plots.delete(plots.keys().next().value);
    return '<figure class="qf26-plot"><figcaption>' + safe(title) + '</figcaption><svg data-qf26-chart="' + id + '" viewBox="0 0 ' + width + ' ' + height + '" tabindex="0" role="img" aria-label="' + safe(title) + '. Use Left and Right arrow keys, Home or End to inspect dates.">' + [0, .5, 1].map(t => '<path d="M' + left + ' ' + (bottom - t * (bottom - top)) + 'H' + right + '" stroke="#dfe3e8"/><text x="2" y="' + (bottom - t * (bottom - top) + 4) + '" font-size="13">' + safe(fmt(min + t * span)) + '</text>').join('') + lines.map((line, i) => '<path d="' + path(line.values) + '" stroke="' + ['#34465e', '#946744', '#576e5c'][i % 3] + '" fill="none" stroke-width="2.5"' + (i ? ' stroke-dasharray="7 4"' : '') + '/>').join('') + '<path id="' + id + '-cursor" d="M' + right + ' ' + top + 'V' + bottom + '" stroke="#727e8e" stroke-dasharray="3 3"/><text x="' + left + '" y="285" font-size="13">' + safe(dates[0]) + '</text><text x="' + right + '" y="303" text-anchor="end" font-size="13">' + safe(dates.at(-1)) + '</text></svg><p id="' + id + '-readout" class="qf26-readout" role="status">' + safe(dates.at(-1)) + ' · ' + lines.map(line => safe(line.name) + ': ' + safe(fmt(line.values.at(-1)))).join(' · ') + '</p><p class="qf26-caption">Hover or focus the plot and use ← / →, Home or End to inspect every dated observation. Solid and dashed lines distinguish series.</p></figure>';
  }
  function inspect(svg, index) {
    const plot = plots.get(svg.dataset.qf26Chart);
    if (!plot) return;
    plot.index = Math.max(0, Math.min(plot.dates.length - 1, index));
    root.document.getElementById(svg.dataset.qf26Chart + '-readout').textContent = plot.dates[plot.index] + ' · ' + plot.lines.map(line => line.name + ': ' + plot.fmt(line.values[plot.index])).join(' · ');
    root.document.getElementById(svg.dataset.qf26Chart + '-cursor').setAttribute('d', 'M' + plot.x(plot.index) + ' 25V252');
  }
  root.document?.addEventListener('pointermove', event => {
    const svg = event.target.closest('svg[data-qf26-chart]'), plot = svg && plots.get(svg.dataset.qf26Chart);
    if (plot) inspect(svg, Math.round(((event.clientX - svg.getBoundingClientRect().left) / svg.getBoundingClientRect().width * plot.width - plot.left) / (plot.right - plot.left) * (plot.dates.length - 1)));
  });
  root.document?.addEventListener('keydown', event => {
    const svg = event.target.closest('svg[data-qf26-chart]'), plot = svg && plots.get(svg.dataset.qf26Chart);
    if (!plot) return;
    const index = event.key === 'ArrowLeft' ? plot.index - 1 : event.key === 'ArrowRight' ? plot.index + 1 : event.key === 'Home' ? 0 : event.key === 'End' ? plot.dates.length - 1 : null;
    if (index !== null) { event.preventDefault(); inspect(svg, index); }
  });
  for (const name of ['qf:data-mode', 'qf:research-context', 'qf:owner-auth-ended']) root.addEventListener?.(name, () => plots.clear());
  root.document?.addEventListener('click', event => {
    const button = event.target.closest('[data-qf26-discipline]');
    if (button) {
      chosen = button.dataset.qf26Discipline;
      if (!catalog.some(item => item.id === chosen)) return;
      root.document.querySelectorAll('[data-qf26-discipline]').forEach(node => node.setAttribute('aria-pressed', String(node === button)));
      root.document.getElementById('qf26-evidence-detail').innerHTML = detail(root.QFResearch20.context());
    }
    const open = event.target.closest('[data-qf26-open]'), tour = event.target.closest('[data-qf26-tour]');
    if (open) {
      const item = catalog.find(row => row.id === open.dataset.qf26Open);
      if (!item) return;
      root.QFNavigate20(item.route);
      if (item.model) root.document.querySelector('[data-qf-model="' + item.model + '"]').click();
    }
    if (tour) {
      const route = tour.dataset.qf26Tour;
      root.QFNavigate20(route === 'engineering' ? 'methods' : route);
      if (route === 'engineering') root.document.querySelector('[data-qf-c22-method="engineering"]').click();
    }
  });
  root.QFEvidence26 = Object.freeze({catalog, methods});
  function histogram(ctx) {
    const returns = root.QFResearchModelsCore22.returns(ctx.prices);
    const bins = root.QFResearchB21.histogram({symbols:[ctx.symbol], returns:{[ctx.symbol]:returns}}, 9);
    const counts = bins.counts[ctx.symbol], maximum = Math.max(1,...counts);
    return '<figure class="qf26-plot"><figcaption>Distribution of simple daily returns</figcaption><svg viewBox="0 0 330 230" role="img" aria-label="Historical daily return frequency: '+returns.length+' returns in nine equal-width bins. Exact ranges and counts are in the table below."><text x="4" y="18" font-size="13">Sessions</text><text x="4" y="42" font-size="13">'+maximum+'</text><path d="M40 35V180H320" stroke="#b2bbc8" fill="none"/>'+counts.map((count,i)=>'<rect x="'+(43+i*30)+'" y="'+(180-count/maximum*140)+'" width="25" height="'+(count/maximum*140)+'" fill="'+(bins.edges[i+1]<=0?'#8a6f5b':'#485c75')+'"><title>'+safe(percent(bins.edges[i]))+' to '+safe(percent(bins.edges[i+1]))+': '+count+' sessions</title></rect>').join('')+'<text x="40" y="208" font-size="13">'+percent(bins.edges[0])+'</text><text x="315" y="225" text-anchor="end" font-size="13">'+percent(bins.edges.at(-1))+'</text></svg><p class="qf26-caption">The left tail contains the most negative returns. Historical VaR is a quantile; Expected Shortfall averages returns at or below that cutoff. Nine equal-width bins summarize this sample, not a fitted future probability distribution.</p><div class="table-wrap"><table><thead><tr><th scope="col">Daily return range</th><th scope="col">Sessions</th></tr></thead><tbody>'+counts.map((count,i)=>'<tr><td>'+percent(bins.edges[i])+' to '+percent(bins.edges[i+1])+(i===8?' (inclusive upper bound)':'')+'</td><td>'+count+'</td></tr>').join('')+'</tbody></table></div></figure>';
  }
  root.QFCharts26 = Object.freeze({curve, histogram});
})(typeof window !== 'undefined' ? window : globalThis);
