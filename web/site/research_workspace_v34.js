/* Three owner tasks. Bounded discovery research; no account writes. */
(function(root){
'use strict';
const $=id=>document.getElementById(id),bridge=()=>root.QFPrivateBridgeV23,context=()=>root.QFResearch20.context();
const active=()=>bridge()?.ready()&&context().mode==='private';
const safe=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=v=>Number.isFinite(v)?(v*100).toFixed(1)+'%':'Unavailable',money=root.QFReadout29.money;
const date=v=>Number.isFinite(Date.parse(v))?new Date(v).toISOString().replace('T',' ').slice(0,16)+' UTC':'Unavailable';
let task='briefing',wasPrivate=false,eligible=null,loading=false,failure='',generation=0,valuation=null,valuationVersion=null,selectedRules={},minGrowth=0,order='cashMargin',selected=new Set(),selectionKey='',refreshed=null;
const reports=new Map();
const nav=document.createElement('nav');nav.id='qf34-workspace-nav';nav.setAttribute('aria-label','Private workspace tasks');
nav.innerHTML=[['briefing','My Briefing'],['research','Research an Investment'],['portfolio','My Portfolio']].map(([key,label])=>'<button type="button" class="btn" data-qf34-workspace="'+key+'">'+label+'</button>').join('');
$('qf24-mode-bar').after(nav);
const host=document.createElement('section');host.id='qf34-briefing';host.className='qf34-briefing';$('qf-v23-explore-content').before(host);
const currentScreen=()=>eligible?root.QFDecision34.screen({snapshot:root.QFPublishedSEC,health:root.QFHealthSnapshot30,eligible,filters:{minGrowth,order}}):null;
const batch=root.QFCompanyStudy35.createBatch({
 valid:c=>active()&&generation===c.generation&&bridge().snapshot()?.version===c.ownerVersion,
 onChange:()=>{if(active()&&task==='briefing')render();},
 run:async(symbol,c,signal,analyzing)=>{
  const input=await root.QFResearch20.loadCompanyStudy(symbol,{signal});analyzing();
  return root.QFCompanyStudy35.study(input,{rules:c.rules,revision:c.key,preferences:{horizon:'long'}});
 }
});
function invalidate(){generation++;batch.cancel();reports.clear();}
function choose(next){if(!active())return;task=next;root.QFNavigate20(next==='portfolio'?'portfolio':'explore');sync();}
async function research(symbol){
 if(!active())return;choose('research');root.QFResearch20.choose(symbol);root.QFExplore27?.show('brief');
 await root.QFResearch20.analyze();
}
const action=(symbol,label)=>'<button type="button" class="btn" '+(symbol?'data-qf34-symbol="'+safe(symbol)+'"':'data-qf34-workspace="research"')+'>'+safe(label)+'</button>';
function resultCard(item){
 if(!item)return '';
 const report=item.result?.report,p=report?.proposal,coverage=report?.researchCoverage||item.coverage;
 const state=coverage?.state||item.state;
 if(!report)return '<article class="qf35-result"><h3>'+safe(item.name)+' · '+safe(item.symbol)+'</h3><p class="qf35-status" role="status">'+safe(state)+'</p><p><strong>Research disposition:</strong> Withheld — no defensible assessment completed.</p>'+(item.reason?'<p>'+safe(item.reason)+'</p>':'')+'</article>';
 const caution=p.breaches[0]||coverage.gaps[0]?.detail||report.conflicts[0]||report.concerns[0]||'Risks beyond the covered evidence remain unknown.';
 return '<article class="qf35-result"><h3>'+safe(item.name)+' · '+safe(item.symbol)+'</h3><dl class="qf36-result-fields"><div><dt>Research coverage</dt><dd class="qf35-status" role="status">'+safe(state)+'</dd></div><div><dt>Research disposition</dt><dd>'+safe(p.label)+'</dd></div></dl><p>'+safe(p.reason)+'</p><p><strong>Main concern:</strong> '+safe(caution)+'</p><p class="tiny">Financial period '+safe(report.snapshot.financialPeriod||'unavailable')+' · market through '+safe(report.snapshot.marketThrough||'unavailable')+' · analyzed '+safe(date(report.snapshot.asOf))+'.</p><p><strong>Next:</strong> '+safe(report.next)+'</p>'+action(item.symbol,'Open full assessment')+'</article>';
}
function portfolioPanel(portfolio,marked){
 const positions=Object.entries(portfolio.holdings||{}).filter(([,u])=>u>0);
 const dates=(marked?.quotes||[]).map(q=>q.timestamp).filter(Boolean).sort();
 let body='<p>'+positions.length+' saved positions · available virtual cash '+safe(money(portfolio.cash))+'.</p>';
 if(marked){
  body+='<p>Marked value <strong>'+safe(money(marked.total_value))+'</strong> · invested value '+safe(money(marked.holdings_value))+'. Quote observations '+safe(date(dates[0]))+' to '+safe(date(dates.at(-1)))+'.</p>';
  const rows=[...(marked.quotes||[]).slice().sort((a,b)=>b.market_value-a.market_value).slice(0,5).map(q=>[q.symbol,q.market_value]),['Cash',marked.cash]];
  if(rows.length>1)body+=root.QFExhibits24.bars('Dated virtual holdings and cash (USD)',rows,money);
  body+='<p class="tiny">Dated marks describe exposure, not transaction permission or future returns. Missing legacy basis remains unavailable; review full accounting in My Portfolio.</p>';
 }else body+='<p>Current exposure and portfolio value need complete dated marks. Saved units and cash do not establish gain or diversification.</p>';
 return '<section class="pane"><h2>Your portfolio</h2>'+body+'<button type="button" class="btn" data-qf34-workspace="portfolio">Open My Portfolio</button></section>';
}
function render(){
 if(!active())return;
 const whyOpen=Boolean($('qf36-selection-why')?.open),historyOpen=Boolean($('qf36-history')?.open);
 const drafts=Object.fromEntries([...host.querySelectorAll('[data-qf34-rule]')].map(f=>[f.dataset.qf34Rule,f.value])),assumptionsOpen=Boolean($('qf35-assumptions')?.open),filtersOpen=Boolean($('qf35-filters')?.open),focusKey=document.activeElement?.dataset?.qf35Select;
 const portfolio=bridge().snapshot(),marked=valuationVersion===portfolio.version?valuation:null;
 const summary=root.QFDecision34.briefing({portfolio,valuation:marked,notes:portfolio.notes,rules:selectedRules});
 const screen=currentScreen(),rows=batch.snapshot(),bySymbol=new Map(rows.map(r=>[r.symbol,r]));
 if(screen?.ready){const key=screen.shortlist.map(r=>r.symbol).join('|');if(key!==selectionKey){selectionKey=key;selected=new Set(screen.shortlist.slice(0,3).map(r=>r.symbol));}}
 const rules=[['maxWeight','Maximum position weight (%)',100,1,100,'The largest share of your dated marked account you want one name to represent.'],['maxDrawdown','Drawdown review boundary (%)',100,1,99,'A historical peak-to-trough loss that triggers review; future losses can be larger.'],['maxPfcf','Price / annual cash-flow ceiling (×)',1,1,500,'A valuation filter you choose, not an objectively correct fair price.'],['amount','Hypothetical addition ($)',1,1,1000000,'An assumed cash-funded addition; it does not prepare or submit a trade.'],['maxCorrelation','Maximum held-position correlation',1,0,1,'Historical co-movement ceiling; incomplete held-name coverage cannot pass this rule.']];
 const priorities=summary.actions.slice(0,3).map(a=>'<article><h3>'+safe(a.label)+(a.symbol?' · '+safe(a.symbol):'')+'</h3><p>'+safe(a.detail)+'</p>'+(a.kind==='marks-missing'?'<button type="button" class="btn" data-qf34-workspace="portfolio">Inspect portfolio marks</button>':a.kind==='rules-missing'?'<button type="button" class="btn" data-qf34-configure>Choose research assumptions</button>':action(a.symbol,'Investigate'))+'</article>').join('')||'<p>No review alerts from the currently covered portfolio and saved thesis dates.</p>';
 let shortlist='<p id="qf34-universe-status" role="status">'+safe(loading?'Loading the owner-authorized eligible universe…':failure||(screen?.ready?'Financial screen ready.':'Research metadata has not been loaded.'))+'</p>';
 if(screen?.ready){
  shortlist+='<p id="qf36-order-description">These companies passed the selected financial-health filters. Ordered by <strong>'+safe({cashMargin:'cash-flow proxy margin',growth:'annual revenue growth',margin:'operating margin'}[screen.order])+'</strong>, highest first—not predicted stock performance. Deeper research checks valuation, risk and portfolio fit.</p><p><strong>'+screen.eligibleCount+' eligible covered issuers</strong> · '+screen.passed+' pass the financial filters. Filters require positive operating profit and cash generation, matching annual sources and financials within 550 days. Inspect exclusions below.</p>';
  shortlist+='<div class="qf35-batch-actions"><button type="button" class="btn primary" id="qf35-analyze-shortlist" '+(!selected.size||batch.busy()?'disabled':'')+'>Analyze selected companies</button><span>'+selected.size+' selected · maximum 5 · sequential studies</span>'+(batch.busy()?'<button type="button" class="btn" id="qf35-cancel-batch">Cancel pending research</button>':'')+'</div><p class="tiny">Three selected by default. Choose up to five, then analyze them using the same rules as individual research.</p>';
  shortlist+='<div class="qf34-shortlist">'+(screen.shortlist.length?screen.shortlist.map(r=>'<article><label class="qf35-selection"><input type="checkbox" data-qf35-select="'+safe(r.symbol)+'" '+(selected.has(r.symbol)?'checked':'')+' '+(batch.busy()?'disabled':'')+'>Include '+safe(r.symbol)+' in batch</label><h3>'+safe(r.name)+' <span class="tiny">'+safe(r.symbol)+'</span></h3><dl><div><dt>Annual revenue growth</dt><dd>'+pct(r.growth)+'</dd></div><div><dt>Operating margin</dt><dd>'+pct(r.margin)+'</dd></div><div><dt>Cash-flow proxy / revenue</dt><dd>'+pct(r.cashMargin)+'</dd></div></dl>'+ '<p class="tiny">Why it passed: positive operating profit and cash generation; growth meets your '+pct(screen.conditions.minGrowth)+' minimum. Financial period '+safe(r.fiscalEnd)+'.</p><p class="tiny">Market-price / valuation research: '+safe(bySymbol.get(r.symbol)?.result?.report?.researchCoverage?.state||bySymbol.get(r.symbol)?.coverage?.state||bySymbol.get(r.symbol)?.state||'Not analyzed in this batch')+'.</p>'+action(r.symbol,'Research individually')+'</article>').join(''):'<p>No companies meet these filters. Zero candidates is a valid result; change a filter deliberately or choose an investment directly.</p>')+'</div>';
  shortlist+='<details id="qf36-selection-why"><summary>Why these companies?</summary><p>'+safe(screen.explanation)+'</p><p>Requires growth at or above your selected minimum, positive operating margin and operating cash flow minus capital spending, compatible annual filing sources, and financials within 550 days. Negative reported equity and anomalous margins above 100% are excluded. The top five are financial matches, not the best five investments.</p><p>Investment-policy performance is not established. Correct calculations and held-out model diagnostics do not demonstrate that this shortlist earns superior returns. A valid historical policy test needs original as-of filings, listing changes and delisted names; the current snapshot is insufficient.</p><p>'+safe(eligible.scope)+' '+safe(eligible.limitations)+'</p><p>Financial extraction '+safe(eligible.financial_cutoff)+' · eligibility response '+safe(date(eligible.eligibility_checked_at))+'. Listing metadata uses an hourly provider cache.</p><p>'+eligible.items.map(r=>safe(r.name)+' ('+safe(r.symbol)+')').join(' · ')+'</p><h3>Financial exclusions</h3><ul>'+screen.excluded.map(r=>'<li>'+safe(r.symbol)+': '+safe(r.reason)+'</li>').join('')+'</ul><h3>Listing exclusions</h3><ul>'+(eligible.excluded||[]).map(r=>'<li>'+safe(r.symbol)+': '+safe(r.reason)+'</li>').join('')+'</ul></details>';
 }
 const recent=[...reports.values(),...rows.filter(r=>r.result).map(r=>r.result.report)].filter(r=>r.snapshot.ownerVersion===portfolio.version);
 const unique=[...new Map(recent.map(r=>[r.snapshot.symbol,r])).values()];
 host.innerHTML='<header><p class="qf33-kicker">PRIVATE · AUTHENTICATED RESEARCH</p><h1>My Briefing</h1><p>Evidence refreshed '+safe(date(refreshed))+'. Research runs on demand; this is not continuous monitoring.</p></header><section class="pane"><h2>What deserves attention</h2><div class="qf34-priorities">'+priorities+'</div><div class="qf27-action-row"><button type="button" class="btn" data-qf34-refresh>Refresh research metadata</button><button type="button" class="btn" data-qf34-workspace="research">Research an Investment</button></div></section><section class="pane" id="qf35-opportunities"><h2>Companies worth investigating</h2><details id="qf35-filters"><summary>Adjust financial filters</summary><div class="qf34-controls"><label>Minimum annual revenue growth (%)<input id="qf34-min-growth" type="number" min="-50" max="200" step="1" value="'+safe(minGrowth*100)+'"></label><label>Order financial matches by<select id="qf34-order"><option value="cashMargin">Cash-flow proxy / revenue</option><option value="growth">Annual revenue growth</option><option value="margin">Operating margin</option></select></label></div></details>'+shortlist+'</section>'+(rows.length?'<section class="pane" id="qf36-results"><h2>Research results</h2><p class="tiny">Coverage describes available evidence; disposition describes the research judgment.</p><div class="qf36-results">'+rows.map(resultCard).join('')+'</div></section>':'')+portfolioPanel(portfolio,marked)+'<details class="pane" id="qf36-history"><summary>Recent research and saved records</summary><p>'+portfolio.notes.length+' saved research records'+(summary.savedTheses?' · '+summary.savedTheses+' current thesis threads':'')+'. Calculated assessments below remain session snapshots; changing account, source universe or assumptions invalidates them.</p><div id="qf34-reviewed">'+(unique.map(r=>'<article><h3>'+safe(r.snapshot.symbol)+' · '+safe(r.proposal.label)+'</h3><p class="tiny">Analyzed '+safe(date(r.snapshot.asOf))+' · market through '+safe(r.snapshot.marketThrough||'unavailable')+'</p>'+action(r.snapshot.symbol,'Reopen research')+'</article>').join('')||'<p>No individual assessments calculated in this session yet.</p>')+'</div></details><details class="pane qf35-assumptions" id="qf35-assumptions"><summary>Research assumptions (optional)</summary><p>Longer-term business, value and portfolio evidence guide the default review. Five-session prediction remains an experiment. Empty controls imply no personal risk or suitability assumptions.</p><form id="qf34-rules"><div class="qf34-controls">'+rules.map(([key,label,scale,min,max,why])=>'<label>'+label+'<small>'+why+'</small><input data-qf34-rule="'+key+'" type="number" min="'+min+'" max="'+max+'" step="any" value="'+safe(drafts[key]??(Number.isFinite(selectedRules[key])?selectedRules[key]*scale:''))+'"></label>').join('')+'</div><button class="btn" type="submit">Apply research conditions</button><p id="qf34-rule-status" role="status"></p></form><p class="tiny">Assumptions stay in this tab and clear on Private mode exit. An illustrative addition is separate from the existing server-verified virtual transaction preview and confirmation.</p></details>';
 if($('qf34-order'))$('qf34-order').value=order;
 if(whyOpen&&$('qf36-selection-why'))$('qf36-selection-why').open=true;
 if(historyOpen)$('qf36-history').open=true;
 if(assumptionsOpen)$('qf35-assumptions').open=true;
 if(filtersOpen&&$('qf35-filters'))$('qf35-filters').open=true;
 if(focusKey){const field=[...host.querySelectorAll('[data-qf35-select]')].find(f=>f.dataset.qf35Select===focusKey);field?.focus({preventScroll:true});}
}
async function loadUniverse(){
 if(!active()||loading||eligible)return;loading=true;failure='';const token=generation;render();
 try{const result=await bridge().universe();if(token!==generation||!active())return;if(result?.schema!=='quantforge.research-universe.v34'||result.licensed_private!==true||!Array.isArray(result.items))throw Error('Invalid universe.');eligible=result;refreshed=result.eligibility_checked_at||new Date().toISOString();}
 catch(_){if(token===generation&&active())failure='The eligible universe is unavailable. Existing individual research remains available; no substitute ranking is generated.';}
 finally{if(token===generation){loading=false;render();}}
}
function sync(){
 const enabled=active();nav.hidden=!enabled;
 if(!enabled){if(wasPrivate){invalidate();eligible=null;loading=false;failure='';selectedRules={};valuation=null;valuationVersion=null;selected.clear();selectionKey='';refreshed=null;task='briefing';}host.hidden=true;host.replaceChildren();wasPrivate=false;$('qf-v23-explore-content').hidden=Boolean(root.QFUnifiedPrivate23?.state?.().landing);return;}
 if(!wasPrivate){task='briefing';wasPrivate=true;}
 const explore=$('page-explore').classList.contains('active');host.hidden=!explore||task!=='briefing';
 if(explore){$('qf-v23-landing').hidden=true;$('qf-v23-explore-content').hidden=task==='briefing';document.body.classList.remove('qf31-home-active');}
 nav.querySelectorAll('button').forEach(b=>b.setAttribute('aria-current',b.dataset.qf34Workspace===task?'page':'false'));
 render();if(!eligible&&!loading&&!failure)void loadUniverse();
}
document.addEventListener('click',event=>{
 if(!active())return;
 if(event.target.closest('[data-qf34-configure]')){event.preventDefault();$('qf35-assumptions').open=true;$('qf34-rules').scrollIntoView({block:'center'});$('qf34-rules input').focus();return;}
 const target=event.target.closest('[data-qf34-workspace]');if(target){choose(target.dataset.qf34Workspace);return;}
 const symbol=event.target.closest('[data-qf34-symbol]')?.dataset.qf34Symbol;if(symbol){void research(symbol);return;}
 if(event.target.closest('[data-qf34-refresh]')){invalidate();eligible=null;failure='';selectionKey='';void loadUniverse();return;}
 if(event.target.closest('#qf35-cancel-batch')){batch.cancel();return;}
 if(event.target.closest('#qf35-analyze-shortlist')){const screen=currentScreen(),candidates=screen?.shortlist.filter(r=>selected.has(r.symbol))||[];if(!candidates.length)return;const c={generation,ownerVersion:bridge().snapshot().version,rules:{...selectedRules},key:'batch-'+generation+'-'+Date.now()};void batch.start(candidates,c);return;}
 if(event.target.closest('#qf-v20-navigation [data-page="explore"]')){task='research';sync();}
});
$('qf-v23-home-button').addEventListener('click',()=>{if(active())choose('briefing');});
host.addEventListener('change',event=>{
 const symbol=event.target.dataset.qf35Select;if(symbol){if(event.target.checked)selected.add(symbol);else selected.delete(symbol);render();return;}
 if(event.target.id==='qf34-min-growth'){const n=Number(event.target.value);if(Number.isFinite(n)&&n>=-50&&n<=200){invalidate();minGrowth=n/100;selectionKey='';render();}}
 if(event.target.id==='qf34-order'){invalidate();order=event.target.value;selectionKey='';render();}
});
host.addEventListener('submit',event=>{if(event.target.id!=='qf34-rules')return;event.preventDefault();const raw={};for(const field of host.querySelectorAll('[data-qf34-rule]')){const scale=['maxWeight','maxDrawdown'].includes(field.dataset.qf34Rule)?100:1;raw[field.dataset.qf34Rule]=field.value===''?null:Number(field.value)/scale;}const result=root.QFDecision34.policy(raw);if(result.errors.length){$('qf34-rule-status').textContent=result.errors.join(' ');return;}invalidate();selectedRules=raw;root.dispatchEvent(new Event('qf:research-rules'));render();$('qf35-assumptions').open=true;$('qf34-rule-status').textContent='Research conditions applied in this tab. No account records were changed.';});
root.addEventListener('qf:canonical-assessment',event=>{const {report,reviewed}=event.detail||{};if(!active()||!reviewed||report?.snapshot?.ownerVersion!==bridge().snapshot()?.version)return;reports.set(report.snapshot.symbol,report);if(task==='briefing')render();});
root.addEventListener('qf:owner-valuation',event=>{if(!active()||event.detail?.version!==bridge().snapshot()?.version)return;valuation=event.detail.snapshot;valuationVersion=event.detail.version;if(task==='briefing')render();});
root.addEventListener('qf:owner-state',()=>{invalidate();valuation=null;valuationVersion=null;sync();});
root.addEventListener('qf:research-universe',()=>{if(active())invalidate();});
for(const name of ['qf:research-context','qf:data-mode','qf:owner-auth-ready','qf:owner-auth-ended'])root.addEventListener(name,sync);
root.addEventListener('qf:route-change',event=>{if(event.detail?.route==='portfolio')task='portfolio';sync();});
root.QFWorkspace34=Object.freeze({rules:()=>({...selectedRules}),choose,research});sync();
})(window);
