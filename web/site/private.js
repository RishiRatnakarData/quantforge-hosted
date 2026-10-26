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
  if(state.signed_in){clearMFA();showStep('ready');await loadState();privatePeers();return;}
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
  const entries=Object.entries(holdings),worth=privateState.cash+valued;
  $('private-concentration').innerHTML=entries.length?entries.map(([symbol,units])=>{const weight=quoted[symbol]?units*quoted[symbol].price/worth:null;return '<div class="row"><span>'+safe(symbol)+'</span><strong>'+(weight===null?'Quote unavailable':percent(weight))+'</strong></div>';}).join(''):'No holdings yet. Visit Virtual trading to begin.';
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
  clearMFA();showStep('login');privateState=null;quoted={};historySeries=null;
  $('private-history-chart').textContent='Load a historical series to begin.';$('private-risk-results').textContent='';$('private-backtest-output').textContent='';$('private-valuation-output').textContent='';$('private-peers').textContent='';$('private-concentration').textContent='';$('private-positions').textContent='';
  $('private-total').textContent='—';$('private-invested').textContent='—';
  $('private-cash').textContent='—';$('private-notes').textContent='';message('Signed out.');privateTab('home');
}
async function currentQuote(){
  message('Retrieving private market observation…');
  const symbol=$('private-symbol').value.trim().toUpperCase();
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
    const r=await api('private/trade',{symbol:$('private-symbol').value.trim().toUpperCase(),side:$('private-side').value,
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
 // Public page labels belong to app.js navigation; never overwrite them.
 const active=document.querySelector('.tabpage.active')?.id==='page-private';
 if(!active)return;
 const badge=document.querySelector('.topbar .badge');
 if(badge)badge.textContent='PRIVATE WORKSPACE';
 const eyebrow=document.querySelector('.topbar .eyebrow');
 if(eyebrow)eyebrow.textContent='Your portfolio · Personal use';
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
$('private-symbol-list').innerHTML=M.ASSETS.map(a=>'<option value="'+safe(a.symbol)+'">'+safe(a.name)+'</option>').join('');
// Do not contact the private API from the public-only pages.
/* V6: authenticated research tools. No Alpaca credentials or private data in public code. */
let historySeries=null;
const finite=n=>typeof n==='number'&&Number.isFinite(n);
const percent=n=>finite(n)?(n*100).toFixed(2)+'%':'Unavailable';
const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
function sampleStdev(a){if(a.length<2)return 0;const m=mean(a);return Math.sqrt(a.reduce((x,y)=>x+(y-m)*(y-m),0)/(a.length-1));}
function maxDD(values){let high=0,deep=0;for(const v of values){high=Math.max(high,v);if(high)deep=Math.min(deep,v/high-1);}return deep;}
function displayTable(headers,rows){return '<div class="table-wrap"><table><thead><tr>'+headers.map(h=>'<th>'+safe(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(v=>'<td>'+safe(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function privateTab(tab){
 document.querySelectorAll('[data-private-view]').forEach(p=>p.hidden=p.dataset.privateView!==tab);
 document.querySelectorAll('.private-nav [data-private-tab]').forEach(b=>b.classList.toggle('active',b.dataset.privateTab===tab));
}
function normalizedSeries(series){
 const rows=series.symbols.map(s=>series.closes[s]);
 if(rows.some(a=>!Array.isArray(a)||a.length!==series.dates.length||a.some(x=>!finite(x)||x<=0)))throw Error('Incomplete historical price series.');
 return rows;
}
function svgIndexChart(series){
 const rows=normalizedSeries(series);const n=series.dates.length;
 const tracks=rows.map(a=>a.map(x=>x/a[0]*100));
 const all=tracks.flat();let lo=Math.min(...all),hi=Math.max(...all);const pad=(hi-lo)||1;lo-=pad*.08;hi+=pad*.08;
 const colors=['#0a6658','#c78a39','#386eac','#874ba0','#b85850'];
 const plots=tracks.map((track,i)=>{
  const points=track.map((v,k)=>`${(15+k*570/(n-1)).toFixed(2)},${(205-(v-lo)/(hi-lo)*185).toFixed(2)}`).join(' ');
  return `<polyline fill="none" stroke="${colors[i%colors.length]}" stroke-width="2" points="${points}"/>`;
 }).join('');
 return '<svg viewBox="0 0 600 245" role="img" aria-label="Historical prices indexed to 100; '+safe(series.symbols.join(', '))+'"><line x1="14" y1="210" x2="588" y2="210" stroke="#cad9d2"/>'+plots+'<text x="14" y="235" fill="#5f746e" font-size="11">'+safe(series.dates[0])+'</text><text x="475" y="235" fill="#5f746e" font-size="11">'+safe(series.dates[n-1])+'</text></svg>'+
 '<div class="controls tiny">'+series.symbols.map((s,i)=>'<span style="color:'+colors[i%colors.length]+'">● '+safe(s)+'</span>').join(' ')+'</div>';
}
function equalReturns(series){
 const rows=normalizedSeries(series), len=series.dates.length;const changes=[];
 for(let t=1;t<len;t++)changes.push(mean(rows.map(a=>a[t]/a[t-1]-1)));
 return changes;
}
function privateRisk(series){
 const ret=equalReturns(series),wealth=[100];for(const r of ret)wealth.push(wealth.at(-1)*(1+r));
 const sorted=[...ret].sort((a,b)=>a-b),bottom=Math.max(1,Math.ceil(.05*sorted.length));
 const var95=Math.max(0,-sorted[bottom-1]),es=Math.max(0,-mean(sorted.slice(0,bottom)));
 const sdev=sampleStdev(ret)*Math.sqrt(252),total=wealth.at(-1)/wealth[0]-1;
 const rows=[['Aligned sessions',String(ret.length)],['Equal-weight daily average return',percent(mean(ret))],['Annualized historical volatility',percent(sdev)],['5% historical daily VaR',percent(var95)],['5% historical daily expected shortfall',percent(es)],['Worst historical drawdown',percent(maxDD(wealth))],['Compounded indexed change',percent(total)]];
 return '<h3 style="margin:18px 0 10px">Historical return statistics</h3>'+displayTable(['Measure','Result'],rows)+'<p class="tiny">Equal-weight daily return series with simple arithmetic returns. VaR/ES are empirical one-day historical statistics, not forward forecasts. Prices exclude dividends.</p>';
}
async function loadHistory(){
 const raw=$('private-history-symbols').value.toUpperCase().replace(/\s+/g,'');
 const syms=raw.split(',');
 if(syms.length<2||syms.length>5||new Set(syms).size!==syms.length||syms.some(x=>!/^\w[A-Z0-9.]{0,9}$/.test(x))) {message('Enter 2–5 distinct stock or ETF tickers.');return;}
 message('Retrieving private market history…');$('private-history-source').textContent='';
 try{
  const d=await api('private/history?symbols='+encodeURIComponent(raw)+'&days='+encodeURIComponent($('private-history-days').value));
  historySeries=d;
  $('private-history-chart').innerHTML=svgIndexChart(d);
  $('private-history-source').textContent=d.source+' · through '+d.as_of;
  $('private-risk-results').innerHTML=privateRisk(d);
  message('Historical market research loaded.');
 }catch(e){historySeries=null;message(e.message);$('private-history-chart').textContent='Market history unavailable.';$('private-risk-results').textContent='';$('private-backtest-output').textContent='';}
}
function wealthStats(values){let out=values.at(-1)/values[0]-1;return [percent(out),percent(maxDD(values))];}
function privateBacktest(){
 if(!historySeries){message('Load historical market research first.');privateTab('research');return;}
 const dollars=Number($('private-test-capital').value),fee=Number($('private-test-fee').value)/10000;
 if(!finite(dollars)||dollars<100||dollars>1_000_000||!finite(fee)||fee<0||fee>.01){message('Check starting balance and fee.');return;}
 const d=historySeries,a=normalizedSeries(d),N=a.length,T=d.dates.length;
 const holdUnits=a.map(b=>dollars/N/b[0]);const hold=[];
 for(let t=0;t<T;t++)hold.push(holdUnits.reduce((v,u,k)=>v+u*a[k][t],0));
 let units=[...holdUnits],equity=[],paid=0;
 for(let t=0;t<T;t++){
  let values=units.map((u,k)=>u*a[k][t]),total=values.reduce((x,y)=>x+y,0);
  if(t>0&&d.dates[t].slice(0,7)!==d.dates[t-1].slice(0,7)){
   const target=total/N;
   const turnover=values.reduce((s,v)=>s+Math.abs(v-target),0);
   const commission=turnover*fee;paid+=commission;
   const newEach=(total-commission)/N;
   units=units.map((u,k)=>newEach/a[k][t]);total-=commission;
  }
  equity.push(total);
 }
 const holdStats=wealthStats(hold),rebalanceStats=wealthStats(equity);
 $('private-backtest-output').innerHTML=displayTable(['Measure','Buy & hold','Monthly rebalance'],[
  ['Ending virtual capital',usd(hold.at(-1)),usd(equity.at(-1))],
  ['Period return',holdStats[0],rebalanceStats[0]],
  ['Maximum drawdown',holdStats[1],rebalanceStats[1]],
  ['Rebalancing costs',usd(0),usd(paid)]
 ])+'<p class="tiny">Equal-weight initial allocation, monthly close rebalances, '+safe($('private-test-fee').value)+' bps on gross dollar turnover. No slippage, dividends, taxes or corporate-action forecasts. Historical illustration only; no brokerage orders.</p>';
 message('Historical strategy comparison calculated.');
}
function privateValuation(){
 const snap=window.QFPublishedSEC;
 if(!snap||!Array.isArray(snap.companies))return;
 const sym=$('private-valuation-company').value,c=snap.companies.find(x=>x.symbol===sym);
 const fcf=Number(c?.annual?.[0]?.metrics?.free_cash_flow_usd);
 const raw=c?.annual?.[0]?.metrics?.free_cash_flow_usd;
 const rate=Number($('private-valuation-wacc').value)/100,g=Number($('private-valuation-growth').value)/100,term=Number($('private-valuation-terminal').value)/100;
 if(raw==null||!finite(fcf)||fcf<=0){$('private-valuation-output').textContent='A positive comparable FCF proxy is not available for this company.';return;}
 if(![rate,g,term].every(finite)||rate<=term||rate<.02||rate>.30||g<-.30||g>.4||term<-.05||term>.08){message('Check growth and discount inputs; discount rate must exceed terminal growth.');return;}
 let discounted=0,fcfNext=fcf;for(let year=1;year<=5;year++){fcfNext*=1+g;discounted+=fcfNext/(1+rate)**year;}
 const terminalValue=(fcfNext*(1+term)/(rate-term))/(1+rate)**5;
 $('private-valuation-output').innerHTML=displayTable(['Calculation','Value'],[
  ['Reported-period FCF proxy',usd(fcf)],
  ['5-year discounted cash flow proxy',usd(discounted)],
  ['Discounted terminal component',usd(terminalValue)],
  ['Illustrative present value',usd(discounted+terminalValue)]
 ])+'<p class="tiny">Based on SEC cash flow from operations less cash PP&E spending, not unlevered FCFF. This is a present-value sensitivity, not a per-share target, equity valuation, or investment recommendation. It omits debt, cash, taxes, and other adjustments.</p>';
}
function privatePeers(){
 const snap=window.QFPublishedSEC;
 if(!snap||!Array.isArray(snap.companies))return;
 const rows=snap.companies.map(c=>{
  const m=c.annual?.[0]?.metrics||{},rev=m.revenue_usd,inc=m.operating_income_usd;
  return [c.name+' ('+c.symbol+')', rev==null?'Unavailable':usd(rev),inc==null||!rev?'Unavailable':percent(inc/rev),m.free_cash_flow_usd==null?'Unavailable':usd(m.free_cash_flow_usd)];
 });
 $('private-peers').innerHTML=displayTable(['Company','Annual revenue','Operating margin','FCF proxy'],rows)+
 '<p class="tiny">Different fiscal year ends and accounting definitions; descriptive comparison only.</p>';
}
async function changeCapital(){
 if(!privateState)return;
 const action=$('private-capital-action').value,amount=$('private-capital-amount').value;
 if(!Number.isFinite(Number(amount))||Number(amount)<1||Number(amount)>1_000_000){message('Enter virtual capital between $1 and $1,000,000.');return;}
 let confirmation='';
 if(action==='reset'){
  if(!window.confirm('Clear your virtual trades and positions? Private research notes will remain.'))return;
  confirmation=window.prompt('Type RESET to confirm resetting the virtual portfolio.','')||'';
  if(confirmation!=='RESET'){message('Reset cancelled.');return;}
 }
 try{
  const data=await api('private/capital',{action,amount,confirmation,expected_version:version});
  privateState=data.portfolio;version=data.version;await loadState();
  message('Virtual account updated. No real funds were moved.');privateTab('home');
 }catch(e){message(e.message);}
}
document.querySelectorAll('[data-private-tab]').forEach(b=>b.addEventListener('click',()=>privateTab(b.dataset.privateTab)));
$('private-history-load').addEventListener('click',loadHistory);
$('private-backtest-run').addEventListener('click',privateBacktest);
$('private-valuation-run').addEventListener('click',privateValuation);
$('private-capital-submit').addEventListener('click',changeCapital);
$('private-valuation-company').innerHTML=(window.QFPublishedSEC?.companies||[]).map(c=>'<option value="'+safe(c.symbol)+'">'+safe(c.name)+'</option>').join('');
privatePeers();

})();
