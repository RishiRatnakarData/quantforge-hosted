/* Public demo: prebuilt real SEC filing facts plus browser-only simulated model examples. */
(function(){
'use strict';
const M=window.QFModel,$=id=>document.getElementById(id);
const SEC_DATA=/* QF_SEC_DATA */ null;
const fmt=n=>Number(n).toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2});
const pct=n=>(100*n).toFixed(1)+'%';
let state={cash:3500,holdings:{MSFT:5,VOO:8,AAPL:3,'BTC/USD':0.006}};
const table=(heads,rows)=>'<div class="table-wrap"><table><thead><tr>'+heads.map(h=>'<th>'+h+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
const error=(id,msg)=>{$(id).textContent=msg||'';};
const num=id=>Number($(id).value);
function nav(name){
 document.querySelectorAll('.tabpage').forEach(e=>e.classList.toggle('active',e.id==='page-'+name));
 document.querySelectorAll('.nav-btn').forEach(e=>e.classList.toggle('active',e.dataset.page===name));
 const badge=document.querySelector('.topbar .badge');
 if(badge){const labels={overview:'REAL SEC DATA + SIMULATIONS',sec:'REPORTED SEC FINANCIALS',portfolio:'SIMULATED PORTFOLIO',quant:'SIMULATED RETURNS',valuation:'ILLUSTRATIVE DCF',ml:'SIMULATED PEER INPUTS',private:'PRIVATE WORKSPACE'};badge.textContent=labels[name]||'PUBLIC DEMO';}
 window.scrollTo({top:0,behavior:'instant'});
}
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
 $('lookthrough-table').innerHTML=table(['Underlying company / category','Value','Of invested'],exp.map(x=>[x.symbol,fmt(x.value),pct(x.pct)]))+'<p class="tiny" style="margin-top:12px">Weights are invented for demonstration; unlabeled holdings are grouped as OTHER.</p>';
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
  $('dcf-result').innerHTML='<div class="pane"><div class="three"><div class="metric"><span class="muted">Illustrative value per share</span><strong>'+fmt(r.value)+'</strong></div><div class="metric"><span class="muted">Terminal share of EV</span><strong>'+pct(r.terminalFraction)+'</strong></div><div class="metric"><span class="muted">Enterprise value</span><strong>'+fmt(r.enterprise)+'B</strong></div></div><h3 class="section-title">WACC / terminal-growth sensitivity</h3>'+table(['WACC','Terminal growth','Per share'],sens)+'<details class="subtle"><summary>Five-year forecast</summary>'+table(['Year','Revenue ($B)','FCF ($B)'],r.forecast.map(x=>[x.year,fmt(x.revenue),fmt(x.fcf)]))+'</details><p class="tiny" style="margin-top:13px">Illustrative revenue, reinvestment ratios, net debt and shares. 5-year unlevered FCF discounted by WACC; perpetuity terminal value. This is not a real-company valuation.</p></div>';
 }catch(e){error('dcf-error',e.message);$('dcf-result').innerHTML='';}
}
function runPeers(){let s=$('ml-company').value;const p=M.peers(s),facts=M.COMPANY_FACTS[s];
 $('ml-result').innerHTML='<div class="pane"><div class="section-title"><h3>Nearest companies to '+M.COMPANY_NAMES[s]+'</h3><span class="mini">Simulated inputs</span></div>'+table(['Company','Ticker','Standardized distance'],p.ranking.slice(0,5).map(x=>[x.name,x.symbol,x.distance.toFixed(2)]))+'<p style="margin-top:18px">Sample-relative atypicality rank: <strong>'+p.unusualRank+' of '+p.total+'</strong> (1 = most distant from the feature mean).</p><div class="subtle"><h3>Features used</h3>'+table(['Metric','Illustrative value'],['Revenue growth','Operating margin','Net margin','Free cash flow / revenue','Debt / assets'].map((name,i)=>[name,pct(facts.features[i])]))+'</div><p class="tiny" style="margin-top:12px">Z-score feature standardization and Euclidean nearest-neighbors. Atypicality is standardized distance to the sample center, not an Isolation Forest or investment signal.</p></div>';
}

