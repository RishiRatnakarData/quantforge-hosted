/* Funding and trading share one account busy/uncertain-write boundary. No provider IO. */
(function(root){
'use strict';
const $=id=>document.getElementById(id),bridge=()=>root.QFPrivateBridgeV23,flow=()=>root.QFPortfolioUI27;
const privateMode=()=>bridge()?.ready()&&root.QFResearch20.context().mode==='private';
const safe=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const usd=n=>Number.isFinite(n)?n.toLocaleString('en-US',{style:'currency',currency:'USD'}):'Unavailable';
const shell=document.querySelector('.qf27-trade-shell');if(!shell)return;
const actions=shell.querySelector('.qf27-action-row'),body=document.createElement('div');body.className='qf28-investment-trade';
for(const node of [...shell.children])if(node!==actions)body.append(node);shell.append(body);
const fund=document.createElement('button');fund.className='btn';fund.id='qf28-fund';fund.textContent='Add / withdraw virtual funds';fund.setAttribute('aria-pressed','false');$('qf27-sell').after(fund);
const panel=document.createElement('section');panel.id='qf28-funding';panel.hidden=true;panel.innerHTML='<h3>Manage virtual funding</h3><p>Move hypothetical cash into or out of this saved virtual account. Contributions change capital, not investment profit. No bank or brokerage transfer occurs.</p>';
panel.append($('qf25-capital-action').closest('.qf24-assumptions'));shell.append(panel);
$('qf25-capital-amount').step='0.01';$('qf25-capital-submit').textContent='Preview funding change';panel.insertAdjacentHTML('beforeend','<div id="qf28-funding-preview"></div><button type="button" id="qf28-funding-confirm" class="btn primary" hidden>Confirm virtual funding</button><p id="qf28-funding-status" role="status" aria-live="polite"></p>');shell.append(panel);
const max=document.createElement('button');max.id='qf28-sell-max';max.className='btn';max.type='button';max.textContent='Use all owned units';max.hidden=true;$('qf27-trade-amount').closest('label').after(max);
const status=text=>$('qf28-funding-status').textContent=text;let preview=null,showing=false;
function clear(){preview=null;$('qf28-funding-preview').replaceChildren();$('qf28-funding-confirm').hidden=true;}
function showFunding(value){if(flow().actionState().busy)return;showing=value;panel.hidden=!value;body.hidden=value;fund.setAttribute('aria-pressed',String(value));if(value){$('qf27-buy').setAttribute('aria-pressed','false');$('qf27-sell').setAttribute('aria-pressed','false');clear();status('');$('qf25-capital-action').focus();}max.hidden=$('qf27-sell').getAttribute('aria-pressed')!=='true';}
fund.addEventListener('click',()=>showFunding(true));for(const id of ['qf27-buy','qf27-sell'])$(id).addEventListener('click',()=>showFunding(false));
max.addEventListener('click',()=>{const ownedMax=Number($('qf27-trade-amount').max);if(Number.isFinite(ownedMax)&&ownedMax>0){$('qf27-trade-amount').value=String(ownedMax);$('qf27-trade-amount').dispatchEvent(new Event('input'));}else $('qf27-trade-status').textContent='Select an owned position before using its maximum quantity.';});
for(const id of ['qf25-capital-action','qf25-capital-amount'])$(id).addEventListener('input',clear);
function busy(value,unknown=false){flow().setActionState(value,unknown);}
function applyState(){const state=flow().actionState();for(const id of ['qf28-fund','qf25-capital-submit','qf28-funding-confirm','qf25-capital-action','qf25-capital-amount','qf28-sell-max'])$(id).disabled=state.busy||state.uncertain;}
root.addEventListener('qf:account-action-state',applyState);
async function review(){
 if(!privateMode()||flow().actionState().busy||flow().actionState().uncertain)return;showFunding(true);clear();const action=$('qf25-capital-action').value,amount=$('qf25-capital-amount').value,version=bridge().snapshot().version;
 if(!Number.isFinite(Number(amount))||Number(amount)<1||Number(amount)>1000000){status('Enter between $1 and $1,000,000 in virtual funding.');return;}
 busy(true);status('Checking virtual cash and net contributions…');
 try{const result=await bridge().previewCapital(action,amount);if(!privateMode()||version!==bridge().snapshot().version){status('Account changed; refresh and preview again.');return;}const p=result.preview;if(!p||!Number.isFinite(p.cash_after)||!Number.isFinite(p.contributions_after))throw Error('Funding preview is incomplete.');preview={...p,version,request_id:root.crypto.randomUUID()};$('qf28-funding-preview').innerHTML='<h4>Review virtual '+safe(action)+'</h4><dl class="qf27-preview-grid">'+[['Amount',usd(p.amount)],['Cash before',usd(p.cash_before)],['Cash after',usd(p.cash_after)],['Net contributions after',usd(p.contributions_after)]].map(([k,v])=>'<div><dt>'+safe(k)+'</dt><dd>'+safe(v)+'</dd></div>').join('')+'</dl><p>The same server Decimal calculation is revalidated when you confirm. This funding is not a return.</p>';$('qf28-funding-confirm').hidden=false;status('Review the funding change before confirming.');}
 catch(e){status(e.message||'Funding preview unavailable. Nothing was saved.');}finally{busy(false);}
}
$('qf28-funding-confirm').addEventListener('click',async()=>{
 if(!privateMode()||!preview||flow().actionState().busy||flow().actionState().uncertain)return;
 if(preview.version!==bridge().snapshot().version){clear();status('Account changed; refresh and preview again.');return;}const p=preview;busy(true);status('Recording one virtual funding change…');let unknown=false;
 try{const saved=await bridge().capital(p.action,p.amount,{request_id:p.request_id});if(!privateMode())return;$('qf27-ledger-filter').value='all';$('qf27-ledger-filter').dispatchEvent(new Event('change'));flow().paint(saved);clear();status('Virtual funding recorded. Cash and contributed capital updated; investment profit is unchanged.');root.dispatchEvent(new Event('qf:owner-state'));}
 catch(e){unknown=!e.status||(e.status>=500&&e.code!=='write_rejected');clear();status(unknown?'The funding response was interrupted and may have saved. Refresh account and inspect recent activity before another attempt. No automatic retry was sent.':e.message);}
 finally{busy(false,unknown);}
});
root.addEventListener('qf:owner-state',()=>{if(preview&&preview.version!==bridge().snapshot()?.version)clear();if(showing&&!flow().actionState().uncertain&&$('qf28-funding-status').textContent.includes('interrupted'))status('Saved account refreshed. Inspect the newest funding receipt before creating another change.');applyState();});
for(const event of ['qf:data-mode','qf:owner-auth-ended'])root.addEventListener(event,()=>{clear();status('');panel.hidden=true;body.hidden=false;showing=false;fund.setAttribute('aria-pressed','false');});
root.QFFunding28=Object.freeze({review});applyState();
})(window);
