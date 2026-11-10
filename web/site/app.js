/* Public demo: prebuilt real SEC filing facts plus browser-only simulated model examples. */
(function(){
'use strict';
const M=window.QFModel,$=id=>document.getElementById(id),SEC=window.QFSecAnalytics;
const SEC_DATA=/* QF_SEC_DATA */ null;
window.QFPublishedSEC=SEC_DATA;
const fmt=n=>Number(n).toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2});
const pct=n=>(100*n).toFixed(1)+'%';
let state={cash:3500,holdings:{MSFT:5,VOO:8,AAPL:3,'BTC/USD':0.006}};
const table=(heads,rows)=>'<div class="table-wrap"><table><thead><tr>'+heads.map(h=>'<th>'+h+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
const error=(id,msg)=>{$(id).textContent=msg||'';};
const num=id=>Number($(id).value);
const PUBLIC_PAGES=new Set(['explore','compare','models','portfolio','methods','overview','sec','quant','valuation','ml','systems','lab']);
const LEGACY_ROUTES={overview:'explore',sec:'explore',lab:'models',quant:'models',valuation:'models',ml:'compare',systems:'methods'};
function nav(name,updateHash=true){
 name=LEGACY_ROUTES[name]||name;
 if(name!=='private' && !PUBLIC_PAGES.has(name))return;
 document.querySelectorAll('.tabpage').forEach(e=>e.classList.toggle('active',e.id==='page-'+name));
 document.querySelectorAll('.nav-btn').forEach(e=>{const active=e.dataset.page===name;e.classList.toggle('active',active);if(active)e.setAttribute('aria-current','page');else e.removeAttribute('aria-current');});
 // Public navigation is always visible; private navigation expands its own task groups.
 const labels={explore:'EXPLORE',compare:'COMPARE',models:'MODELS',overview:'RESEARCH OVERVIEW',sec:'HISTORICAL SEC DATA',portfolio:'SIMULATED PORTFOLIO',quant:'SIMULATED RISK MODEL',valuation:'DCF ASSUMPTIONS',ml:'REPORTED SEC COMPANY COMPARISON',methods:'DATA & ENGINEERING',systems:'RESEARCH METHODS',lab:'INTERACTIVE ANALYSIS',private:'PRIVATE WORKSPACE'};
 const badge=document.querySelector('.topbar .badge');if(badge)badge.textContent=labels[name];
 const eyebrow=document.querySelector('.topbar .eyebrow');if(eyebrow)eyebrow.textContent=name==='private'?'Your portfolio · Personal use':'Financial research · models and data';
 if(updateHash){const route=name==='private'?'#private/decision':'#'+name;if(location.hash!==route)history.pushState(null,'',route);}
 window.scrollTo({top:0,behavior:'instant'});
 window.dispatchEvent(new CustomEvent('qf:route-change',{detail:{route:name}}));
}

window.QFNavigate20=nav;
function portfolio(){
 const holds=M.exposure(state.holdings),total=holds.total+state.cash;
 $('home-value').textContent=$('portfolio-total').textContent=fmt(total);
 $('home-cash').textContent=$('portfolio-cash').textContent=fmt(state.cash);
 $('home-invested').textContent=$('portfolio-invested').textContent=fmt(holds.total);
 $('home-allocation').innerHTML=holds.holdings.map(({s,value})=>'<div class="row" style="margin:10px 0 3px"><span>'+M.bySymbol[s].name+' <span class="muted">('+s+')</span></span><strong>'+pct(total?value/total:0)+'</strong></div><div class="progress"><span style="width:'+(total?value/total*100:0)+'%"></span></div>').join('');
 $('portfolio-table').innerHTML=table(['Investment','Units','Illustrative price','Value','Weight'],[
 ...holds.holdings.map(({s,value})=>[M.bySymbol[s].name+' <span class="tiny">('+s+')</span>',state.holdings[s].toFixed(6),fmt(M.bySymbol[s].price),fmt(value),pct(total?value/total:0)]),
 ['Cash','—','—',fmt(state.cash),pct(total?state.cash/total:1)]]);
 const exp=holds.lookthrough.filter(x=>x.symbol!=='OTHER'&&x.symbol!=='BONDS');
 $('lookthrough-table').innerHTML=table(['Underlying company / category','Value','Of invested'],exp.map(x=>[x.symbol,fmt(x.value),pct(x.pct)]))+'<p class="tiny" style="margin-top:12px">These example ETF weights are hypothetical; unspecified holdings are grouped as OTHER.</p>';
}
function transact(){
 const s=$('trade-symbol').value,action=$('trade-action').value,amount=num('trade-amount'),fee=amount*0.0005;
 if(!(amount>0&&Number.isFinite(amount))){$('trade-message').textContent='Enter a positive amount.';return;}
 const units=amount/M.bySymbol[s].price;
 if(action==='buy'){
  if(amount+fee>state.cash+1e-7){$('trade-message').textContent='Not enough sample cash, including the fee.';return;}
  state.cash-=amount+fee;state.holdings[s]=(state.holdings[s]||0)+units;
 }else{
  if((state.holdings[s]||0)+1e-8<units){$('trade-message').textContent='Not enough units to sell.';return;}
  state.holdings[s]-=units;if(state.holdings[s]<1e-8)delete state.holdings[s];state.cash+=amount-fee;
 }
 $('trade-message').innerHTML='<span class="good">Recorded in this browser session.</span> Fee: '+fmt(fee)+'.';portfolio();
}
function rebalance(){
 const targets={MSFT:num('target-msft'),VOO:num('target-voo'),AAPL:num('target-aapl'),'BTC/USD':num('target-btc'),cash:num('target-cash')};
 const sum=Object.values(targets).reduce((a,b)=>a+b,0),el=$('rebalance-result');
 if(Object.values(targets).some(x=>!Number.isFinite(x)||x<0)||Math.abs(sum-100)>0.01){el.innerHTML='<p class="error">Target percentages must be nonnegative and total 100%.</p>';return;}
 const exp=M.exposure(state.holdings),total=exp.total+state.cash;
 const rows=Object.keys(targets).filter(x=>x!=='cash').map(s=>{
  const actual=(state.holdings[s]||0)*M.bySymbol[s].price,delta=total*targets[s]/100-actual;
  return [M.bySymbol[s].name,fmt(actual),fmt(total*targets[s]/100),delta>0.005?'Buy':delta < -0.005?'Sell':'Hold',fmt(Math.abs(delta)),fmt(Math.abs(delta)*0.0005)];
 });
 el.innerHTML=table(['Investment','Current','Target','Action','Gross','Est. fee'],rows)+'<div class="tiny" style="margin-top:10px">This is a suggested trade list. Cash sufficiency, lot sizes and market slippage require separate checks. No trade is placed.</div>';
}
function runQuant(){
 error('quant-error','');
 const s=[...document.querySelectorAll('input[name="quant-asset"]:checked')].map(x=>x.value);
 const budget=num('quant-budget'),cap=num('quant-max')/100,crypto=num('quant-crypto')/100;
 if(s.length<2||s.length>7){error('quant-error','Choose 2–7 investments.');return;}
 if(!Number.isFinite(budget)||budget<100||!Number.isFinite(cap)||cap<=0||cap>1||!Number.isFinite(crypto)||crypto<0||crypto>1){error('quant-error','Check the allocation inputs.');return;}
 try{
  const o=M.optimize(s,cap,crypto),a=M.monteCarlo(o.base,o.cov,budget,4221),b=M.monteCarlo(o.weights,o.cov,budget,4221);
  const rows=[['Annualized model volatility',pct(o.baselineVol),pct(o.optimalVol)],['Modeled 21-day VaR 95%',fmt(a.var95),fmt(b.var95)],['Modeled expected shortfall',fmt(a.es95),fmt(b.es95)],['5th-percentile value',fmt(a.low),fmt(b.low)],['Median value',fmt(a.median),fmt(b.median)],['95th-percentile value',fmt(a.high),fmt(b.high)],...s.map((sym,i)=>[M.bySymbol[sym].name,pct(o.base[i]),pct(o.weights[i])])];
  const cor=o.cov.map((row,i)=>[s[i],...row.map((x,j)=>((x / Math.sqrt(o.cov[i][i]*o.cov[j][j]))||0).toFixed(2))]);
  $('quant-result').innerHTML='<div class="pane"><div class="section-title"><h3>Allocation comparison</h3><span class="mini">Simulated data</span></div>'+table(['Metric','Baseline','Constrained'],rows)+'<details class="subtle"><summary>Correlation matrix</summary>'+table(['',...s],cor)+'</details><p class="tiny" style="margin-top:14px">Optimization minimizes estimated variance with weight limits and a small turnover penalty. 276 synthetic daily return observations, 21-session simulations, zero forecast drift. These are not calibrated market risk forecasts.</p></div>';
 }catch(e){error('quant-error',e.message);$('quant-result').innerHTML='';}
}
function runDCF(){
 error('dcf-error','');let s=$('dcf-company').value,opts={growth:num('dcf-growth')/100,wacc:num('dcf-wacc')/100,terminal:num('dcf-term')/100};
 if($('dcf-margin').value.trim())opts.margin=num('dcf-margin')/100;
 try{
  const r=M.dcf(s,opts);
  let sens=[];for(const dw of [-0.01,0,0.01])for(const dg of [-0.005,0,0.005]){const w=opts.wacc+dw,g=opts.terminal+dg;let v='—';if(w>g){v=fmt(M.dcf(s,{...opts,wacc:w,terminal:g}).value);}sens.push([(w*100).toFixed(1)+'%',(g*100).toFixed(2)+'%',v]);}
  $('dcf-result').innerHTML='<div class="pane">'+(r.enterprise<0||r.value<0?'<div class="notice qf-dcf-warning" role="status"><strong>Adverse valuation scenario.</strong> Under these assumptions, discounted future cash flows imply a negative enterprise or per-share model value. This is not a possible quoted stock-price target or a prediction of a negative share price. Review cash generation, discount rate and terminal growth, then compare the sensitivity table; no result is silently clamped.</div>':'<p class="tiny" style="margin-bottom:14px">All amounts below are hypothetical outputs under selected assumptions, not market-price estimates.</p>')+'<div class="three"><div class="metric"><span class="muted">Illustrative value per share</span><strong>'+fmt(r.value)+'</strong></div><div class="metric"><span class="muted">Terminal share of EV</span><strong>'+pct(r.terminalFraction)+'</strong></div><div class="metric"><span class="muted">Enterprise value</span><strong>'+fmt(r.enterprise)+'B</strong></div></div><h3 class="section-title">WACC / terminal-growth sensitivity</h3>'+table(['WACC','Terminal growth','Per share'],sens)+'<details class="subtle"><summary>Five-year forecast</summary>'+table(['Year','Revenue ($B)','FCF ($B)'],r.forecast.map(x=>[x.year,fmt(x.revenue),fmt(x.fcf)]))+'</details><p class="tiny" style="margin-top:13px">Illustrative revenue, reinvestment ratios, net debt and shares. 5-year unlevered FCF discounted by WACC; perpetuity terminal value. This is not a real-company valuation.</p></div>';
 }catch(e){error('dcf-error',e.message);$('dcf-result').innerHTML='';}
}
function runPeers(){
 const symbol=$('ml-company').value,sectorOnly=$('ml-sector-only').checked;
 const model=window.QFPublicSECPeers?.compare(SEC_DATA,symbol,{sectorOnly});
 if(!model?.ready){$('ml-result').innerHTML='<div class="pane notice" role="status"><strong>Financial peer comparison unavailable</strong><p>'+safeText(model?.reason||'SEC comparison is unavailable.')+'</p><button type="button" class="btn sm" data-sec-symbol="'+safeText(symbol)+'">View available company financials</button></div>';return;}
 const peers=model.peers.slice(0,10);
 const max=Math.max(1,...peers.map(x=>x.distance));
 const bars=peers.map((c,i)=>'<div class="qf-peer-visual-row"><div><strong>'+safeText(c.name)+'</strong><span class="tiny"> '+safeText(c.symbol)+'</span></div><div class="qf-peer-visual-track" role="img" aria-label="Financial distance '+c.distance.toFixed(2)+'"><span style="width:'+Math.max(3,100*(1-c.distance/(max+0.01))).toFixed(1)+'%"></span></div><strong>'+c.distance.toFixed(2)+'</strong></div>').join('');
 const data=peers.map((c,i)=>[String(i+1),safeText(c.name)+' ('+safeText(c.symbol)+')',safeText(c.sector),safeText(c.fiscalEnd),c.distance.toFixed(2),'<button type="button" class="btn sm" data-sec-symbol="'+safeText(c.symbol)+'">Financials</button>']);
 const f=model.features.map((feature,j)=>[safeText(feature.label),model.selected.values[model.indices[j]].toFixed(1)+'%',safeText(feature.description)]);
 $('ml-result').innerHTML='<div class="pane"><div class="section-title"><h3>Companies with similar reported financial profiles</h3><span class="mini">SEC filing data · '+model.featureCount+' common ratios</span></div>'+
  '<p><strong>'+safeText(model.selected.name)+'</strong> ('+safeText(symbol)+') · FY '+safeText(model.selected.fiscalEnd)+'</p>'+
  '<p class="tiny">'+model.compared+' companies with the same usable features out of '+model.universe+' published companies. SEC cutoff '+safeText(model.cutoff)+'. '+safeText(model.caution)+'</p>'+
  '<div class="qf-peer-visual" aria-label="Closest peer distances"><h4>Closest financial profiles</h4><p class="tiny">Longer bars indicate a closer statistical match; numbers are distances, not quality ratings.</p>'+bars+'</div>'+
  '<details class="subtle"><summary>See peer figures and reporting dates</summary>'+table(['#','Company','Broad group','Fiscal year','Distance','Open'],data)+'</details>'+
  '<div class="subtle"><h3>Financial ratios used in this comparison</h3>'+table(['Ratio','Reported-derived value','Meaning'],f)+'</div>'+
  '<p class="tiny">'+safeText(model.message)+' <a href="'+safeText(model.selected.companyfacts)+'" rel="noopener noreferrer" target="_blank">SEC Company Facts source</a>.</p></div>';
}

// SEC comparison uses a static, pre-reviewed companyfacts snapshot. No browser API calls.
const billions=v=>(typeof v==='number'&&Number.isFinite(v))?'$'+(v/1e9).toFixed(2)+'B':'Not reported';
const ratio=(a,b)=>(typeof a==='number'&&typeof b==='number'&&b>0)?(a/b*100).toFixed(1)+'%':'Not available';
const safeText=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const secMetricLabel=(value,key)=>value===null?'Not reported':(SEC.METRICS[key].unit==='usd'?billions(value):value.toFixed(1)+'%');
function renderSECTrend(company){
 const container=$('sec-trend'),series=SEC.revenueSeries(company);
 if(series.length<2){container.textContent='Insufficient comparable annual revenue observations for a trend.';return;}
 const max=Math.max(...series.map(item=>item.revenue_usd));
 if(max<=0){container.textContent='Revenue trend unavailable.';return;}
 const xSlots=series.map((item,i)=>100+i*185),bottom=187,height=151;
 const bars=series.map((item,i)=>{
  const h=item.revenue_usd/max*height,x=xSlots[i],y=bottom-h;
  return `<rect x="${x}" y="${y.toFixed(2)}" width="91" height="${h.toFixed(2)}" rx="5" fill="#1d665a"/>`+
   `<text x="${x+45.5}" y="${Math.max(17,y-10).toFixed(2)}" text-anchor="middle" fill="#183c33" font-size="13" font-weight="700">${safeText(billions(item.revenue_usd))}</text>`+
   `<text x="${x+45.5}" y="216" text-anchor="middle" fill="#536f66" font-size="12">FY ${safeText(item.fiscal_end.slice(0,4))}</text>`;
 });
 container.innerHTML=`<svg viewBox="0 0 650 237" role="img" aria-label="${safeText(company.name)} SEC-reported annual revenue, oldest to newest fiscal period"><title>${safeText(company.name)} annual SEC revenue</title><desc>Up to three fiscal reporting periods. Exact values are repeated in the accessible table below.</desc><line x1="56" y1="187" x2="614" y2="187" stroke="#c8dcd3" stroke-width="2"/>${bars.join('')}</svg>`+
  '<p class="trend-caption">Revenue in USD billions · chronological issuer fiscal years. Values are historical filing data, not share-price performance.</p>';
}
function renderSECRanking(){
 const key=$('sec-rank-metric').value, rows=SEC.ranking(SEC_DATA,key).slice(0,30);
 const peerPanel=$('qf-sec-peer-chart-v81');if(peerPanel&&window.QFPublicVisualsV81)peerPanel.innerHTML=window.QFPublicVisualsV81.rankingHtml(rows,SEC.METRICS[key].label,SEC.METRICS[key].unit);
 let rank=0;
 $('sec-compare').innerHTML=table(['Rank','Company','Sector*','FY ended',SEC.METRICS[key].label],rows.map(row=>{
  const hasValue=row.value!==null;if(hasValue)rank++;
  return [hasValue?'<span class="sec-rank-highlight">'+rank+'</span>':'—',safeText(row.name)+' <span class="tiny">('+safeText(row.symbol)+')</span>',safeText(row.sector),safeText(row.fiscal_end),secMetricLabel(row.value,key)];
 }));
}
function renderSECProvenance(company){
 const latest=company.annual[0],fields=[['Revenue','revenue_usd'],['Operating income','operating_income_usd'],['Net income','net_income_usd'],['Operating cash flow','operating_cash_flow_usd'],['Cash PP&E purchases','capex_usd']];
 $('sec-provenance').innerHTML=table(['Metric','US-GAAP tag','Filed','Accession'],fields.map(([label,key])=>{
  const source=latest.sources?.[key];
  return [label,source?safeText(source.tag):'Not reported',source?safeText(source.filed):'—',source?safeText(source.accession):'—'];
 }))+'<p class="tiny" style="margin-top:9px">Fiscal year ending '+safeText(latest.fiscal_end)+'. Free cash flow is a derived proxy, not a separately reported SEC line item. Source facts and filing details are preserved in the downloadable CSV.</p>';
}
function downloadSECCsv(){
 if(!SEC_DATA||!Array.isArray(SEC_DATA.companies))return;
 const content=SEC.snapshotCsv(SEC_DATA);
 const file=new Blob(['\ufeff'+content],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(file),link=document.createElement('a');
 link.href=url;link.download='quantforge-sec-annual-'+SEC_DATA.as_of+'.csv';
 document.body.appendChild(link);link.click();link.remove();
 URL.revokeObjectURL(url);
}

function renderV81SecCharts(company){
 const graph=$('qf-sec-chart-v81'),projection=$('qf-sec-project-output-v81');
 if(!graph||!window.QFPublicVisualsV81)return;
 graph.innerHTML=window.QFPublicVisualsV81.historicalHtml(company,$('qf-sec-metric-v81').value);
 // A newly chosen issuer invalidates the previously calculated hypothetical future path.
 if(projection)projection.textContent='Assumptions have not yet been applied to this company. Select a growth rate and calculate.';
}
function refreshV81Chart(){
 const company=SEC_DATA?.companies?.find(c=>c.symbol===$('sec-company').value);
 if(company&&window.QFPublicVisualsV81)$('qf-sec-chart-v81').innerHTML=window.QFPublicVisualsV81.historicalHtml(company,$('qf-sec-metric-v81').value);
}
function projectV81(){
 const company=SEC_DATA?.companies?.find(c=>c.symbol===$('sec-company').value);
 if(!company||!window.QFPublicVisualsV81)return;
 const growth=$('qf-sec-growth-v81').value.trim()===''?NaN:Number($('qf-sec-growth-v81').value);
 const years=Number($('qf-sec-horizon-v81').value);
 $('qf-sec-project-output-v81').innerHTML=window.QFPublicVisualsV81.projectionHtml(company,growth,years);
}

function renderSEC(){
 const out=$('sec-figures'),years=$('sec-years'),peers=$('sec-compare'),scenario=$('sec-scenario');
 if(!SEC_DATA || !Array.isArray(SEC_DATA.companies) || SEC_DATA.companies.length===0){
  $('sec-status').textContent='No SEC snapshot published';
  out.innerHTML='<div class="notice">Real financials have not been published yet. The maintainer must generate and validate the SEC snapshot. No invented issuer data will be substituted.</div>';
  years.textContent='';peers.textContent='';scenario.textContent='';$('sec-trend').textContent='';$('sec-provenance').textContent='';return;
 }
 const company=SEC_DATA.companies.find(c=>c.symbol===$('sec-company').value);
 if(!company || !company.annual.length)return;
 const latest=company.annual[0],m=latest.metrics,prior=company.annual[1]?.metrics;
 const yoy=prior ? ratio(m.revenue_usd-prior.revenue_usd,prior.revenue_usd) : 'Not available';
 const margin=ratio(m.operating_income_usd,m.revenue_usd);
 $('sec-status').textContent='SEC filing data cutoff: '+(company.as_of||SEC_DATA.as_of);
 out.innerHTML='<div class="metric"><span class="muted">Revenue · fiscal year ending '+latest.fiscal_end+'</span><strong>'+billions(m.revenue_usd)+'</strong></div>'+
 '<div class="metric"><span class="muted">Operating margin</span><strong>'+margin+'</strong></div>'+
 '<div class="metric"><span class="muted">Revenue YoY change</span><strong>'+yoy+'</strong></div>';
 const rows=company.annual.map(r=>{const f=r.metrics;return [r.fiscal_end,billions(f.revenue_usd),billions(f.operating_income_usd),ratio(f.operating_income_usd,f.revenue_usd),billions(f.free_cash_flow_usd)];});
 years.innerHTML=table(['FY ended','Revenue','Operating income','Operating margin','FCF proxy'],rows);
 renderSECTrend(company);renderSECRanking();renderSECProvenance(company);renderV81SecCharts(company);
 $('sec-source').innerHTML='Source: <a href="'+company.source_url+'" rel="noopener noreferrer" target="_blank">SEC Company Facts, '+company.symbol+'</a>. Each metric is selected from an eligible 10-K filed by '+(company.as_of||SEC_DATA.as_of)+'. FCF proxy = reported operating cash flow minus cash purchases of property and equipment (not FCFF). Missing values remain blank. *Sector groups are editorial and fiscal periods differ; compare across sectors cautiously. Sources and accession IDs are in the snapshot file.';
 const shock=Number($('sec-margin-shock').value);
 if(typeof m.operating_income_usd!=='number'||typeof m.revenue_usd!=='number'){
  scenario.textContent='Margin stress is unavailable because this issuer lacks a comparable reported operating-income or revenue figure for the selected fiscal year.';return;
 }
 if(!Number.isFinite(shock)||shock < -15||shock > 15){
  scenario.textContent='Enter a valid margin shock between -15 and +15 percentage points.';return;
 }
 const hypothetical=m.revenue_usd*(m.operating_income_usd/m.revenue_usd+shock/100);
 scenario.innerHTML='<div class="notice"><strong>Hypothetical margin stress:</strong> '+(shock>=0?'+':'')+shock.toFixed(1)+' pp applied to FY revenue implies '+billions(hypothetical)+' operating income, a '+billions(hypothetical-m.operating_income_usd)+' change from the reported amount. This is a sensitivity, not a forecast.</div>';
}

function renderSECHighlights(){
 const out=$('home-sec-highlights'),status=$('home-sec-updated');
 if(!out || !status)return;
 if(!SEC_DATA || !Array.isArray(SEC_DATA.companies) || !SEC_DATA.companies.length){
  out.textContent='SEC filing snapshot unavailable in this build. Sample simulations remain accessible.';
  status.textContent='No reported financial figures have been substituted.';
  return;
 }
 const highlights=['MSFT','AAPL','NVDA'].map(symbol=>SEC_DATA.companies.find(c=>c.symbol===symbol)).filter(Boolean);
 out.innerHTML=highlights.map(c=>{
  const annual=c.annual[0];
  return '<div class="metric"><span class="muted">'+c.name+' ('+c.symbol+') · FY '+annual.fiscal_end+'</span><strong>'+billions(annual.metrics.revenue_usd)+'</strong><span class="tiny">Reported annual revenue · SEC filing</span></div>';
 }).join('');
 status.textContent='Filed by '+SEC_DATA.as_of+' · historical annual data, not live prices';
}

function filterSECCompaniesV79(){
 if(!SEC_DATA||!Array.isArray(SEC_DATA.companies))return;
 const q=$('sec-company-search-v79').value.trim().toLowerCase();
 const visible=SEC_DATA.companies.filter(c=>!q||c.name.toLowerCase().includes(q)||c.symbol.toLowerCase().includes(q));
 const select=$('sec-company'),previous=select.value;
 const option=c=>'<option value="'+safeText(c.symbol)+'">'+safeText(c.name)+' ('+safeText(c.symbol)+')</option>';
 if(!q) $('sec-company').innerHTML=SEC_DATA.companies.map(c=>'<option value="'+safeText(c.symbol)+'">'+safeText(c.name)+' ('+safeText(c.symbol)+')</option>').join('');
 else select.innerHTML=visible.map(option).join('');
 if(visible.some(c=>c.symbol===previous))select.value=previous;
 $('sec-company-count-v79').textContent=visible.length+' of '+SEC_DATA.companies.length+' published SEC companies';
 if(visible.length)renderSEC();
 else{
  $('sec-figures').textContent='No published company matches this search.';
  for(const id of ['sec-years','sec-trend','sec-compare','sec-provenance','sec-scenario','sec-source'])$(id).textContent='';
 }
}
function populate(){
 if(SEC_DATA && Array.isArray(SEC_DATA.companies)){
  filterSECCompaniesV79();
 }
 const options=M.ASSETS.map(a=>'<option value="'+a.symbol+'">'+a.name+' ('+a.symbol+')</option>').join('');
 $('trade-symbol').innerHTML=options;
 $('assets-list').innerHTML=M.ASSETS.map(a=>'<button class="asset" data-symbol="'+a.symbol+'"><strong>'+a.name+'</strong><span>'+a.symbol+' · '+a.kind+' · '+fmt(a.price)+'</span></button>').join('');
 $('quant-assets').innerHTML=['MSFT','VOO','AAPL','QQQ','BND','BTC/USD','ETH/USD'].map(s=>'<label class="inline-checkbox"><input type="checkbox" name="quant-asset" value="'+s+'" '+(['MSFT','VOO','BND'].includes(s)?'checked':'')+'>'+M.bySymbol[s].name+'</label>').join('');
 $('ml-company').innerHTML=(SEC_DATA?.companies||[]).map(c=>{const ready=window.QFPublicSECPeers?.compare(SEC_DATA,c.symbol)?.ready;return '<option value="'+safeText(c.symbol)+'"'+(ready?'':' disabled')+'>'+safeText(c.name)+' ('+safeText(c.symbol)+')'+(ready?'':' — Financials only')+'</option>';}).join('');
 portfolio();runQuant();runDCF();runPeers();renderSEC();renderSECHighlights();
 if(window.QFPublicEvidence)window.QFPublicEvidence.render(SEC_DATA, document.getElementById("systems-sec-quant-v76"));
 if(window.QFResearchLab)window.QFResearchLab.mount(SEC_DATA);
}
document.addEventListener('click',e=>{
 const btn=e.target.closest('[data-page], [data-go], [data-symbol], [data-sec-symbol]');if(!btn)return;
 if(btn.dataset.page)nav(btn.dataset.page);
 else if(btn.dataset.go)nav(btn.dataset.go);
 else if(btn.dataset.secSymbol){
  const symbol=btn.dataset.secSymbol;
  if(SEC_DATA && SEC_DATA.companies.some(c=>c.symbol===symbol)){$('sec-company').value=symbol;renderSEC();nav('sec');}
 }
 else if(btn.dataset.symbol){$('trade-symbol').value=btn.dataset.symbol;nav('portfolio');}
});
$('trade-submit').addEventListener('click',transact);
$('rebalance-submit').addEventListener('click',rebalance);
$('quant-run').addEventListener('click',runQuant);
$('dcf-run').addEventListener('click',runDCF);
$('ml-run').addEventListener('click',runPeers);
$('ml-company').addEventListener('change',runPeers);
$('ml-sector-only').addEventListener('change',runPeers);
$('sec-company-search-v79').addEventListener('input',filterSECCompaniesV79);
$('sec-company').addEventListener('change',renderSEC);
$('qf-sec-metric-v81').addEventListener('change',refreshV81Chart);
$('qf-sec-project-v81').addEventListener('click',projectV81);
$('sec-margin-shock').addEventListener('input',renderSEC);
$('sec-rank-metric').addEventListener('change',renderSECRanking);
$('sec-export').addEventListener('click',downloadSECCsv);
function restorePublicRoute(){const target=location.hash.slice(1);if(!target)nav('explore',false);else if(PUBLIC_PAGES.has(target))nav(target,false);else if(target.startsWith('private/')){nav('private',false);window.dispatchEvent(new Event('qf:private-route'));}}
window.addEventListener('popstate',restorePublicRoute);
window.addEventListener('hashchange',restorePublicRoute);
populate();
const initial=window.location.hash.slice(1);if(PUBLIC_PAGES.has(initial))nav(initial,false);else if(initial.startsWith('private/'))nav('private',false);else nav('explore',false);
const qfCountV81=$('qf-company-count-v81');if(qfCountV81)qfCountV81.textContent=SEC_DATA?.companies?.length?SEC_DATA.companies.length+' companies':'Company financials unavailable';
const methodsAsOf=$('methods-asof');if(methodsAsOf && SEC_DATA && SEC_DATA.as_of)methodsAsOf.textContent='SEC filing cutoff · '+SEC_DATA.as_of;

})();
