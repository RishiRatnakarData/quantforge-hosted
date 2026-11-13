/* Guided investment research reuses the five-section shell and versioned private notes. */
(function(root){
'use strict';
const $=id=>document.getElementById(id),ctx=()=>root.QFResearch20.context(),J=root.QFResearchGuide30;
const safe=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=root.QFReadout29.money,pct=v=>Number.isFinite(v)?(v*100).toFixed(1)+'%':'Unavailable';
const healthData=root.QFHealthSnapshot30||{companies:{}};
const guide=document.createElement('section');guide.id='qf30-guide';guide.className='pane';const brief=$('qf27-explore-brief');const findings=brief.querySelector('.qf-v20-findings');if(findings)findings.after(guide);else brief.append(guide);
const companyInfo=document.createElement('p');companyInfo.id='qf30-freshness';companyInfo.className='qf30-freshness';document.querySelector('.qf27-identity').append(companyInfo);
const fields=[['cash_usd','Cash & cash equivalents'],['assets_usd','Assets'],['liabilities_usd','Liabilities'],['equity_usd','Stockholders’ equity'],['current_assets_usd','Current assets'],['current_liabilities_usd','Current liabilities'],['long_term_debt_current_usd','Current long-term debt component'],['long_term_debt_noncurrent_usd','Noncurrent long-term debt component']];
function renderHealth(){
 const c=ctx(),data=healthData.companies[c.symbol],rows=(data?.annual||[]).slice().sort((a,b)=>a.fiscal_end.localeCompare(b.fiscal_end)),latest=rows.at(-1),r=J.health(latest);
 $('qf-v20-filing-status').textContent='Balance sheet fiscal end '+(latest?.fiscal_end||'unavailable')+' · extraction cutoff '+(data?.cutoff||'unavailable')+' · instant USD facts.';
 $('qf-v20-financial-chart').hidden=false;$('qf-v20-financial-table').hidden=true;
 $('qf-v20-financial-kpis').replaceChildren();
 $('qf27-financial-interpretation').textContent=latest?'Balance-sheet facts at '+latest.fiscal_end+'; ratios require the same accession and a positive denominator.':'No compatible cached balance-sheet facts for this instrument. Missing is not zero.';
 const lines=[['Assets','assets_usd'],['Liabilities','liabilities_usd'],['Cash','cash_usd']].map(([name,key],i)=>({name,values:rows.map(r=>Number.isFinite(r.metrics[key])?r.metrics[key]/1e9:null),color:['#424a53','#85909b','#60756a'][i]})).filter(l=>l.values.some(Number.isFinite));
 const chart=rows.length>1&&lines.length?root.QFCharts26.curve('Reported balance sheet (USD billions)',rows.map(r=>r.fiscal_end),lines,{allowGaps:true,format:'number'}):'';
 const records=fields.map(([key,label])=>{const source=latest?.sources[key];return '<tr><th scope="row">'+label+'</th><td>'+safe(money(latest?.metrics[key]))+'</td><td>'+safe(source?.filed||'Unavailable')+'</td><td>'+safe(source?.accession||'Unavailable')+'</td></tr>';}).join('');
 $('qf-v20-financial-chart').innerHTML=chart+'<div class="qf30-health-ratios"><p><strong>Current ratio: '+(r.current_ratio===null?'Unavailable':r.current_ratio.toFixed(2)+'×')+'</strong><br>Current assets / current liabilities. It describes reported short-term coverage, not cash available to invest.</p><p><strong>Liabilities / assets: '+pct(r.liabilities_to_assets)+'</strong><br>All reported liabilities include more than borrowing. This is not a debt-only ratio.</p><p><strong>Long-term debt components: '+safe(money(r.long_term_debt_components))+'</strong><br>Current + noncurrent long-term debt only; other borrowing, leases and commitments may be absent. This is not total debt.</p></div><div class="table-wrap"><table><caption>Latest covered balance sheet · '+safe(latest?.fiscal_end||'unavailable')+' · USD</caption><thead><tr><th>Fact</th><th>Reported value</th><th>Filed</th><th>Accession</th></tr></thead><tbody>'+records+'</tbody></table></div>';
 $('qf29-financial-explanation').innerHTML='<p>These instant facts share a fiscal end; they are not annual cash-flow totals. Banks, insurers and other issuers may not report a classified balance sheet, making liquidity ratios unavailable or inappropriate for cross-sector comparison. Negative equity is preserved.</p><p><strong>Investigate next:</strong> Read debt maturities, covenants, restricted cash and contractual commitments in the official filing. These facts alone do not establish solvency.</p>'+(data?'<p><a target="_blank" rel="noopener noreferrer" href="'+safe(data.source_url)+'">SEC Company Facts · CIK '+safe(data.cik)+'</a> · extraction cutoff '+safe(data.cutoff)+'. Latest eligible annual facts only; no TTM or quarterly inference.</p>':'');
 document.querySelectorAll('[data-qf27-finance]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.qf27Finance==='health')));
}
const summary=document.createElement('section');summary.id='qf32-summary';summary.className='qf32-summary';guide.before(summary);
let preferences={};
function drawSummary(c){
 const existing=brief.querySelector('section.qf-v20-findings');if(existing)existing.hidden=c.mode==='private'&&!$('qf-v20-run-state').textContent.startsWith('Calculated for '+c.name);
 summary.hidden=c.mode!=='private';if(summary.hidden){summary.replaceChildren();return;}
 const risk=c.origin==='market'?root.QFResearchCore20.priceStatistics(c.prices||[]):null;
 const prediction=c.origin==='market'?root.QFModelsMethods22?.evidence?.()?.prediction:null;
 const held=Number(root.QFPrivateBridgeV23.snapshot()?.holdings?.[c.symbol])>0;
 const d=J.decisionSummary({financial:c.financial,observed:c.origin==='market',risk,prediction,held,preferences});
 summary.innerHTML='<h2>Investment research summary</h2><p><strong>'+safe(d.disposition)+'</strong> · '+safe(c.name)+' · fiscal '+safe(c.financial.source.period||'unavailable')+'</p><div class="qf32-preferences"><label>Research horizon (optional)<select id="qf32-horizon"><option value="">Choose a horizon</option><option value="short">Under three years</option><option value="long">Three years or longer</option></select></label><label>Drawdown review boundary (optional)<select id="qf32-drawdown"><option value="">No boundary set</option><option value="0.15">15% peak-to-trough loss</option><option value="0.3">30% peak-to-trough loss</option><option value="0.5">50% peak-to-trough loss</option></select></label></div><p class="tiny">Optional reflection preferences stay in this tab and clear on sign-out. They do not determine investment suitability.</p>'+[['What looks favorable?',d.favorable.join(' ')||'No supported favorable finding from the covered measures.'],['What needs caution?',d.concerns.join(' ')],['What do the models suggest?',d.model],['How does this relate to my objectives?',d.context],['What should I investigate next?',d.next],['What would change the conclusion?',d.invalidation]].map(([t,b])=>'<h3>'+safe(t)+'</h3><p>'+safe(b)+'</p>').join('');
 const actions=document.createElement('div');actions.className='qf27-action-row';actions.innerHTML='<button class="btn" data-qf30-action="risk">Models &amp; evaluation</button><button class="btn" data-qf30-action="compare">Compare alternatives</button><button class="btn" data-qf30-action="research">My saved research</button>';summary.append(actions);
 $('qf32-horizon').value=preferences.horizon||'';$('qf32-drawdown').value=preferences.drawdown||'';
}
summary.addEventListener('change',e=>{if(e.target.id==='qf32-horizon')preferences.horizon=e.target.value;if(e.target.id==='qf32-drawdown')preferences.drawdown=e.target.value;const focus=e.target.id;drawSummary(ctx());$(focus).focus();});
root.addEventListener('qf:owner-auth-ended',()=>{preferences={};drawSummary(ctx());});
function drawGuide(){
 drawSummary(ctx());
 guide.hidden=ctx().mode==='private';
 const c=ctx(),issuer=root.QFPublishedSEC.companies.find(x=>x.symbol===c.symbol),f=c.financial,dates=f.annual.flatMap(r=>Object.values(r.sources).map(s=>s.filed)).filter(Boolean).sort(),market=c.origin==='market'&&c.prices?.length?c.prices.at(-1).date:null;
 companyInfo.textContent='SEC cutoff '+(issuer?.as_of||c.snapshot)+' · financial period '+(f.source.period||'unavailable')+' · latest included filing '+(dates.at(-1)||'unavailable')+(market?' · observed market close '+market+' (provider details below)':' · no observed market close loaded')+'.';
 const q=root.QFResearchCore20.priceStatistics(c.origin==='market'?c.prices||[]:[]);
 const steps=[
 ['Understand the business','The selected issuer is '+c.name+(issuer?.cik?' · CIK '+issuer.cik:'')+'. Structured statements do not establish its products, customers or competitive advantage. Read Item 1 (Business) and segment disclosures before writing your own description.','financials','Read financial evidence'],
 ['Examine financial performance','Latest annual revenue: '+money(f.metrics.revenue_usd)+'; operating margin: '+pct(f.metrics.operating_margin)+'; cash-flow proxy: '+money(f.metrics.free_cash_flow_usd)+'. Free cash flow here means operating cash flow minus cash property-and-equipment purchases, not cash available to shareholders.','cash','Inspect cash generation'],
 ['Separate price from valuation','An observed close is a dated market price. Revenue and income are accounting flows. A DCF is a scenario driven by assumed growth, discount and terminal rates; our cash-flow proxy present value has no fair-share-price claim. Missing debt, cash or diluted shares can prevent an equity bridge.','valuation','Test valuation assumptions'],
 ['Put historical risk in context',q?'Observed annualized log-return volatility '+pct(q.annual_volatility)+' and maximum drawdown '+pct(q.max_drawdown)+' across '+q.sessions+' closes ('+q.first+' to '+q.last+'). Volatility measures return variability; drawdown measures decline from an earlier peak. Neither bounds future loss.':'Observed company market risk is unavailable in this mode. Synthetic demonstrations explain the computation but cannot describe this company’s investment risk.','risk','Inspect risk and uncertainty'],
 ['Compare alternatives','Compare compatible fiscal periods, units and business models. Market studies need aligned dates and matching feeds. Eligible funds can diversify single-company exposure, but a similar historical price path does not make an instrument the best investment. Fund fees and holdings are not verified here.','compare','Compare this company'],
 ['Record and revisit your thinking','Write a thesis in your own words: evidence, concerns, assumptions, disconfirming facts, open questions and a review date. Calculated findings and user beliefs remain distinct. Revisions add dated records; earlier notes remain available.','research',c.mode==='private'?'Open my research':'Learn the thesis process']
 ];
 const accession=f.annual[0]?.sources?.revenue_usd?.accession,filing=issuer?.cik&&/^\d{10}-\d{2}-\d{6}$/.test(accession||'')?'https://www.sec.gov/Archives/edgar/data/'+issuer.cik+'/'+accession.replaceAll('-','')+'/'+accession+'-index.html':null;
 guide.innerHTML=(filing?'<p><a href="'+filing+'" target="_blank" rel="noopener noreferrer">Official annual filing index</a> · inspect Business, risk factors and segment disclosures.</p>':'')+'<h2>Build a research case for '+safe(c.name)+'</h2><p>Follow the evidence from business to financials, valuation, risk and alternatives. These prompts guide investigation; they do not produce a stock score or Buy/Hold/Sell verdict.</p><p><button class="btn" data-qf30-action="case-study">See a worked SEC research case</button></p><div class="qf30-research-steps">'+steps.map(([title,body,action,label],i)=>'<article class="qf30-step" id="qf30-step-'+i+'"><h3>'+safe(title)+'</h3><p>'+safe(body)+'</p>'+(action==='research'&&c.mode!=='private'?'':'<button class="btn" data-qf30-action="'+action+'">'+safe(label)+'</button>')+'</article>').join('')+'</div>';
}
const journal=document.createElement('section');journal.id='qf30-journal';journal.className='qf30-journal';journal.innerHTML='<h3>My investment thesis</h3><p>Your beliefs and questions, separate from system observations. All prompts are optional; complete only what helps your research.</p><form id="qf30-thesis-form"><div class="qf30-thesis-fields">'+J.prompts.map(([key,label])=>'<label for="qf30-'+key+'">'+safe(label)+'<textarea id="qf30-'+key+'" maxlength="220" rows="2"></textarea></label>').join('')+'</div><label class="qf30-review-field" for="qf30-review">Review on (optional)<input id="qf30-review" type="date"></label><p id="qf30-revision-context"></p><div class="qf27-action-row"><button class="btn primary" type="submit" id="qf30-save">Save thesis as a dated record</button><button class="btn" type="button" id="qf30-new">Start a new thesis</button></div><p role="status" id="qf30-journal-status"></p></form><p>Saves add dated records without changing earlier entries. The shared archive holds 100 records; when full, new saves stop. Review dates help you plan; they do not send reminders.</p>';
const notes=$('qf24-notes');notes.querySelector('h2').textContent='My saved research';notes.querySelector('[data-qf-v23-panel="notes"]').prepend(journal);
let base=null,busy=false,lastSymbol=ctx().symbol,generation=0;
function clear(){base=null;for(const [key] of J.prompts)$('qf30-'+key).value='';$('qf30-review').value='';$('qf30-revision-context').textContent='New thesis · earlier notes remain in the archive below.';}
function status(text){$('qf30-journal-status').textContent=text;}
$('qf30-new').addEventListener('click',()=>{clear();status('New unsaved thesis.');});
document.addEventListener('click',event=>{
 const edit=event.target.closest('[data-qf-v23-edit]');if(!edit)return;
 const note=root.QFPrivateBridgeV23.snapshot()?.notes[Number(edit.dataset.qfV23Edit)],d=J.decode(note?.text);if(!d)return;
 event.preventDefault();event.stopImmediatePropagation();base={note:{...note},data:d};for(const [key] of J.prompts)$('qf30-'+key).value=d[key];$('qf30-review').value=d.review||'';
 $('qf30-revision-context').textContent='Reviewing revision '+d.revision+' saved '+note.at+'. Its evidence period was '+(d.period||'unavailable')+'; current financial period is '+(ctx().financial.source.period||'unavailable')+'. Your earlier beliefs are preserved; compare the current charts before revising.';
 $('qf30-revision-context').textContent+=' Recorded revenue '+money(d.observed?.revenue_usd)+' versus current '+money(ctx().financial.metrics.revenue_usd)+'; recorded operating margin '+pct(d.observed?.operating_margin)+' versus current '+pct(ctx().financial.metrics.operating_margin)+'; recorded FCF proxy '+money(d.observed?.free_cash_flow_usd)+' versus current '+money(ctx().financial.metrics.free_cash_flow_usd)+'. Changes may reflect period, coverage or restatement differences; these are not investment gains.';status('Editing a new revision. The original will remain unchanged.');$('qf30-interest').focus();
},true);
$('qf30-thesis-form').addEventListener('submit',async event=>{
 event.preventDefault();if(busy)return;const c=ctx(),bridge=root.QFPrivateBridgeV23;if(c.mode!=='private'||!bridge.ready()){status('MFA-verified private research is required.');return;}
 const snapshot=bridge.snapshot(),token=generation;try{
  if(base&&!snapshot.notes.some(n=>n.text===base.note.text&&n.at===base.note.at&&n.symbol===c.symbol))throw Error('The original record changed. Refresh and review it again.');
  const values=Object.fromEntries(J.prompts.map(([key])=>[key,$('qf30-'+key).value]));values.review=$('qf30-review').value;
  const text=J.encode(values,{id:base?.data.id||root.crypto.randomUUID(),revision:base?Math.max(base.data.revision,...snapshot.notes.map(n=>J.decode(n.text)).filter(d=>d?.id===base.data.id).map(d=>d.revision))+1:1,parent:base?.note.at||'',period:c.financial.source.period,snapshot:root.QFPublishedSEC.companies.find(x=>x.symbol===c.symbol)?.as_of||c.snapshot,observed:c.financial.metrics});
  busy=true;$('qf30-save').disabled=true;await bridge.saveNote(text,c.symbol);
  if(token!==generation||ctx().mode!=='private'||ctx().symbol!==c.symbol)return;
  clear();root.dispatchEvent(new Event('qf:research-context'));status('Thesis saved. Earlier records and their timestamps were preserved.');
 }catch(e){if(token===generation)status(e.message||'Save unavailable. Refresh before retrying an uncertain result.');}finally{busy=false;$('qf30-save').disabled=false;}
});
function researchAction(event){const action=event.target.closest('[data-qf30-action]')?.dataset.qf30Action;if(!action)return;
 if(action==='case-study'){root.QFNavigate20('methods');document.querySelector('[data-qf-c22-method="overview"]').click();$('qf27-case-study').scrollIntoView({block:'start'});return;}
 if(action==='compare'){$('qf-v20-add-compare').click();return;}
 if(['risk','valuation'].includes(action)){root.QFNavigate20('models');document.querySelector('[data-qf-model="'+action+'"]').click();return;}
 if(action==='research'){if(ctx().mode==='private')root.QFExplore27.show('research');return;}
 root.QFExplore27.show('financials');if(action==='cash')document.querySelector('[data-qf27-finance="cash"]').click();
}
guide.addEventListener('click',researchAction);summary.addEventListener('click',researchAction);
root.addEventListener('qf:analyze-company',()=>{const existing=brief.querySelector('section.qf-v20-findings');if(existing)existing.hidden=false;});
function sync(){drawGuide();if(ctx().mode!=='private'||lastSymbol!==ctx().symbol){generation++;clear();status('');}lastSymbol=ctx().symbol;}
for(const event of ['qf:research-context','qf:data-mode','qf:owner-auth-ended'])root.addEventListener(event,sync);
function migrate(){if(/^#(?:(?:explore|private)[\/-])?(?:news|context|sentiment|filings)(?:[\/-].*)?$/.test(location.hash)){history.replaceState(null,'','#explore');root.QFNavigate20('explore');root.QFExplore27.show('financials');}}
root.addEventListener('hashchange',migrate);migrate();clear();sync();root.QFGuideUI30=Object.freeze({renderHealth});
})(window);
