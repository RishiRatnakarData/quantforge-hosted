/* Shared name-first picker. Listing metadata never establishes market-data entitlement. */
(function(root){
'use strict';
const safe=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const valid=s=>typeof s==='string'&&/^[A-Z0-9./-]{1,15}$/.test(s);
const recent=[];const queryText=text=>text.trim().match(/\(([A-Z0-9./-]{1,15})\)$/i)?.[1]||text.trim();
function instrument(item){if(item.asset_class==='crypto')return 'Crypto';if(/\b(leveraged|inverse|ultra|direxion|graniteshares|t-rex|2x|3x|daily bull|daily bear)\b/i.test(item.name))return 'Leveraged / inverse fund (name indication)';return item.instrument_type||(/\b(etf|fund|trust|ultra|direxion|graniteshares|t-rex|2x|3x)\b/i.test(item.name)?'ETF / fund':'Equity listing');}
function rank(items,query){const q=queryText(query).toLowerCase();if(!q)return items.filter(x=>x&&valid(x.symbol)&&typeof x.name==='string');return items.filter(x=>x&&valid(x.symbol)&&typeof x.name==='string'&&(x.name.toLowerCase().includes(q)||x.symbol.toLowerCase().includes(q))).slice().sort((a,b)=>{
 const score=x=>(x.symbol.toLowerCase()===q?1000:0)+(x.name.toLowerCase()===q?800:0)+(x.name.toLowerCase().startsWith(q)?200:0)+(/fund|ETF|leverag|inverse/i.test(instrument(x))?0:30);
 return score(b)-score(a)||a.name.localeCompare(b.name);
});}
function describe(item,privateMode,covered){return [instrument(item)+(item.instrument_type_source?.startsWith('name')?' (name-based subtype; verify listing)':''),item.exchange||'Exchange not supplied',covered?'SEC annual statements covered':'SEC snapshot not covered',privateMode?'Price history: not verified until loaded':'Public financials; no observed market prices',privateMode&&item.tradable!==false?'Virtual transactions: listing eligible; fresh quote required':'Virtual transactions: unavailable in public mode'];}
function mount({input,panel,mode,search,published,onSelect,owned,assetClasses=['us_equity']}){
 let token=0,timer,controller,rows=[],active=-1,chosen=false;
 input.setAttribute('role','combobox');input.setAttribute('aria-controls',panel.id);input.setAttribute('aria-expanded','false');input.setAttribute('aria-autocomplete','list');input.removeAttribute('list');panel.setAttribute('role','listbox');panel.classList.add('qf27-picker-results');panel.hidden=true;
 function close(){panel.hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');active=-1;}
 function reset(){chosen=false;token++;clearTimeout(timer);controller?.abort();rows=[];panel.replaceChildren();close();}
 function select(index){const item=rows[index];if(!item)return;chosen=true;token++;controller?.abort();clearTimeout(timer);const prior=recent.indexOf(item.symbol);if(prior>=0)recent.splice(prior,1);recent.unshift(item.symbol);recent.splice(8);close();input.value='';onSelect(item);}
 function paint(items){rows=rank(items,input.value);if(!queryText(input.value)){const saved=mode()==='private'?(root.QFPrivateBridgeV23?.snapshot?.()?.watchlist||[]):[];const priority=x=>recent.includes(x.symbol)?recent.indexOf(x.symbol):saved.includes(x.symbol)?8:20;rows.sort((a,b)=>priority(a)-priority(b));}rows=rows.slice(0,12);active=-1;panel.innerHTML=rows.length?rows.map((item,i)=>'<button id="'+panel.id+'-'+i+'" type="button" role="option" aria-selected="false" data-qf27-index="'+i+'" data-qf27-symbol="'+safe(item.symbol)+'"><strong>'+safe(item.name)+' <span>'+safe(item.symbol)+'</span></strong><small>'+describe(item,mode()==='private',published.some(c=>c.symbol===item.symbol)).map(safe).join(' · ')+'</small></button>').join(''):'<p>No eligible matches. Try a full company name or exact ticker.</p>';panel.hidden=false;input.setAttribute('aria-expanded','true');}
 async function find(){const id=++token,q=queryText(input.value);controller?.abort();controller=new AbortController();
  const positions=owned?.();if(Array.isArray(positions)){paint(positions.filter(x=>!q||x.name.toLowerCase().includes(q.toLowerCase())||x.symbol.toLowerCase().includes(q.toLowerCase())));return;}
  if(mode()!=='private'){let list=published.filter(x=>!q||x.name.toLowerCase().includes(q.toLowerCase())||x.symbol.toLowerCase().includes(q.toLowerCase()));if(!q)list.sort((a,b)=>(recent.includes(a.symbol)?recent.indexOf(a.symbol):-1+100)-(recent.includes(b.symbol)?recent.indexOf(b.symbol):-1+100));paint(list);return;}
  panel.hidden=false;input.setAttribute('aria-expanded','true');panel.textContent='Searching authenticated provider listings…';
  try{const result=await search(q,controller.signal);if(id!==token||mode()!=='private')return;if(result.licensed_private!==true||!Array.isArray(result.items))throw Error('Directory unavailable');paint(result.items.filter(x=>assetClasses.includes(x.asset_class)));}
  catch(e){if(id===token&&e.name!=='AbortError'){rows=[];panel.textContent='Provider search unavailable. Existing selections remain available; no substitute list is used.';}}
 }
 input.addEventListener('input',()=>{chosen=false;token++;controller?.abort();rows=[];close();clearTimeout(timer);timer=setTimeout(find,200);});input.addEventListener('focus',()=>{if(panel.hidden&&!chosen)void find();});
 input.addEventListener('keydown',e=>{
  if(e.key==='Escape'){reset();return;}
  if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();if(panel.hidden){void find();return;}active=Math.max(0,Math.min(rows.length-1,active+(e.key==='ArrowDown'?1:-1)));panel.querySelectorAll('[role=option]').forEach((button,i)=>button.setAttribute('aria-selected',String(i===active)));if(active>=0){input.setAttribute('aria-activedescendant',panel.id+'-'+active);panel.children[active]?.scrollIntoView({block:'nearest'});}}
  if(e.key==='Enter'&&active>=0){e.preventDefault();select(active);}
 });
 panel.addEventListener('click',e=>{const option=e.target.closest('[data-qf27-index]');if(option)select(Number(option.dataset.qf27Index));});
 root.document.addEventListener('click',e=>{if(e.target!==input&&!panel.contains(e.target))close();});
 for(const event of ['qf:data-mode','qf:owner-auth-ended'])root.addEventListener(event,()=>{recent.length=0;reset();input.value='';});
 return Object.freeze({reset,find});
}
const api=Object.freeze({mount,rank,describe,instrument});root.QFInvestmentPicker27=api;
if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
