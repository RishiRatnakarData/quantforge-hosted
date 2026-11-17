/* Release C: Models and Methods UI. One selected-company context, no independent provider IO. */
(function(root){
'use strict';
const $=id=>document.getElementById(id),C=root.QFResearchModelsCore22;
if(!C||!$('page-models')||!$('qf-c22-methods-main'))return;
const safe=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const percent=(x,n=1)=>typeof x==='number'&&Number.isFinite(x)?(x*100).toFixed(n)+'%':'Unavailable';
const number=(x,n=2)=>typeof x==='number'&&Number.isFinite(x)?x.toFixed(n):'Unavailable';
const billions=x=>typeof x==='number'&&Number.isFinite(x)?(x<0?'−':'')+'$'+(Math.abs(x)/1e9).toFixed(2)+'B':'Unavailable';
// Source repository is private: show checked local references without dead public links.
const source=(file,label)=>'<span class="qf24-source">'+safe(label)+' · <code>'+safe(file)+'</code> (repository access required)</span>';
let category='prediction',phase='results',method='overview',stamp='',cached=null;
const categories=['prediction','risk','valuation','strategy'],phases=['results','evaluation','method'];
function context(){return root.QFResearch20?.context?.()||null;}
function header(ctx,detail){return '<div class="qf-c22-provenance"><span class="qf-c22-tag '+(category==='valuation'?'reported':ctx?.origin==='market'?'observed':'synthetic')+'">'+
 (category==='valuation'?'Reported SEC cash flow · modeled growth and discount assumptions':ctx?.origin==='market'?'Authenticated historical market observations':ctx?.origin==='synthetic'?'Synthetic price experiment · NOT real market history':'Price history unavailable')+
 '</span><span>'+safe(ctx?.symbol||'No selected company')+'</span><span>'+safe(detail||'')+'</span></div>';}
function table(headers,rows){return '<div class="table-wrap"><table><thead><tr>'+headers.map(v=>'<th scope="col">'+safe(v)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(v=>'<td>'+safe(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function metrics(items){return '<div class="qf-c22-metrics">'+items.map(([name,value,sub])=>'<div class="qf-c22-metric"><small>'+safe(name)+'</small><strong>'+safe(value)+'</strong>'+(sub?'<span>'+safe(sub)+'</span>':'')+'</div>').join('')+'</div>';}
function line(values,labels,label){
 return root.QFCharts26.curve(label,labels,[{name:'Annualized volatility',values}],{format:'percent'});
}
function twoLines(a,b,labels){
 return root.QFCharts26.curve('Historical strategy and passive benchmark (start = 100)',labels,[{name:'Filtered strategy',values:a},{name:'Buy and hold',values:b}]);
}
function outputUnavailable(reason){return '<section class="pane qf-c22-unavailable"><h2>Not enough eligible evidence</h2><p>'+safe(reason)+'</p><p class="tiny">The reported SEC financials in Explore remain independent of private market-price availability.</p></section>';}
function modelData(ctx){
 if(!ctx)return null;
 const id=[ctx.symbol,ctx.origin,ctx.prices?.length||0,ctx.prices?.[0]?.date||'',ctx.prices?.at(-1)?.date||''].join('|');
 if(stamp===id&&cached)return cached;
 stamp=id;cached={};
 cached.risk=ctx.prices&&ctx.prices.length?C.risk(ctx.prices,ctx.symbol.includes('/')?365:252):{ready:false,reason:'No authorized or clearly labeled illustrative historical price series is loaded.'};
 cached.valuation=C.valuation(ctx.financial);
 cached.strategy=ctx.prices&&ctx.prices.length?C.strategy(ctx.prices):{ready:false,reason:'No eligible price history is loaded.'};
 if(ctx.prices?.length){
  const p=ctx.prices;
  const h={symbols:[ctx.symbol],dates:p.map(x=>x.date),closes:{[ctx.symbol]:p.map(x=>x.close)},asset_classes:{[ctx.symbol]:'us_equity'},source:ctx.origin==='market'?'Entitled owner market history':'Deterministic public demonstration'};
  cached.prediction=root.QFPrivatePredictiveMLV180?.analyze(h,ctx.symbol)||{ready:false,reason:'The logistic classifier is unavailable.'};
 }else cached.prediction={ready:false,reason:'No eligible market-price input is available; no model is run.'};
 return cached;
}
function prediction(ctx,models){
 const p=models.prediction;
 if(!p.ready)return outputUnavailable(p.reason);
 const m=metrics([['Test windows',String(p.testWindows),'Non-overlapping later 5-session labels'],['Accuracy',percent(p.evaluatedAccuracy), 'Historical baseline '+percent(p.baselineAccuracy)],['Brier score',number(p.evaluatedBrier,3),'Baseline '+number(p.baselineBrier,3)],['Signal screen',p.qualified?'Exploratory':'Withheld','Not an investment recommendation']]);
 const reliability=table(['Predicted-probability bin','Test windows','Average model score','Observed positive share'],(p.calibration||[]).map(b=>[percent(b.range[0],0)+'–'+percent(b.range[1],0),String(b.count),percent(b.mean_prediction),percent(b.observed_positive)]));
 if(phase==='results')return header(ctx,p.firstTestDate+' to '+p.lastTestDate)+m+
  '<section class="pane"><h2>Five-session direction experiment</h2><p>'+safe(p.status)+'. '+safe(p.explanation)+'</p><p class="tiny">A binary direction classifier—not a future stock-price projection. The current score is not presented as a calibrated trading probability. Prices are '+(ctx.origin==='market'?'entitled private observations.':'a reproducible synthetic fixture.')+'</p></section>';
 if(phase==='evaluation')return header(ctx,p.firstTestDate+' to '+p.lastTestDate)+
  '<section class="pane"><h2>Chronological held-out evaluation</h2>'+m+
  '<p>Each test date uses only training labels whose five-session outcomes have already matured. Test windows are five sessions apart. The baseline is the expanding historical positive-outcome frequency, not a random guess.</p>'+reliability+
  '<p class="tiny">These are coarse, descriptive reliability bins. Small bin sizes make calibration unstable; there is no independently calibrated or statistically established market edge. Held-out positive fraction: '+percent(p.testPositiveRate)+'.</p></section>';
 return '<section class="pane"><h2>How prediction works</h2><p>L2-regularized logistic regression standardizes lagged returns and history-derived variability on past training observations, then outputs a directional class score. Training is expanding; future five-session outcomes never enter a past fit.</p><p><strong>Features:</strong> '+safe(p.features.join(' · '))+'</p><p><strong>Decision gate:</strong> at least 12 held-out windows, Brier improvement greater than 0.005, and directional accuracy no worse than the baseline. Clearing the screen is exploratory, not evidence of profitable forecasting.</p><p><strong>Source:</strong> '+source('web/site/private_predictive_ml_v180.js','Logistic implementation')+' · '+source('web/tests/private_predictive_ml_v180.test.cjs','Model regression tests')+'</p></section>';
}
function risk(ctx,models){
 const r=models.risk;if(!r.ready)return outputUnavailable(r.reason);
 const m=metrics([['Realized annualized volatility',percent(r.annual_volatility),'Sample daily deviation × √'+r.sessions_per_year],['Maximum drawdown',percent(r.max_drawdown),'Historical peak to trough'],['1-day VaR (95%)',percent(r.daily_var95_loss),'Observed 5th-percentile loss'],['1-day Expected Shortfall',percent(r.daily_es95_loss),'Average of observed worst 5% tail']]);
 if(phase==='results')return header(ctx,r.first+' to '+r.last)+m+'<section class="pane"><h2>60-session rolling volatility</h2>'+line(r.rolling.map(x=>x.volatility),r.rolling.map(x=>x.date),'Rolling annualized historical volatility')+'<p class="tiny">Historical close-to-close variation; no projected future risk band.</p></section>';
 if(phase==='evaluation')return header(ctx,r.observations+' observed daily returns')+'<section class="pane"><h2>Historical stability and uncertainty</h2>'+
  metrics([['Earlier half volatility',percent(r.split_volatility[0])],['Later half volatility',percent(r.split_volatility[1])],['Worst observed day',percent(r.worst_day)],['Positive-return sessions',percent(r.positive_share)]])+
  (r.bootstrap?'<p>Moving-block bootstrap (300 deterministic resamples, '+r.bootstrap.block_length+'-session blocks): '+percent(r.bootstrap.low)+' to '+percent(r.bootstrap.high)+' for realized annualized volatility <strong>sample sensitivity</strong>.</p>':'<p>Moving-block bootstrap withheld: fewer than 180 daily returns.</p>')+
  '<p class="tiny">Blocks preserve some local dependence, but stationary-block assumptions and short windows can still fail. These bounds are not calibrated future volatility, VaR, or portfolio return intervals.</p></section>';
 return '<section class="pane"><h2>How risk is measured</h2><p>Simple daily return = close(t) / close(t−1) − 1. Volatility is the sample standard deviation × √'+r.sessions_per_year+'. Historical 95% VaR is the nonnegative loss at the 5th percentile; Expected Shortfall averages returns at or below that cutoff. Maximum drawdown is the most negative close / preceding peak − 1.</p><p>All estimates depend on dates, adjustment convention, sample and future market behavior. Market benchmark/factor regression remains in Portfolio Analysis and the retained private research engines where aligned sources permit.</p><p>'+source('web/site/research_models_core_v22.js','Risk implementation')+' · '+source('web/tests/research_models_core_v22.test.cjs','Numerical tests')+'</p></section>';
}
function valuation(ctx,models){
 const v=models.valuation,real=v.scenarios.filter(s=>s.ready);
 if(!real.length)return outputUnavailable(v.scenarios[0]?.reason||'SEC cash-flow inputs do not support a positive scenario estimate.');
 const scenarios=table(['Scenario','5-year FCF proxy growth','Discount','Terminal growth','PV proxy','Terminal contribution'],real.map(s=>[s.name,percent(s.growth),percent(s.discount),percent(s.terminal),billions(s.proxy_pv),percent(s.terminal_share)]));
 const note='<p class="tiny">Reported SEC cash-flow proxy through fiscal '+safe(v.period||'unknown')+'. Hypothetical growth/discount assumptions. This is NOT an enterprise value, equity value, share-price target or observed market quotation.</p>';
 if(phase==='results')return header(ctx,'Fiscal period '+(v.period||'unavailable'))+'<section class="pane"><h2>Cash-flow scenario sensitivity</h2>'+scenarios+note+'</section>';
 if(phase==='evaluation')return header(ctx,'Sensitivity, not model skill')+'<section class="pane"><h2>Discount and terminal-rate sensitivity</h2><p>PV of the same historical SEC cash-flow proxy under a fixed 4% five-year hypothetical growth assumption.</p>'+table(['Discount rate','1% terminal','2% terminal','3% terminal'],v.sensitivity.map(x=>[percent(x.discount),...x.cells.map(y=>y.ready?billions(y.proxy_pv):'Unavailable')]))+note+'</section>';
 return '<section class="pane"><h2>How the cash-flow proxy is discounted</h2><p>Annual proxy FCF = reported operating cash flow − cash property-and-equipment purchases. For years 1–5: FCF(t) = FCF(0) × (1 + growth)^t. The final-year terminal amount uses growth after year 5 and a discount rate strictly greater than the terminal growth rate.</p><p>Discount all values back to the present. The calculation intentionally excludes an unverified balance-sheet bridge, debt, cash and share count. Nonpositive or missing FCF is withheld rather than forced into a favorable valuation.</p><p>'+source('web/site/research_models_core_v22.js','Scenario calculation')+' · '+source('web/tests/research_models_core_v22.test.cjs','Input and sensitivity tests')+'</p></section>';
}
function strategy(ctx,models){
 const r=models.strategy;if(!r.ready)return outputUnavailable(r.reason);
 const m=metrics([['Filtered strategy',percent(r.strategy.total_return),'Cumulative historical price-only'],['Buy and hold',percent(r.benchmark.total_return),'Passive price-only benchmark'],['Later-window strategy',percent(r.evaluation.strategy_return),'Fixed rules; after '+r.evaluation.first],['Later-window passive',percent(r.evaluation.passive_return),'Same later-window dates']]);
 if(phase==='results')return header(ctx,r.first+' to '+r.last)+m+'<section class="pane"><h2>Historical strategy and passive benchmark</h2>'+twoLines(r.indexed,r.passive,r.dates)+'<p class="tiny">Both indexed to 100: 110 means 10% above the first value, not a $110 share price. '+safe(r.assumption)+'</p></section>';
 if(phase==='evaluation')return header(ctx,'Chronologically later '+r.evaluation.sessions+' sessions')+'<section class="pane"><h2>Validation and friction</h2>'+m+
  '<p>The last third of the available post-warmup timeline is displayed separately. The 20/60-session rule was fixed in advance; it was not tuned against these dates. This is a chronological <em>diagnostic</em>, not a claim of untouched research validation across many companies.</p><p>Switch exposure: '+r.turnover+' unit-weight transitions · assumed fee '+percent(r.fee,2)+' per switch. Buy-and-hold pays a single entry fee. The analysis omits bid/ask spread, dividends, cash interest and execution constraints.</p></section>';
 return '<section class="pane"><h2>How the strategy is computed</h2><p>At each prior close, compute the average of the previous 20 and 60 closes. Hold one unit of exposure for the next close-to-close interval only when the shorter average exceeds the longer one; otherwise hold cash. Fees reduce wealth on exposure changes.</p><p>No future close is used to choose yesterday’s exposure. This single-rule example is not the same as an optimized, multiple-asset walk-forward system; those constrained engines remain in the authenticated research modules.</p><p>'+source('web/site/research_models_core_v22.js','Strategy study')+' · '+source('web/tests/research_models_core_v22.test.cjs','Chronology and cost tests')+' · '+source('web/site/private_walkforward_v65.js','Retained multi-asset walk-forward')+'</p></section>';
}
function renderModel(){
 const ctx=context(),host=$('qf-c22-model-output');if(!ctx){host.textContent='Choose a company in Explore to run a research experiment.';return;}
 const models=modelData(ctx);
 const content={prediction,risk,valuation,strategy};host.innerHTML=content[category](ctx,models)+(root.QFMethods27?.modelEvidence(category,phase,ctx,models)||'')+(root.QFExhibits24?.model(category,phase,ctx,models)||'')+(category==='strategy'?'<section class="pane"><h2>Rolling multi-asset allocation study</h2><p>Reuse the Compare basket: fit on 126 past closes, evaluate the next 21 sessions, then roll forward. Long-only weights are capped at 60%; both strategies pay modeled rebalancing costs. This restores the existing walk-forward engine in the shared workspace.</p><button type="button" class="btn primary" id="qf24-walkforward-run">Run rolling allocation study</button><div id="qf24-walkforward-output" aria-live="polite"></div></section>':'');
 host.insertAdjacentHTML('beforeend',root.QFDeepUI25?.modelSection(category,phase)||'');
 $('qf-v20-model-selected').textContent=ctx.name+' ('+ctx.symbol+') · current research selection · '+(ctx.origin==='market'?'observed owner prices':ctx.origin==='synthetic'?'illustrative public prices':'price data unavailable')+' · SEC snapshot '+ctx.snapshot;
 document.querySelectorAll('[data-qf-model]').forEach(b=>{const on=b.dataset.qfModel===category;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
 document.querySelectorAll('[data-qf-c22-phase]').forEach(b=>{const on=b.dataset.qfC22Phase===phase;b.classList.toggle('active',on);b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;if(on)$('qf-c22-model-output').setAttribute('aria-labelledby',b.id);});
}
function renderMethods(){
 root.QFMethods27?.beforeRender?.();
 document.querySelectorAll('[data-qf-c22-method]').forEach(b=>{const on=b.dataset.qfC22Method===method;b.classList.toggle('active',on);b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;if(on)$('qf-c22-method-content').setAttribute('aria-labelledby',b.id);});
 const host=$('qf-c22-method-content'),snap=root.QFPublishedSEC,n=Array.isArray(snap?.companies)?snap.companies.length:0;
 if(method==='overview'&&root.QFMethods27){host.innerHTML=root.QFMethods27.overview(context());return;}
 if(method==='statistical'&&root.QFMethods27){host.innerHTML=root.QFMethods27.statistical(context());root.QFMethods27.afterRender();return;}
 const methods={
  overview:'<section class="pane"><h2>Why QuantForge exists</h2><p>I built QuantForge to understand financial data using my background in statistics and programming. It joins traceable company financial statements, transparent modeling experiments and hypothetical portfolio research, without treating a statistical estimate as investment advice.</p><div class="qf-c22-flow" aria-label="Research pipeline"><div>SEC and entitled market sources</div><span>→</span><div>Validation and normalization</div><span>→</span><div>Numerical research engines</div><span>→</span><div>Evidence with limitations</div><span>→</span><div>Explore, Compare, Models, Portfolio</div></div><p>Public data: historical SEC snapshot and labeled synthetic price demonstrations. Owner-only mode: MFA-protected, entitled market and personal records. The same numerical definitions are used when inputs are eligible.</p></section>',
  data:'<section class="pane"><h2>Source records, quality and lineage</h2>'+metrics([['SEC coverage',String(n)+' issuers','Published historical Company Facts snapshot'],['Snapshot as of',snap?.as_of||'Not available','Not a real-time market or PIT feed'],['Issuer key','CIK + symbol','Filing source/accession when present']])+table(['Stage','Input / validation','Output and limitation'],[['Ingest','SEC Company Facts XBRL by CIK; annual filing records','Historical Company Facts snapshot'],['Validate','Fiscal end, accession, filing date, units, duplicate periods and missing tags','Rejected or explicitly unavailable records'],['Normalize','Consistent USD values and fiscal-year selection','Reported revenue, income and cash-flow series'],['Derive','Growth, margins, operating cash flow less cash PP&E purchases','Derived metrics with original source fields'],['Publish','Deterministic JSON, dataset cutoff and CSP build checks','Static public snapshot; no private positions or provider tokens']])+ '<p>Incremental refresh and revisions must be tested against actual published snapshots before claiming a live data warehouse. There is no invented SQL database behind these browser observations.</p><p>'+source('tools/build_public_sec_snapshot.py','SEC pipeline')+' · '+source('web/site/sec_analytics.js','Financial metric transforms')+' · '+source('web/site/sec_snapshot.json','Published source dataset')+'</p></section>',
  statistical:'<section class="pane"><h2>Statistics tied to questions and validation</h2>'+table(['Research question','Method, test and limitations','Source'],[['Does price direction exhibit a measurable baseline advantage?','L2 logistic regression, mature five-session labels, past-only fits, Brier and accuracy against historical frequency; small samples and regimes','private_predictive_ml_v180.js'],['What historical downside occurred?','Rolling realized volatility, empirical VaR/ES and maximum drawdown; moving-block sample sensitivity is not a prediction','research_models_core_v22.js'],['How sensitive is discounted cash flow?','Five-year FCF-proxy scenario discounting and rate sensitivity; no equity/share-value bridge','research_models_core_v22.js'],['How does an explicit price rule compare?','Past-only moving averages, passive benchmark, modeled switch fees and later-period study; no execution claim','research_models_core_v22.js'],['How does an allocation change risk?','Aligned return covariance, correlation, caps and sample minimum-variance optimization; in-sample fit only','research_compare_portfolio_v21.js']])+ '<p>'+source('web/site/research_models_core_v22.js','Release C calculations and limits')+' · '+source('web/tests/research_models_core_v22.test.cjs','Numerical regression suite')+'</p></section>',
  engineering:'<section class="pane"><h2>Components, trust boundaries and verification</h2>'+table(['Layer','Implementation and assurance','Verification'],[['Shared browser','One five-route shell, company selection, data-origin labels, responsive charts, CSV outputs','Chromium desktop/mobile keyboard journeys'],['Public delivery','Cloudflare static JSON/JS, deterministic build, strict hash-based Content Security Policy','Build, CSP and privacy audits'],['Owner-only services','FastAPI owner identity and Supabase authenticator MFA, permitted Alpaca prices; no live orders','Private API unit tests and separate owner browser acceptance'],['Statistical services','Pure JavaScript computations with bounded inputs and no network/storage dependencies','Node model regression and chronological leakage tests'],['Release process','Pinned tracked baseline, manifest hashes, backup/rollback, Python Ruff/pytest and GitHub Actions','CI is not a replacement for signed-in production acceptance']])+ '<p>'+source('cloud/api.py','Authenticated Python API')+' · '+source('tools/build_unified_site.py','Deterministic bundle builder')+' · '+source('.github/workflows/ci.yml','Automated CI configuration')+' · '+source('tools/smoke_release_c_browser.py','Release C browser acceptance')+'</p><p class="tiny">An automated test is evidence of an implemented guardrail, not proof of production uptime, market entitlement or penetration-tested security.</p></section>'
 };
 host.innerHTML=(method==='statistical'||method==='engineering'?'':methods[method])+(method==='engineering'?'':(root.QFExhibits24?.methods(method,context())||''))+(root.QFEvidence26?.methods(method,context())||'')+(root.QFMethods27?.additions(method,context())||'')+(root.QFFinalEvidence28?.methods(method,context())||'')+(method==='data'?(root.QFDeepUI25?.dataSection()||''):'');
}
function showModel(name){if(!categories.includes(name))return;category=name;phase='results';renderModel();}
function refresh(){stamp='';cached=null;if($('page-models').classList.contains('active'))renderModel();if($('page-methods').classList.contains('active'))renderMethods();}
document.addEventListener('click',e=>{
 const cat=e.target.closest('#page-models [data-qf-model]');if(cat){showModel(cat.dataset.qfModel);return;}
 const sub=e.target.closest('#page-models [data-qf-c22-phase]');if(sub&&phases.includes(sub.dataset.qfC22Phase)){phase=sub.dataset.qfC22Phase;renderModel();return;}
 const met=e.target.closest('#page-methods [data-qf-c22-method]');if(met&&['overview','data','statistical','engineering'].includes(met.dataset.qfC22Method)){method=met.dataset.qfC22Method;renderMethods();}
});
for(const [attribute,panel] of [['data-qf-c22-phase','qf-c22-model-output'],['data-qf-c22-method','qf-c22-method-content']]){
 for(const tab of document.querySelectorAll('['+attribute+']')){tab.id='qf29-'+tab.getAttribute(attribute)+'-'+panel;tab.setAttribute('aria-controls',panel);}
}
// Re-render on source changes and route transitions, never reuse stale price experiments.
root.addEventListener('qf:research-context',refresh);root.addEventListener('qf:data-mode',refresh);root.addEventListener('qf:owner-auth-ended',refresh);
root.addEventListener('qf:route-change',e=>{if(e.detail?.route==='models')renderModel();if(e.detail?.route==='methods')renderMethods();});
renderMethods();
root.QFModelsMethods22=Object.freeze({showModel,refresh,refreshMethods:renderMethods,evidence:()=>modelData(context())});
})(typeof window!=='undefined'?window:globalThis);
