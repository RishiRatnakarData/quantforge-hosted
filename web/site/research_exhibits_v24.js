/* In-page research exhibits. Native MathML; no remote fonts, scripts or private persistence. */
(function(root){
'use strict';
const safe=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=x=>Number.isFinite(x)?(100*x).toFixed(1)+'%':'Unavailable';
const bn=x=>Number.isFinite(x)?'$'+(x/1e9).toFixed(2)+'B':'Unavailable';
const equations={
 prediction:['Probability equals one divided by one plus exponential of negative score','<mi>p</mi><mo>=</mo><mfrac><mn>1</mn><mrow><mn>1</mn><mo>+</mo><msup><mi>e</mi><mrow><mo>−</mo><mi>z</mi></mrow></msup></mrow></mfrac>'],
 risk:['Daily return equals current close divided by prior close minus one','<msub><mi>r</mi><mi>t</mi></msub><mo>=</mo><mfrac><msub><mi>P</mi><mi>t</mi></msub><msub><mi>P</mi><mrow><mi>t</mi><mo>−</mo><mn>1</mn></mrow></msub></mfrac><mo>−</mo><mn>1</mn>'],
 valuation:['Present value equals sum of discounted cash flows plus discounted terminal value','<mi>PV</mi><mo>=</mo><munderover><mo>∑</mo><mrow><mi>t</mi><mo>=</mo><mn>1</mn></mrow><mn>5</mn></munderover><mfrac><msub><mi>FCF</mi><mi>t</mi></msub><msup><mrow><mo>(</mo><mn>1</mn><mo>+</mo><mi>d</mi><mo>)</mo></mrow><mi>t</mi></msup></mfrac><mo>+</mo><mfrac><mi>TV</mi><msup><mrow><mo>(</mo><mn>1</mn><mo>+</mo><mi>d</mi><mo>)</mo></mrow><mn>5</mn></msup></mfrac>'],
 strategy:['Net daily return equals prior position times daily return minus fee times position change','<msub><mi>r</mi><mtext>net,t</mtext></msub><mo>=</mo><msub><mi>w</mi><mrow><mi>t</mi><mo>−</mo><mn>1</mn></mrow></msub><msub><mi>r</mi><mi>t</mi></msub><mo>−</mo><mi>c</mi><mo>|</mo><mi>Δw</mi><mo>|</mo>'],
 portfolio:['Portfolio variance equals weight transpose times covariance times weight','<msubsup><mi>σ</mi><mi>p</mi><mn>2</mn></msubsup><mo>=</mo><msup><mi>w</mi><mi>T</mi></msup><mi>Σ</mi><mi>w</mi>'],
 nlp:['Cosine similarity equals dot product divided by the product of vector lengths','<mi>similarity</mi><mo>=</mo><mfrac><mrow><mi>a</mi><mo>·</mo><mi>b</mi></mrow><mrow><mo>‖</mo><mi>a</mi><mo>‖</mo><mo>‖</mo><mi>b</mi><mo>‖</mo></mrow></mfrac>']
};
function formula(key){const [label,body]=equations[key];return '<div class="qf24-equation"><math xmlns="http://www.w3.org/1998/Math/MathML" display="block" aria-label="'+label+'">'+body+'</math></div>';}
function bars(title,rows,format=pct){
 const clean=rows.filter(r=>Number.isFinite(r[1]));if(!clean.length)return '<p>No eligible observations for this exhibit.</p>';
 const max=Math.max(...clean.map(r=>Math.abs(r[1])),0.00001),h=clean.length*45+25;
 if(root.innerWidth<740){
  const w=Math.max(240,Math.min(360,root.innerWidth-96)),limit=Math.floor((w-100)/7.2);
  return '<figure class="qf24-figure"><figcaption>'+safe(title)+'</figcaption><svg viewBox="0 0 '+w+' '+(clean.length*64+8)+'" role="img" aria-label="'+safe(title)+'">'+clean.map(([name,v],i)=>{const label=String(name),short=label.length>limit?label.slice(0,limit-1)+'…':label;return '<g><title>'+safe(label)+': '+safe(format(v))+'</title><text x="0" y="'+(i*64+19)+'" font-size="14">'+safe(short)+'</text><text x="'+w+'" y="'+(i*64+19)+'" text-anchor="end" font-size="14">'+safe(format(v))+'</text><rect x="0" y="'+(i*64+31)+'" width="'+Math.max(1,Math.abs(v)/max*w)+'" height="17" rx="3" fill="'+(v<0?'#8a6248':'#424e5c')+'"/></g>';}).join('')+'</svg><div class="qf24-readable">'+clean.map(([n,v])=>safe(n)+': '+safe(format(v))).join(' · ')+'</div></figure>';
 }
 return '<figure class="qf24-figure"><figcaption>'+safe(title)+'</figcaption><svg viewBox="0 0 720 '+h+'" role="img" aria-label="'+safe(title)+'">'+clean.map(([name,v],i)=>'<g><text x="0" y="'+(i*45+22)+'" font-size="14">'+safe(name)+'</text><rect x="220" y="'+(i*45+6)+'" width="'+Math.max(1,Math.abs(v)/max*355)+'" height="25" rx="3" fill="'+(v<0?'#8a6248':'#424e5c')+'"><title>'+safe(name)+': '+safe(format(v))+'</title></rect><text x="595" y="'+(i*45+24)+'" font-size="14">'+safe(format(v))+'</text></g>').join('')+'</svg><div class="qf24-readable">'+clean.map(([n,v])=>safe(n)+': '+safe(format(v))).join(' · ')+'</div></figure>';
}
function calibration(p){
 const bins=(p.calibration||[]).filter(b=>b.count>0),w=root.innerWidth<740?Math.max(210,Math.min(360,root.innerWidth-112)):720,left=36,right=w-16,top=34,bottom=230;
 return '<figure class="qf24-figure"><figcaption>Did predicted scores match observed outcomes?</figcaption><p class="qf28-axis-label">Observed positive share (%)</p><svg viewBox="0 0 '+w+' 275" role="img" aria-label="Calibration diagram. Diagonal is perfect agreement; labeled points are held-out bins."><path d="M'+left+' '+bottom+'L'+right+' '+top+'" stroke="#949ba4" stroke-dasharray="7 5" fill="none"/>'+[0,.5,1].map(v=>'<text x="0" y="'+(bottom-(bottom-top)*v+4)+'" font-size="13">'+Math.round(v*100)+'</text>').join('')+bins.map((b,i)=>'<circle cx="'+(left+(right-left)*b.mean_prediction)+'" cy="'+(bottom-(bottom-top)*b.observed_positive)+'" r="'+Math.min(12,5+Math.sqrt(b.count))+'" fill="#343e4a"><title>Bin '+(i+1)+': '+b.count+' test windows; score '+pct(b.mean_prediction)+'; observed positive '+pct(b.observed_positive)+'</title></circle>').join('')+'<text x="'+left+'" y="258" font-size="13">0%</text><text x="'+right+'" y="258" text-anchor="end" font-size="13">100%</text></svg><p class="qf28-axis-label">Average predicted score (%) →</p><p>Small bins can sit far from the diagonal by chance. The Evaluation table exposes each exact bin and count; this plot does not establish calibrated future probabilities.</p></figure>';
}
function section(title,body){return '<section class="pane qf24-exhibit"><h2>'+safe(title)+'</h2>'+body+'</section>';}
function model(category,phase,ctx,models){
 const C=root.QFResearchModelsCore22,m=models[category];if(!m?.ready&&category!=='valuation')return '';
 if(phase==='method')return section('Equation and a worked example',formula(category)+{
  prediction:'<p>The score z combines standardized past features and fitted coefficients. A score of 0 gives 50%; a score of 1 gives 73.1%. Those are mathematical examples, not measured forecasting skill. L2 regularization penalizes large fitted coefficients.</p>',
  risk:'<p>A close rising from $100 to $102 gives a 2% simple daily return. Sample standard deviation measures variability around the historical average. Annualizing by √252 assumes equity trading sessions; it is not a worst-case bound.</p>',
  valuation:'<p>FCF is the reported operating-cash-flow-minus-capex proxy; d is an assumed discount rate. Terminal value uses year-five cash flow × (1 + terminal growth) / (d − terminal growth). A $100 cash flow one year away is worth $90.91 at a 10% assumed discount rate.</p>',
  strategy:'<p>w is the exposure set from an earlier close; c is the assumed switching fee. A 1% price gain with full exposure and a 0.05% entry fee gives a 0.95% modeled first-day return. Cash interest and execution slippage remain excluded.</p>'
 }[category]);
 if(category==='prediction')return section('Model evidence, beside its baseline',bars('Held-out directional accuracy',[['Logistic model',m.evaluatedAccuracy],['Historical base rate',m.baselineAccuracy]])+calibration(m));
 if(category==='risk'){
  let peak=ctx.prices[0].close;
  const rows=ctx.prices.map(p=>{peak=Math.max(peak,p.close);return [p.date,p.close/peak-1];});
  return section('Downside through this history',root.QFCharts26.curve('Historical drawdown from the preceding peak',rows.map(r=>r[0]),[{name:'Drawdown',values:rows.map(r=>r[1])}],{format:'percent'})+'<p>Every close is measured against the highest preceding close, including that date. A 20% loss requires a 25% gain to recover. This is an observed path within these inputs, not a future loss bound.</p>'+root.QFCharts26.histogram(ctx));
 }
 if(category==='valuation'){
  const v=models.valuation.scenarios.find(s=>s.name==='Base');if(!v?.ready)return '';
  return section('Where the discounted scenario comes from',bars('Base scenario present-value components',[...v.cash_flows.map(x=>['Year '+x.year,x.discounted]),['Beyond year five',v.terminal_pv]],bn)+'<p>'+pct(v.terminal_share)+' of the base scenario comes from the terminal assumption. A large share makes the result particularly sensitive to distant growth and discount rates.</p><div class="qf24-assumptions"><label>Five-year growth (%)<input id="qf24-dcf-growth" type="number" min="-50" max="50" value="4" step="0.5"></label><label>Discount rate (%)<input id="qf24-dcf-discount" type="number" min="1" max="50" value="10" step="0.5"></label><label>Terminal growth (%)<input id="qf24-dcf-terminal" type="number" min="-10" max="20" value="2" step="0.5"></label><button class="btn" id="qf24-dcf-run">Calculate scenario</button></div><div id="qf24-dcf-output" role="status"></div>');
 }
 if(category==='strategy')return section('How much do assumed costs change the result?',bars('Cumulative strategy return under fixed cost assumptions',[0,0.0005,0.002,0.005].map(f=>[(10000*f).toFixed(0)+' bp per switch',C.strategy(ctx.prices,f).strategy.total_return]))+'<p>The same past-only rule and dates are recomputed at every fee level. This is cost sensitivity; it is not multi-asset walk-forward optimization.</p>');
 return '';
}
function methods(view,ctx){
 if(view==='statistical')return [
 ['prediction','Can a direction model beat a simple base rate?','Past returns and volatility feed a regularized logistic fit. Five-session labels must mature before training. Compare held-out accuracy, Brier and coarse calibration with the expanding historical frequency; withhold weak signals.','At score 0 the sigmoid is 50%; this identity says nothing about market accuracy.','web/site/private_predictive_ml_v180.js'],
 ['risk','How much downside occurred in the sample?','Use dated close-to-close returns, sample volatility, empirical one-day VaR/ES and running-peak drawdown. Moving blocks assess sample sensitivity, not future loss coverage.','A $100 to $90 move is −10%; recovering requires +11.1%.','web/site/research_models_core_v22.js'],
 ['valuation','What would assumed cash flows be worth today?','Use SEC operating cash flow minus PP&E purchases with original fiscal period and filing provenance. Require a positive proxy and discount above terminal growth; withhold unsupported equity/share targets.','A $110 payment one year away discounted at 10% is $100.','web/site/research_models_core_v22.js'],
 ['portfolio','How do weights and co-movement affect risk?','Align all observations on common dates before estimating sample covariance. Constrained minimum variance fits this sample; future regimes and estimation error can reverse its apparent benefit.','Two 50% positions with 20% volatility and zero correlation have 14.1% modeled volatility. At correlation 1, it is 20%.','web/site/research_compare_portfolio_v21.js'],
 ['strategy','Does a fixed historical rule survive friction?','Choose exposure using earlier closes only; include switching costs and a passive benchmark over identical dates. Separate later-period diagnostics from research-wide untouched validation.','A 1% gain less a 0.05% entry cost gives 0.95%, before slippage or dividends.','web/site/private_walkforward_v65.js']
 ].map(([key,title,body,example,path])=>section(title,formula(key)+'<p>'+body+'</p><p class="qf24-worked"><strong>Worked example:</strong> '+example+'</p><p class="tiny">Implementation reference: <a href="https://github.com/RishiRatnakarData/quantforge-hosted/blob/main/'+path.split('/').map(encodeURIComponent).join('/')+'" target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer"><code>'+safe(path)+'</code></a>.</p>')).join('');
 if(view==='overview')return section('Two data modes, one research workflow','<div class="qf24-trust-grid"><div><h3>Public research</h3><p>Published SEC statements retain fiscal dates and filing references. Market-path exhibits use reproducible synthetic inputs, clearly labeled beside each result.</p><strong>No private account requests</strong></div><div><h3>Private research</h3><p>Owner verification and MFA precede provider access. The API keeps credentials server-side; entitled history, notes and virtual transactions stay in the authenticated session.</p><strong>Provider failures remain local</strong></div></div><p>Selection → source validation → eligible calculation → evidence → explanation. A selected company is separate from a successfully loaded dataset or a completed experiment.</p>');
 if(view==='data'){
  const f=ctx?.financial,rows=(f?.annual||[]).slice(0,4);
  return section('Trace the selected company to its filings','<p>'+safe(ctx?.name)+' · snapshot '+safe(ctx?.snapshot)+'. Each annual observation has its own fiscal end and source record; these dates are not interchangeable with market dates.</p>'+bars('Reported revenue by fiscal period',rows.map(r=>[r.fiscal_end,r.metrics.revenue_usd]),bn)+'<ol class="qf24-lineage"><li>SEC Company Facts: validate CIK, accession, filing date and units.</li><li>Select annual observations; retain missing metrics and negative cash flow.</li><li>Derive growth, margins and cash-flow proxy from compatible inputs.</li><li>Publish a deterministic snapshot; expose filing references in Explore and CSV.</li></ol><p>Amendments can change historical observations. A current snapshot alone is not a point-in-time backtest archive.</p>');
 }
 if(view==='engineering')return section('What the security boundary actually does','<div class="qf24-trust-grid"><div><h3>Browser → Pages proxy</h3><p>Same-origin requests, restrictive CSP hashes, escaped source strings and safe CSV cells. No provider credentials in browser assets.</p></div><div><h3>Proxy → FastAPI → Supabase / Alpaca</h3><p>Proxy secret, origin/action checks, verified owner and MFA, RLS, bounded histories and version-checked virtual state writes. No real-money order path.</p></div></div><p>Automated proof includes Python numerical/API tests, Node computation tests, deterministic CSP/privacy audits and isolated mocked-browser journeys. Real owner MFA, entitlements, persistence and deployment revisions need separate acceptance.</p>');
 return '';
}
root.QFExhibits24=Object.freeze({formula,bars,model,methods});
root.document?.addEventListener('click',e=>{
 if(e.target.closest('#qf24-walkforward-run')){
  const host=document.getElementById('qf24-walkforward-output'),button=e.target.closest('button');
  host.textContent='Loading aligned histories and evaluating rolling windows…';button.disabled=true;
  root.QFResearch20.walkforward().then(r=>{
   if(!host.isConnected)return;
   const first=r.windows[0],last=r.windows.at(-1);
   host.innerHTML='<p><strong>'+(r.origin==='market'?'PRIVATE · observed provider histories':'PUBLIC · synthetic historical experiment')+'</strong> · '+safe(r.symbols.join(', '))+' · '+r.windows.length+' disjoint test windows</p>'+bars('Out-of-sample cumulative change',[['Fitted minimum variance',r.optimized.metrics.change],['Equal-weight benchmark',r.benchmark.metrics.change]])+'<p>Training begins '+safe(first.trainingStart)+' and first ends '+safe(first.trainingEnd)+'. The first test begins '+safe(first.testStart)+'; the last ends '+safe(last.testEnd)+'. 5 bp modeled fee per dollar turned over; no dividends, spread or execution guarantee.</p><div class="table-wrap"><table><thead><tr><th>Training end</th><th>Next test start</th><th>Test end</th><th>Fitted weights</th></tr></thead><tbody>'+r.windows.map(w=>'<tr><td>'+safe(w.trainingEnd)+'</td><td>'+safe(w.testStart)+'</td><td>'+safe(w.testEnd)+'</td><td>'+w.weights.map((v,i)=>safe(r.symbols[i])+': '+pct(v)).join(' · ')+'</td></tr>').join('')+'</tbody></table></div><p>Minimum variance uses a fixed 20% diagonal shrinkage of off-diagonal covariances. This engine differs from the fixed single-company price filter above and the in-sample What If? allocation.</p>';
  }).catch(()=>{if(host.isConnected)host.textContent='Study unavailable. Use 2–5 eligible companies with enough common-date history, then run again.';}).finally(()=>{if(button.isConnected)button.disabled=false;});
  return;
 }
 if(!e.target.closest('#qf24-dcf-run'))return;
 const $=id=>document.getElementById(id),output=$('qf24-dcf-output');
 try{const v=root.QFResearchModelsCore22.dcfProxy(root.QFResearch20.context().financial,{growth:Number($('qf24-dcf-growth').value)/100,discount:Number($('qf24-dcf-discount').value)/100,terminal:Number($('qf24-dcf-terminal').value)/100});
  output.textContent=v.ready?'Hypothetical proxy PV: '+bn(v.proxy_pv)+' · terminal contribution '+pct(v.terminal_share)+'. No enterprise, equity or share-price value is implied.':v.reason;
 }catch(_){output.textContent='Use bounded rates and a discount rate strictly above terminal growth.';}
});
})(typeof window!=='undefined'?window:globalThis);
