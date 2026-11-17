/* Release A shared stock-first UI. Price IO is owner-only; SEC is published. */
(function(){
'use strict';
const $=id=>document.getElementById(id),Q=window.QFResearchCore20;
const data=window.QFPublishedSEC;
if(!Q||!data||!Array.isArray(data.companies))return;
const companies=[...data.companies].sort((a,b)=>a.name.localeCompare(b.name));
const bySymbol=new Map(companies.map(c=>[c.symbol,c]));
const esc=v=>String(v??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const value=(x,d=1)=>typeof x==='number'&&Number.isFinite(x)?x.toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d}):'Not reported';
const pct=x=>typeof x==='number'&&Number.isFinite(x)?value(x*100,1)+'%':'Not reported';
const money=x=>typeof x==='number'&&Number.isFinite(x)?(x<0?'−':'')+'$'+value(Math.abs(x)/1e9,2)+'B':'Not reported';
const usd=x=>typeof x==='number'&&Number.isFinite(x)?'$'+value(x,2):'Unavailable';
const evidenceId=id=>esc(({ 'sec:revenue_growth':'Annual revenue comparison','sec:operating_margin':'Reported operating income / revenue','sec:free_cash_flow_usd':'Operating cash flow less PP&E purchases','market:drawdown':'Dated close-to-peak losses','market:volatility':'Dated close-return variability'})[id]||'Source observation');
const safeUrl=s=>{try{const u=new URL(s);return u.protocol==='https:'&&u.hostname&&u.username===''&&u.password===''?u.href:null;}catch(_){return null;}};
const state={symbol:bySymbol.has('MSFT')?'MSFT':companies[0].symbol,range:365,finance:'revenue_usd',price:null,priceSource:null,
 privateReady:false,privateMode:false,priceToken:0,runToken:0,benchmark:null,benchmarkOn:false,benchToken:0,
 result:null,compare:[],model:'prediction',loadingPrice:false,compareToken:0,comparison:null,compareSource:null,financeSort:'symbol',financeSortDirection:1,financeCompare:null,portfolioToken:0,ownerToken:0,portfolioData:null,portfolioWeights:null,portfolioBase:null,portfolioKey:null,portfolioOrigin:'',portfolioScenario:null,optimization:null,benchmarkB:null};
let resultsOpen=false,pendingPrice=Promise.resolve(),studyEpoch=0;
for(const event of ['qf:owner-auth-ended','qf:owner-state','qf:data-mode'])window.addEventListener(event,()=>{studyEpoch++;});
function company(){return bySymbol.get(state.symbol);}
function mode(){return state.privateMode&&state.privateReady?'private':'public';}
async function getPrivate(path,signal){
 const res=await fetch('/api/'+path,{credentials:'same-origin',cache:'no-store',signal});
 let json;try{json=await res.json();}catch(_){throw Error('Research API unavailable. Historical SEC figures remain available.');}
 if(!res.ok)throw Error(window.QFErrors24.apiError(res.status,path,json?.code));
 return json;
}
function setAccount(){
 $('qf-v20-account-status').textContent=mode()==='private'?'PRIVATE · MFA VERIFIED':'Public SEC financial research · labeled model demonstrations';
 $('qf-v20-mode').textContent=mode()==='private'?'My workspace':'Sign in';
 $('qf-v20-benchmark-wrap').hidden=mode()!=='private';
 $('qf-v20-universe').textContent=data.companies.length+' SEC companies · '+(mode()==='private'?'provider name search':'public financial research');
}
function rememberAsset(asset){
 if(!asset||!/^[A-Z][A-Z0-9.]{0,9}$/.test(asset.symbol))throw Error('Invalid investment.');
 if(mode()==='public'&&!data.companies.some(c=>c.symbol===asset.symbol))throw Error('Not in public SEC coverage.');
 if(!bySymbol.has(asset.symbol)){const item={...asset,cik:null,annual:[],sector:'Provider listing · SEC financials not covered'};bySymbol.set(item.symbol,item);companies.push(item);}
 return bySymbol.get(asset.symbol);
}
function addAsset(asset){const c=rememberAsset(asset);if(state.compare.includes(c.symbol)){$('qf-b21-compare-state').textContent=c.name+' is already selected.';return false;}if(state.compare.length>=5){$('qf-b21-compare-state').textContent='Five investments are selected. Remove one before adding another.';return false;}state.compare.push(c.symbol);invalidateComparison();renderCompareChips();window.dispatchEvent(new Event('qf:research-universe'));return true;}
function searchAssets(query,signal){return getPrivate('private/assets?'+new URLSearchParams({category:query?'all':'popular',query:query.slice(0,60)}),signal);}
function selectCompany(symbol){
 if(!bySymbol.has(symbol)||(mode()==='public'&&!data.companies.some(c=>c.symbol===symbol)))return;

 state.symbol=symbol;state.result=null;state.price=null;state.priceSource=null;state.benchmark=null;state.priceToken++;state.runToken++;state.benchToken++;
 const c=company();
 $('qf-v20-search').value=c.name+' ('+c.symbol+')';
 $('qf-v20-search-results').hidden=true;$('qf-v20-search').setAttribute('aria-expanded','false');
 $('qf-v20-company').textContent=c.name;$('qf-v20-symbol').textContent=c.symbol;$('qf-v20-sector').textContent=c.sector||'SEC-reported company';
 $('qf-v20-current').textContent='—';$('qf-v20-change').textContent='Loading appropriate price data…';
 $('qf-v20-model-selected').textContent='Selected company: '+c.name+' ('+c.symbol+'). Synthetic public model examples remain separate from its reported financial statements.';
 const dcf=$('dcf-company');if(dcf&&[...dcf.options].some(o=>o.value===symbol))dcf.value=symbol;
 $('qf-v20-findings').replaceChildren();$('qf-v20-run-state').textContent='Click Analyze company for an evidence-linked summary.';
 const f=Q.financialSummary(c,data.as_of);
 renderFinances(f);renderSource(f);renderChartEmpty('Preparing chart…');
 setAccount();window.dispatchEvent(new Event('qf:research-context'));pendingPrice=loadPrice();
}
function renderChartEmpty(msg){$('qf-v20-chart').textContent=msg;$('qf-v20-price-stats').replaceChildren();$('qf-v20-price-table').replaceChildren();}
function renderSource(f){
 if(!company().cik){$('qf-v20-coverage').innerHTML='<p>SEC snapshot: no coverage for this provider-listed asset.</p><p id="qf-v20-price-coverage">Market data: checking entitlement</p>';$('qf-v20-sec-source').textContent='No SEC statements are imputed for this asset.';$('qf-v20-filing-status').textContent='No annual statements in the published snapshot.';return;}
 const sourceUrl='https://data.sec.gov/api/xbrl/companyfacts/CIK'+String(company().cik).padStart(10,'0')+'.json';
 $('qf-v20-coverage').innerHTML='<p><strong>SEC dataset:</strong> '+esc(data.as_of)+' snapshot · '+esc(f.source.period||'unknown fiscal year')+' latest covered period</p><p><a href="'+sourceUrl+'" target="_blank" rel="noopener noreferrer">SEC Company Facts, issuer CIK '+esc(company().cik)+'</a></p><p id="qf-v20-price-coverage">Market data: checking availability</p>';
 $('qf-v20-sec-source').innerHTML='<a href="'+sourceUrl+'" rel="noopener noreferrer" target="_blank">Primary SEC issuer record</a>. Historical observations may be restated in subsequently filed annual reports. The cash-flow proxy is operating cash flow less cash property-and-equipment purchases, not a full FCFF valuation.';
 $('qf-v20-filing-status').textContent='Latest included fiscal year: '+(f.source.period||'not available')+' · snapshot cutoff '+data.as_of+' · monetary values USD';
}
function renderFinances(f){
 const m=f.metrics;
 const cells=[['Annual revenue',money(m.revenue_usd)],['Revenue growth',pct(m.revenue_growth)],['Net income',money(m.net_income_usd)],['Operating margin',pct(m.operating_margin)],['Cash-flow proxy',money(m.free_cash_flow_usd)],['Net margin',pct(m.net_margin)]];
 $('qf-v20-financial-kpis').innerHTML=cells.map(([name,v])=>'<div><small>'+esc(name)+'</small><strong>'+esc(v)+'</strong></div>').join('');
 document.querySelectorAll('[data-qf-financial]').forEach(b=>b.classList.toggle('active',b.dataset.qfFinancial===state.finance));
 const annual=[...f.annual].reverse().slice(-7);
 const k=state.finance;
 const rows=annual.map(r=>({date:r.fiscal_end,v:typeof r.metrics[k]==='number'?r.metrics[k]:null}));
 const present=rows.filter(r=>r.v!==null&&Number.isFinite(r.v));
 if(present.length){
  const lo=Math.min(0,...present.map(r=>r.v)),hi=Math.max(0,...present.map(r=>r.v)),span=hi-lo||1;
  const w=550,h=190,barW=Math.min(55,430/rows.length);
  const zero=165-(0-lo)/span*138;
  const bars=rows.map((r,i)=>{
   const x=45+i*(470/rows.length)+8;
   if(r.v===null||!Number.isFinite(r.v))return '<text x="'+(x+barW/2)+'" y="99" text-anchor="middle">n/a</text>';
   const y=165-(r.v-lo)/span*138;
   return '<rect x="'+x.toFixed(1)+'" y="'+Math.min(y,zero).toFixed(1)+'" height="'+Math.max(1,Math.abs(zero-y)).toFixed(1)+'" width="'+barW.toFixed(1)+'" rx="3" fill="'+(r.v>=0?'#227b69':'#c57d67')+'"><title>'+esc(r.date)+': '+esc(money(r.v))+'</title></rect>';
  }).join('');
  const years=rows.map((r,i)=>'<text x="'+(45+i*(470/rows.length)+8+barW/2).toFixed(1)+'" y="184" text-anchor="middle">'+esc(r.date.slice(0,4))+'</text>').join('');
  $('qf-v20-financial-chart').innerHTML='<svg class="qf-v20-fin-svg" viewBox="0 0 '+w+' '+h+'" role="img" aria-label="Reported historical annual '+esc(k.replaceAll('_',' '))+' by fiscal year"><line x1="45" x2="530" y1="'+zero.toFixed(1)+'" y2="'+zero.toFixed(1)+'" stroke="#a5bdb0"/>'+bars+years+'</svg>';
 }else $('qf-v20-financial-chart').textContent='This historical metric is not reported in a comparable form for this issuer.';
 $('qf-v20-financial-table').innerHTML='<table><thead><tr><th>Fiscal year</th><th>Revenue ($B)</th><th>Net income ($B)</th><th>Cash flow ($B)</th><th>Revenue filed / accession</th></tr></thead><tbody>'+f.annual.map(r=>{
  const file=r.sources?.revenue_usd;
  return '<tr><td>'+esc(r.fiscal_end)+'</td><td>'+esc(money(r.metrics?.revenue_usd))+'</td><td>'+esc(money(r.metrics?.net_income_usd))+'</td><td>'+esc(money(r.metrics?.free_cash_flow_usd))+'</td><td>'+esc(file?.filed||'Not available')+'<small class="tiny"> '+esc(file?.accession||'')+'</small></td></tr>';
 }).join('')+'</tbody></table>';
}
function renderPriceData(){
 const source=state.priceSource;
 if(!state.price||!source){renderChartEmpty('Historical price data is unavailable. SEC financials and analysis remain available.');return;}
 const real=source.type==='market';
 $('qf-v20-source-badge').textContent=real?'Observed · '+(source.equity_feed||'feed not supplied').toUpperCase():'Illustrative · synthetic';
 const rawPrice=Q.chartWindow(state.price,state.range);
 const price=real||!rawPrice.length?rawPrice:rawPrice.map(p=>({...p,close:100*p.close/rawPrice[0].close}));
 if(!price.length){renderChartEmpty('No observations in this chart range.');return;}
 $('qf-v20-current').textContent=real?usd(price[price.length-1].close):value(price[price.length-1].close,1)+' index';
 $('qf-v20-change').textContent=(real?'Observed close':'Illustrative index · 100 at window start')+' · '+price[price.length-1].date;
 const overall=real?Q.priceStatistics(Q.chartWindow(state.price,Math.max(30,Number(state.range)||730)),state.symbol.includes('/')?365:252):null;
 const change=price[price.length-1].close/price[0].close-1;
 $('qf-v20-price-stats').innerHTML=[['Window change',pct(change)],['Price observations',String(price.length)],['Observed max drawdown',overall?pct(overall.max_drawdown):'Not evaluated']].map(x=>'<div><small>'+esc(x[0])+'</small><strong>'+esc(x[1])+'</strong></div>').join('');
 const scopeText=real?source.source+' · '+source.coverage:'Deterministic synthetic company-labeled chart demonstration. NOT observed '+company().name+' prices, an estimate, or an investment return.';
 $('qf-v20-chart-source').textContent=scopeText;
 const coverage=$('qf-v20-price-coverage');if(coverage)coverage.textContent='Price: '+scopeText+' · '+price[0].date+' through '+price[price.length-1].date;
 const benchmark=real&&state.benchmarkOn&&state.benchmark?Q.chartWindow(state.benchmark,state.range):null;
 drawPriceChart(price,benchmark,real);
 const sampled=price.length>10?[...price.slice(0,2),...price.slice(-8)]:price;
 $('qf-v20-price-table').innerHTML='<p>Underlying dated closes · '+(price.length>10?'first 2 and latest 8 shown; export for all':'all available observations')+'</p><div class="table-wrap"><table><thead><tr><th>Date</th><th>'+(real?'Close (USD)':'Illustrative index')+'</th></tr></thead><tbody>'+sampled.map(p=>'<tr><td>'+esc(p.date)+'</td><td>'+esc(real?usd(p.close):value(p.close,2)+' index')+'</td></tr>').join('')+'</tbody></table></div>';
}
function drawPriceChart(price,benchmark,real){
 const W=Math.max(210,$('qf-v20-chart').clientWidth||720),H=292,left=55,right=W-26,top=20,bottom=247;
 let series=price,bench=null,normalized=false;
 if(benchmark?.length){
  const matches=new Map(benchmark.map(r=>[r.date,r.close]));
  const paired=price.filter(r=>matches.has(r.date));
  if(paired.length>=15){series=paired;normalized=true;
   const first=paired[0].close,base=matches.get(paired[0].date);
   bench=paired.map(r=>({date:r.date,close:100*matches.get(r.date)/base}));
   series=paired.map(r=>({date:r.date,close:100*r.close/first}));
  }
 }
 let lo=Math.min(...series.map(p=>p.close),...(bench||[]).map(p=>p.close));
 let hi=Math.max(...series.map(p=>p.close),...(bench||[]).map(p=>p.close));
 const span=hi-lo||1;lo-=span*0.08;hi+=span*0.08;
 const X=i=>left+(right-left)*i/Math.max(1,series.length-1);
 const Y=n=>bottom-(n-lo)/(hi-lo)*(bottom-top);
 const path=xs=>xs.map((r,i)=>(i?'L':'M')+X(i).toFixed(2)+','+Y(r.close).toFixed(2)).join(' ');
 const grid=Array.from({length:5},(_,i)=>{
  const y=top+(bottom-top)*i/4;
  return '<line x1="'+left+'" x2="'+right+'" y1="'+y+'" y2="'+y+'" stroke="#e0eae5"/><text x="'+(left-9)+'" y="'+(y+4)+'" font-size="10" text-anchor="end" fill="#637b70">'+(normalized||!real?value(hi-(hi-lo)*i/4,0):'$'+value(hi-(hi-lo)*i/4,0))+'</text>';
 }).join('');
 const ticks=window.QFReadout29.axisTicks(series.map(r=>r.date),W).map(({index:i,label})=>{
  return '<text class="qf29-price-tick" x="'+X(i)+'" y="270" font-size="12" text-anchor="'+(i===0?'start':i===series.length-1?'end':'middle')+'" fill="#526173">'+esc(label)+'</text>';
 }).join('');
 const mark=real?'':'<text x="'+(W/2)+'" y="55" text-anchor="middle" font-size="'+(W<500?10:19)+'" font-weight="750" fill="#d4e5dc">SYNTHETIC · NOT REAL MARKET PRICES</text>';
 $('qf-v20-chart').innerHTML='<svg viewBox="0 0 '+W+' '+H+'" tabindex="0" role="img" aria-label="'+(real?'Observed':'Synthetic demonstration')+' close-price chart '+esc(series[0].date)+' to '+esc(series[series.length-1].date)+'. Arrow keys inspect values."><title>'+(real?'Observed, price-only historical closes':'Synthetic illustration, not actual company market prices')+'</title>'+grid+ticks+mark+'<path d="'+path(series)+'" fill="none" stroke="#19826c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'+(bench?'<path d="'+path(bench)+'" fill="none" stroke="#b88c45" stroke-width="2" stroke-dasharray="6 5"/>':'')+'<line id="qf-v20-crosshair" x1="'+X(series.length-1)+'" x2="'+X(series.length-1)+'" y1="'+top+'" y2="'+bottom+'" stroke="#839c91" stroke-dasharray="3 4"/><circle id="qf-v20-crossdot" cx="'+X(series.length-1)+'" cy="'+Y(series[series.length-1].close)+'" r="5" fill="#155f50" stroke="#fff" stroke-width="2"/></svg><div class="qf-v20-cursor" aria-live="polite"><span id="qf-v20-cursor-value"></span><span>'+(normalized?'Indexed to 100 · common observed dates · SPY dashed':real?'Close price · hover or use arrow keys':'Illustrative index · not a stock quote')+'</span></div>';
 const svg=$('qf-v20-chart').querySelector('svg');let index=series.length-1;
 const update=i=>{index=Math.min(series.length-1,Math.max(0,i));
  const x=X(index);$('qf-v20-crosshair').setAttribute('x1',x);$('qf-v20-crosshair').setAttribute('x2',x);
  $('qf-v20-crossdot').setAttribute('cx',x);$('qf-v20-crossdot').setAttribute('cy',Y(series[index].close));
  $('qf-v20-cursor-value').textContent=series[index].date+' · '+(normalized||!real?value(series[index].close,2)+' index':'$'+value(series[index].close,2))+(bench?' · SPY '+value(bench[index].close,2):'');};
 update(index);
 svg.addEventListener('pointermove',e=>{
  const rect=svg.getBoundingClientRect(),ratio=(e.clientX-rect.left)/rect.width;
  update(Math.round((ratio*W-left)/(right-left)*(series.length-1)));
 });
 svg.addEventListener('keydown',e=>{
  const next=e.key==='ArrowLeft'?index-1:e.key==='ArrowRight'?index+1:e.key==='Home'?0:e.key==='End'?series.length-1:null;
  if(next!==null){e.preventDefault();update(next);}
 });
}
async function loadPrice(){
 const token=++state.priceToken;
 state.price=null;state.priceSource=null;state.benchmark=null;state.benchToken++;
 const symbol=state.symbol,privateResearch=mode()==='private';
 if(!privateResearch){
  state.price=Q.syntheticPrice(symbol);
  state.priceSource={type:'synthetic',source:'Seeded deterministic simulation (browser only)',coverage:'No link to actual company price observations.'};
  renderPriceData();window.dispatchEvent(new Event('qf:research-context'));return;
 }
 renderChartEmpty('Requesting owner-authorized historical closes…');
 try{
  const days=state.range===730||state.range==='ALL'?730:365;
  const raw=await getPrivate('private/history-single?'+new URLSearchParams({symbol,days:String(days)}));
  if(token!==state.priceToken||symbol!==state.symbol)return;
  if(raw.licensed_private!==true||raw.symbol!==symbol||raw.ohlcv_available!==false)throw Error('Unexpected or unsupported market-data contract.');
  state.price=Q.priceSeries(raw.observations);
  state.priceSource={...raw,type:'market'};
  renderPriceData();window.dispatchEvent(new Event('qf:research-context'));
  if(state.benchmarkOn)loadBenchmark();
 }catch(e){if(token!==state.priceToken)return;
  state.price=null;state.priceSource=null;renderChartEmpty('Observed prices unavailable: '+String(e.message||e).slice(0,170)+'. SEC financials remain available.');
  $('qf-v20-current').textContent='Unavailable';$('qf-v20-change').textContent='No synthetic fallback used in private mode';
  $('qf-v20-source-badge').textContent='Market data unavailable';
  const coverage=$('qf-v20-price-coverage');if(coverage)coverage.textContent='Private market observations unavailable; no replacement or fabricated prices.';
  window.dispatchEvent(new Event('qf:research-context'));
 }
}
async function loadBenchmark(){
 const token=++state.benchToken;
 if(!state.benchmarkOn||mode()!=='private'||state.symbol==='SPY'||state.priceSource?.type!=='market'){state.benchmark=null;renderPriceData();return;}
 try{
  const days=state.range===730||state.range==='ALL'?730:365;
  const raw=await getPrivate('private/history-single?'+new URLSearchParams({symbol:'SPY',days:String(days)}));
  if(token!==state.benchToken||!state.benchmarkOn)return;
  if(state.priceSource?.equity_feed&&raw.equity_feed!==state.priceSource.equity_feed){state.benchmark=null;renderPriceData();$('qf-v20-chart-source').textContent+=' SPY benchmark withheld because a compatible feed was not verified.';return;}
  state.benchmark=Q.priceSeries(raw.observations);renderPriceData();
 }catch(_){if(token===state.benchToken){state.benchmark=null;renderPriceData();$('qf-v20-chart-source').textContent+=' SPY benchmark unavailable; company closes still shown.';}}
}
async function analyze(){
 const token=++state.runToken,selected=state.symbol,kind=mode(),ownerVersion=window.QFPrivateBridgeV23?.snapshot()?.version;
 if(kind==='private')await pendingPrice;
 if(token!==state.runToken||selected!==state.symbol||kind!==mode()||ownerVersion!==window.QFPrivateBridgeV23?.snapshot()?.version)return;
 const f=Q.financialSummary(company(),data.as_of);
 const result=Q.researchResult(f,state.price,state.priceSource);
 if(token!==state.runToken)return;
 state.result=result;
 $('qf-v20-run-state').textContent='Calculated for '+company().name+' · SEC snapshot '+data.as_of+' · '+(result.price_source==='market'?'observed private market risk':'no eligible observed market risk');
 $('qf-v20-findings').innerHTML=result.findings.map(f=>'<article class="qf-v20-finding '+esc(f.kind)+'"><span>'+esc(f.kind)+'</span><p>'+esc(f.text)+'</p><small>Evidence: '+(f.evidence_ids.length?f.evidence_ids.map(evidenceId).join(' · '):'Methodological limitation')+'</small></article>').join('')+'<div class="qf-v20-finding"><span>Uncertainties</span><p>'+esc(result.limitations.slice(0,3).join(' '))+'</p></div>';
 window.dispatchEvent(new Event('qf:analyze-company'));
}
function csv(rows,name){
 const safe=v=>{
  if(v===null||v===undefined)return '';
  if(typeof v==='number'&&Number.isFinite(v))return String(v);
  let text=String(v);
  if(/^[\s\u0000-\u001f]*[=+@-]/.test(text))text="'"+text;
  return '"'+text.replaceAll('"','""')+'"';
 };
 const text=rows.map(row=>row.map(safe).join(',')).join('\r\n')+'\r\n';
 const blob=new Blob([text],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download=name;document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
}
function exportPrice(){
 if(!state.price)return;
 const observed=state.priceSource.type==='market',rows=state.price;
 const origin=rows[0]?.close;
 csv([['symbol','date',observed?'close_usd':'illustrative_index_100_at_first_date','price_origin','source_description'],
  ...rows.map(p=>[state.symbol,p.date,observed?p.close:100*p.close/origin,state.priceSource.type,state.priceSource.source])],
 'quantforge-'+state.symbol+'-'+(observed?'observed-closes':'synthetic-index')+'.csv');
}
function exportSEC(){
 const f=Q.financialSummary(company(),data.as_of);
 const columns=['revenue_usd','net_income_usd','operating_income_usd','operating_cash_flow_usd','capex_usd','free_cash_flow_usd'];
 const rows=[['symbol','snapshot_as_of','fiscal_end',...columns,...columns.filter(k=>k!=='free_cash_flow_usd').flatMap(k=>[k+'_filed',k+'_accession'])]];
 for(const r of f.annual)rows.push([state.symbol,data.as_of,r.fiscal_end,...columns.map(k=>r.metrics[k]??null),...columns.filter(k=>k!=='free_cash_flow_usd').flatMap(k=>[r.sources?.[k]?.filed??null,r.sources?.[k]?.accession??null])]);
 csv(rows,'quantforge-'+state.symbol+'-reported-sec.csv');
}
function addCompare(){if(!state.compare.includes(state.symbol)&&state.compare.length<5){state.compare.push(state.symbol);invalidateComparison();}renderCompareChips();}
function renderCompareChips(){
 $('qf-v20-compare-chips').innerHTML=state.compare.map(s=>'<button type="button" data-qf-remove="'+esc(s)+'" aria-label="Remove '+esc(s)+'">'+esc(bySymbol.get(s).name)+' · '+esc(s)+' ×</button>').join('');
 $('qf-b21-compare-count').textContent=state.compare.length+' / 5 selected';
}
const B=window.QFResearchB21;
const colorSet=['#136b59','#4a6cba','#d88a3c','#9963ad','#b4515a','#566c79'];
const rowsOrNull=value=>typeof value==='number'&&Number.isFinite(value);
function money2(v){return rowsOrNull(v)?'$'+value(v,2):'—';}
function percentOrNA(v){return rowsOrNull(v)?pct(v):'—';}
function names(){return state.compare.map(s=>bySymbol.get(s)?.name||s);}
function invalidateComparison(){
 state.compareToken++;state.comparison=null;state.compareSource=null;state.benchmarkB=null;
 state.portfolioScenario=null;state.portfolioData=null;state.portfolioWeights=null;state.portfolioBase=null;state.portfolioOrigin='';state.optimization=null;state.financeCompare=null;state.portfolioToken++;
 $('qf-b21-compare-export').disabled=true;$('qf-b21-finance-export').disabled=true;$('qf-b21-portfolio-export').disabled=true;
 $('qf-b21-compare-state').textContent='Selection changed. Click Compare to calculate results for the current companies.';
 $('qf-b21-compare-chart').textContent='Run Compare to load eligible history on common dates.';
 $('qf-b21-finance-table').textContent='Selection changed. Run Compare to refresh this financial table.';
 $('qf-b21-risk-table').textContent='No shared history loaded.';
 $('qf-b21-distribution').replaceChildren();$('qf-b21-risk-scatter').replaceChildren();$('qf-b21-correlation').textContent='No common return history loaded.';
 $('qf-b21-optimizer-output').replaceChildren();
 window.dispatchEvent(new Event('qf:research-universe'));
 const brief=$('qf24-compare-brief');if(brief)brief.replaceChildren();
}
function linePlot(target,dates,series){
 if(!dates||dates.length<2||!series.length){$(target).textContent='No eligible aligned data for this chart.';return;}
 const W=Math.max(210,$(target).clientWidth||Math.min(870,window.innerWidth-112)),H=275,left=57,right=W-15,top=20,bottom=234;
 const numbers=series.flatMap(s=>s.values).filter(rowsOrNull);if(!numbers.length){$(target).textContent='No finite observations.';return;}
 let lo=Math.min(...numbers),hi=Math.max(...numbers);if(hi-lo<0.01){lo-=2;hi+=2;}const margin=(hi-lo)*0.10;lo-=margin;hi+=margin;
 const X=i=>left+(right-left)*i/(dates.length-1),Y=v=>bottom-(v-lo)/(hi-lo)*(bottom-top);
 const lines=series.map((s,i)=>'<path fill="none" stroke="'+colorSet[i%colorSet.length]+'" stroke-width="2.8" stroke-linejoin="round" d="'+s.values.map((v,j)=>(j?'L':'M')+X(j).toFixed(1)+' '+Y(v).toFixed(1)).join(' ')+'"/>').join('');
 const guide=[0,0.5,1].map(f=>{const v=lo+f*(hi-lo),y=Y(v);return '<line x1="'+left+'" x2="'+right+'" y1="'+y+'" y2="'+y+'" stroke="#dce9e4"/><text x="'+(left-9)+'" y="'+(y+4)+'" font-size="12" text-anchor="end" fill="#526e62">'+value(v,1)+'</text>';}).join('');
 const legend='<div class="qf-b21-chart-legend">'+series.map((s,i)=>'<span class="qf-b21-chart-label"><span style="color:'+colorSet[i%colorSet.length]+'">●</span> '+esc(s.label)+'</span>').join('')+'</div>';
 $(target).innerHTML='<svg viewBox="0 0 '+W+' '+H+'" role="img" tabindex="0" aria-label="'+esc(series.map(s=>s.label).join(', '))+' compared on '+esc(dates[0])+' through '+esc(dates.at(-1))+'; use left and right arrows to inspect values">'+guide+lines+
  '<text x="'+left+'" y="'+(H-28)+'" fill="#526e62" font-size="13">'+esc(dates[0])+'</text><text x="'+right+'" y="'+(H-10)+'" text-anchor="end" fill="#526e62" font-size="13">'+esc(dates.at(-1))+'</text><line id="'+target+'-cross" x1="'+right+'" x2="'+right+'" y1="'+top+'" y2="'+bottom+'" stroke="#647b70" stroke-dasharray="3 4"/></svg>'+legend+'<p role="status" class="tiny" id="'+target+'-cursor"></p>';
 const svg=$(target).querySelector('svg');let index=dates.length-1;
 const update=i=>{index=Math.max(0,Math.min(dates.length-1,i));const x=X(index).toFixed(1);const cross=$(target+'-cross');cross.setAttribute('x1',x);cross.setAttribute('x2',x);
  $(target+'-cursor').textContent=dates[index]+' · '+series.map(s=>s.label+': '+value(s.values[index],2)).join(' · ');};
 svg.addEventListener('pointermove',e=>{const rect=svg.getBoundingClientRect(),px=(e.clientX-rect.left)/rect.width;update(Math.round((px*W-left)/(right-left)*(dates.length-1)));});
 svg.addEventListener('keydown',e=>{const n=e.key==='ArrowLeft'?index-1:e.key==='ArrowRight'?index+1:e.key==='Home'?0:e.key==='End'?dates.length-1:null;if(n!==null){e.preventDefault();update(n);}});
 update(index);
}
function renderFinanceComparison(){
 const symbols=state.compare;
 const fs=symbols.map(s=>({symbol:s,f:B&&Q.financialSummary(bySymbol.get(s),data.as_of)}));
 const entries=[['symbol','Company'],['fiscal','FY end'],['revenue','Revenue ($B)'],['growth','Growth'],['margin','Operating margin'],['fcf','FCF proxy ($B)']];
 const raw=fs.map(({symbol,f})=>({symbol,name:bySymbol.get(symbol).name,fiscal:f.source?.period||'',revenue:f.metrics.revenue_usd,growth:f.metrics.revenue_growth,margin:f.metrics.operating_margin,fcf:f.metrics.free_cash_flow_usd,f}));
 state.financeCompare=raw;
 const field=state.financeSort||'symbol',sign=state.financeSortDirection||1;
 raw.sort((a,b)=>{const x=a[field],y=b[field];if(x==null)return y==null?0:1;if(y==null)return -1;return (typeof x==='number'?x-y:String(x).localeCompare(String(y)))*sign;});
 const moneyB=n=>rowsOrNull(n)?value(n/1e9,2):'—';
 const body=raw.map(r=>'<tr><th scope="row">'+esc(r.name)+' ('+esc(r.symbol)+')</th><td>'+esc(r.fiscal||'—')+'</td><td>'+esc(moneyB(r.revenue))+'</td><td>'+esc(percentOrNA(r.growth))+'</td><td>'+esc(percentOrNA(r.margin))+'</td><td>'+esc(moneyB(r.fcf))+'</td></tr>').join('');
 $('qf-b21-finance-table').innerHTML='<table><thead><tr>'+entries.map(([key,label])=>'<th scope="col"><button type="button" class="qf-b21-sort" data-qf-b21-sort="'+key+'" aria-label="Sort by '+label+'">'+label+'</button></th>').join('')+'</tr></thead><tbody>'+body+'</tbody></table><p class="tiny">SEC snapshot '+esc(data.as_of)+' · FCF is operating cash flow minus cash PPE purchases. Fiscal periods differ; ratios may not be comparable for banks and operating companies. — means unavailable, not zero.</p>';
 $('qf-b21-finance-export').disabled=false;
 const chart=$('qf24-financial-contrast');if(chart)chart.innerHTML=window.QFExhibits24.bars('Reported operating margin by issuer (latest covered fiscal year)',raw.map(r=>[r.symbol,r.margin]));
 const brief=$('qf24-compare-brief');if(brief)brief.innerHTML='<h3>How these companies differ</h3>'+raw.map(r=>'<p><strong>'+esc(r.name)+'</strong> · fiscal '+esc(r.fiscal||'period unavailable')+': '+(rowsOrNull(r.growth)?'revenue '+(r.growth>=0?'grew ':'fell ')+esc(pct(Math.abs(r.growth))):'revenue growth is unavailable')+'; '+(rowsOrNull(r.margin)?'operating margin '+esc(pct(r.margin)):'operating margin unavailable')+'; '+(rowsOrNull(r.fcf)?'cash-flow proxy '+esc(money(r.fcf)):'cash-flow proxy unavailable')+'.</p>').join('')+'<p>These are accounting comparisons, not a ranking of investments. Fiscal periods and industry definitions differ; bank ratios need particular care.</p>';

}
function riskTable(result){
 const m=result.metrics;
 $('qf-b21-risk-table').innerHTML='<table><thead><tr><th>Company</th><th>Change</th><th>Annualized vol.</th><th>Max drawdown</th><th>Daily ES 95%</th></tr></thead><tbody>'+result.symbols.map(s=>'<tr><th>'+esc(s)+'</th><td>'+esc(pct(m[s].total_return))+'</td><td>'+esc(pct(m[s].annual_volatility))+'</td><td>'+esc(pct(m[s].max_drawdown))+'</td><td>'+esc(pct(m[s].daily_es95_loss))+'</td></tr>').join('')+'</tbody></table>';
 const W=window.innerWidth<740?Math.max(260,Math.min(460,window.innerWidth-96)):460,H=220,x0=40,x1=W-18,y0=22,y1=187;
 const maxX=Math.max(0.01,...result.symbols.map(s=>m[s].annual_volatility))*1.17;
 const lowY=Math.min(0,...result.symbols.map(s=>m[s].total_return))*1.12-0.01,highY=Math.max(0.01,...result.symbols.map(s=>m[s].total_return))*1.12+0.01;
 const X=v=>x0+(x1-x0)*v/maxX,Y=v=>y1-(y1-y0)*(v-lowY)/(highY-lowY);
 $('qf-b21-risk-scatter').innerHTML='<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="Historical return versus annualized price volatility scatter"><line x1="'+x0+'" x2="'+x1+'" y1="'+y1+'" y2="'+y1+'" stroke="#9db4aa"/><line x1="'+x0+'" x2="'+x0+'" y1="'+y0+'" y2="'+y1+'" stroke="#9db4aa"/>'+result.symbols.map((s,i)=>'<circle cx="'+X(m[s].annual_volatility)+'" cy="'+Y(m[s].total_return)+'" r="6" fill="'+colorSet[i]+'"><title>'+esc(s)+': '+esc(pct(m[s].total_return))+' price change; '+esc(pct(m[s].annual_volatility))+' annualized volatility</title></circle>').join('')+'<text x="'+(x1-8)+'" y="'+(H-6)+'" text-anchor="end" font-size="12">Historical annualized volatility →</text><text x="6" y="16" font-size="12">Price change ↑</text></svg><p class="tiny">'+result.symbols.map((s,i)=>'<span style="display:inline-block;margin-right:16px"><span style="color:'+colorSet[i]+'" aria-hidden="true">●</span> '+esc(s)+'</span>').join('')+'</p>';
}
function heatmap(target,result){
 if(!result){$(target).textContent='No common-dated risk sample available.';return;}
 const names=result.symbols, C=result.correlation_matrix;
 const row=C.map((cells,i)=>'<tr><th scope="row">'+esc(names[i])+'</th>'+cells.map(v=>{
  const safe=rowsOrNull(v),shade=safe?'rgba('+(v>=0?'26,111,85':'170,104,73')+','+(0.10+Math.abs(v)*0.45).toFixed(2)+')':'#edf1ef';
  return '<td style="background:'+shade+'" aria-label="'+esc(names[i])+' correlation '+(safe?v.toFixed(3):'unavailable')+'">'+(safe?v.toFixed(2):'—')+'</td>';
 }).join('')+'</tr>').join('');
 $(target).innerHTML='<table><thead><tr><th></th>'+names.map(s=>'<th scope="col">'+esc(s)+'</th>').join('')+'</tr></thead><tbody>'+row+'</tbody></table>';
}
function renderHistogram(result){
 const hist=B.histogram(result,9),W=window.innerWidth<740?Math.max(260,Math.min(520,window.innerWidth-96)):520,H=195,base=157,maxCount=Math.max(1,...Object.values(hist.counts).flat());
 const band=(W-70)/9;
 $('qf-b21-distribution').innerHTML='<svg role="img" viewBox="0 0 '+W+' '+H+'" aria-label="Daily return histogram for each company">'+result.symbols.flatMap((s,j)=>hist.counts[s].map((count,i)=>{
  const barWidth=band/result.symbols.length*0.82,x=50+band*i+j*(band/result.symbols.length),h=count/maxCount*126;
  return '<rect x="'+x.toFixed(2)+'" y="'+(base-h).toFixed(2)+'" width="'+barWidth.toFixed(2)+'" height="'+h.toFixed(2)+'" fill="'+colorSet[j]+'"><title>'+esc(s)+' · '+value(hist.edges[i]*100,1)+'% to '+value(hist.edges[i+1]*100,1)+'%: '+count+' sessions</title></rect>';
 })).join('')+'<line x1="50" y1="'+base+'" x2="'+(W-20)+'" y2="'+base+'" stroke="#a8bdb3"/><text x="50" y="181" font-size="12">'+value(hist.edges[0]*100,1)+'%</text><text x="'+(W-20)+'" y="181" font-size="12" text-anchor="end">'+value(hist.edges.at(-1)*100,1)+'%</text></svg><div class="qf-b21-chart-legend">'+result.symbols.map((s,i)=>'<span class="qf-b21-chart-label" style="color:'+colorSet[i]+'">● '+esc(s)+'</span>').join('')+'</div>';
}
function publicBatch(symbols,days){
 const cutoff=days;const observations=Object.fromEntries(symbols.map(s=>[s,Q.chartWindow(Q.syntheticPrice(s),cutoff)]));
 const aligned=B.align(observations,symbols);
 return {aligned,source:'Deterministic simulated price histories — NOT observed '+symbols.join(', ')+' shares; no actual company returns.',kind:'synthetic'};
}
async function fetchBatch(symbols,days){
 if(mode()!=='private')return publicBatch(symbols,days);
 const data=await getPrivate('private/history?'+new URLSearchParams({symbols:symbols.join(','),days:String(days)}));
 return {aligned:B.fromBatch(data,symbols),source:String(data.source||'Alpaca owner-only split-adjusted daily closes')+' · '+String(data.coverage||''),kind:'market',equityFeed:data.equity_feed||null};
}
async function fetchBenchmark(aligned,days,kind,equityFeed=null){
 try{
  let series;
  if(kind==='market'){const raw=await getPrivate('private/history-single?'+new URLSearchParams({symbol:'SPY',days:String(days)}));if(equityFeed&&raw.equity_feed!==equityFeed)return null;series=Q.priceSeries(raw.observations);}else series=Q.chartWindow(Q.syntheticPrice('SPY'),days);
  const dates=new Map(series.map(row=>[row.date,row.close]));if(!aligned.dates.every(d=>dates.has(d)))return null;
  const first=dates.get(aligned.dates[0]);return {symbol:'SPY',kind,values:aligned.dates.map(d=>dates.get(d)/first*100)};
 }catch(_){return null;}
}
async function runCompare(){
 const symbols=state.compare.slice();const request=++state.compareToken;
 if(symbols.length<2||symbols.length>5){$('qf-b21-compare-state').textContent='Select 2–5 distinct companies first.';return;}
 state.comparison=null;state.compareSource=null;state.portfolioData=null;state.portfolioScenario=null;state.benchmarkB=null;state.optimization=null;state.portfolioToken++;
 $('qf-b21-compare-export').disabled=true;$('qf-b21-portfolio-export').disabled=true;
 $('qf-b21-risk-table').textContent='Loading a new common-date sample…';$('qf-b21-risk-scatter').replaceChildren();$('qf-b21-distribution').replaceChildren();$('qf-b21-correlation').textContent='Waiting for the new sample.';$('qf-b21-optimizer-output').replaceChildren();
 renderPortfolioResearch();renderFinanceComparison();
 $('qf-b21-compare-state').textContent='Aligning '+symbols.length+' company histories on shared observed dates…';
 $('qf-b21-compare-chart').textContent='Loading eligible price history…';
 try{
  const days=Number($('qf-b21-compare-range').value);
  const batch=await fetchBatch(symbols,days);
  if(request!==state.compareToken||symbols.join(',')!==state.compare.join(','))return;
  const result=B.compare(batch.aligned);
  state.comparison=result;state.compareSource=batch;state.portfolioData=result;state.portfolioOrigin=batch.source;
  const benchmark=await fetchBenchmark(batch.aligned,days,batch.kind,batch.equityFeed);
  if(request!==state.compareToken)return;
  state.benchmarkB=benchmark;
  $('qf-b21-compare-state').textContent=symbols.length+' companies · '+result.coverage.common_closes+' identical dated closes · '+result.coverage.first+' through '+result.coverage.last;
  const plot=result.symbols.map((s,i)=>({label:s,values:result.indexed[s]}));
  if(benchmark)plot.push({label:batch.kind==='market'?'SPY observed':'SPY illustrative',values:benchmark.values});
  linePlot('qf-b21-compare-chart',result.dates,plot);
  $('qf-b21-compare-provenance').textContent=batch.source+' '+result.convention+' Benchmark is '+(benchmark?(batch.kind==='market'?'observed price-only':'synthetic and illustrative'):'withheld: matching dates and compatible feed were not verified')+'. No missing dates were filled. Each line starts at 100: a level of 110 means 10% above its first observation, not a $110 share price.';
  riskTable(result);renderHistogram(result);heatmap('qf-b21-correlation',result);$('qf-b21-compare-export').disabled=false;
  if($('page-portfolio').classList.contains('active'))renderPortfolioResearch();
 }catch(e){if(request!==state.compareToken)return;
  state.comparison=null;state.compareSource=null;state.portfolioData=null;state.portfolioScenario=null;state.benchmarkB=null;
  $('qf-b21-compare-export').disabled=true;$('qf-b21-portfolio-export').disabled=true;
  $('qf-b21-risk-table').textContent='Risk statistics unavailable for this request.';$('qf-b21-risk-scatter').replaceChildren();$('qf-b21-distribution').textContent='No current return sample.';$('qf-b21-correlation').textContent='No current common-date return sample.';renderPortfolioResearch();
  $('qf-b21-compare-state').textContent='History unavailable: '+String(e.message||e).slice(0,180)+' SEC comparison remains available.';
  $('qf-b21-compare-chart').textContent='No compatible common-date price history. No synthetic fallback in owner mode.';
  $('qf-b21-compare-provenance').textContent='Unavailable market history; SEC financial rows are independent.';
 }
}
function currentUniverse(){
 if(state.compare.length>=2)return state.compare.slice();
 const chosen=[state.symbol,...['MSFT','AAPL','NVDA'].filter(s=>s!==state.symbol&&bySymbol.has(s))];
 state.compare=chosen.slice(0,3);renderCompareChips();
 return state.compare.slice();
}
function resetWeights(symbols){
 const key=symbols.join(',');if(state.portfolioKey===key&&state.portfolioWeights)return;
 state.portfolioKey=key;state.portfolioWeights=B.suggestedWeights(symbols);state.portfolioBase={...state.portfolioWeights};state.optimization=null;
}
function weightPercentageSet(symbols,symbol,next){
 const previous=state.portfolioWeights,clamped=Math.max(0,Math.min(100,Math.round(next)));
 const others=[...symbols,'cash'].filter(s=>s!==symbol);const desired=100-clamped;
 const initial=others.map(s=>Math.max(0,Math.round((previous[s]||0)*100)));
 const sum=initial.reduce((a,b)=>a+b,0);
 const raw=others.map((s,i)=>sum>0?initial[i]*desired/sum:desired/others.length);
 const ints=raw.map(Math.floor),remainder=desired-ints.reduce((a,b)=>a+b,0);
 [...others.keys()].sort((a,b)=>(raw[b]-ints[b])-(raw[a]-ints[a])).slice(0,remainder).forEach(i=>ints[i]++);
 const weights={[symbol]:clamped/100};others.forEach((s,i)=>{weights[s]=ints[i]/100;});B.validWeights(symbols,weights);
 state.portfolioWeights=weights;window.dispatchEvent(new Event('qf:research-universe'));
}
function renderSliders(){
 const symbols=currentUniverse(),weights=state.portfolioWeights,controls=[...$('qf-b21-weight-controls').querySelectorAll('[data-qf-b21-weight]')],keys=[...symbols,'cash'];
 // Keep native range elements alive during drag and repeated keyboard adjustments.
 if(controls.length===keys.length&&controls.every((control,i)=>control.dataset.qfB21Weight===keys[i])){for(const control of controls){const n=Math.round(weights[control.dataset.qfB21Weight]*100);control.value=String(n);control.closest('label').querySelector('output').textContent=n+'%';}return;}
 $('qf-b21-weight-controls').innerHTML=[...symbols,'cash'].map(s=>'<label class="qf-b21-slider-line"><span>'+esc(s==='cash'?'Cash':(bySymbol.get(s)?.name||s))+'</span><input type="range" min="0" max="100" step="1" value="'+Math.round(weights[s]*100)+'" data-qf-b21-weight="'+esc(s)+'" aria-label="'+esc(s)+' allocation percentage"/><output>'+Math.round(weights[s]*100)+'%</output></label>').join('');
 $('qf-b21-weights-total').textContent='Total 100% · '+symbols.length+' companies + cash · adjustments maintain full allocation';
}
function renderConcentration(){
 const symbols=currentUniverse();if(!state.portfolioWeights)return;
 const c=B.concentration(symbols,state.portfolioWeights);
 $('qf-b21-concentration').innerHTML=[['Invested weight',pct(c.invested_share)],['Cash',pct(c.cash_share)],['Concentration · HHI',c.invested_hhi===null?'N/A (all cash)':value(c.invested_hhi,3)],['Effective positions',c.effective_positions===null?'N/A':value(c.effective_positions,2)]].map(([a,b])=>'<div><small>'+esc(a)+'</small><strong>'+esc(b)+'</strong></div>').join('');
}
function renderPortfolioResearch(){
 const symbols=currentUniverse();resetWeights(symbols);renderSliders();renderConcentration();
 const result=state.portfolioData;
 if(!result||result.symbols.join(',')!==symbols.join(',')){
  state.portfolioScenario=null;
  $('qf-b21-overview-chart').textContent='Eligible common-date history is not loaded.';
  $('qf-b21-whatif-chart').textContent='Historical chart unavailable. Allocation and concentration remain interactive.';
  $('qf-b21-overview-stats').replaceChildren();$('qf-b21-whatif-stats').replaceChildren();
  $('qf-b21-analysis-stats').replaceChildren();heatmap('qf-b21-analysis-corr',null);
  $('qf-b21-analysis-stress').textContent='No aligned history; risk statistics withheld rather than invented.';
  $('qf-b21-portfolio-export').disabled=true;
  return;
 }
 let amount=Number($('qf-b21-amount').value);if(!Number.isFinite(amount)||amount<100||amount>1e8){
  state.portfolioScenario=null;$('qf-b21-portfolio-export').disabled=true;$('qf-b21-amount').setAttribute('aria-invalid','true');
  $('qf-b21-whatif-chart').textContent='Enter a hypothetical starting value from $100 to $100 million.';$('qf-b21-whatif-stats').replaceChildren();$('qf-b21-analysis-stats').replaceChildren();heatmap('qf-b21-analysis-corr',null);$('qf-b21-analysis-stress').textContent='Correct the starting value to recompute this allocation study.';$('qf-b21-whatif-provenance').textContent='Scenario not calculated. Enter a valid hypothetical starting value to inspect current results.';return;
 }
 $('qf-b21-amount').removeAttribute('aria-invalid');
 const baseline=B.scenario(result,state.portfolioBase,amount),selected=B.scenario(result,state.portfolioWeights,amount);
 state.portfolioScenario={baseline,selected};
 const benchmark=state.benchmarkB&&state.benchmarkB.values.length===result.dates.length?state.benchmarkB:null;
 const lines=[{label:'Your weights',values:selected.indexed},{label:'Starting weights',values:baseline.indexed}];
 if(benchmark)lines.push({label:benchmark.kind==='market'?'SPY observed':'SPY simulated',values:benchmark.values});
 linePlot('qf-b21-overview-chart',result.dates,[{label:'Illustrative current basket',values:baseline.indexed},...(benchmark?[{label:benchmark.kind==='market'?'SPY observed':'SPY simulated',values:benchmark.values}]:[])]);
 linePlot('qf-b21-whatif-chart',result.dates,lines);
 const info=state.portfolioOrigin||'Synthetic illustrated price samples.';
 $('qf-b21-overview-data-status').textContent=result.coverage.first+' to '+result.coverage.last+' · '+result.coverage.common_closes+' common closes · '+info;
 $('qf-b21-overview-stats').innerHTML=[['Illustrative period change',pct(baseline.summary.total_return)],['Historical annualized volatility',pct(baseline.summary.annual_volatility)],['Max drawdown',pct(baseline.summary.max_drawdown)]].map(([a,b])=>'<div><small>'+esc(a)+'</small><strong>'+esc(b)+'</strong></div>').join('');
 $('qf-b21-whatif-stats').innerHTML=[['Historical period change',pct(selected.summary.total_return)],['Annualized volatility',pct(selected.summary.annual_volatility)],['Max drawdown',pct(selected.summary.max_drawdown)],['Historical daily ES 95%',pct(selected.summary.daily_es95_loss)]].map(([a,b])=>'<div><small>'+esc(a)+'</small><strong>'+esc(b)+'</strong></div>').join('');
 $('qf-b21-whatif-provenance').textContent=info+' Historical daily constant-weight rebalancing; no fees, interest, taxes or dividends modeled. Starting value '+usd(amount)+'. '+(benchmark?'Benchmark series indexed on all matching dates.':'Benchmark withheld because matching dates and compatible feed were not verified.')+' Chart levels start at 100 and show relative change, not a share price. No recorded account P&L or future prediction.';
 const split=selected.split_vol;
 $('qf-b21-analysis-stats').innerHTML=[['Annualized volatility',pct(selected.summary.annual_volatility)],['Maximum drawdown',pct(selected.summary.max_drawdown)],['Daily loss VaR 95%',pct(selected.summary.daily_var95_loss)],['Daily loss ES 95%',pct(selected.summary.daily_es95_loss)]].map(([a,b])=>'<div><small>'+esc(a)+'</small><strong>'+esc(b)+'</strong></div>').join('');
 $('qf-b21-analysis-source').textContent=info+' Common-date return matrix: '+result.coverage.common_closes+' observations. VaR/ES are daily empirical losses, not worst-case bounds.';
 heatmap('qf-b21-analysis-corr',result);
 $('qf-b21-analysis-stress').textContent='Worst observed sample day: '+pct(selected.summary.worst_day)+'. '+(split?'First-half vs second-half annualized historical volatility: '+pct(split.first_half)+' vs '+pct(split.second_half)+'. This is a stability diagnostic, not a confidence interval.':'Sample too short for a two-half volatility comparison.')+' Neither historical stress nor fitted minimum variance establishes future outcomes.';
 $('qf-b21-portfolio-export').disabled=false;
}
async function loadPortfolioResearch(){
 const symbols=currentUniverse(),key=symbols.join(',');resetWeights(symbols);renderPortfolioResearch();
 if(state.portfolioData?.symbols.join(',')===key)return;
 const token=++state.portfolioToken;
 $('qf-b21-overview-data-status').textContent='Loading '+symbols.length+' company histories for the portfolio study…';
 try{
  const days=Number($('qf-b21-compare-range').value);
  const batch=await fetchBatch(symbols,days);
  if(token!==state.portfolioToken||state.compare.join(',')!==key)return;
  const result=B.compare(batch.aligned);
  const benchmark=await fetchBenchmark(batch.aligned,days,batch.kind,batch.equityFeed);
  if(token!==state.portfolioToken||state.compare.join(',')!==key)return;
  state.portfolioData=result;state.portfolioOrigin=batch.source;state.benchmarkB=benchmark;
  renderPortfolioResearch();
 }catch(e){if(token!==state.portfolioToken)return;
  state.portfolioData=null;
  $('qf-b21-overview-data-status').textContent='History unavailable: '+String(e.message||e).slice(0,150)+'. Allocation math still works.';
  renderPortfolioResearch();
 }
}
async function loadOwnerVirtualState(){
 const token=++state.ownerToken,el=$('qf-b21-owner-account');
 el.hidden=mode()!=='private';if(el.hidden){$('qf-b21-owner-account-table').replaceChildren();return;}
 $('qf-b21-owner-account-status').textContent='Loading MFA-protected virtual account balances…';
 try{
  const accepted=window.QFPrivateBridgeV23?.snapshot();const r=accepted?{portfolio:accepted,version:accepted.version}:await getPrivate('private/state');if(token!==state.ownerToken||mode()!=='private')return;
  const p=r.portfolio||{},holdings=p.holdings||{},cash=p.cash;
  if(!rowsOrNull(cash)||typeof holdings!=='object'||Array.isArray(holdings))throw Error('Owner virtual state missing expected fields.');
  const rows=Object.entries(holdings).filter(([s,q])=>/^[A-Z0-9./-]{1,15}$/.test(s)&&rowsOrNull(q)&&q>=0).slice(0,30);
  $('qf-b21-owner-account-table').innerHTML='<table><thead><tr><th>Virtual position</th><th>Quantity</th></tr></thead><tbody>'+rows.map(([s,q])=>'<tr><th>'+esc(s)+'</th><td>'+esc(value(q,6))+'</td></tr>').join('')+'<tr><th>Cash (owner only)</th><td>'+esc(usd(cash))+'</td></tr></tbody></table>';
  $('qf-b21-owner-account-status').textContent='Saved owner state · version '+String(Number(r.version)||0)+'. Loading entitled market observations for conditional valuation…';
  if(rows.length>8||rows.length!==Object.keys(holdings).filter(s=>holdings[s]!==0).length)throw Error('Too many or invalid owner positions for complete quote coverage; P&L withheld.');
  const symbols=rows.filter(([,q])=>q>0).map(([s])=>s);
  const quoteResponse=symbols.length?await getPrivate('private/quotes?'+new URLSearchParams({symbols:symbols.join(',')})):{quotes:[]};
  if(token!==state.ownerToken||mode()!=='private')return;
  const snapshot=B.ownerSnapshot(p,quoteResponse.quotes,new Date().toISOString());
  $('qf-b21-owner-account-table').innerHTML=   '<table><thead><tr><th>Owner-only holding</th><th>Units</th><th>Authorized quote</th><th>Indicative value</th><th>Last quote date</th></tr></thead><tbody>'+
   snapshot.quotes.map(q=>'<tr><th>'+esc(q.symbol)+'</th><td>'+esc(value(q.units,6))+'</td><td>'+esc(usd(q.price))+'</td><td>'+esc(usd(q.market_value))+'</td><td>'+esc(q.timestamp.slice(0,16))+'</td></tr>').join('')+
   '<tr><th>Uninvested virtual cash</th><td>—</td><td>—</td><td>'+esc(usd(snapshot.cash))+'</td><td>Ledger</td></tr></tbody></table>';
  $('qf-b21-owner-account-status').textContent=snapshot.note;window.dispatchEvent(new CustomEvent('qf:owner-valuation',{detail:{snapshot,version:r.version}}));
 }catch(e){if(token===state.ownerToken)$('qf-b21-owner-account-status').textContent='Owner-only portfolio valuation withheld: '+String(e.message||e).slice(0,150)+'. Stored holdings and cash remain visible when authorized.';}
}
function lowerRisk(){
 if(!state.portfolioData){$('qf-b21-optimizer-output').textContent='Minimum variance unavailable without common-date price history.';return;}
 try{
  const run=B.minimumVariance(state.portfolioData,state.portfolioWeights,0.7);state.optimization=run;
  $('qf-b21-optimizer-output').innerHTML='<div class="qf-b21-note"><strong>Historical minimum-variance experiment</strong><p>Annualized fitted volatility: '+esc(pct(run.base.summary.annual_volatility))+' → '+esc(pct(run.optimized.summary.annual_volatility))+'. Kept cash '+esc(pct(run.weights.cash))+', maximum company allocation 70%.</p><p>'+esc(run.limitation)+'</p><button class="btn sm" type="button" id="qf-b21-apply-optimizer">Apply illustrative weights</button></div>';
  // Avoid mixing model language with financial advice; these are constrained fitted weights only.
 }catch(e){$('qf-b21-optimizer-output').textContent='Optimization withheld: '+String(e.message||e).slice(0,180);}
}
function exportComparison(){
 if(!state.comparison)return;
 const r=state.comparison,header=['date',...r.symbols.map(s=>s+'_close_usd'),...r.symbols.map(s=>s+'_indexed')];
 csv([header,...r.dates.map((d,i)=>[d,...r.symbols.map(s=>r.indexed[s][i]===null?null:state.compareSource.aligned.closes[s][i]),...r.symbols.map(s=>r.indexed[s][i])])],
  'quantforge-compare-'+(state.compareSource.kind==='market'?'private-observed':'synthetic-example')+'.csv');
}
function exportComparisonSEC(){if(!state.financeCompare)return;
 const rows=[['symbol','issuer','snapshot_as_of','fiscal_end','revenue_usd','revenue_growth_fraction','operating_margin_fraction','fcf_proxy_usd','revenue_filing_accession']];
 for(const r of state.financeCompare){rows.push([r.symbol,r.name,data.as_of,r.fiscal,r.revenue,r.growth,r.margin,r.fcf,r.f.annual[0]?.sources?.revenue_usd?.accession||null]);}
 csv(rows,'quantforge-reported-sec-comparison.csv');
}
function exportPortfolio(){const amount=Number($('qf-b21-amount').value);if(!Number.isFinite(amount)||amount<100||amount>1e8||!state.portfolioScenario||!state.portfolioData)return;
 const {selected,baseline}=state.portfolioScenario;
 csv([['date','hypothetical_selected_index','starting_weight_index','market_source_kind'],...selected.dates.map((d,i)=>[d,selected.indexed[i],baseline.indexed[i],state.compareSource?.kind|| (mode()==='private'?'market':'synthetic')])],
  'quantforge-hypothetical-portfolio-study.csv');
}

function showModel(name){
 state.model=name;
 if(window.QFModelsMethods22)window.QFModelsMethods22.showModel(name);
}
function mountModels(){
 // Legacy model DOM and its tested handlers stay in their hidden original routes.
 // Release C presents new evidence views instead of moving old accordion panels.
}
function authUpdate(){
 const signed=$('private-signed');const ready=signed&&!signed.hidden;
 if(state.privateReady===ready)return;
 state.privateReady=ready;invalidateComparison();state.portfolioToken++;state.ownerToken++;
 if(ready)loadOwnerVirtualState();else $('qf-b21-owner-account').hidden=true;
 if(ready){state.privateMode=true;setAccount();if(location.hash.startsWith('#private/'))window.QFNavigate20('explore');selectCompany(state.symbol);}
 else if(state.privateMode){state.privateMode=false;setAccount();selectCompany(data.companies.some(c=>c.symbol===state.symbol)?state.symbol:'MSFT');}
}
function init(){
 $('qf-v20-universe').textContent=companies.length+' covered companies · SEC snapshot '+data.as_of;
 window.QFInvestmentPicker27.mount({input:$('qf-v20-search'),panel:$('qf-v20-search-results'),mode,search:searchAssets,published:data.companies,onSelect:asset=>{rememberAsset(asset);selectCompany(asset.symbol);}});
 document.addEventListener('click',e=>{
  if(e.target.closest('[data-qf-portfolio]'))setTimeout(renderPortfolioResearch,0);
  const range=e.target.closest('[data-qf-range]');if(range){
   const next=range.dataset.qfRange==='ALL'?'ALL':Number(range.dataset.qfRange);
   state.range=next;document.querySelectorAll('[data-qf-range]').forEach(b=>b.classList.toggle('active',b===range));
   if(mode()==='private'&&(next===730||next==='ALL')&&state.priceSource?.type==='market'&&state.price.length<340)pendingPrice=loadPrice();else renderPriceData();return;
  }
  const financial=e.target.closest('[data-qf-financial]');if(financial){state.finance=financial.dataset.qfFinancial;renderFinances(Q.financialSummary(company(),data.as_of));return;}
  const rm=e.target.closest('[data-qf-remove]');if(rm){state.compare=state.compare.filter(s=>s!==rm.dataset.qfRemove);invalidateComparison();renderCompareChips();return;}
  const model=e.target.closest('[data-qf-model]');if(model){showModel(model.dataset.qfModel);return;}
  const sort=e.target.closest('[data-qf-b21-sort]');if(sort&&['symbol','fiscal','revenue','growth','margin','fcf'].includes(sort.dataset.qfB21Sort)){
   if(state.financeSort===sort.dataset.qfB21Sort)state.financeSortDirection*=-1;
   else {state.financeSort=sort.dataset.qfB21Sort;state.financeSortDirection=1;}
   renderFinanceComparison();return;
  }
  if(e.target.closest('#qf-b21-edit-universe')){window.QFNavigate20('compare');return;}
  if(e.target.closest('#qf-b21-lower-risk')){lowerRisk();return;}
  if(e.target.closest('#qf-b21-apply-optimizer')&&state.optimization){
   state.portfolioWeights={...state.optimization.weights};renderPortfolioResearch();return;
  }
 });
 $('qf-v20-analyze').addEventListener('click',analyze);
 $('qf-v20-add-compare').addEventListener('click',()=>{addCompare();window.QFNavigate20('compare');});
 $('qf-v20-export-price').addEventListener('click',exportPrice);
 $('qf-v20-benchmark').addEventListener('change',e=>{state.benchmarkOn=e.target.checked;if(state.benchmarkOn)loadBenchmark();else{state.benchmark=null;state.benchToken++;renderPriceData();}});
 $('qf-v20-export-sec').addEventListener('click',exportSEC);
 const comparePanel=document.createElement('div');comparePanel.id='qf27-compare-options';$('qf-v20-compare-search').after(comparePanel);$('qf-v20-compare-options').remove();
 window.QFInvestmentPicker27.mount({input:$('qf-v20-compare-search'),panel:comparePanel,mode,search:searchAssets,published:data.companies,onSelect:addAsset});
 $('qf-v20-compare-run').addEventListener('click',runCompare);
 $('qf-b21-compare-range').addEventListener('change',()=>{invalidateComparison();state.portfolioToken++;});
 $('qf-b21-compare-export').addEventListener('click',exportComparison);
 $('qf-b21-finance-export').addEventListener('click',exportComparisonSEC);
 $('qf-b21-portfolio-export').addEventListener('click',exportPortfolio);
 $('qf-b21-amount').addEventListener('input',renderPortfolioResearch);
 $('qf-b21-weight-controls').addEventListener('input',e=>{
  const control=e.target.closest('[data-qf-b21-weight]');if(!control)return;
  weightPercentageSet(currentUniverse(),control.dataset.qfB21Weight,Number(control.value));
  state.optimization=null;$('qf-b21-optimizer-output').replaceChildren();renderPortfolioResearch();
 });
 mountModels();
 const auth=$('private-signed');if(auth)new MutationObserver(authUpdate).observe(auth,{attributes:true,attributeFilter:['hidden']});
 window.addEventListener('qf:owner-state',()=>{if(mode()==='private'&&$('page-portfolio').classList.contains('active'))void loadOwnerVirtualState();});
 window.addEventListener('qf:route-change',e=>{
  if(e.detail.route==='compare'){if(!state.compare.includes(state.symbol))addCompare();}
  if(e.detail.route==='portfolio'){loadPortfolioResearch();if(mode()==='private')loadOwnerVirtualState();}
  if(e.detail.route==='explore')setAccount();
 });
 selectCompany(state.symbol);renderCompareChips();authUpdate();
}
init();
window.QFResearch20=Object.freeze({choose:selectCompany,analyze,
 async loadCompanyStudy(symbol,{signal}={}){
  const portfolio=window.QFPrivateBridgeV23?.snapshot(),epoch=studyEpoch;
  const valid=()=>mode()==='private'&&state.privateReady&&portfolio&&window.QFPrivateBridgeV23?.snapshot()?.version===portfolio.version&&epoch===studyEpoch&&!signal?.aborted;
  if(!valid())throw Error('An MFA-verified owner session is required.');
  const read=async(path,requestSignal)=>{if(!valid())throw Error('Research authorization changed.');const value=await getPrivate(path,requestSignal);if(!valid())throw Error('Research context changed.');return value;};
  const input=await window.QFCompanyStudy35.load({symbol,snapshot:data,portfolio,read,signal});
  if(!valid())throw Error('Research context changed.');return input;
 },
 async acquireStudy(scope){
  const selected=state.symbol,kind=mode(),token=state.priceToken,universe=state.compare.join(',');
  const market=selected==='SPY'?'VTI':'SPY';
  const ownerAtStart=kind==='private'?window.QFPrivateBridgeV23?.snapshot():null;
  const heldForStudy=Object.entries(ownerAtStart?.holdings||{}).filter(([symbol,units])=>!symbol.includes('/')&&Number.isFinite(units)&&units>0).map(([symbol])=>symbol).slice(0,3);
  let symbols=scope==='factors'?[selected,market,'IWM','IVE']:scope==='company'?[selected,market,...heldForStudy]:(state.compare.length>=2?state.compare.slice():[selected,market]);
  symbols=[...new Set(symbols)];if(!symbols.includes(selected))symbols=[selected,...symbols].slice(0,5);
  const batch=scope==='valuation'?{aligned:{symbols:[],dates:[],closes:{}},source:'SEC capital and independently dated market quote; no historical price path required',kind:kind==='private'?'market':'synthetic'}:await fetchBatch(symbols,730);
  if(kind!==mode()||selected!==state.symbol||token!==state.priceToken||universe!==state.compare.join(','))throw Error('Research context changed.');
  let quote=null,quotes=null,portfolio=null,capital=null,studyCompany=company(),readFailures=[];
  if(kind==='private'&&['company','valuation'].includes(scope)){
   portfolio=window.QFPrivateBridgeV23?.snapshot();
   const names=[...new Set([selected,...Object.keys(portfolio?.holdings||{})])].slice(0,8);
   const requests=await Promise.allSettled([getPrivate('private/quotes?'+new URLSearchParams({symbols:names.join(',')})),getPrivate('private/valuation-capital?'+new URLSearchParams({symbol:selected})),getPrivate('private/sec/company?'+new URLSearchParams({symbol:selected}))]);
   readFailures=requests.flatMap((r,i)=>r.status==='rejected'?[['quotes','capital','company'][i]]:[]);
   if(requests[0].status==='fulfilled'){const response=requests[0].value;quote=response.quotes?.find(q=>q.symbol===selected)||null;quotes=Object.fromEntries((response.quotes||[]).map(q=>[q.symbol,q]));}
   if(requests[1].status==='fulfilled')capital=requests[1].value;
   if(requests[2].status==='fulfilled'&&requests[2].value.symbol===selected&&Array.isArray(requests[2].value.annual))studyCompany=requests[2].value;
  }
  if(kind!==mode()||selected!==state.symbol||token!==state.priceToken||universe!==state.compare.join(','))throw Error('Research context changed.');
  if(kind==='private'&&window.QFPrivateBridgeV23?.snapshot()?.version!==ownerAtStart?.version)throw Error('The account changed during research. Analyze again.');
  return {scope,symbol:selected,company:studyCompany,capital,snapshot:data,assessmentPrices:state.price?state.price.map(r=>({...r})):[],assessmentSource:state.priceSource?.source,readFailures,history:{...batch.aligned,sessions_per_year:252,source:batch.source,calendar:'equity_sessions'},origin:batch.kind,asOf:new Date().toISOString(),quote,quotes,portfolio,weights:scope==='portfolio'?state.portfolioWeights:null};
 },
 async walkforward(){
  const symbols=currentUniverse(),kind=mode(),selection=state.symbol,token=state.compareToken;
  const batch=await fetchBatch(symbols,730);
  if(kind!==mode()||selection!==state.symbol||token!==state.compareToken||symbols.join(',')!==state.compare.join(','))throw Error('Research context changed. Run the study again.');
  const history={...batch.aligned,sessions_per_year:252,source:batch.source};
  const result=window.QFPrivateWalkforward.run(history,{train:126,step:21,feeBps:5,cap:0.6});
  return {...result,origin:batch.kind};
 },
 switchMode(next){
  if(!['private','public'].includes(next)||(next==='private'&&!state.privateReady))return;
  state.privateMode=next==='private';if(next==='public')state.compare=state.compare.filter(s=>data.companies.some(c=>c.symbol===s));renderCompareChips();invalidateComparison();state.ownerToken++;
  $('qf-b21-owner-account').hidden=true;$('qf-b21-owner-account-table').replaceChildren();
  const chosen=next==='public'&&!data.companies.some(c=>c.symbol===state.symbol)?'MSFT':state.symbol;
  selectCompany(chosen);window.dispatchEvent(new Event('qf:data-mode'));if(next==='private'&&$('page-portfolio').classList.contains('active'))void loadOwnerVirtualState();return true;
 },
 searchAssets,reloadPortfolio:loadPortfolioResearch,exportRows:csv,chooseAsset(asset){rememberAsset(asset);selectCompany(asset.symbol);},addAssetToCompare:addAsset,assetInfo:symbol=>bySymbol.get(symbol)||{symbol,name:symbol+' · saved investment'},
 context:()=>({symbol:state.symbol,name:company().name,origin:state.priceSource?.type||null,
  mode:mode(),authenticated:state.privateReady,revision:state.priceToken,universe:state.compare.slice(),weights:state.portfolioWeights?{...state.portfolioWeights}:null,
  prices:state.price?state.price.map(p=>({date:p.date,close:p.close})):null,
  financial:Q.financialSummary(company(),data.as_of),snapshot:data.as_of})});
})();
