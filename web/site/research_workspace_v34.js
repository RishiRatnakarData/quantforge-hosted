/* Private Explore workflows inside the shared five-section navigation. Bounded discovery research; no account writes. */
(function(root){
'use strict';
const $=id=>document.getElementById(id),bridge=()=>root.QFPrivateBridgeV23,context=()=>root.QFResearch20.context();
const active=()=>bridge()?.ready()&&context().mode==='private';
const safe=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=v=>Number.isFinite(v)?(v*100).toFixed(1)+'%':'Unavailable',money=root.QFReadout29.money;
const date=v=>Number.isFinite(Date.parse(v))?new Date(v).toISOString().replace('T',' ').slice(0,16)+' UTC':'Unavailable';
let internalNavigation=false,task='home',wasPrivate=false,eligible=null,loading=false,failure='',generation=0,valuation=null,valuationVersion=null,selectedRules={},minGrowth=0,order='cashMargin',selected=new Set(),selectionKey='',refreshed=null;
const reports=new Map();
const host=document.createElement('section');host.id='qf34-briefing';host.className='qf34-briefing';$('qf-v23-explore-content').before(host);
const home=document.createElement('section');home.id='qf37-research-home';home.className='qf37-research-home';host.before(home);
home.innerHTML='<header><h1>Research</h1><p>Explore companies, evaluate financial evidence, and investigate investment opportunities.</p></header><div class="qf37-search"><label for="qf37-company-search">Search company name or ticker</label><input id="qf37-company-search" type="search" autocomplete="off" placeholder="Company name or ticker"><div id="qf37-company-options"></div></div><p id="qf37-selection-status" role="status" hidden></p><div class="qf37-choices"><section><h2>Analyze a company</h2><p>Review financials, valuation, historical risk and model evidence.</p><button type="button" class="btn primary" data-qf34-workspace="research">Analyze company</button></section><section><h2>Discover companies</h2><p>Screen eligible companies and research up to five financial matches.</p><button type="button" class="btn" data-qf34-workspace="discovery">Discover companies</button></section></div><details id="qf37-recent"><summary>Recent research and saved records</summary><div id="qf37-recent-content"></div></details><details class="qf37-advanced"><summary>Advanced research</summary><div class="qf27-action-row"><button type="button" class="btn" data-qf34-configure>Research conditions</button></div></details>';
const trail=document.createElement('nav');trail.id='qf38-explore-context';trail.setAttribute('aria-label','Explore research workflow');trail.innerHTML='<button type="button" class="btn" data-qf34-workspace="home">Back to Research</button><button type="button" class="btn" data-qf34-workspace="discovery">Discover companies</button>';$('qf-v23-explore-content').before(trail);
const notices=document.createElement('section');notices.id='qf37-portfolio-notices';notices.className='pane';$('qf-v20-portfolio-overview').prepend(notices);
const picker=root.QFInvestmentPicker27.mount({input:$('qf37-company-search'),panel:$('qf37-company-options'),mode:()=>context().mode,search:root.QFResearch20.searchAssets,published:root.QFPublishedSEC.companies,onSelect:asset=>{if(!active())return;choose('research');root.QFResearch20.chooseAsset(asset);root.QFExplore27?.show('brief');void root.QFResearch20.analyze();}});
const currentScreen=()=>eligible?root.QFDecision34.screen({snapshot:root.QFPublishedSEC,health:root.QFHealthSnapshot30,eligible,filters:{minGrowth,order}}):null;
const batch=root.QFCompanyStudy35.createBatch({
 valid:c=>active()&&generation===c.generation&&bridge().snapshot()?.version===c.ownerVersion,
 onChange:()=>{if(active()&&task==='discovery')render();},
 run:async(symbol,c,signal,analyzing)=>{
  const input=await root.QFResearch20.loadCompanyStudy(symbol,{signal});analyzing();
  return root.QFCompanyStudy35.study(input,{rules:c.rules,revision:c.key,preferences:{horizon:'long'}});
 }
});
function invalidate(){generation++;batch.cancel();reports.clear();}
function choose(next){
 if(!active())return;
 $('qf37-selection-status').hidden=true;$('qf37-selection-status').textContent='';
 task=next==='briefing'?'home':next;
 if(!['home','research','discovery','portfolio'].includes(task))task='home';
 internalNavigation=true;try{root.QFNavigate20(task==='portfolio'?'portfolio':'explore');}finally{internalNavigation=false;}sync();
 if(task==='home')$('qf37-company-search').focus({preventScroll:true});
}

async function research(symbol){
 if(!active())return;root.QFResearch20.choose(symbol);
 if(context().symbol!==symbol){choose('home');const status=$('qf37-selection-status');status.textContent='A company assessment could not be opened for '+symbol+'. Select an eligible company by name, or use Portfolio analysis for this holding.';status.hidden=false;return;}
 choose('research');root.QFExplore27?.show('brief');
 await root.QFResearch20.analyze();
}
const action=(symbol,label)=>'<button type="button" class="btn" '+(symbol?'data-qf34-symbol="'+safe(symbol)+'"':'data-qf34-workspace="research"')+'>'+safe(label)+'</button>';
function resultCard(item){
 if(!item)return '';
 const report=item.result?.report,p=report?.proposal,coverage=report?.researchCoverage||item.coverage;
 const state=coverage?.state||item.state;
 if(!report)return '<article class="qf35-result"><h3>'+safe(item.name)+' · '+safe(item.symbol)+'</h3><p class="qf35-status" role="status">'+safe(state)+'</p><p><strong>Research disposition:</strong> Withheld — no defensible assessment completed.</p>'+(item.reason?'<p>'+safe(item.reason)+'</p>':'')+'</article>';
 const caution=p.breaches[0]||coverage.gaps[0]?.detail||report.conflicts[0]||report.concerns[0]||'Risks beyond the covered evidence remain unknown.';
 return '<article class="qf35-result"><h3>'+safe(item.name)+' · '+safe(item.symbol)+'</h3><dl class="qf36-result-fields"><div><dt>Research coverage</dt><dd class="qf35-status" role="status">'+safe(state)+'</dd></div><div><dt>Research disposition</dt><dd>'+safe(p.label)+'</dd></div></dl><p><strong>Supporting observation:</strong> '+safe(report.favorable[0]||'No supported favorable observation.')+'</p><p>'+safe(p.reason)+'</p><p><strong>Main concern:</strong> '+safe(caution)+'</p><p class="tiny">Financial period '+safe(report.snapshot.financialPeriod||'unavailable')+' · market through '+safe(report.snapshot.marketThrough||'unavailable')+' · analyzed '+safe(date(report.snapshot.asOf))+'.</p><p><strong>Next:</strong> '+safe(report.next)+'</p>'+action(item.symbol,'Open full assessment')+'</article>';
}
function render(){
 if(!active())return;
 const whyOpen=Boolean($('qf36-selection-why')?.open),historyOpen=Boolean($('qf36-history')?.open);
 const drafts=Object.fromEntries([...host.querySelectorAll('[data-qf34-rule]')].map(f=>[f.dataset.qf34Rule,f.value])),assumptionsOpen=Boolean($('qf35-assumptions')?.open),filtersOpen=Boolean($('qf35-filters')?.open),focusKey=document.activeElement?.dataset?.qf35Select,focusRule=document.activeElement?.dataset?.qf34Rule,focusControl=['qf34-min-growth','qf34-order'].includes(document.activeElement?.id)?document.activeElement.id:null;
 const portfolio=bridge().snapshot(),marked=valuationVersion===portfolio.version?valuation:null;
 const summary=root.QFDecision34.briefing({portfolio,valuation:marked,notes:portfolio.notes,rules:selectedRules});
 const screen=currentScreen(),rows=batch.snapshot(),bySymbol=new Map(rows.map(r=>[r.symbol,r]));
 if(screen?.ready){const key=screen.shortlist.map(r=>r.symbol).join('|');if(key!==selectionKey){selectionKey=key;selected=new Set(screen.shortlist.slice(0,3).map(r=>r.symbol));}}
 const rules=[['maxWeight','Maximum position weight (%)',100,1,100,'The largest share of your dated marked account you want one name to represent.'],['maxDrawdown','Drawdown review boundary (%)',100,1,99,'A historical peak-to-trough loss that triggers review; future losses can be larger.'],['maxPfcf','Price / annual cash-flow ceiling (×)',1,1,500,'A valuation filter you choose, not an objectively correct fair price.'],['amount','Hypothetical addition ($)',1,1,1000000,'An assumed cash-funded addition; it does not prepare or submit a trade.'],['maxCorrelation','Maximum held-position correlation',1,0,1,'Historical co-movement ceiling; incomplete held-name coverage cannot pass this rule.']];
 notices.hidden=false;
 const alerts=summary.actions.filter(a=>['concentration','marks-missing','review-due'].includes(a.kind));
 notices.hidden=!alerts.length;
 notices.innerHTML=alerts.length?'<h2>Account review</h2>'+alerts.map(a=>'<article><h3>'+safe(a.label)+(a.symbol?' · '+safe(a.symbol):'')+'</h3><p>'+safe(a.detail)+'</p>'+(a.symbol?action(a.symbol,'Open assessment'):'')+'</article>').join(''):'';
 let shortlist='<p id="qf34-universe-status" role="status">'+safe(loading?'Loading the owner-authorized eligible universe…':failure||(screen?.ready?'Financial screen ready.':'Research metadata has not been loaded.'))+'</p>';
 if(screen?.ready){
  shortlist+='<p id="qf36-order-description">These companies passed the selected financial-health filters. Ordered by <strong>'+safe({cashMargin:'cash-flow proxy margin',growth:'annual revenue growth',margin:'operating margin'}[screen.order])+'</strong>, highest first—not predicted stock performance. Deeper research checks valuation, risk and portfolio fit.</p><p><strong>'+screen.eligibleCount+' eligible covered issuers</strong> · '+screen.passed+' pass the financial filters. Filters require positive operating profit and cash generation, matching annual sources and financials within 550 days. Inspect exclusions below.</p>';
  shortlist+='<div class="qf35-batch-actions"><button type="button" class="btn primary" id="qf35-analyze-shortlist" '+(!selected.size||batch.busy()?'disabled':'')+'>Analyze selected companies</button><span>'+selected.size+' selected · maximum 5 · sequential studies</span>'+(batch.busy()?'<button type="button" class="btn" id="qf35-cancel-batch">Cancel pending research</button>':'')+'</div><p class="tiny">Three selected by default. Choose up to five, then analyze them using the same rules as individual research.</p>';
  shortlist+='<div class="qf34-shortlist">'+(screen.shortlist.length?screen.shortlist.map(r=>'<article><label class="qf35-selection"><input type="checkbox" data-qf35-select="'+safe(r.symbol)+'" '+(selected.has(r.symbol)?'checked':'')+' '+(batch.busy()?'disabled':'')+'>Include '+safe(r.symbol)+' in batch</label><h3>'+safe(r.name)+' <span class="tiny">'+safe(r.symbol)+'</span></h3><dl><div><dt>Annual revenue growth</dt><dd>'+pct(r.growth)+'</dd></div><div><dt>Operating margin</dt><dd>'+pct(r.margin)+'</dd></div><div><dt>Cash-flow proxy / revenue</dt><dd>'+pct(r.cashMargin)+'</dd></div></dl>'+ '<p class="tiny">Why it passed: positive operating profit and cash generation; growth meets your '+pct(screen.conditions.minGrowth)+' minimum. Financial period '+safe(r.fiscalEnd)+'.</p><p class="tiny">Market-price / valuation research: '+safe(bySymbol.get(r.symbol)?.result?.report?.researchCoverage?.state||bySymbol.get(r.symbol)?.coverage?.state||bySymbol.get(r.symbol)?.state||'Not analyzed in this batch')+'.</p>'+action(r.symbol,'Research individually')+'</article>').join(''):'<p>No companies meet these filters. Zero candidates is a valid result; change a filter deliberately or choose an investment directly.</p>')+'</div>';
  shortlist+='<details id="qf36-selection-why"><summary>Why these companies?</summary><p>'+safe(screen.explanation)+'</p><p>Requires growth at or above your selected minimum, positive operating margin and operating cash flow minus capital spending, compatible annual filing sources, and financials within 550 days. Negative reported equity and anomalous margins above 100% are excluded. The top five are financial matches, not the best five investments.</p><p>Investment-policy performance is not established. Correct calculations and held-out model diagnostics do not demonstrate that this shortlist earns superior returns. A valid historical policy test needs original as-of filings, listing changes and delisted names; the current snapshot is insufficient.</p><p>'+safe(eligible.scope)+' '+safe(eligible.limitations)+'</p><p>Financial extraction '+safe(eligible.financial_cutoff)+' · eligibility response '+safe(date(eligible.eligibility_checked_at))+'. Listing metadata uses an hourly provider cache.</p><p>'+eligible.items.map(r=>safe(r.name)+' ('+safe(r.symbol)+')').join(' · ')+'</p><h3>Financial exclusions</h3><ul>'+screen.excluded.map(r=>'<li>'+safe(r.symbol)+': '+safe(r.reason)+'</li>').join('')+'</ul><h3>Listing exclusions</h3><ul>'+(eligible.excluded||[]).map(r=>'<li>'+safe(r.symbol)+': '+safe(r.reason)+'</li>').join('')+'</ul></details>';
 }
 const recent=[...reports.values(),...rows.filter(r=>r.result).map(r=>r.result.report)].filter(r=>r.snapshot.ownerVersion===portfolio.version);
 const unique=[...new Map(recent.sort((a,b)=>Date.parse(a.snapshot.asOf)-Date.parse(b.snapshot.asOf)).map(r=>[r.snapshot.symbol,r])).values()].sort((a,b)=>Date.parse(a.snapshot.asOf)-Date.parse(b.snapshot.asOf));
 host.innerHTML='<header><button type="button" class="btn" data-qf34-workspace="home">Back to Research</button><h1>Discover companies</h1><p>Find financial-screen candidates, then investigate their valuation, risk and portfolio fit.</p></header><section class="pane" id="qf35-opportunities"><h2>Companies worth investigating</h2><details id="qf35-filters"><summary>Adjust financial filters</summary><div class="qf34-controls"><label>Minimum annual revenue growth (%)<input id="qf34-min-growth" type="number" min="-50" max="200" step="1" value="'+safe(minGrowth*100)+'"></label><label>Order financial matches by<select id="qf34-order"><option value="cashMargin">Cash-flow proxy / revenue</option><option value="growth">Annual revenue growth</option><option value="margin">Operating margin</option></select></label></div></details>'+shortlist+'</section>'+(rows.length?'<section class="pane" id="qf36-results"><h2>Research results</h2><p class="tiny">Coverage describes available evidence; disposition describes the research judgment.</p><div class="qf36-results">'+rows.map(resultCard).join('')+'</div></section>':'')+'<details class="pane" id="qf36-history"><summary>Recent research and saved records</summary><p>'+portfolio.notes.length+' saved research records'+(summary.savedTheses?' · '+summary.savedTheses+' current thesis threads':'')+'. Calculated assessments below remain session snapshots; changing account, source universe or assumptions invalidates them.</p><div id="qf34-reviewed">'+(unique.map(r=>'<article><h3>'+safe(r.snapshot.symbol)+' · '+safe(r.proposal.label)+'</h3><p class="tiny">Analyzed '+safe(date(r.snapshot.asOf))+' · market through '+safe(r.snapshot.marketThrough||'unavailable')+'</p>'+action(r.snapshot.symbol,'Reopen research')+'</article>').join('')||'<p>No individual assessments calculated in this session yet.</p>')+'</div></details><details class="pane qf35-assumptions" id="qf35-assumptions"><summary>Research assumptions (optional)</summary><p>Longer-term business, value and portfolio evidence guide the default review. Five-session prediction remains an experiment. Empty controls imply no personal risk or suitability assumptions.</p><form id="qf34-rules"><div class="qf34-controls">'+rules.map(([key,label,scale,min,max,why])=>'<label>'+label+'<small>'+why+'</small><input data-qf34-rule="'+key+'" type="number" min="'+min+'" max="'+max+'" step="any" value="'+safe(drafts[key]??(Number.isFinite(selectedRules[key])?selectedRules[key]*scale:''))+'"></label>').join('')+'</div><button class="btn" type="submit">Apply research conditions</button><p id="qf34-rule-status" role="status"></p></form><p class="tiny">Assumptions stay in this tab and clear on Private mode exit. An illustrative addition is separate from the existing server-verified virtual transaction preview and confirmation.</p></details>';
 $('qf37-recent-content').innerHTML='<p>'+portfolio.notes.length+' saved research records. Open a company to inspect its notes.</p>'+unique.slice(-5).reverse().map(r=>'<p>'+safe(r.snapshot.symbol)+' · '+safe(r.proposal.label)+' · '+safe(date(r.snapshot.asOf))+' '+action(r.snapshot.symbol,'Open assessment')+'</p>').join('');
 if($('qf34-order'))$('qf34-order').value=order;
 if(whyOpen&&$('qf36-selection-why'))$('qf36-selection-why').open=true;
 if(historyOpen)$('qf36-history').open=true;
 if(assumptionsOpen)$('qf35-assumptions').open=true;
 if(filtersOpen&&$('qf35-filters'))$('qf35-filters').open=true;
 if(focusRule)[...host.querySelectorAll('[data-qf34-rule]')].find(f=>f.dataset.qf34Rule===focusRule)?.focus({preventScroll:true});
 if(focusControl)$(focusControl)?.focus({preventScroll:true});
 if(focusKey){const field=[...host.querySelectorAll('[data-qf35-select]')].find(f=>f.dataset.qf35Select===focusKey);field?.focus({preventScroll:true});}
}
async function loadUniverse(){
 if(!active()||loading||eligible)return;loading=true;failure='';const token=generation;render();
 try{const result=await bridge().universe();if(token!==generation||!active())return;if(result?.schema!=='quantforge.research-universe.v34'||result.licensed_private!==true||!Array.isArray(result.items))throw Error('Invalid universe.');eligible=result;refreshed=result.eligibility_checked_at||new Date().toISOString();}
 catch(_){if(token===generation&&active())failure='The eligible universe is unavailable. Existing individual research remains available; no substitute ranking is generated.';}
 finally{if(token===generation){loading=false;render();}}
}
function sync(){
 const enabled=active();trail.hidden=true;document.body.classList.toggle('qf37-private',Boolean(enabled));$('qf-v20-navigation').setAttribute('aria-label','QuantForge research sections');
 if(!enabled){if(wasPrivate){invalidate();eligible=null;loading=false;failure='';selectedRules={};valuation=null;valuationVersion=null;selected.clear();selectionKey='';refreshed=null;task='home';}host.hidden=true;host.replaceChildren();home.hidden=true;$('qf37-selection-status').hidden=true;$('qf37-selection-status').textContent='';$('qf37-recent-content').replaceChildren();notices.hidden=true;notices.replaceChildren();picker.reset();$('qf37-company-search').value='';wasPrivate=false;$('qf-v23-explore-content').hidden=Boolean(root.QFUnifiedPrivate23?.state?.().landing);return;}
 if(!wasPrivate){task='home';wasPrivate=true;if(!$('page-explore').classList.contains('active')){root.QFNavigate20('explore');return;}}
 const explore=$('page-explore').classList.contains('active');trail.hidden=!explore||task!=='research';host.hidden=!explore||task!=='discovery';home.hidden=!explore||task!=='home';
 if(explore){$('qf-v23-landing').hidden=true;$('qf-v23-explore-content').hidden=task!=='research';document.body.classList.remove('qf31-home-active');}
 render();if(task==='discovery'&&!eligible&&!loading&&!failure)void loadUniverse();
}
document.addEventListener('click',event=>{
 if(!active())return;
 if(event.target.closest('[data-qf34-configure]')){event.preventDefault();choose('discovery');$('qf35-assumptions').open=true;$('qf34-rules').scrollIntoView({block:'center'});$('qf34-rules').querySelector('input').focus();return;}
 const target=event.target.closest('[data-qf34-workspace]');if(target){choose(target.dataset.qf34Workspace);return;}
 if(event.target.closest('[data-qf-v23-open="notes"]')){choose('research');root.QFExplore27?.show('research');return;}
 const symbol=event.target.closest('[data-qf34-symbol]')?.dataset.qf34Symbol;if(symbol){void research(symbol);return;}
 if(event.target.closest('[data-qf34-refresh]')){invalidate();eligible=null;failure='';selectionKey='';void loadUniverse();return;}
 if(event.target.closest('#qf35-cancel-batch')){batch.cancel();return;}
 if(event.target.closest('#qf35-analyze-shortlist')){const screen=currentScreen(),candidates=screen?.shortlist.filter(r=>selected.has(r.symbol))||[];if(!candidates.length)return;const c={generation,ownerVersion:bridge().snapshot().version,rules:{...selectedRules},key:'batch-'+generation+'-'+Date.now()};void batch.start(candidates,c);return;}
});
$('qf-v23-home-button').addEventListener('click',()=>{if(active())choose('home');});
host.addEventListener('change',event=>{
 const symbol=event.target.dataset.qf35Select;if(symbol){if(event.target.checked)selected.add(symbol);else selected.delete(symbol);render();return;}
 if(event.target.id==='qf34-min-growth'){const n=Number(event.target.value);if(Number.isFinite(n)&&n>=-50&&n<=200){invalidate();minGrowth=n/100;selectionKey='';render();}}
 if(event.target.id==='qf34-order'){invalidate();order=event.target.value;selectionKey='';render();}
});
host.addEventListener('submit',event=>{if(event.target.id!=='qf34-rules')return;event.preventDefault();const raw={};for(const field of host.querySelectorAll('[data-qf34-rule]')){const scale=['maxWeight','maxDrawdown'].includes(field.dataset.qf34Rule)?100:1;raw[field.dataset.qf34Rule]=field.value===''?null:Number(field.value)/scale;}const result=root.QFDecision34.policy(raw);if(result.errors.length){$('qf34-rule-status').textContent=result.errors.join(' ');return;}invalidate();selectedRules=raw;root.dispatchEvent(new Event('qf:research-rules'));render();$('qf35-assumptions').open=true;$('qf34-rule-status').textContent='Research conditions applied in this tab. No account records were changed.';});
root.addEventListener('qf:canonical-assessment',event=>{const {report,reviewed}=event.detail||{};if(!active()||!reviewed||report?.snapshot?.ownerVersion!==bridge().snapshot()?.version)return;reports.set(report.snapshot.symbol,report);render();});
root.addEventListener('qf:owner-valuation',event=>{if(!active()||event.detail?.version!==bridge().snapshot()?.version)return;valuation=event.detail.snapshot;valuationVersion=event.detail.version;render();});
root.addEventListener('qf:owner-state',()=>{invalidate();valuation=null;valuationVersion=null;sync();});
root.addEventListener('qf:research-universe',()=>{if(active()){invalidate();render();}});
for(const name of ['qf:research-context','qf:data-mode','qf:owner-auth-ready','qf:owner-auth-ended'])root.addEventListener(name,sync);
root.addEventListener('qf:route-change',event=>{if(event.detail?.route==='portfolio')task='portfolio';else if(['compare','models','methods'].includes(event.detail?.route))task='research';else if(event.detail?.route==='explore'&&!internalNavigation)task='home';sync();});
function legacyRoute(){if(active()&&/^#(?:briefing|research|discover|private\/(?:briefing|research|discover))$/.test(location.hash)){const discovery=location.hash.endsWith('discover');history.replaceState(null,'','#explore');choose(discovery?'discovery':'home');}}
root.addEventListener('qf:owner-auth-ready',legacyRoute);root.addEventListener('hashchange',legacyRoute);root.addEventListener('popstate',()=>{if(active()&&location.hash==='#explore')choose('home');legacyRoute();});
root.QFWorkspace34=Object.freeze({rules:()=>({...selectedRules}),choose,research});sync();legacyRoute();
})(window);
