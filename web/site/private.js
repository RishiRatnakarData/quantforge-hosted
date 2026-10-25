/* Hosted private mode, same Cloudflare website. No credentials or provider keys in source. */
(function () {
'use strict';
const $=id=>document.getElementById(id);
const M=window.QFModel;
let privateState=null, version=0, quoted={};
const usd=n=>Number(n).toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2});
const safe=s=>String(s).replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
function message(msg){$('private-message').textContent=msg;}
async function api(path, body){
  const init={credentials:'same-origin',cache:'no-store'};
  if(body!==undefined){init.method='POST';init.headers={'Content-Type':'application/json','X-QF-Action':'1'};init.body=JSON.stringify(body);}
  const r=await fetch('/api/'+path,init);
  let data;try{data=await r.json();}catch(_){throw Error('Service unavailable. Free hosting may be waking up.');}
  if(!r.ok)throw Error(data.detail || data.error || ('HTTP '+r.status));
  return data;
}
function showSignedIn(ok){$('private-login').hidden=ok;$('private-signed').hidden=!ok;
  $('private-status').textContent=ok?'Private · Signed in':'Private · Sign in required';
}
async function loadState(){
  const d=await api('private/state');privateState=d.portfolio;version=d.version;
  quoted={}; // Never carry fictional quotes across a private session.
  const symbols=Object.keys(privateState.holdings || {});
  if(symbols.length){
    try{const q=await api('private/quotes?symbols='+encodeURIComponent(symbols.join(',')));
      for(const item of q.quotes) quoted[item.symbol]=item;
    }catch(e){message('Portfolio loaded, but live quotes are unavailable: '+e.message);}
  }
  render();
}
function render(){
  if(!privateState)return;
  const holdings=privateState.holdings||{};let valued=0, incomplete=false;
  const rows=Object.entries(holdings).map(([sym,qty])=>{
    const q=quoted[sym],v=q?qty*q.price:null;
    if(v===null)incomplete=true;else valued+=v;
    return '<tr><td>'+safe(M.bySymbol[sym]?.name||sym)+' ('+safe(sym)+')</td><td>'+Number(qty).toFixed(6)+'</td><td>'+
        (q?usd(q.price):'Unavailable')+'</td><td>'+(v===null?'Unavailable':usd(v))+'</td><td>'+
        (q?safe(q.venue)+' · '+safe(q.timestamp):'—')+'</td></tr>';
  });
  $('private-cash').textContent=usd(privateState.cash);
  $('private-invested').textContent=incomplete?'Incomplete':usd(valued);
  $('private-total').textContent=incomplete?'Incomplete':usd(privateState.cash+valued);
  $('private-positions').innerHTML='<div class="table-wrap"><table><thead><tr><th>Investment</th><th>Units</th><th>Observed price</th><th>Value</th><th>Source / time</th></tr></thead><tbody>'+
    (rows.join('')||'<tr><td colspan="5">No virtual holdings yet.</td></tr>')+'</tbody></table></div>';
  $('private-watchlist').textContent=(privateState.watchlist||[]).join(', ')||'None';
  $('private-notes').innerHTML=(privateState.notes||[]).slice(0,8).map(n=>'<div class="subtle">'+safe(n.text)+'</div>').join('');
}
async function login(){
  message('Signing in…');
  try{
    await api('auth/login',{email:$('private-email').value.trim(),password:$('private-password').value});
    $('private-password').value='';showSignedIn(true);await loadState();message('Signed in.');
  }catch(e){showSignedIn(false);message(e.message);}
}
async function logout(){
  try{await api('auth/logout',{});}catch(_){ /* Clear visible private content regardless */ }
  showSignedIn(false);privateState=null;quoted={};$('private-positions').textContent='';
  $('private-total').textContent='—';$('private-invested').textContent='—';
  $('private-cash').textContent='—';$('private-notes').textContent='';message('Signed out.');
}
async function currentQuote(){
  message('Retrieving private market observation…');
  const symbol=$('private-symbol').value;
  try{
    const r=await api('private/quotes?symbols='+encodeURIComponent(symbol));
    const q=r.quotes[0];quoted[symbol]=q;
    $('private-quote').textContent=usd(q.price)+' · '+q.venue+' · '+q.timestamp+' (last trade, not executable price)';
    message('Quote loaded.');if(privateState)render();
  }catch(e){$('private-quote').textContent='Unavailable';message(e.message);}
}
async function trade(){
  if(!privateState){message('Sign in first.');return;}
  message('Validating virtual trade…');
  try{
    const r=await api('private/trade',{symbol:$('private-symbol').value,side:$('private-side').value,
      amount:$('private-amount').value,expected_version:version});
    privateState=r.portfolio;version=r.version;await loadState();
    message('Virtual transaction recorded. No brokerage order sent.');
  }catch(e){message(e.message);}
}
async function addNote(){
  if(!privateState)return;
  const t=$('private-note').value.trim();if(!t)return;
  const notes=[{text:t,at:new Date().toISOString(),symbol:$('private-symbol').value},...(privateState.notes||[])].slice(0,100);
  try{
    const d=await api('private/notes',{expected_version:version,watchlist:privateState.watchlist||[],notes});
    privateState=d.portfolio;version=d.version;$('private-note').value='';render();message('Private note saved.');
  }catch(e){message(e.message);}
}
async function checkSession(){
  try{const s=await api('auth/session');if(s.signed_in){showSignedIn(true);await loadState();}
    else showSignedIn(false);
  }catch(e){showSignedIn(false);message('Private service is unavailable. The public demo still works.');}
}
function updateMode(){
 const active=document.querySelector('.tabpage.active')?.id==='page-private';
 const badge=document.querySelector('.topbar .badge');
 if(badge)badge.textContent=active?'PRIVATE WORKSPACE':'FICTIONAL DATA';
 const eyebrow=document.querySelector('.topbar .eyebrow');
 if(eyebrow)eyebrow.textContent=active?'Your portfolio · Personal use':'Investment research · Public demonstration';
}
$('private-login-submit').addEventListener('click',login);
$('private-logout').addEventListener('click',logout);
$('private-quote-submit').addEventListener('click',currentQuote);
$('private-trade-submit').addEventListener('click',trade);
$('private-note-submit').addEventListener('click',addNote);
document.addEventListener('click',e=>{const b=e.target.closest('[data-page],[data-go]');if(b){queueMicrotask(updateMode);if(b.dataset.page==='private')checkSession();}});
$('private-symbol').innerHTML=M.ASSETS.map(a=>'<option value="'+safe(a.symbol)+'">'+safe(a.name)+' ('+safe(a.symbol)+')</option>').join('');
// Do not contact the private API while recruiters use the public demo.
})();
