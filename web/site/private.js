/* Hosted private mode, same Cloudflare website. No credentials or provider keys in source. */
(function () {
'use strict';
const $=id=>document.getElementById(id);
const M=window.QFModel;
let privateState=null, version=0, quoted={}, mfaFactorId=null;
let researchSelection=[];
let valuationCompanies={};
let assetNames={};
const browserState={mode:'trade',category:'popular',letter:'',query:'',page:0,pages:1};
let browserRequest=0, browserDebounce;

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
  $('private-notes').innerHTML=(privateState.notes||[]).map((n,i)=>'<div class="saved-note"><div class="saved-note-body"><p>'+safe(n.text)+'</p><span class="tiny">'+safe(n.at||'Saved note')+'</span></div><button class="btn sm" type="button" data-note-delete="'+i+'" aria-label="Delete note '+(i+1)+'">Delete</button></div>').join('')||'<p class="tiny">No notes saved.</p>';
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
  clearMFA();showStep('login');privateState=null;quoted={};historySeries=null;closeAssetBrowser();researchSelection=[];$('private-symbol').value='';$('private-selected-asset').textContent='No investment selected';renderResearchSelection();
  optimizerResult=null;$('private-opt-export').disabled=true;$('private-opt-output').textContent='Load market history to begin.';$('private-opt-risk').textContent='';
  $('private-history-chart').textContent='Load a historical series to begin.';$('private-risk-results').textContent='';$('private-backtest-output').textContent='';$('private-valuation-output').textContent='';$('private-peers').textContent='';$('private-concentration').textContent='';$('private-positions').textContent='';
  $('private-total').textContent='—';$('private-invested').textContent='—';
  $('private-cash').textContent='—';$('private-notes').textContent='';valuationCompanies={};$('private-valuation-company').value='';$('private-valuation-selected').textContent='No company selected';message('Signed out.');privateTab('home');
}
async function currentQuote(){
  message('Retrieving private market observation…');
  const symbol=$('private-symbol').value.trim().toUpperCase();
  if(!symbol){message('Choose an investment with Browse investments first.');return;}
  try{
    const r=await api('private/quotes?symbols='+encodeURIComponent(symbol));
    const q=r.quotes[0];quoted[symbol]=q;
    $('private-quote').textContent=usd(q.price)+' · '+q.venue+' · '+q.timestamp+' (last trade, not executable price)';
    message('Quote loaded.');if(privateState)render();
  }catch(e){$('private-quote').textContent='Unavailable';message(e.message);}
}
async function trade(){
  if(!privateState){message('Sign in first.');return;}
  if(!$('private-symbol').value){message('Choose an investment before trading.');return;}
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
async function deleteNote(index){
 if(!privateState || !Number.isInteger(index))return;
 const previous=privateState.notes||[];
 if(index<0||index>=previous.length)return;
 if(!window.confirm('Delete this saved research note? This cannot be undone.'))return;
 const notes=previous.filter((_,i)=>i!==index);
 try{
  const d=await api('private/notes',{expected_version:version,watchlist:privateState.watchlist||[],notes});
  privateState=d.portfolio;version=d.version;render();message('Selected note deleted.');
 }catch(e){message('Note was not deleted: '+e.message);}
}
$('private-notes').addEventListener('click',e=>{
 const button=e.target.closest('[data-note-delete]');
 if(button&&$('private-notes').contains(button))deleteNote(Number(button.dataset.noteDelete));
});
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
// Investment names come from private Alpaca asset discovery after MFA.
// Do not contact the private API from the public-only pages.
/* Private asset directory: click-to-select. Name search is optional. */
function renderResearchSelection(){
 const target=$('private-history-selection');
 $('private-history-symbols').value=researchSelection.join(',');
 if(!researchSelection.length){target.textContent='Choose investments to compare.';return;}
 target.innerHTML=researchSelection.map(symbol=>'<button type="button" class="asset-chip" data-research-remove="'+safe(symbol)+'" aria-label="Remove '+safe(symbol)+'">'+safe(assetNames[symbol]||symbol)+' ('+safe(symbol)+') ×</button>').join('');
}
function closeAssetBrowser(){
 browserRequest++;
 const dialog=$('private-asset-browser');
 if(dialog)dialog.hidden=true;
}
async function openAssetBrowser(mode){
 if(!privateState){message('Sign in and verify your authenticator first.');return;}
 browserState.mode=mode;
 browserState.category='popular';browserState.letter='';browserState.query='';browserState.page=0;
 $('asset-browser-search').value='';
 $('private-asset-browser').hidden=false;
 $('asset-browser-letters').innerHTML=['All',...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'].map(letter=>'<button type="button" data-asset-letter="'+(letter==='All'?'':letter)+'">'+letter+'</button>').join('');
 await loadBrowserPage();
 $('asset-browser-close').focus();
}
function browserParams(){
 return 'private/assets?'+new URLSearchParams({category:browserState.category,letter:browserState.letter,query:browserState.query,page:String(browserState.page)});
}
async function loadBrowserPage(){
 const id=++browserRequest;
 $('asset-browser-status').textContent='Loading investments…';
 $('asset-browser-results').textContent='';
 try{
  const data=await api(browserParams());
  if(id!==browserRequest||$('private-asset-browser').hidden||!privateState)return;
  browserState.pages=data.pages;
  $('asset-browser-status').textContent=data.total+' available investments · '+data.source;
  $('asset-browser-results').innerHTML=data.items.length?data.items.map(a=>'<button class="picker-item" type="button" data-asset-select="'+safe(a.symbol)+'" data-asset-kind="'+safe(a.asset_class)+'" data-asset-name="'+safe(a.name)+'"><strong>'+safe(a.name)+'</strong><span>'+safe(a.symbol)+' · '+safe(a.exchange||a.asset_class)+'</span></button>').join(''):'<p>No investments found for this filter. Choose another letter or category.</p>';
  $('asset-browser-page').textContent='Page '+(data.page+1)+' of '+data.pages;
  $('asset-browser-prev').disabled=!data.has_previous;
  $('asset-browser-next').disabled=!data.has_next;
  document.querySelectorAll('[data-asset-category]').forEach(b=>b.classList.toggle('active',b.dataset.assetCategory===browserState.category));
  document.querySelectorAll('[data-asset-letter]').forEach(b=>b.classList.toggle('active',b.dataset.assetLetter===browserState.letter));
 }catch(e){if(id===browserRequest)$('asset-browser-status').textContent=e.message;}
}
function chooseAsset(symbol,name,kind){
 if(!privateState)return;
 assetNames[symbol]=name;
 if(browserState.mode==='valuation'){
  if(kind==='crypto'){message('Crypto assets do not have SEC corporate financial statements.');return;}
  $('private-valuation-company').value=symbol;
  $('private-valuation-selected').textContent=name+' ('+symbol+')';
  $('private-valuation-output').textContent='Select Run scenario to load available SEC filings.';
  message('Selected '+name+'. SEC statements will be checked when you run the scenario.');
 }else if(browserState.mode==='trade'){
  $('private-symbol').value=symbol;
  $('private-selected-asset').textContent=name+' ('+symbol+')';
  $('private-quote').textContent='Get market price to inspect the current observation.';
  message('Selected '+name+'. No trade has been placed.');
 }else{
  if(kind==='crypto'){message('Historical research currently uses U.S. stocks and ETFs.');return;}
  if(!researchSelection.includes(symbol)){
   if(researchSelection.length>=5){message('You can compare up to five investments. Remove one first.');return;}
   researchSelection.push(symbol);
  }
  renderResearchSelection();historySeries=null;optimizerResult=null;$('private-opt-export').disabled=true;$('private-opt-output').textContent='Selection changed. Load the updated historical series first.';$('private-opt-risk').textContent='';
  $('private-history-chart').textContent='Load market history for the selected investments.';
  $('private-backtest-output').textContent='';
  message('Added '+name+' to your historical research selection.');
 }
 closeAssetBrowser();
}
$('private-browse-trade').addEventListener('click',()=>openAssetBrowser('trade'));
$('private-browse-research').addEventListener('click',()=>openAssetBrowser('research'));
$('private-browse-valuation').addEventListener('click',()=>openAssetBrowser('valuation'));
$('asset-browser-close').addEventListener('click',closeAssetBrowser);
$('asset-browser-prev').addEventListener('click',()=>{if(browserState.page>0){browserState.page--;loadBrowserPage();}});
$('asset-browser-next').addEventListener('click',()=>{if(browserState.page+1<browserState.pages){browserState.page++;loadBrowserPage();}});
$('asset-browser-search').addEventListener('input',()=>{
 clearTimeout(browserDebounce);
 browserDebounce=setTimeout(()=>{browserState.query=$('asset-browser-search').value;browserState.page=0;loadBrowserPage();},220);
});
$('private-asset-browser').addEventListener('click',e=>{
 if(e.target.id==='private-asset-browser'){closeAssetBrowser();return;}
 const cat=e.target.closest('[data-asset-category]');
 if(cat){browserState.category=cat.dataset.assetCategory;browserState.letter='';browserState.page=0;loadBrowserPage();return;}
 const letter=e.target.closest('[data-asset-letter]');
 if(letter){browserState.letter=letter.dataset.assetLetter;browserState.page=0;loadBrowserPage();return;}
 const asset=e.target.closest('[data-asset-select]');
 if(asset){chooseAsset(asset.dataset.assetSelect,asset.dataset.assetName,asset.dataset.assetKind);}
});
$('private-history-selection').addEventListener('click',e=>{
 const b=e.target.closest('[data-research-remove]');
 if(!b)return;
 researchSelection=researchSelection.filter(s=>s!==b.dataset.researchRemove);
 renderResearchSelection();historySeries=null;optimizerResult=null;$('private-opt-export').disabled=true;$('private-opt-output').textContent='Selection changed. Load the updated historical series first.';$('private-opt-risk').textContent='';
 $('private-history-chart').textContent='Load market history for the selected investments.';
 $('private-backtest-output').textContent='';
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('private-asset-browser').hidden)closeAssetBrowser();});
renderResearchSelection();

/* V6: authenticated research tools. No Alpaca credentials or private data in public code. */
let optimizerResult=null;
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
 const raw=researchSelection.join(',');
 const syms=researchSelection;
 if(syms.length<2||syms.length>5){message('Select 2–5 different stocks or ETFs using Browse investments.');return;}
 message('Retrieving private market history…');$('private-history-source').textContent='';
 try{
  const d=await api('private/history?symbols='+encodeURIComponent(raw)+'&days='+encodeURIComponent($('private-history-days').value));
  // A pending fetch may finish after sign-out or a changed investment selection.
  if(!privateState || researchSelection.join(',')!==raw)return;
  optimizerResult=null;$('private-opt-export').disabled=true;
  $('private-opt-output').textContent='History loaded. Open Optimization to calculate allocations.';
  $('private-opt-risk').textContent='Risk diagnostics appear after an allocation is calculated.';
  historySeries=d;
  $('private-history-chart').innerHTML=svgIndexChart(d);
  $('private-history-source').textContent=d.source+' · through '+d.as_of;
  $('private-risk-results').innerHTML=privateRisk(d);
  message('Historical market research loaded.');
 }catch(e){optimizerResult=null;$('private-opt-export').disabled=true;historySeries=null;message(e.message);$('private-history-chart').textContent='Market history unavailable.';$('private-risk-results').textContent='';$('private-backtest-output').textContent='';}
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
async function privateValuation(){
 const symbol=$('private-valuation-company').value;
 if(!symbol){message('Choose a company with Browse companies first.');return;}
 $('private-valuation-output').textContent='Loading available SEC annual filings…';
 let company=valuationCompanies[symbol];
 if(!company){
  try{
   company=await api('private/sec/company?symbol='+encodeURIComponent(symbol));
   if(!privateState)return;
   valuationCompanies[symbol]=company;
  }catch(e){$('private-valuation-output').textContent='No comparable SEC figures were loaded. '+e.message;message(e.message);return;}
 }
 const metrics=company.annual?.[0]?.metrics||{},raw=metrics.free_cash_flow_usd;
 const companyName=company.name+' ('+company.symbol+')';
 const rows=[['Issuer',companyName],['SEC annual period ending',company.annual?.[0]?.fiscal_end||'Unavailable'],
 ['Revenue',metrics.revenue_usd==null?'Unavailable':usd(metrics.revenue_usd)],
 ['Operating income',metrics.operating_income_usd==null?'Unavailable':usd(metrics.operating_income_usd)],
 ['Operating cash flow',metrics.operating_cash_flow_usd==null?'Unavailable':usd(metrics.operating_cash_flow_usd)],
 ['Cash PP&E purchases',metrics.capex_usd==null?'Unavailable':usd(metrics.capex_usd)],
 ['Free-cash-flow proxy',raw==null?'Unavailable':usd(raw)]];
 const source=/^https:\/\/data\.sec\.gov\/api\/xbrl\/companyfacts\/CIK[0-9]{10}\.json$/.test(company.source_url||'')?company.source_url:'';
 const provenance='<p class="tiny">Source: '+safe(company.source||'SEC EDGAR')+' · Data cutoff: '+safe(company.as_of||'unknown')+
  ' · CIK '+safe(company.cik||'unknown')+' · SEC Company Facts / 10-K annual disclosures. '+(source?'<a href="'+safe(source)+'" target="_blank" rel="noopener noreferrer">Inspect SEC facts</a>':'')+'</p>';
 let output='<h3 style="margin:17px 0 10px">Reported financials</h3>'+displayTable(['Measure','Reported / derived'],rows)+provenance;
 const fcf=Number(raw),rate=Number($('private-valuation-wacc').value)/100,
  growth=Number($('private-valuation-growth').value)/100,
  terminal=Number($('private-valuation-terminal').value)/100;
 if(raw==null||!finite(fcf)||fcf<=0){
  output+='<p class="notice">A positive comparable cash-flow proxy is unavailable for this issuer. The reported values above remain useful, but no valuation scenario was calculated.</p>';
 }else if(![rate,growth,terminal].every(finite)||rate<=terminal||rate<.02||rate>.30||growth<-.30||growth>.4||terminal<-.05||terminal>.08){
  output+='<p class="error">Check assumptions: discount rate must exceed terminal growth and all values must remain within their limits.</p>';
 }else{
  let discounted=0,fcfNext=fcf;
  for(let year=1;year<=5;year++){fcfNext*=1+growth;discounted+=fcfNext/(1+rate)**year;}
  const terminalValue=(fcfNext*(1+terminal)/(rate-terminal))/(1+rate)**5;
  output+='<h3 style="margin:18px 0 10px">Hypothetical sensitivity</h3>'+displayTable(['Calculation','Scenario'],[
   ['Reported-period FCF proxy',usd(fcf)],['Five-year discounted proxy',usd(discounted)],
   ['Discounted terminal component',usd(terminalValue)],
   ['Illustrative present value',usd(discounted+terminalValue)]])+
   '<p class="tiny">FCF proxy = operating cash flow minus cash PP&E purchases, not unlevered FCFF. This is not per-share fair value. Debt, cash, taxes, other adjustments, and terminal-model uncertainty are excluded.</p>';
 }
 // Do not allow late fetches from a prior selection to replace the current issuer.
 if($('private-valuation-company').value!==symbol)return;
 $('private-valuation-output').innerHTML=output;
 privatePeers();message('SEC filings loaded for '+companyName+'.');
}
function privatePeers(){
 const rows=Object.values(valuationCompanies).slice(-8).map(company=>{
  const m=company.annual?.[0]?.metrics||{},rev=m.revenue_usd,inc=m.operating_income_usd;
  return [company.name+' ('+company.symbol+')',company.annual?.[0]?.fiscal_end||'Unavailable',
   rev==null?'Unavailable':usd(rev),inc==null||!rev?'Unavailable':percent(inc/rev),
   m.free_cash_flow_usd==null?'Unavailable':usd(m.free_cash_flow_usd)];
 });
 $('private-peers').innerHTML=rows.length?displayTable(['Company','Fiscal year end','Revenue','Operating margin','FCF proxy'],rows)+
  '<p class="tiny">Selected-company comparisons use different fiscal periods and accounting practices; not sector-normalized rankings.</p>':
  '<p class="tiny">Select companies above and run their SEC scenarios to build your own comparison table.</p>';
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

/* V6.3: purely historical owner-only optimization; never invokes /trade or /capital. */
function optPct(x){return typeof x==='number'&&Number.isFinite(x)?(100*x).toFixed(2)+'%':'Unavailable';}
function optSvgFrontier(points){
 const xs=points.map(p=>p.risk),ys=points.map(p=>p.historicalMean);
 const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
 const xscale=x=>30+540*(x-xmin)/(xmax-xmin||1),yscale=y=>200-175*(y-ymin)/(ymax-ymin||1);
 const plot=points.map(p=>xscale(p.risk).toFixed(2)+','+yscale(p.historicalMean).toFixed(2)).join(' ');
 return '<svg viewBox="0 0 600 245" role="img" aria-label="In-sample portfolio risk-return trade-off"><line x1="30" y1="202" x2="575" y2="202" stroke="#cad9d2"/><polyline points="'+plot+'" fill="none" stroke="#196c58" stroke-width="2"/>'+points.map(p=>'<circle cx="'+xscale(p.risk).toFixed(2)+'" cy="'+yscale(p.historicalMean).toFixed(2)+'" r="4" fill="#196c58"/>').join('')+'<text x="30" y="236" font-size="11" fill="#526a60">Annualized historical volatility →</text><text x="30" y="13" font-size="11" fill="#526a60">Historical mean (not a forecast)</text></svg>';
}
function optimizationTable(res){
 const risks=res.optimized.riskContributions;
 return displayTable(['Investment','Equal weight','Optimized','Variance contribution'],res.symbols.map((sym,i)=>[
  (assetNames[sym]||sym)+' ('+sym+')',optPct(res.equalWeights[i]),optPct(res.chosen[i]),optPct(risks[i])]));
}
function optimizerDiagnostics(res){
 const eq=res.equal,op=res.optimized;
 const comparison=displayTable(['Measure','Equal-weight','Optimized'],[
  ['Annualized historical volatility',optPct(eq.annualVolatility),optPct(op.annualVolatility)],
  ['Historical arithmetic annual mean',optPct(eq.annualHistoricalMean),optPct(op.annualHistoricalMean)],
  ['Historical compounded change',optPct(eq.compoundChange),optPct(op.compoundChange)],
  ['Maximum drawdown',optPct(eq.maxDrawdown),optPct(op.maxDrawdown)],
  ['One-day 95% historical VaR',optPct(eq.dailyVaR),optPct(op.dailyVaR)],
  ['One-day 95% historical expected shortfall',optPct(eq.dailyES),optPct(op.dailyES)],
  ['Worst rolling five-session change',optPct(eq.worst5),optPct(op.worst5)],
  ['Worst rolling 20-session change',optPct(eq.worst20),optPct(op.worst20)],
  ['Effective number of holdings',eq.effectiveHoldings.toFixed(2),op.effectiveHoldings.toFixed(2)]
 ]);
 const matrix=displayTable(['Investment',...res.symbols],res.symbols.map((sym,i)=>[
  sym,...res.correlation[i].map(x=>x===null?'Unavailable':x.toFixed(3))]));
 return '<h3>Equal-weight versus optimized</h3>'+comparison+'<h3 style="margin:20px 0 8px">Historical correlation matrix</h3>'+matrix+
  '<h3 style="margin:20px 0 8px">In-sample risk–return trade-off</h3>'+optSvgFrontier(res.frontier)+
  '<p class="tiny">All statistics use the same observed period. A portfolio selected using these data is in-sample; the displayed historical result is not an out-of-sample backtest. Daily rebalancing is assumed when compounding weighted returns. No dividends, borrow costs, slippage, or brokerage orders are included. Variance contributions may be negative for hedging assets.</p>';
}
function runOptimization(){
 if(!privateState){message('Sign in to run private portfolio research.');return;}
 if(!historySeries){message('Go to Market research and load 2–5 investments first.');privateTab('research');return;}
 $('private-opt-output').textContent='Calculating historical allocation…';
 try{
  const result=window.QFPrivateOptimizer.run(historySeries,{
   objective:$('private-opt-objective').value,maxWeight:Number($('private-opt-cap').value)});
  optimizerResult=result;
  $('private-opt-export').disabled=false;
  $('private-opt-output').innerHTML='<p class="tiny">'+safe(result.periodStart)+' to '+safe(result.periodEnd)+' · '+result.observations+' aligned return sessions · '+safe(result.source)+'</p>'+optimizationTable(result)+
   '<p class="tiny">Allocation constraints: no shorts or leverage, each position limited to '+optPct(result.maxWeight)+'. Weights sum to 100%. Calculations do not alter your virtual holdings.</p>';
  $('private-opt-risk').innerHTML=optimizerDiagnostics(result);
  message('Historical portfolio optimization completed; no transactions were placed.');
 }catch(e){optimizerResult=null;$('private-opt-export').disabled=true;$('private-opt-output').textContent=e.message;$('private-opt-risk').textContent='';message(e.message);}
}
function exportOptimization(){
 if(!privateState||!optimizerResult)return;
 const result=optimizerResult;
 const clean=s=>{let v=String(s).replace(/"/g,'""');if(/^[=+@\-]/.test(v))v="'"+v;return '"'+v+'"';};
 const head=['symbol','company','equal_weight','optimized_weight','variance_contribution','period_start','period_end','objective','price_source'];
 const lines=[head.join(',')];
 for(let i=0;i<result.symbols.length;i++){
  const sym=result.symbols[i];lines.push([sym,assetNames[sym]||sym,result.equalWeights[i],result.chosen[i],result.optimized.riskContributions[i],result.periodStart,result.periodEnd,result.objective,result.source].map(clean).join(','));
 }
 const blob=new Blob([lines.join('\r\n')+'\r\n'],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download='quantforge-private-optimized-allocations.csv';document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
 message('Historical allocation CSV exported locally. No data was uploaded.');
}
$('private-opt-run').addEventListener('click',runOptimization);
$('private-opt-export').addEventListener('click',exportOptimization);
for(const id of ['private-opt-objective','private-opt-cap'])$(id).addEventListener('change',()=>{optimizerResult=null;$('private-opt-export').disabled=true;$('private-opt-output').textContent='Settings changed. Calculate allocations to update the results.';$('private-opt-risk').textContent='';});

document.querySelectorAll('[data-private-tab]').forEach(b=>b.addEventListener('click',()=>privateTab(b.dataset.privateTab)));
$('private-history-load').addEventListener('click',loadHistory);
$('private-backtest-run').addEventListener('click',privateBacktest);
$('private-valuation-run').addEventListener('click',privateValuation);
$('private-capital-submit').addEventListener('click',changeCapital);
privatePeers();

})();
