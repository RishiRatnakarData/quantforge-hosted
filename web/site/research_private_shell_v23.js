/* Unified owner experience. No independent tokens, storage or non-MFA API path. */
(function(){
'use strict';
const $=id=>document.getElementById(id);
const bridge=()=>window.QFPrivateBridgeV23;
const drawer=$('qf-v23-owner-panel');
if(!drawer||!$('qf-v23-home-button'))return;
let active='notes',busy=false,landing=false;
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtUSD=n=>Number.isFinite(n)?n.toLocaleString('en-US',{style:'currency',currency:'USD'}):'Unavailable';
function ready(){return Boolean(bridge()?.ready());}
function setStatus(text){$('qf-v23-owner-status').textContent=String(text||'');}
function close(){if(drawer.open)drawer.close();}
function setLanding(value){
 if(value)window.QFNavigate20('explore');
 landing=Boolean(value);
 $('qf-v23-landing').hidden=!landing;
 $('qf-v23-explore-content').hidden=landing;
}
function setTab(name){
 if(!['notes','portfolio'].includes(name))return;
 active=name;
 drawer.querySelectorAll('[data-qf-v23-panel]').forEach(e=>e.hidden=e.dataset.qfV23Panel!==name);
 drawer.querySelectorAll('[data-qf-v23-tab]').forEach(e=>{const selected=e.dataset.qfV23Tab===name;e.classList.toggle('active',selected);e.setAttribute('aria-pressed',String(selected));});
}
function paintAccount(data){
 const host=$('qf-v23-account-overview');
 if(!data){host.textContent='Your private portfolio is unavailable. Sign in again.';return;}
 const holdings=Object.entries(data.holdings).filter(([,units])=>Number(units)>0);
 host.innerHTML='<div class="qf-v23-owner-kpis"><div><small>Virtual cash</small><strong>'+escapeHTML(fmtUSD(data.cash))+'</strong></div><div><small>Positions</small><strong>'+holdings.length+'</strong></div></div>'+
  '<div class="qf-v23-owner-account-table table-wrap"><table><thead><tr><th>Investment</th><th>Units</th></tr></thead><tbody>'+
  (holdings.map(([sym,n])=>'<tr><td>'+escapeHTML(sym)+'</td><td>'+escapeHTML(Number(n).toLocaleString('en-US',{maximumFractionDigits:6}))+'</td></tr>').join('')||'<tr><td colspan="2">No virtual holdings yet.</td></tr>')+
  '</tbody></table></div><p class="tiny">No account valuation shown without verified current quotes. Transactions use server-validated provider observations.</p>';
}
function paintNotes(data){
 const host=$('qf-v23-note-list');
 host.replaceChildren();
 if(!data){host.textContent='Private notes unavailable.';return;}
 const notes=data.notes.filter(n=>n.text&&!window.QFPrivateResearchIntelligenceV96?.readArchive?.(n));
 if(!notes.length){host.textContent='No personal research notes saved.';return;}
 for(const note of notes){
  const actualIndex=data.notes.indexOf(note);
  const row=document.createElement('div');row.className='qf-v23-note-entry';
  const body=document.createElement('div'),content=document.createElement('p'),metadata=document.createElement('small');
  content.textContent=note.text;metadata.textContent=(note.symbol||'Research')+' · '+(note.at||'Saved');
  body.append(content,metadata);
  const del=document.createElement('button');del.type='button';del.className='btn sm';del.textContent='Delete';del.dataset.qfV23Delete=String(actualIndex);
  row.append(body,del);host.append(row);
 }
}
function paint(data){paintNotes(data);paintAccount(data);}
function selectedCompany(){return window.QFResearch20?.context?.()||null;}
function syncAccount(){
 const signed=ready(),button=$('qf-v20-mode');
 button.textContent=signed?'My workspace':'Sign in';
 button.setAttribute('aria-label',signed?'Open owner notes and virtual portfolio':'Sign in to private research');
 document.querySelectorAll('.qf-v23-owner-action').forEach(e=>e.hidden=!signed);
 if(!signed){close();$('qf-v23-note-list').replaceChildren();$('qf-v23-account-overview').textContent='Private account requires MFA.';}
}
function populateAssets(){
 const assets=window.QFPublishedSEC?.companies||[];
 const choices=[...assets.map(c=>({s:c.symbol,label:c.name})),...['VOO','QQQ','SPY','BND'].map(s=>({s,label:s+' ETF'}))];
 const seen=new Set();
 const select=$('qf-v23-trade-symbol');select.replaceChildren();
 for(const a of choices){if(seen.has(a.s))continue;seen.add(a.s);const option=document.createElement('option');option.value=a.s;option.textContent=a.label+' ('+a.s+')';select.append(option);}
}
async function open(name){
 if(!ready()){window.QFNavigate20('private');return;}
 setTab(name||'notes');syncAccount();setStatus('');
 const selected=selectedCompany();$('qf-v23-note-company').textContent=selected?selected.name+' ('+selected.symbol+')':'';
 if(selected&&[...$('qf-v23-trade-symbol').options].some(o=>o.value===selected.symbol))$('qf-v23-trade-symbol').value=selected.symbol;
 if(!drawer.open)drawer.showModal();
 try{const snapshot=await bridge().refresh();if(!ready())throw Error('Session ended.');paint(snapshot);}catch(e){if(ready())setStatus('Unable to refresh private data: '+String(e.message||e));}
}
async function work(job,ok){
 if(busy)return;busy=true;setStatus('Saving securely…');
 for(const btn of drawer.querySelectorAll('button'))if(btn.id!=='qf-v23-close')btn.disabled=true;
 try{const data=await job();if(!ready()&&data!==null)throw Error('Session ended.');paint(data);setStatus(ok);}
 catch(e){setStatus(String(e.message||e).slice(0,220));}
 finally{busy=false;for(const btn of drawer.querySelectorAll('button'))btn.disabled=false;}
}
$('qf-v23-home-button').addEventListener('click',()=>setLanding(true));
$('qf-v23-open-research').addEventListener('click',()=>{setLanding(false);$('qf-v20-search').focus();});
$('qf-v20-mode').addEventListener('click',event=>{if(ready()){event.preventDefault();event.stopImmediatePropagation();void open('notes');}},true);
document.addEventListener('click',event=>{
 const launch=event.target.closest('[data-qf-v23-open]');if(launch){event.preventDefault();void open(launch.dataset.qfV23Open);return;}
 const panel=event.target.closest('[data-qf-v23-tab]');if(panel){setTab(panel.dataset.qfV23Tab);return;}
 const remove=event.target.closest('[data-qf-v23-delete]');if(remove&&ready()){
  const i=Number(remove.dataset.qfV23Delete);if(!window.confirm('Delete this private note?'))return;
  void work(()=>bridge().deleteNote(i),'Research note deleted.');
 }
});
$('qf-v23-close').addEventListener('click',close);
$('qf-v23-save').addEventListener('click',()=>{const text=$('qf-v23-note').value.trim(),sym=selectedCompany()?.symbol;
 if(!text||!sym){setStatus('Select a company and enter a note.');return;}
 void work(async()=>{const data=await bridge().saveNote(text,sym);$('qf-v23-note').value='';return data;},'Research note saved.');
});
$('qf-v23-trade-submit').addEventListener('click',()=>{
 const symbol=$('qf-v23-trade-symbol').value,side=$('qf-v23-trade-side').value,amount=$('qf-v23-trade-amount').value;
 if(!window.confirm('Record this virtual '+side+' for '+symbol+'? No real brokerage order will be placed.'))return;
 void work(()=>bridge().trade(symbol,side,amount),'Virtual transaction recorded. No live order sent.');
});
$('qf-v23-refresh').addEventListener('click',()=>void work(()=>bridge().refresh(),'Owner data refreshed.'));
$('qf-v23-signout').addEventListener('click',()=>{
 if(!ready())return;
 void work(async()=>{await bridge().signOut();syncAccount();window.QFNavigate20('explore');return null;},'Signed out.');
});
window.addEventListener('qf:route-change',event=>{
 if(event.detail?.route==='private'&&ready()){
  const oldRoute=location.hash.match(/^#private\/([a-z]+)$/)?.[1];
  const destination=['home','trade'].includes(oldRoute)?'portfolio':
    ['lab','optimization','backtest','walkforward','valuation'].includes(oldRoute)?'models':
    oldRoute==='ideas'?'compare':'explore';
  window.QFNavigate20(destination);return;
 }
 if(event.detail?.route==='explore')setLanding(false);
 if(event.detail?.route!=='explore')landing=false;
});
window.addEventListener('qf:owner-auth-ready',()=>{syncAccount();window.QFNavigate20('explore');});
window.addEventListener('qf:owner-auth-ended',()=>{syncAccount();window.QFNavigate20('explore');});
const signed=$('private-signed');if(signed)new MutationObserver(syncAccount).observe(signed,{attributes:true,attributeFilter:['hidden']});
// A signed-in session opening a previously bookmarked legacy view uses the shared app instead.
if(ready()&&location.hash.startsWith('#private/'))window.QFNavigate20('explore');
populateAssets();syncAccount();
window.QFUnifiedPrivate23=Object.freeze({open,home:()=>setLanding(true),state:()=>({signedIn:ready(),landing})});
})();
