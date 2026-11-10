/* Release A shared stock-first UI. Price and news IO is owner-only; SEC is published. */
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
const evidenceId=id=>esc(id.replaceAll(':',' · '));
const safeUrl=s=>{try{const u=new URL(s);return u.protocol==='https:'&&u.hostname&&u.username===''&&u.password===''?u.href:null;}catch(_){return null;}};
const state={symbol:bySymbol.has('MSFT')?'MSFT':companies[0].symbol,range:365,finance:'revenue_usd',price:null,priceSource:null,
 privateReady:false,privateMode:false,priceToken:0,newsToken:0,runToken:0,benchmark:null,benchmarkOn:false,benchToken:0,
 result:null,compare:[],model:'prediction',loadingPrice:false};
let resultsOpen=false;
function company(){return bySymbol.get(state.symbol);}
function mode(){return state.privateMode&&state.privateReady?'private':'public';}
async function getPrivate(path){
 const res=await fetch('/api/'+path,{credentials:'same-origin',cache:'no-store'});
 let json;try{json=await res.json();}catch(_){throw Error('Research API unavailable. Historical SEC figures remain available.');}
 if(!res.ok)throw Error(String(json?.detail||'Private data unavailable.').slice(0,180));
 return json;
}
function setAccount(){
 $('qf-v20-account-status').textContent=mode()==='private'?'MFA verified · entitled owner data':'Public SEC research · illustrative price chart';
 $('qf-v20-mode').textContent=mode()==='private'?'Private tools / sign out':'Private workspace';
 $('qf-v20-benchmark-wrap').hidden=mode()!=='private';
 $('qf-v20-universe').textContent=companies.length+' SEC companies · '+(mode()==='private'?'private market feed':'public demonstration');
}
function searchResults(query){
 const q=query.trim().toLowerCase();
 if(!q){$('qf-v20-search-results').hidden=true;$('qf-v20-search').setAttribute('aria-expanded','false');return;}
 const matches=companies.filter(c=>c.symbol.toLowerCase().includes(q)||c.name.toLowerCase().includes(q)).slice(0,9);
 $('qf-v20-search-results').innerHTML=matches.length?matches.map(c=>'<button type="button" role="option" data-qf-pick="'+esc(c.symbol)+'"><span>'+esc(c.name)+'</span><strong>'+esc(c.symbol)+'</strong></button>').join(''):'<p class="tiny" style="padding:12px">No covered issuer matches. Try another name.</p>';
 $('qf-v20-search-results').hidden=false;$('qf-v20-search').setAttribute('aria-expanded','true');
}
function selectCompany(symbol){
 if(!bySymbol.has(symbol))return;
 state.symbol=symbol;state.result=null;state.price=null;state.priceSource=null;state.benchmark=null;state.priceToken++;state.newsToken++;state.runToken++;state.benchToken++;
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
 renderNewsEmpty(mode()==='private'?'Checking dated headlines…':'News is available only through owner-authorized market providers. No public headlines are invented.');
 setAccount();loadPrice();loadNews();
}
function renderChartEmpty(msg){$('qf-v20-chart').textContent=msg;$('qf-v20-price-stats').replaceChildren();$('qf-v20-price-table').replaceChildren();}
function renderSource(f){
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
 $('qf-v20-source-badge').textContent=real?'Observed · '+(source.equity_feed||'crypto').toUpperCase():'Illustrative · synthetic';
 const price=Q.chartWindow(state.price,state.range);
 if(!price.length){renderChartEmpty('No observations in this chart range.');return;}
 $('qf-v20-current').textContent=usd(price[price.length-1].close);
 $('qf-v20-change').textContent=(real?'Observed close':'Simulated example')+' · '+price[price.length-1].date;
 const overall=real?Q.priceStatistics(Q.chartWindow(state.price,Math.max(30,Number(state.range)||730))):null;
 const change=price[price.length-1].close/price[0].close-1;
 $('qf-v20-price-stats').innerHTML=[['Window change',pct(change)],['Price observations',String(price.length)],['Observed max drawdown',overall?pct(overall.max_drawdown):'Not evaluated']].map(x=>'<div><small>'+esc(x[0])+'</small><strong>'+esc(x[1])+'</strong></div>').join('');
 const scopeText=real?source.source+' · '+source.coverage:'Deterministic synthetic company-labeled chart demonstration. NOT observed '+company().name+' prices, an estimate, or an investment return.';
 $('qf-v20-chart-source').textContent=scopeText;
 const coverage=$('qf-v20-price-coverage');if(coverage)coverage.textContent='Price: '+scopeText+' · '+price[0].date+' through '+price[price.length-1].date;
 const benchmark=real&&state.benchmarkOn&&state.benchmark?Q.chartWindow(state.benchmark,state.range):null;
 drawPriceChart(price,benchmark,real);
 const sampled=price.length>10?[...price.slice(0,2),...price.slice(-8)]:price;
 $('qf-v20-price-table').innerHTML='<p>Underlying dated closes · '+(price.length>10?'first 2 and latest 8 shown; export for all':'all available observations')+'</p><div class="table-wrap"><table><thead><tr><th>Date</th><th>Close (USD)</th></tr></thead><tbody>'+sampled.map(p=>'<tr><td>'+esc(p.date)+'</td><td>'+esc(usd(p.close))+'</td></tr>').join('')+'</tbody></table></div>';
}
function drawPriceChart(price,benchmark,real){
 const W=720,H=292,left=55,right=694,top=20,bottom=247;
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
  return '<line x1="'+left+'" x2="'+right+'" y1="'+y+'" y2="'+y+'" stroke="#e0eae5"/><text x="'+(left-9)+'" y="'+(y+4)+'" font-size="10" text-anchor="end" fill="#637b70">'+(normalized?value(hi-(hi-lo)*i/4,0):'$'+value(hi-(hi-lo)*i/4,0))+'</text>';
 }).join('');
 const ticks=[0,0.25,0.5,0.75,1].map(t=>{
  const i=Math.round((series.length-1)*t);
  return '<text x="'+X(i)+'" y="270" font-size="11" text-anchor="middle" fill="#688177">'+esc(series[i].date.slice(0,7))+'</text>';
 }).join('');
 const mark=real?'':'<text x="375" y="55" text-anchor="middle" font-size="19" font-weight="750" fill="#d4e5dc">SYNTHETIC · NOT REAL MARKET PRICES</text>';
 $('qf-v20-chart').innerHTML='<svg viewBox="0 0 '+W+' '+H+'" tabindex="0" role="img" aria-label="'+(real?'Observed':'Synthetic demonstration')+' close-price chart '+esc(series[0].date)+' to '+esc(series[series.length-1].date)+'. Arrow keys inspect values."><title>'+(real?'Observed, price-only historical closes':'Synthetic illustration, not actual company market prices')+'</title>'+grid+ticks+mark+'<path d="'+path(series)+'" fill="none" stroke="#19826c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'+(bench?'<path d="'+path(bench)+'" fill="none" stroke="#b88c45" stroke-width="2" stroke-dasharray="6 5"/>':'')+'<line id="qf-v20-crosshair" x1="'+X(series.length-1)+'" x2="'+X(series.length-1)+'" y1="'+top+'" y2="'+bottom+'" stroke="#839c91" stroke-dasharray="3 4"/><circle id="qf-v20-crossdot" cx="'+X(series.length-1)+'" cy="'+Y(series[series.length-1].close)+'" r="5" fill="#155f50" stroke="#fff" stroke-width="2"/></svg><div class="qf-v20-cursor" aria-live="polite"><span id="qf-v20-cursor-value"></span><span>'+(normalized?'Indexed to 100 · common observed dates · SPY dashed':'Close price · hover or use arrow keys')+'</span></div>';
 const svg=$('qf-v20-chart').querySelector('svg');let index=series.length-1;
 const update=i=>{index=Math.min(series.length-1,Math.max(0,i));
  const x=X(index);$('qf-v20-crosshair').setAttribute('x1',x);$('qf-v20-crosshair').setAttribute('x2',x);
  $('qf-v20-crossdot').setAttribute('cx',x);$('qf-v20-crossdot').setAttribute('cy',Y(series[index].close));
  $('qf-v20-cursor-value').textContent=series[index].date+' · '+(normalized?value(series[index].close,2)+' indexed':'$'+value(series[index].close,2))+(bench?' · SPY '+value(bench[index].close,2):'');};
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
  renderPriceData();return;
 }
 renderChartEmpty('Requesting owner-authorized historical closes…');
 try{
  const days=state.range===730||state.range==='ALL'?730:365;
  const raw=await getPrivate('private/history-single?'+new URLSearchParams({symbol,days:String(days)}));
  if(token!==state.priceToken||symbol!==state.symbol)return;
  if(raw.licensed_private!==true||raw.symbol!==symbol||raw.ohlcv_available!==false)throw Error('Unexpected or unsupported market-data contract.');
  state.price=Q.priceSeries(raw.observations);
  state.priceSource={...raw,type:'market'};
  renderPriceData();
  if(state.benchmarkOn)loadBenchmark();
 }catch(e){if(token!==state.priceToken)return;
  state.price=null;state.priceSource=null;renderChartEmpty('Observed prices unavailable: '+String(e.message||e).slice(0,170)+'. SEC financials remain available.');
  $('qf-v20-current').textContent='Unavailable';$('qf-v20-change').textContent='No synthetic fallback used in private mode';
  $('qf-v20-source-badge').textContent='Market data unavailable';
  const coverage=$('qf-v20-price-coverage');if(coverage)coverage.textContent='Private market observations unavailable; no replacement or fabricated prices.';
 }
}
async function loadBenchmark(){
 const token=++state.benchToken;
 if(!state.benchmarkOn||mode()!=='private'||state.symbol==='SPY'||state.priceSource?.type!=='market'){state.benchmark=null;renderPriceData();return;}
 try{
  const days=state.range===730||state.range==='ALL'?730:365;
  const raw=await getPrivate('private/history-single?'+new URLSearchParams({symbol:'SPY',days:String(days)}));
  if(token!==state.benchToken||!state.benchmarkOn)return;
  state.benchmark=Q.priceSeries(raw.observations);renderPriceData();
 }catch(_){if(token===state.benchToken){state.benchmark=null;renderPriceData();$('qf-v20-chart-source').textContent+=' SPY benchmark unavailable; company closes still shown.';}}
}
function renderNewsEmpty(text){$('qf-v20-news').textContent=text;}
async function loadNews(){
 const token=++state.newsToken;
 if(mode()!=='private'){renderNewsEmpty('Public mode: licensed recent headlines are not redistributed. Sign in to see eligible dated owner-only news.');return;}
 const symbol=state.symbol;
 renderNewsEmpty('Checking dated provider headlines…');
 try{
  const news=await getPrivate('private/news-research?symbols='+encodeURIComponent(symbol));
  if(token!==state.newsToken||symbol!==state.symbol)return;
  const row=Array.isArray(news.rows)?news.rows.find(r=>r.symbol===symbol):null;
  if(!row||!row.headlines?.length){renderNewsEmpty('No eligible dated headlines returned. Company financial research remains available.');return;}
  const headlines=row.headlines.slice(0,4);
  $('qf-v20-news').innerHTML='<p class="tiny">'+esc(row.articles)+' dated headlines · '+esc(row.tone||'tone unavailable')+' · '+esc((row.topics||[]).join(', ')||'No strong topic cluster')+'</p>'+headlines.map(h=>{
   const url=safeUrl(h.url),title=esc(h.headline||'Untitled headline');
   return '<article class="qf-v20-news-item">'+(url?'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+title+'</a>':'<strong>'+title+'</strong>')+'<small>'+esc(String(h.created_at||'').slice(0,10))+' · '+esc(h.source||'Source not supplied')+' · lexical tone: '+esc(h.tone||'not assessed')+'</small></article>';
  }).join('')+'<p class="tiny">Topics: TF-IDF lexical matching; tone: dictionary and negation. Neither forecasts returns.</p>';
 }catch(e){if(token===state.newsToken)renderNewsEmpty('Headlines unavailable ('+String(e.message||e).slice(0,90)+'). Financial and price research still work.');}
}
function analyze(){
 const token=++state.runToken;
 const f=Q.financialSummary(company(),data.as_of);
 const result=Q.researchResult(f,state.price,state.priceSource);
 if(token!==state.runToken)return;
 state.result=result;
 $('qf-v20-run-state').textContent='Calculated for '+company().name+' · SEC snapshot '+data.as_of+' · '+(result.price_source==='market'?'observed private market risk':'no eligible observed market risk');
 $('qf-v20-findings').innerHTML=result.findings.map(f=>'<article class="qf-v20-finding '+esc(f.kind)+'"><span>'+esc(f.kind)+'</span><p>'+esc(f.text)+'</p><small>Evidence: '+(f.evidence_ids.length?f.evidence_ids.map(evidenceId).join(' · '):'Methodological limitation')+'</small></article>').join('')+'<div class="qf-v20-finding"><span>Uncertainties</span><p>'+esc(result.limitations.slice(0,3).join(' '))+'</p></div>';
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
 csv([['symbol','date','close_usd','price_origin','source_description'],...state.price.map(p=>[state.symbol,p.date,p.close,state.priceSource.type,state.priceSource.source])],
 'quantforge-'+state.symbol+'-'+state.priceSource.type+'-closes.csv');
}
function exportSEC(){
 const f=Q.financialSummary(company(),data.as_of);
 const columns=['revenue_usd','net_income_usd','operating_income_usd','operating_cash_flow_usd','capex_usd','free_cash_flow_usd'];
 const rows=[['symbol','snapshot_as_of','fiscal_end',...columns,...columns.filter(k=>k!=='free_cash_flow_usd').flatMap(k=>[k+'_filed',k+'_accession'])]];
 for(const r of f.annual)rows.push([state.symbol,data.as_of,r.fiscal_end,...columns.map(k=>r.metrics[k]??null),...columns.filter(k=>k!=='free_cash_flow_usd').flatMap(k=>[r.sources?.[k]?.filed??null,r.sources?.[k]?.accession??null])]);
 csv(rows,'quantforge-'+state.symbol+'-reported-sec.csv');
}
function addCompare(){if(!state.compare.includes(state.symbol)&&state.compare.length<5)state.compare.push(state.symbol);renderCompareChips();}
function renderCompareChips(){
 $('qf-v20-compare-chips').innerHTML=state.compare.map(s=>'<button type="button" data-qf-remove="'+esc(s)+'" aria-label="Remove '+esc(s)+'">'+esc(bySymbol.get(s).name)+' · '+esc(s)+' ×</button>').join('');
}
function runCompare(){
 if(state.compare.length<2||state.compare.length>5){$('qf-v20-compare-output').textContent='Choose 2–5 distinct covered companies. Return to Explore to choose your starting company.';return;}
 const details=state.compare.map(s=>({c:bySymbol.get(s),f:Q.financialSummary(bySymbol.get(s),data.as_of)}));
 const cells=details.map(({c,f})=>'<tr><th>'+esc(c.name)+' ('+esc(c.symbol)+')</th><td>'+esc(f.source.period)+'</td><td>'+esc(money(f.metrics.revenue_usd))+'</td><td>'+esc(pct(f.metrics.revenue_growth))+'</td><td>'+esc(pct(f.metrics.operating_margin))+'</td><td>'+esc(money(f.metrics.free_cash_flow_usd))+'</td></tr>').join('');
 $('qf-v20-compare-output').innerHTML='<div class="notice">Only annual SEC metrics are compared. Fiscal periods and business models may differ; the historical stock-return comparison is not yet enabled in Release A.</div><div class="table-wrap"><table><thead><tr><th>Company</th><th>Fiscal end</th><th>Revenue</th><th>Growth</th><th>Operating margin</th><th>FCF proxy</th></tr></thead><tbody>'+cells+'</tbody></table></div>';
}
function showModel(name){
 state.model=name;
 document.querySelectorAll('[data-qf-model]').forEach(b=>b.classList.toggle('active',b.dataset.qfModel===name));
 for(const route of ['prediction','risk','valuation','strategy'])$('qf-v20-model-'+route).hidden=route!==name;
}
function mountModels(){
 const v=$('qf-v181-title')?.closest('.qf-v181-validation-exhibit');
 if(v)$('qf-v20-model-evidence-target').appendChild(v);
 const move=(from,to)=>{const source=$(from),dest=$(to);if(source&&dest){const nodes=[...source.children];for(const child of nodes)dest.appendChild(child);}};
 move('page-quant','qf-v20-model-risk');
 move('page-valuation','qf-v20-model-valuation');
 const walk=$('lab-walkforward');if(walk)$('qf-v20-model-strategy').appendChild(walk);
 // Existing tested public numerical engines retain their original IDs and event handlers.
 showModel('prediction');
}
function authUpdate(){
 const signed=$('private-signed');const ready=signed&&!signed.hidden;
 if(state.privateReady===ready)return;
 state.privateReady=ready;
 if(ready){state.privateMode=true;setAccount();if(location.hash.startsWith('#private/'))window.QFNavigate20('explore');selectCompany(state.symbol);}
 else if(state.privateMode){state.privateMode=false;setAccount();selectCompany(state.symbol);}
}
function init(){
 $('qf-v20-universe').textContent=companies.length+' covered companies · SEC snapshot '+data.as_of;
 $('qf-v20-search').addEventListener('input',e=>searchResults(e.target.value));
 $('qf-v20-search').addEventListener('keydown',e=>{
  if(e.key==='Escape'){$('qf-v20-search-results').hidden=true;return;}
  if(e.key==='ArrowDown'&&!$('qf-v20-search-results').hidden){e.preventDefault();$('qf-v20-search-results').querySelector('button')?.focus();}
  if(e.key==='Enter'){const buttons=$('qf-v20-search-results').querySelectorAll('[data-qf-pick]');if(buttons.length===1){e.preventDefault();selectCompany(buttons[0].dataset.qfPick);}}
 });
 $('qf-v20-search-results').addEventListener('keydown',e=>{
  if(e.key==='Escape'){e.preventDefault();$('qf-v20-search-results').hidden=true;$('qf-v20-search').focus();}
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){const btns=[...$('qf-v20-search-results').querySelectorAll('button')],i=btns.indexOf(document.activeElement);if(btns.length){e.preventDefault();btns[Math.max(0,Math.min(btns.length-1,i+(e.key==='ArrowDown'?1:-1)))].focus();}}
 });
 document.addEventListener('click',e=>{
  const pick=e.target.closest('[data-qf-pick]');if(pick){selectCompany(pick.dataset.qfPick);return;}
  if(!e.target.closest('.qf-v20-search-area'))$('qf-v20-search-results').hidden=true;
  const range=e.target.closest('[data-qf-range]');if(range){
   const next=range.dataset.qfRange==='ALL'?'ALL':Number(range.dataset.qfRange);
   state.range=next;document.querySelectorAll('[data-qf-range]').forEach(b=>b.classList.toggle('active',b===range));
   if(mode()==='private'&&(next===730||next==='ALL')&&state.priceSource?.type==='market'&&state.price.length<340)loadPrice();else renderPriceData();return;
  }
  const financial=e.target.closest('[data-qf-financial]');if(financial){state.finance=financial.dataset.qfFinancial;renderFinances(Q.financialSummary(company(),data.as_of));return;}
  const rm=e.target.closest('[data-qf-remove]');if(rm){state.compare=state.compare.filter(s=>s!==rm.dataset.qfRemove);renderCompareChips();return;}
  const model=e.target.closest('[data-qf-model]');if(model){showModel(model.dataset.qfModel);return;}
 });
 $('qf-v20-analyze').addEventListener('click',analyze);
 $('qf-v20-add-compare').addEventListener('click',()=>{addCompare();window.QFNavigate20('compare');});
 $('qf-v20-export-price').addEventListener('click',exportPrice);
 $('qf-v20-benchmark').addEventListener('change',e=>{state.benchmarkOn=e.target.checked;if(state.benchmarkOn)loadBenchmark();else{state.benchmark=null;state.benchToken++;renderPriceData();}});
 $('qf-v20-export-sec').addEventListener('click',exportSEC);
 $('qf-v20-compare-options').innerHTML=companies.map(c=>'<option value="'+esc(c.name+' ('+c.symbol+')')+'"></option>').join('');
 $('qf-v20-compare-search').addEventListener('change',e=>{
  const query=e.target.value.trim().toLowerCase(),c=companies.find(c=>c.symbol.toLowerCase()===query||(c.name+' ('+c.symbol+')').toLowerCase()===query);
  if(c&&!state.compare.includes(c.symbol)&&state.compare.length<5)state.compare.push(c.symbol);
  renderCompareChips();e.target.value='';
 });
 $('qf-v20-compare-run').addEventListener('click',runCompare);
 mountModels();
 const auth=$('private-signed');if(auth)new MutationObserver(authUpdate).observe(auth,{attributes:true,attributeFilter:['hidden']});
 window.addEventListener('qf:route-change',e=>{if(e.detail.route==='compare'){if(!state.compare.includes(state.symbol))addCompare();}if(e.detail.route==='explore')setAccount();});
 selectCompany(state.symbol);authUpdate();
}
init();
window.QFResearch20=Object.freeze({choose:selectCompany,analyze});
})();
