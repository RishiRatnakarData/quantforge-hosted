/* Contextual owner tools reuse the original MFA and versioned-state bridge. */
(function(){
'use strict';
const $=id=>document.getElementById(id),bridge=()=>window.QFPrivateBridgeV23;
const drawer=$('qf-v23-owner-panel');if(!drawer)return;
 $('main-content').prepend($('qf24-mode-bar'));
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const usd=n=>Number.isFinite(n)?n.toLocaleString('en-US',{style:'currency',currency:'USD'}):'Unavailable';
const context=()=>window.QFResearch20?.context?.();
const signed=()=>Boolean(bridge()?.ready()),privateMode=()=>signed()&&context()?.mode==='private';
let busy=false,landing=false,request=0,assetRequest=0,timer,editing=null,lastSymbol=null;
const notePanel=drawer.querySelector('[data-qf-v23-panel="notes"]'),tradePanel=drawer.querySelector('[data-qf-v23-panel="portfolio"]');
function host(id,title){const section=document.createElement('section');section.id=id;section.className='qf24-context';section.hidden=true;const h=document.createElement('h2');h.textContent=title;section.append(h);return section;}
const notes=host('qf24-notes','Saved research for this company');notes.append(notePanel);notePanel.hidden=false;
const saveBrief=document.createElement('button');saveBrief.id='qf24-save-brief';saveBrief.className='btn';saveBrief.textContent='Save current research brief';notePanel.insertBefore(saveBrief,$('qf-v23-note-list'));
const noteStatus=document.createElement('p');noteStatus.id='qf24-note-status';noteStatus.setAttribute('role','status');notes.append(noteStatus);
$('qf-v23-explore-content').append(notes);
const account=host('qf24-transactions','Saved virtual account and transactions');account.append(tradePanel);tradePanel.hidden=false;
const tradeStatus=document.createElement('p');tradeStatus.id='qf24-trade-status';tradeStatus.setAttribute('role','status');account.append(tradeStatus);
$('qf-v20-portfolio-overview').prepend(account);
const historyPanel=document.createElement('section');historyPanel.id='qf25-account-history';historyPanel.className='qf24-context';historyPanel.hidden=true;
historyPanel.innerHTML='<h2>Recorded virtual-account value</h2><p>Each point is an owner-requested, server-verified mark. Contributions are shown separately; no past account values are inferred from today’s holdings.</p><button id="qf25-record-mark" class="btn primary">Record current valuation</button><div id="qf25-account-chart"></div><div class="qf24-assumptions"><label>Virtual funding action<select id="qf25-capital-action"><option value="deposit">Deposit virtual funds</option><option value="withdraw">Withdraw virtual funds</option></select></label><label>Amount ($)<input id="qf25-capital-amount" type="number" min="1" max="1000000" value="1000"></label><button class="btn" id="qf25-capital-submit">Record funding change</button></div><p id="qf25-account-status" role="status"></p>';
$('qf-v20-portfolio-overview').prepend(historyPanel);
function paintHistory(data){
 const host=$('qf25-account-chart');host.replaceChildren();
 try{const r=window.QFAccountHistory25.summarize(data.valuations||[]);if(!r.count){host.textContent='No recorded marks yet. Record a valuation to start genuine account history.';return;}
 host.innerHTML=window.QFDeepUI25?.curve('Recorded value and net contributed capital (USD)',r.points.map(p=>p.at.slice(0,16)),[{name:'Account value',values:r.points.map(p=>p.value)},{name:'Net contributions',values:r.points.map(p=>p.net_contributions)}])||'';
 const info=document.createElement('p');info.textContent=r.count+' recorded marks · value change '+usd(r.value_change)+' · net funding change '+usd(r.capital_change)+' · change attributable to paper P&L '+usd(r.pnl_change)+'. Percentage or time-weighted returns are withheld: marks do not value every external flow at its exact event time.';host.append(info);
 }catch(_){host.textContent='Recorded history is inconsistent; performance withheld. Refresh the account.';}
}
$('qf25-record-mark').addEventListener('click',()=>void work(()=>bridge().recordSnapshot(),'Server-verified valuation recorded.'));
$('qf25-capital-submit').addEventListener('click',()=>void window.QFFunding28?.review());

drawer.querySelector('.qf-v23-owner-tabs').remove();
$('qf-v23-owner-title').textContent='Account';
const accountHelp=document.createElement('p');accountHelp.className='pane';accountHelp.id='qf27-account-menu-summary';accountHelp.textContent='Account overview loads after verified sign-in.';drawer.insertBefore(accountHelp,$('qf-v23-owner-status'));
account.append($('qf-b21-owner-account'));
function status(text){$('qf-v23-owner-status').textContent=text;noteStatus.textContent=text;tradeStatus.textContent=text;$('qf25-account-status').textContent=text;}
function close(){if(drawer.open)drawer.close();}
function renderHomeEvidence(){
 const host=$('qf31-home-chart');if(!host)return;
 const issuer=window.QFPublishedSEC?.companies?.find(c=>c.symbol==='MSFT');
 const rows=(issuer?.annual||[]).filter(r=>typeof r?.fiscal_end==='string'&&Number.isFinite(r?.metrics?.revenue_usd)&&r.metrics.revenue_usd>0).sort((a,b)=>a.fiscal_end.localeCompare(b.fiscal_end)).slice(-5);
 host.replaceChildren();
 if(rows.length<2){host.textContent='The published SEC example is unavailable. Use Explore to inspect currently covered company financials.';return;}
 const maximum=Math.max(...rows.map(r=>r.metrics.revenue_usd));
 const list=document.createElement('div');list.className='qf31-home-bars';list.setAttribute('role','list');list.setAttribute('aria-label','Microsoft annual reported revenue by fiscal year');
 for(const r of rows){
  const item=document.createElement('div');item.className='qf31-home-column';item.setAttribute('role','listitem');
  const amount='$'+(r.metrics.revenue_usd/1e9).toLocaleString('en-US',{maximumFractionDigits:0})+'B';
  item.setAttribute('aria-label','Fiscal '+r.fiscal_end.slice(0,4)+': '+amount);
  const value=document.createElement('strong');value.className='qf31-home-value';value.textContent=amount;
  const rail=document.createElement('div');rail.className='qf31-home-bar-rail';
  const bar=document.createElement('span');bar.className='qf31-home-bar';bar.style.height=(Math.max(4,r.metrics.revenue_usd/maximum*100))+'%';rail.append(bar);
  const year=document.createElement('span');year.className='qf31-home-year';year.textContent=r.fiscal_end.slice(0,4);
  item.append(value,rail,year);list.append(item);
 }
 const latest=rows.at(-1);
 const note=document.createElement('p');note.className='qf31-home-date';
 note.textContent='Fiscal years '+rows[0].fiscal_end.slice(0,4)+'–'+latest.fiscal_end.slice(0,4)+' · USD · Latest included filing '+(latest.sources?.revenue_usd?.filed||'date unavailable');
 host.append(list,note);
}
function home(value){if(value){window.QFNavigate20('explore');renderHomeEvidence();}landing=Boolean(value);$('qf-v23-landing').hidden=!landing;$('qf-v23-explore-content').hidden=landing;}
function paint(data){
 const list=$('qf-v23-note-list');list.replaceChildren();
 if(!data)return;paintHistory(data);
 const company=context();if(lastSymbol!==company.symbol){editing=null;$('qf-v23-note').value='';lastSymbol=company.symbol;}$('qf-v23-note-company').textContent=company.name+' ('+company.symbol+')';
 const visible=data.notes.map((n,i)=>({n,i})).filter(({n})=>n.symbol===company.symbol);
 if(!visible.length)list.textContent='No notes saved for this company yet.';
 for(const {n,i} of visible){const row=document.createElement('div');row.className='qf-v23-note-entry';const body=document.createElement('div'),p=document.createElement('p'),meta=document.createElement('small'),del=document.createElement('button');const archived=window.QFPrivateResearchIntelligenceV96?.readArchive?.(n);const thesis=window.QFResearchGuide30?.decode(n.text);p.textContent=thesis?window.QFResearchGuide30.describe(thesis):archived?'Saved historical assessment · '+archived.date+' · '+archived.universe.join(', ')+' · '+archived.covered+' completed methods. Recorded research screen: '+archived.action+'. This archive is a historical record, not a current recommendation.':n.text;meta.textContent=n.at;body.append(p,meta);del.className='btn sm';del.textContent='Delete';del.dataset.qfV23Delete=String(i);if(!archived){const edit=document.createElement('button');edit.type='button';edit.className='btn sm';edit.textContent='Edit';edit.dataset.qfV23Edit=String(i);row.append(edit);}row.prepend(body);row.append(del);list.append(row);}
 window.QFPortfolioUI27?.paint(data);
}
function sync(){
 const active=privateMode();notes.hidden=!active;account.hidden=!active;historyPanel.hidden=!active;
 const bar=$('qf24-mode-bar');bar.dataset.mode=active?'private':'public';
 $('qf24-mode-label').textContent=active?'PRIVATE · MFA VERIFIED · PROVIDER DATA SUBJECT TO ENTITLEMENT':'PUBLIC · SEC FINANCIALS · LABELED MODEL DEMONSTRATIONS';
 const toggle=$('qf24-switch-mode');toggle.hidden=!signed();toggle.textContent=active?'View public demo':'Return to private research';
 $('qf-v20-mode').textContent=signed()?'Account':'Sign in';
 document.querySelectorAll('.qf-v23-owner-action').forEach(e=>e.hidden=!active);
 document.querySelectorAll('[data-qf24-sample-account]').forEach(e=>e.hidden=active);
 if(!active){request++;assetRequest++;clearTimeout(timer);$('qf-v23-note-list').replaceChildren();$('qf-v23-note').value='';$('qf25-account-chart').replaceChildren();editing=null;lastSymbol=null;status('');close();}
 else{const saved=bridge().snapshot();paint(saved);accountHelp.innerHTML='<h3>MFA-verified owner session</h3><p>Research mode: '+escapeHTML(context().mode)+'. Provider access is checked when each dataset loads. '+(context().origin==='market'?'Observed price history is loaded for '+escapeHTML(context().symbol)+'.':'No observed market history is currently loaded.')+'</p><div class="qf27-account-kpis"><div><span>Saved research records</span><strong>'+saved.notes.length+'</strong></div><div><span>Virtual cash</span><strong>'+escapeHTML(usd(saved.cash))+'</strong></div><div><span>Positions</span><strong>'+Object.keys(saved.holdings).length+'</strong></div></div><p>Company notes are available beside research in Explore; virtual account actions are in Portfolio.</p><div class="qf27-action-row"><button type="button" class="btn" data-qf-v23-open="notes">Company notes</button><button type="button" class="btn" data-qf-v23-open="portfolio">Virtual portfolio</button></div>';}
}
async function refresh(){const token=++request;try{const data=await bridge().refresh();if(token===request&&privateMode())paint(data);}catch(_){if(token===request&&privateMode())status('Unable to refresh private data. Try again.');}}
async function work(job,ok){
 if(busy||!privateMode())return;busy=true;const token=request;status('Saving securely…');
 const buttons=[...notes.querySelectorAll('button'),...account.querySelectorAll('button'),...historyPanel.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);
 try{const data=await job();if(token===request&&privateMode()){paint(data);status(ok);window.dispatchEvent(new Event('qf:owner-state'));}}
 catch(e){if(token===request&&privateMode())status(String(e.message||'Save unavailable.').slice(0,220));}
 finally{busy=false;buttons.forEach(b=>b.disabled=false);}
}
async function open(name){
 close();
 if(!signed()){window.QFNavigate20('private');return;}
 if(!privateMode())window.QFResearch20.switchMode('private');
 if(name==='portfolio'){window.QFNavigate20('portfolio');document.querySelector('[data-qf-portfolio="overview"]').click();account.scrollIntoView({block:'start'});}
 else{home(false);window.QFNavigate20('explore');window.QFExplore27?.show('research');notes.scrollIntoView({block:'start'});$('qf-v23-note').focus();}
 await refresh();
}
$('qf24-switch-mode').addEventListener('click',()=>{close();window.QFResearch20.switchMode(privateMode()?'public':'private');sync();});
$('qf-v23-home-button').addEventListener('click',()=>home(true));
/* Home search is the sole primary action; feature navigation remains in the sidebar. */
function find(){const query=$('qf24-home-search').value;home(false);const input=$('qf-v20-search');input.value=query;setTimeout(()=>input.dispatchEvent(new Event('input')),0);input.focus();}
$('qf24-home-find').addEventListener('click',find);$('qf24-home-search').addEventListener('keydown',e=>{if(e.key==='Enter')find();});
$('qf-v20-mode').addEventListener('click',e=>{if(signed()){e.preventDefault();e.stopImmediatePropagation();drawer.showModal();}},true);
document.addEventListener('click',e=>{
 const action=e.target.closest('[data-qf-v23-open]');if(action){e.preventDefault();void open(action.dataset.qfV23Open);}
 const edit=e.target.closest('[data-qf-v23-edit]');if(edit&&privateMode()){editing=Number(edit.dataset.qfV23Edit);const note=bridge().snapshot()?.notes[editing];if(note&&note.symbol===context().symbol){$('qf-v23-note').value=note.text;$('qf-v23-note').focus();status('Revising a saved note. Save adds a new dated record and preserves the original.');}else editing=null;}
 const del=e.target.closest('[data-qf-v23-delete]');if(del&&privateMode()&&window.confirm('Delete this private note?'))void work(()=>bridge().deleteNote(Number(del.dataset.qfV23Delete)),'Research note deleted.');
});
$('qf-v23-close').addEventListener('click',close);
$('qf-v23-save').addEventListener('click',()=>{const text=$('qf-v23-note').value.trim(),symbol=context().symbol;if(!text){status('Enter a research note first.');return;}void work(async()=>{const data=editing===null?await bridge().saveNote(text,symbol):await bridge().updateNote(editing,text,symbol);editing=null;$('qf-v23-note').value='';return data;},'Research note saved.');});
saveBrief.addEventListener('click',()=>{const ctx=context(),text=$('qf-v20-findings').innerText.trim();if(!text||!$('qf-v20-run-state').textContent.startsWith('Calculated for')){status('Analyze this company before saving its brief.');return;}const note=ctx.name+' ('+ctx.symbol+') · SEC snapshot '+ctx.snapshot+' · '+$('qf-v20-chart-source').textContent+'\n'+text;void work(()=>bridge().saveNote(note.slice(0,2000),ctx.symbol),'Research brief saved as a dated note.');});
$('qf-v23-refresh').addEventListener('click',()=>void refresh());
$('qf-v23-signout').addEventListener('click',async()=>{try{await bridge().signOut();sync();close();window.QFNavigate20('explore');}catch(_){status('Sign-out could not be completed. Try again.');}});
window.addEventListener('qf:route-change',e=>{if(e.detail?.route==='private'&&signed()){window.QFNavigate20('explore');return;}if(e.detail?.route==='explore')home(false);sync();});
window.addEventListener('qf:research-context',sync);window.addEventListener('qf:data-mode',sync);
window.addEventListener('qf:owner-auth-ready',()=>{sync();if(document.querySelector('.tabpage.active')?.id==='page-private')window.QFNavigate20('explore');});window.addEventListener('qf:owner-auth-ended',()=>{sync();window.QFNavigate20('explore');});
const legacy=$('private-signed');if(legacy)new MutationObserver(sync).observe(legacy,{attributes:true,attributeFilter:['hidden']});
sync();
function showFreshHome(){
 if(location.protocol!=='https:' || !['/','/index.html'].includes(location.pathname) || location.hash || signed())return;
 if(document.querySelector('.tabpage.active')?.id!=='page-explore')return;
 renderHomeEvidence();
 landing=true;
 $('qf-v23-landing').hidden=false;
 $('qf-v23-explore-content').hidden=true;
}
if(document.readyState==='complete')queueMicrotask(showFreshHome);
else window.addEventListener('load',showFreshHome,{once:true});
window.QFUnifiedPrivate23=Object.freeze({open,home:()=>home(true),state:()=>({signedIn:signed(),landing})});
})();