// SEC comparison uses a static, pre-reviewed companyfacts snapshot. No browser API calls.
const billions=v=>(typeof v==='number'&&Number.isFinite(v))?'$'+(v/1e9).toFixed(2)+'B':'Not reported';
const ratio=(a,b)=>(typeof a==='number'&&typeof b==='number'&&b>0)?(a/b*100).toFixed(1)+'%':'Not available';
function renderSEC(){
 const out=$('sec-figures'),years=$('sec-years'),peers=$('sec-compare'),scenario=$('sec-scenario');
 if(!SEC_DATA || !Array.isArray(SEC_DATA.companies) || SEC_DATA.companies.length===0){
  $('sec-status').textContent='No SEC snapshot published';
  out.innerHTML='<div class="notice">Real financials have not been published yet. The maintainer must generate and validate the SEC snapshot. No invented issuer data will be substituted.</div>';
  years.textContent='';peers.textContent='';scenario.textContent='';return;
 }
 const company=SEC_DATA.companies.find(c=>c.symbol===$('sec-company').value);
 if(!company || !company.annual.length)return;
 const latest=company.annual[0],m=latest.metrics,prior=company.annual[1]?.metrics;
 const yoy=prior ? ratio(m.revenue_usd-prior.revenue_usd,prior.revenue_usd) : 'Not available';
 const margin=ratio(m.operating_income_usd,m.revenue_usd);
 $('sec-status').textContent='SEC filing data as of '+SEC_DATA.as_of;
 out.innerHTML='<div class="metric"><span class="muted">Revenue · fiscal year ending '+latest.fiscal_end+'</span><strong>'+billions(m.revenue_usd)+'</strong></div>'+
 '<div class="metric"><span class="muted">Operating margin</span><strong>'+margin+'</strong></div>'+
 '<div class="metric"><span class="muted">Revenue YoY change</span><strong>'+yoy+'</strong></div>';
 const rows=company.annual.map(r=>{const f=r.metrics;return [r.fiscal_end,billions(f.revenue_usd),billions(f.operating_income_usd),ratio(f.operating_income_usd,f.revenue_usd),billions(f.free_cash_flow_usd)];});
 years.innerHTML=table(['FY ended','Revenue','Operating income','Operating margin','FCF proxy'],rows);
 peers.innerHTML=table(['Company','Sector*','FY ended','Revenue','Operating margin'],SEC_DATA.companies.map(c=>{const f=c.annual[0];return [c.name,c.sector||'Not classified',f.fiscal_end,billions(f.metrics.revenue_usd),ratio(f.metrics.operating_income_usd,f.metrics.revenue_usd)];}));
 $('sec-source').innerHTML='Source: <a href="'+company.source_url+'" rel="noopener noreferrer" target="_blank">SEC Company Facts, '+company.symbol+'</a>. Each metric is selected from an eligible 10-K filed by '+SEC_DATA.as_of+'. FCF proxy = reported operating cash flow minus cash purchases of property and equipment (not FCFF). Missing values remain blank. *Sector groups are editorial and fiscal periods differ; compare across sectors cautiously. Sources and accession IDs are in the snapshot file.';
 const shock=Number($('sec-margin-shock').value);
 if(!Number.isFinite(shock)||shock < -15||shock > 15||typeof m.operating_income_usd!=='number'||typeof m.revenue_usd!=='number'){
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

function populate(){
 if(SEC_DATA && Array.isArray(SEC_DATA.companies)){
  $('sec-company').innerHTML=SEC_DATA.companies.map(c=>'<option value="'+c.symbol+'">'+c.name+' ('+c.symbol+')</option>').join('');
 }
 const options=M.ASSETS.map(a=>'<option value="'+a.symbol+'">'+a.name+' ('+a.symbol+')</option>').join('');
 $('trade-symbol').innerHTML=options;
 $('assets-list').innerHTML=M.ASSETS.map(a=>'<button class="asset" data-symbol="'+a.symbol+'"><strong>'+a.name+'</strong><span>'+a.symbol+' · '+a.kind+' · '+fmt(a.price)+'</span></button>').join('');
 $('quant-assets').innerHTML=['MSFT','VOO','AAPL','QQQ','BND','BTC/USD','ETH/USD'].map(s=>'<label class="inline-checkbox"><input type="checkbox" name="quant-asset" value="'+s+'" '+(['MSFT','VOO','BND'].includes(s)?'checked':'')+'>'+M.bySymbol[s].name+'</label>').join('');
 $('ml-company').innerHTML=Object.keys(M.COMPANY_FACTS).map(s=>'<option value="'+s+'">'+M.COMPANY_NAMES[s]+'</option>').join('');
 portfolio();runQuant();runDCF();runPeers();renderSEC();renderSECHighlights();
}
document.addEventListener('click',e=>{
 const btn=e.target.closest('[data-page], [data-go], [data-symbol]');if(!btn)return;
 if(btn.dataset.page)nav(btn.dataset.page);
 else if(btn.dataset.go)nav(btn.dataset.go);
 else if(btn.dataset.symbol){$('trade-symbol').value=btn.dataset.symbol;nav('portfolio');}
});
$('trade-submit').addEventListener('click',transact);
$('rebalance-submit').addEventListener('click',rebalance);
$('quant-run').addEventListener('click',runQuant);
$('dcf-run').addEventListener('click',runDCF);
$('ml-run').addEventListener('click',runPeers);
$('sec-company').addEventListener('change',renderSEC);
$('sec-margin-shock').addEventListener('input',renderSEC);
populate();
})();
