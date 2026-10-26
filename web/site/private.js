/* Hosted private mode, same Cloudflare website. No credentials or provider keys in source. */
(function () {
'use strict';
const $=id=>document.getElementById(id);
const M=window.QFModel;
let privateState=null, version=0, quoted={}, mfaFactorId=null;
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
function showStep(step){
  $('private-login').hidden=step!=='login';
  $('private-mfa').hidden=step!=='mfa';
  $('private-signed').hidden=step!=='ready';
  $('private-status').textContent=step==='ready'?'Private · Authenticator verified':
    step==='mfa'?'Private · Authenticator required':'Private · Sign in required';
}
function clearMFA(){
  mfaFactorId=null;
  $('private-mfa-code').value='';
  $('private-mfa-qr').removeAttribute('src');
  $('private-mfa-qr-wrap').hidden=true;
  $('private-mfa-setup-actions').hidden=true;
}
async function handleAuthState(state){
  if(state.signed_in){clearMFA();showStep('ready');await loadState();return;}
  if(!state.mfa_required){clearMFA();showStep('login');return;}
  showStep('mfa');
  if(state.mfa_setup){
    $('private-mfa-title').textContent='Set up your authenticator';
    $('private-mfa-instructions').textContent='Scan this private QR code in an authenticator app, then enter its six-digit code.';
    if(!mfaFactorId){$('private-mfa-setup-actions').hidden=false;}
    // Enrollment is a user action, never a GET/session side effect. Keep any
    // existing QR visible during an in-progress enrollment in this tab.
  }else{
    clearMFA();
    const factors=await api('auth/mfa/factors');
    mfaFactorId=factors.factor_id;
    $('private-mfa-title').textContent='Verify your authenticator';
    $('private-mfa-instructions').textContent='Enter the current code from your enrolled authenticator app.';
  }
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
    const state=await api('auth/login',{email:$('private-email').value.trim(),password:$('private-password').value});
    $('private-password').value='';await handleAuthState(state);
    message(state.signed_in?'Signed in.':'Password accepted. Authenticator verification required.');
  }catch(e){message(e.message);}
}
async function startMFASetup(){
  message('Starting authenticator setup…');
  try{
    const enroll=await api('auth/mfa/enroll',{});
    mfaFactorId=enroll.factor_id;
    $('private-mfa-setup-actions').hidden=true;
    // Supabase provides SVG markup. Show it as an image, never inject HTML.
    $('private-mfa-qr').src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(enroll.qr_svg);
    $('private-mfa-qr-wrap').hidden=false;
    message('Scan the QR, then verify the current code. Keep this page open until setup is complete.');
  }catch(e){message(e.message);}
}
async function verifyMFA(){
  const code=$('private-mfa-code').value.trim();
  if(!/^[0-9]{6}$/.test(code)){message('Enter the six-digit code.');return;}
  message('Verifying authenticator…');
  try{
    const data=await api('auth/mfa/verify',{factor_id:mfaFactorId||undefined,code});
    await handleAuthState(data);message('Authenticator verified. Your private workspace is unlocked.');
  }catch(e){message(e.message);}
}
async function logout(){
  try{await api('auth/logout',{});}catch(_){ /* Clear visible private content regardless */ }
  clearMFA();showStep('login');privateState=null;quoted={};$('private-positions').textContent='';
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
  try{const s=await api('auth/session');await handleAuthState(s);}
  catch(e){message('Private authentication needs attention: '+e.message);}
}
function updateMode(){
 const active=document.querySelector('.tabpage.active')?.id==='page-private';
 const badge=document.querySelector('.topbar .badge');
 if(badge)badge.textContent=active?'PRIVATE WORKSPACE':'FICTIONAL DATA';
 const eyebrow=document.querySelector('.topbar .eyebrow');
 if(eyebrow)eyebrow.textContent=active?'Your portfolio · Personal use':'Investment research · Public demonstration';
}
$('private-login-submit').addEventListener('click',login);
$('private-mfa-submit').addEventListener('click',verifyMFA);
$('private-mfa-start').addEventListener('click',startMFASetup);
$('private-mfa-logout').addEventListener('click',logout);
$('private-logout').addEventListener('click',logout);
$('private-quote-submit').addEventListener('click',currentQuote);
$('private-trade-submit').addEventListener('click',trade);
$('private-note-submit').addEventListener('click',addNote);
document.addEventListener('click',e=>{const b=e.target.closest('[data-page],[data-go]');if(b){queueMicrotask(updateMode);if(b.dataset.page==='private')checkSession();}});
$('private-symbol').innerHTML=M.ASSETS.map(a=>'<option value="'+safe(a.symbol)+'">'+safe(a.name)+' ('+safe(a.symbol)+')</option>').join('');
// Do not contact the private API while recruiters use the public demo.
})();
