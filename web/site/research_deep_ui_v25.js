/* Shared deep-result presentation. Inputs and imported optional evidence remain session-only. */
(function(root){
'use strict';
const $=id=>document.getElementById(id),safe=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=x=>Number.isFinite(x)?(100*x).toFixed(1)+'%':'Unavailable',num=x=>Number.isFinite(x)?x.toFixed(3):'Unavailable',usd=x=>Number.isFinite(x)?'$'+x.toLocaleString('en-US',{maximumFractionDigits:2}):'Unavailable';
const table=(heads,rows)=>'<div class="table-wrap"><table><thead><tr>'+heads.map(h=>'<th scope="col">'+safe(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(v=>'<td>'+safe(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
const bars=(title,rows,fmt=pct)=>root.QFExhibits24.bars(title,rows,fmt);
let archive=null,factors=null,sequence=0,cache=new Map(),chartSequence=0;const charts=new Map();
function stamp(){const c=root.QFResearch20.context();return [c.symbol,c.mode,c.revision,JSON.stringify(c.universe),JSON.stringify(c.weights)].join('|');}
function unavailable(r){return '<p class="qf25-unavailable">'+safe(r?.reason||'Eligible evidence is unavailable.')+'</p>';}
function curve(title,dates,lines){
 if(!dates?.length||!lines.length)return '';
 const width=Math.max(320,Math.min(760,root.innerWidth-(root.innerWidth>=800?340:60))),height=300,left=65,right=width-20,bottom=250,top=25;const chartId='qf25-chart-'+(++chartSequence);charts.set(chartId,{dates,lines,width,left,right,index:dates.length-1});if(charts.size>128)charts.delete(charts.keys().next().value);
 const values=lines.flatMap(l=>l.values),low=Math.min(...values),high=Math.max(...values),span=high-low||1;
 const x=i=>left+(right-left)*i/Math.max(1,dates.length-1),y=v=>bottom-(v-low)/span*(bottom-top);
 return '<figure class="qf24-figure"><figcaption>'+safe(title)+'</figcaption><svg data-qf25-chart="'+chartId+'" viewBox="0 0 '+width+' '+height+'" role="img" tabindex="0" aria-label="'+safe(title)+'">'+[0,.5,1].map(f=>'<text x="5" y="'+(bottom-f*(bottom-top))+'" font-size="13">'+safe((low+span*f).toFixed(1))+'</text><path d="M65 '+(bottom-f*(bottom-top))+'H'+right+'" stroke="#e0e4e9"/>').join('')+lines.map((l,j)=>'<path d="'+l.values.map((v,i)=>(i?'L':'M')+x(i).toFixed(1)+' '+y(v).toFixed(1)).join(' ')+'" fill="none" stroke="'+['#344b67','#9b6b45','#657d65'][j%3]+'" stroke-width="2.5"'+(j===1?' stroke-dasharray="6 4"':'')+'/>').join('')+'<text x="65" y="280" font-size="13">'+safe(dates[0])+'</text><text x="'+right+'" y="280" text-anchor="end" font-size="13">'+safe(dates.at(-1))+'</text></svg><p id="'+chartId+'-cursor" role="status">'+lines.map(l=>safe(l.name)+': '+num(l.values.at(-1))).join(' · ')+'</p></figure>';
}
function section(scope,title,description){
 const saved=cache.get(scope),content=saved?.stamp===stamp()?saved.html:'';
 return '<section class="pane qf25-panel"><h2>'+safe(title)+'</h2><p>'+safe(description)+'</p><button type="button" class="btn primary" data-qf25-run="'+scope+'">'+(scope==='factors'?'Analyze market sensitivity':scope==='data'?'Audit filing evidence':'Run research diagnostics')+'</button><div id="qf25-'+scope+'" class="qf25-output" aria-live="polite">'+content+'</div></section>';
}
function modelSection(category,phase){
 if(category==='risk')return section('factors','Market sensitivity and factor evidence','Compare this company with independently loaded broad-market and style ETF histories. This is historical co-movement, not a future return model.');
 if(category==='strategy')return section('strategy','Strategy stability and robustness','The original constrained optimizer, walk-forward, passive benchmark and leave-one-window-out diagnostics use the same evaluation dates.');
 if(category==='valuation')return section('valuation','Observed-price financial ratios','Authenticated quotes and dated SEC shares support observed market-cap multiples. Missing capital or stale inputs withhold ratios; this is separate from the hypothetical cash-flow model.')+'<section class="pane qf25-panel"><h2>Revenue and cash-generation scenarios</h2><p>Start from the selected company’s SEC annual revenue. Growth and cash-flow margin below are explicit assumptions, not estimates learned from future results.</p><div class="qf24-assumptions"><label>Assumed annual growth (%)<input id="qf25-growth" type="number" min="-30" max="40" value="6"></label><label>Assumed cash-flow margin (%)<input id="qf25-margin" type="number" min="-25" max="60" value="12"></label><button class="btn primary" id="qf25-forecast-run">Build scenarios</button></div><div id="qf25-forecast" aria-live="polite"></div></section>';
 return '';
}
function dataSection(){return section('data','Filing availability and revision diagnostics','Audit the selected research basket at historical decision dates. The current snapshot is not a complete archive of original filings.')+'<section class="pane"><h2>Optional independent evidence</h2><p>Routine research works without either file. These inputs are parsed locally in this browser session and are cleared on sign-out or data-mode changes. Schema validation does not independently authenticate a file as SEC or factor-library data.</p><label for="qf25-archive-file">SEC filing-revision archive JSON (optional, up to 5 MB)</label><input id="qf25-archive-file" type="file" accept=".json,application/json"><label for="qf25-factor-file">Extracted daily Fama–French three-factor CSV (optional, up to 2 MB)</label><input id="qf25-factor-file" type="file" accept=".csv,text/csv"><p id="qf25-import-status" role="status">No optional evidence loaded. ETF proxies are not official Fama–French factors.</p></section>';}
function peers(){
 const host=$('qf25-peers');if(!host)return;
 const c=root.QFResearch20.context(),broad=$('qf27-peer-scope')?.value==='all';
 const r=root.QFPublicSECPeers.compare(root.QFPublishedSEC,c.symbol,{sectorOnly:!broad});
 host.innerHTML='<p>Selected in Explore: <strong>'+safe(c.name)+' ('+safe(c.symbol)+')</strong></p>'+(r.ready?'<p>'+r.featureCount+' shared ratios · '+r.eligible+' eligible issuers · '+r.excluded+' excluded. '+safe(r.caution)+'</p>'+bars('Financial-profile distance (smaller = more similar)',r.peers.slice(0,6).map(p=>[p.symbol,p.distance]),num)+table(['Issuer','Fiscal year','Distance',...r.features.map(f=>f.label)],r.peers.slice(0,8).map(p=>[p.name,p.fiscalEnd||p.period||'See SEC source',num(p.distance),...r.indices.map(i=>num(p.values[i])+'%')]))+bars('Selected issuer versus nearest financial profile (percentage points)',r.indices.flatMap(i=>[[r.selected.symbol+' · '+root.QFPublicSECPeers.features[i].label,r.selected.values[i]],[r.peers[0].symbol+' · '+root.QFPublicSECPeers.features[i].label,r.peers[0].values[i]]]),x=>x.toFixed(1)+'%')+'<p>Selected fiscal end '+safe(r.selected.fiscalEnd)+'; nearest peer fiscal end '+safe(r.peers[0].fiscalEnd)+'. '+(r.groupFallback?'The same-industry sample was too small; the retained engine explicitly fell back to broader peers. ':'')+safe(r.message)+'</p>':unavailable(r));
}
function summary(packet){
 const R=packet.results,policy=R.policy;
 let html='<p><strong>'+(packet.origin==='market'?'Private historical observations':'Synthetic market-path experiment')+'</strong> · '+safe(packet.symbol)+'</p>';
 if(R.candidate.ready){const c=R.candidate;html+='<p>Historical downside: maximum drawdown '+pct(c.metrics.maxDrawdown)+', one-day tail-average loss '+pct(c.metrics.dailyES95)+'. These describe the loaded sample.</p>';}
 if(policy.ready){html+='<p>Evidence state: '+safe(policy.review.readiness)+'. '+safe(policy.assessment.reason)+'</p>'+table(['Method','Outcome','Scope'],policy.ledger.map(l=>[l.title,l.status,l.detail]));}
 if(packet.results.unified?.ready)html+=table(['Evidence domain','Status'],packet.results.unified.domains.map(d=>[d.name||d.key,d.status]));
 if(packet.results.comparative?.ready)html+='<h3>Research-screen sensitivity</h3>'+table(['Assumed risk screen','Evidence state'],packet.results.comparative.policies.rows.map(r=>[r.risk,r.readiness]))+'<p>'+safe(packet.results.comparative.policies.note)+'</p>';
 return html+'<p>No automatic trade or suitability decision follows from these screens. Open Models for evaluations and Methods → Data for filing-coverage diagnostics.</p>';
}
function strategy(packet){
 const R=packet.results,w=R.walkforward,r=R.robustness;
 let html=w.ready?curve('Rolling out-of-sample wealth (initial 10,000 virtual units)',w.dates,[{name:'Fitted allocation',values:w.optimized.wealth},{name:'Equal-weight rebalanced',values:w.benchmark.wealth}])+table(['Study','Change','Max drawdown','Fees (virtual units)'],[['Fitted allocation',pct(w.optimized.metrics.change),pct(w.optimized.metrics.maxDrawdown),usd(w.optimized.fees)],['Equal-weight rebalanced',pct(w.benchmark.metrics.change),pct(w.benchmark.metrics.maxDrawdown),usd(w.benchmark.fees)]]):unavailable(w);
 if(r.ready)html+=bars('Fixed diagnostic cases: historical active difference (percentage points)',r.strategyCases.map(c=>[c.label,c.activeDifferencePp]),x=>x.toFixed(2)+' pp')+'<p>Leave-one-window-out active spread: '+num(r.summary.looMinActivePp)+' to '+num(r.summary.looMaxActivePp)+' percentage points. '+(r.summary.windowDependentSign?'The sign changes when a window is removed.':'The sign is stable across these omitted-window diagnostics.')+'</p><p>'+r.warnings.map(safe).join(' ')+'</p>';
 else html+=unavailable(r);
 return html;
}
function factorResult(packet){
 const r=packet.results.proxy,f=packet.results.french;
 let html='';
 if(r.ready&&r.market.ready){const m=r.market;html=bars('Historical market and ETF-proxy loadings',[['Broad market '+m.benchmark,m.singleBeta],...(m.multi.ready?m.multi.coefficients.map((v,i)=>[m.multi.predictorLabels[i],v]):[])],num)+'<p>Single-market R² '+pct(m.singleR2)+' across '+m.observations+' aligned daily returns ('+safe(m.from)+' to '+safe(m.to)+'). '+(m.multi.ready?'Multi-proxy adjusted R² '+pct(m.multi.adjustedR2)+'.':safe(m.multi.reason))+'</p><p>'+r.limitations.map(safe).join(' ')+'</p>';}
 else html=unavailable(r.ready?r.market:r);
 html+='<h3>Independent daily FF3 study</h3>';
 if(f.ready)html+=table(['Coefficient','Estimate'],[['Daily alpha',num(f.model.alphaDaily)],...f.model.factorBetas.map((b,i)=>[['Market excess','SMB','HML'][i],num(b)])])+'<p>Aligned dates '+safe(f.from)+' to '+safe(f.to)+', '+f.aligned+' returns; holdout RMSE '+num(f.holdout.rmse)+' versus prior-mean baseline '+num(f.holdout.baselineRmse)+'. '+safe(f.holdout.interpretation)+'</p><p>'+f.limitations.map(safe).join(' ')+'</p>';
 else html+=unavailable(f)+'<p>Load an optional extracted daily factor CSV in Methods → Data. No upload is required for ETF-proxy analysis.</p>';
 return html;
}
function observedValue(packet){const r=packet.results.value;if(!r.ready)return unavailable(r);return table(['Observed quantity','Value','Source period'],[['Market cap (price × shares)',usd(r.marketCap),r.priceTime],['Price / annual revenue',num(r.pSales)+'×',r.fiscalEnd],['FCF-proxy yield',pct(r.fcfYield),r.fiscalEnd],['Reported share count',Number(r.shares).toLocaleString('en-US'),r.sharesTime]])+'<p>'+r.warnings.map(safe).join(' ')+'</p><p>'+r.limitations.map(safe).join(' ')+'</p>'; }
function portfolio(packet){
 const r=packet.results,o=r.optimization,s=r.simulation;
 let html=o.ready?bars('Constrained fitted weights',o.symbols.map((sym,i)=>[sym,o.chosen[i]]))+'<p>Fitted annual volatility '+pct(o.optimized.annualVolatility)+' versus equal weights '+pct(o.equal.annualVolatility)+'. This is an in-sample covariance fit, separate from the rolling evaluation in Models.</p>':unavailable(o);
 if(s.ready)html+=bars('21-session scenario value quantiles (initial 10,000 virtual units)',[['5th percentile',s.low],['Median',s.median],['95th percentile',s.high]],usd)+'<p>1,800 seeded paths. Scenario VaR '+usd(s.var95)+'; tail-average loss '+usd(s.es95)+'. '+safe(s.assumption)+'</p>';
 else html+=unavailable(s);
 return html;
}
function data(packet){
 const R=packet.results;
 let html=table(['Diagnostic','Eligible result?','Explanation'],['filing','coverage','archive','archiveQuality','historical','historicalRobustness','attribution','integrity'].map(key=>{const r=R[key];return [({filing:'Point-in-time replay',coverage:'Issuer filing coverage',archive:'Revision archive replay',archiveQuality:'Archive checkpoint quality',historical:'Common-window historical panel',historicalRobustness:'Fixed historical robustness',attribution:'Historical attribution',integrity:'Evidence integrity'})[key],r.ready?'Calculated':'Withheld',r.reason||r.interpretation||r.classification||'Inspect the scoped results below.'];}));
 const c=R.coverage;if(c.ready)html+=table(['Issuer','Scheduled windows','Eligible','Withheld','Coverage'],c.rows.map(r=>[r.symbol,r.scheduled,r.eligible,r.withheld,r.coveragePct+'%']))+'<p>'+c.limitations.map(safe).join(' ')+'</p>';
 const p=R.historical;if(p.ready)html+='<p>Historical filing coverage: '+p.coverage.complete+' complete of '+p.coverage.scheduled+' scheduled windows.</p>'+(p.performance.ready?table(['Filing-filtered rule','Same-window passive'],[[pct(p.performance.modelReturn),pct(p.performance.equalWeightReturn)]]):unavailable(p.performance));
 if(R.historicalRobustness.ready)html+='<p>'+safe(R.historicalRobustness.interpretation)+' '+R.historicalRobustness.eligibleScenarios+' / '+R.historicalRobustness.scenarioCount+' complete preset scenarios.</p>';
 if(R.attribution.ready)html+='<p>Attribution is calculated only from the complete filing-covered panel. '+safe(R.attribution.note||'All required windows passed the retained attribution guards.')+'</p>';
 if(R.integrity.ready)html+=table(['Integrity gate','Status','Evidence'],R.integrity.gates.map(g=>[g.key,g.status,g.detail]));
 return html;
}
async function execute(scope){
 const target=$('qf25-'+scope);if(!target)return;
 const token=++sequence,signature=stamp();target.textContent='Loading eligible inputs and running retained research engines…';
 try{
  const input=await root.QFResearch20.acquireStudy(scope);
  if(token!==sequence||signature!==stamp()||!target.isConnected)return;
  const packet=root.QFDeepResearch25.run({...input,archive,factors});
  const renderer={company:summary,strategy,factors:factorResult,portfolio,data,valuation:observedValue}[scope];
  const html='<p class="qf25-source">'+safe(input.history.source)+' · '+(input.history.dates.length?safe(input.history.dates[0])+' through '+safe(input.history.dates.at(-1)):'No historical-price path required for these ratios')+'</p>'+renderer(packet);
  cache.set(scope,{stamp:signature,html});target.innerHTML=html;
 }catch(_){if(token===sequence&&signature===stamp()&&target.isConnected)target.textContent='Research unavailable for these inputs. Check history coverage or provider access; SEC financials remain independent.';}
}
function clear(){sequence++;cache.clear();charts.clear();document.querySelectorAll('.qf25-output').forEach(n=>{if(n.textContent)n.textContent='Research context changed. Run this view again for the current inputs.';});peers();}
function inspectChart(svg,index){const c=charts.get(svg.dataset.qf25Chart);if(!c)return;c.index=Math.max(0,Math.min(c.dates.length-1,index));const cursor=$(svg.dataset.qf25Chart+'-cursor');if(cursor)cursor.textContent=c.dates[c.index]+' · '+c.lines.map(l=>l.name+': '+num(l.values[c.index])).join(' · ');}
document.addEventListener('pointermove',e=>{const svg=e.target.closest('svg[data-qf25-chart]');if(!svg)return;const c=charts.get(svg.dataset.qf25Chart);if(!c)return;const box=svg.getBoundingClientRect();inspectChart(svg,Math.round((((e.clientX-box.left)/box.width)*c.width-c.left)/(c.right-c.left)*(c.dates.length-1)));});
document.addEventListener('keydown',e=>{const svg=e.target.closest('svg[data-qf25-chart]'),c=svg&&charts.get(svg.dataset.qf25Chart);if(!c)return;const index=e.key==='ArrowLeft'?c.index-1:e.key==='ArrowRight'?c.index+1:e.key==='Home'?0:e.key==='End'?c.dates.length-1:null;if(index!==null){e.preventDefault();inspectChart(svg,index);}});
document.addEventListener('click',e=>{
 const run=e.target.closest('[data-qf25-run]');if(run)void execute(run.dataset.qf25Run);
 if(e.target.closest('#qf25-forecast-run')){
  const host=$('qf25-forecast'),ctx=root.QFResearch20.context();
  try{const r=root.QFPrivateForecast.run({symbol:ctx.symbol,name:ctx.name,annual:ctx.financial.annual},{growth:Number($('qf25-growth').value)/100,fcfMargin:Number($('qf25-margin').value)/100,years:5,discount:.10,terminal:.02});
   host.innerHTML='<p>Latest reported revenue baseline '+usd(r.baseRev)+' · reported cash-flow proxy margin '+pct(r.baseMargin)+'. The forward margin below is an explicit assumption, including any turnaround from a negative historical value.</p>'+curve('Assumed annual revenue after the latest reported fiscal year',r.scenarios[0].projection.map(p=>'Year '+p.year),r.scenarios.map(s=>({name:s.name,values:s.projection.map(p=>p.revenue/1e9)})))+'<p>Revenue chart units: USD billions. Baseline fiscal year '+safe(r.fiscalEnd)+'; assumed discount 10%, terminal growth 2%.</p>'+table(['Scenario','Annual growth','FCF margin','Year 5 revenue ($B)','Year 5 FCF proxy ($B)'],r.scenarios.map(s=>[s.name,pct(s.growth),pct(s.margin),(s.projection.at(-1).revenue/1e9).toFixed(2),s.projection.at(-1).fcf===null?'Unavailable':(s.projection.at(-1).fcf/1e9).toFixed(2)]))+'<p>The model retains missing cash-flow coverage and negative assumptions. These paths are scenarios, not a company forecast or equity value.</p>';
  }catch(_){host.textContent='At least two compatible reported annual revenues and bounded growth/margin assumptions are required.';}
 }
});
document.addEventListener('change',async e=>{
 if(e.target.id==='qf27-peer-scope')peers();
 if(!['qf25-archive-file','qf25-factor-file'].includes(e.target.id))return;
 const file=e.target.files?.[0],host=$('qf25-import-status'),signature=stamp();if(!file)return;
 if(e.target.id==='qf25-archive-file')archive=null;else factors=null;sequence++;cache.clear();document.querySelectorAll('.qf25-output').forEach(n=>{if(n.textContent)n.textContent='Independent evidence changed. Run this view again.';});
 try{
  const isArchive=e.target.id==='qf25-archive-file';if(file.size>(isArchive?5:2)*1024*1024)throw Error('Evidence file exceeds its size limit.');
  const text=await file.text();if(signature!==stamp()||!host.isConnected)return;
  if(isArchive){const value=JSON.parse(text),checked=root.QFPrivateArchivedSECValidationV99.validateArchive(value,root.QFPublishedSEC);if(!checked.ready)throw Error(checked.reason);archive=value;}
  else factors=root.QFPrivateFrenchFactorsV87.parseDailyCsv(text);
  sequence++;cache.clear();host.textContent=(archive?'Validated revision archive in session. ':'')+(factors?'Parsed independent factor CSV in session. ':'')+'Run the relevant audit or factor study to evaluate exact-date coverage.';
 }catch(e){host.textContent='Evidence not loaded: '+String(e.message||'Invalid file.').slice(0,180);}
});
root.addEventListener('qf:research-context',clear);root.addEventListener('qf:research-universe',clear);
root.addEventListener('qf:data-mode',()=>{archive=null;factors=null;for(const id of ['qf25-archive-file','qf25-factor-file'])if($(id))$(id).value='';if($('qf25-import-status'))$('qf25-import-status').textContent='Optional evidence cleared for this data mode.';clear();});
root.addEventListener('qf:owner-auth-ended',()=>{archive=null;factors=null;clear();});
root.addEventListener('qf:analyze-company',()=>void execute('company'));
root.addEventListener('qf:route-change',e=>{if(e.detail?.route==='compare')peers();});
const peerPanel=document.createElement('section');peerPanel.className='pane';peerPanel.innerHTML='<h2>Financial-profile peers</h2><p>Compare the selected company on the same reported ratio dimensions. This is descriptive similarity, never a stock ranking.</p><label for="qf27-peer-scope">Financial-profile peer universe</label><select id="qf27-peer-scope"><option value="industry">Same-industry financial peers</option><option value="all">All eligible SEC-covered companies</option></select><p>This choice changes only financial-profile peers, not your main Compare basket. Broader industries can have different accounting and business models.</p><div id="qf25-peers"></div>';$('page-compare').append(peerPanel);
const research=document.createElement('section');research.className='pane qf25-panel';research.innerHTML='<h2>Connected research evidence</h2><p>The company research action also runs eligible historical engines. Missing observations remain withheld.</p><div id="qf25-company" class="qf25-output" aria-live="polite">Analyze the selected company to assemble its research evidence.</div>';$('qf-v23-explore-content').insertBefore(research,$('qf24-notes'));
$('qf-v20-portfolio-analysis').insertAdjacentHTML('beforeend',section('portfolio','Allocation scenarios and sampled uncertainty','Compare fitted allocation risk with equal weights, then inspect an explicitly assumed 21-session Monte Carlo scenario.'));
root.QFDeepUI25=Object.freeze({modelSection,dataSection,execute,curve});peers();root.QFModelsMethods22?.refresh();
})(window);
