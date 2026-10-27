/* QuantForge V7.9: private, deterministic research explanation engine.
   Explicit input only; no API, network, storage, account mutation, or trade actions. */
(function(root){
'use strict';
const ok=x=>typeof x==='number'&&Number.isFinite(x);
const pct=x=>`${(100*x).toFixed(1)}%`;
const dollars=x=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(x);
const isDate=x=>/^\d{4}-\d{2}-\d{2}(?:T.*)?$/.test(String(x||''));
function analyze(input){
 const s=input&&typeof input==='object'?input:{};
 const notes=[],actions=[],facts=[],warnings=[];
 const holdings=s.holdings&&typeof s.holdings==='object'?s.holdings:{};
 const quotes=s.quotes&&typeof s.quotes==='object'?s.quotes:{};
 const entries=Object.entries(holdings).filter(([sym,qty])=>/^[A-Z0-9./-]{1,24}$/.test(sym)&&ok(qty)&&qty>0);
 const cash=ok(s.cash)&&s.cash>=0?s.cash:null;
 const missing=entries.filter(([sym])=>!ok(quotes[sym]?.price)||quotes[sym].price<=0).map(x=>x[0]);
 const valued=entries.filter(([sym])=>!missing.includes(sym)).map(([sym,qty])=>({symbol:sym,value:qty*quotes[sym].price}));
 const invested=valued.reduce((a,x)=>a+x.value,0);
 const complete=cash!==null&&missing.length===0;
 const total=complete?cash+invested:null;
 const max=complete&&total>0&&valued.length?valued.reduce((a,b)=>a.value>=b.value?a:b):null;
 if(total===null){warnings.push('The total portfolio value is not reliable because cash or at least one holding quote is unavailable. Concentration percentages are withheld.');}
 else if(total===0){facts.push('The virtual portfolio has no funded positions.');}
 else {
  facts.push(`Virtual portfolio: ${dollars(total)} total, including ${dollars(cash)} cash and ${dollars(invested)} in priced holdings.`);
  if(max){const w=max.value/total;facts.push(`Largest priced position: ${max.symbol}, ${pct(w)} of total virtual value.`);
   if(w>.35){warnings.push(`Concentration check: ${max.symbol} represents ${pct(w)} of the virtual portfolio. A single-company loss could disproportionately affect the result. The 35% screening threshold is a prompt to review, not a recommended target.`);}
  }
 }
 if(s.now&&isDate(s.now)){
  const now=Date.parse(s.now),stale=entries.filter(([sym])=>{
   if(missing.includes(sym))return false;
   const observed=Date.parse(String(quotes[sym]?.timestamp||''));
   return Number.isFinite(observed)&&Number.isFinite(now)&&(now-observed)>7*86400000;
  }).map(x=>x[0]);
  if(stale.length){warnings.push(`Last available quotes for ${stale.join(', ')} are more than seven calendar days old. Review source timestamps before drawing conclusions.`);}
 }
 if(missing.length)actions.push({id:'trade',text:`Refresh observed prices for ${missing.join(', ')} before relying on portfolio weights.`});
 if(!entries.length)actions.push({id:'ideas',text:'Start with Investment screening to compare candidates; you do not need to make a virtual trade.'});
 const history=s.history;
 const historicalValid=history&&Array.isArray(history.symbols)&&history.symbols.length>=2&&Array.isArray(history.dates)&&history.dates.length>=2;
 if(!historicalValid){actions.push({id:'research',text:'Choose 2–5 investments and load historical market data before interpreting strategy risk.'});}
 else {
  facts.push(`Loaded research: ${history.symbols.join(', ')}; ${history.dates[0]} through ${history.dates[history.dates.length-1]}.`);
  warnings.push('Historical price-only returns may exclude dividends and other execution costs; they are not total-return forecasts.');
  const selected=Array.isArray(s.selected)?s.selected:[];
  if(selected.length&&(selected.length!==history.symbols.length||selected.some(x=>!history.symbols.includes(x)))){
   warnings.push('The current investment selection differs from loaded historical data. Reload before comparing strategies.');
   actions.push({id:'research',text:'Reload historical data for the current selection.'});
  }
 }
 const opt=s.optimizer;
 if(opt&&historicalValid&&Array.isArray(opt.symbols)&&opt.symbols.join('|')===history.symbols.join('|')&&
     ok(opt.equal?.annualVolatility)&&ok(opt.optimized?.annualVolatility)){
  facts.push(`Portfolio allocation model (fitted sample): equal-weight volatility ${pct(opt.equal.annualVolatility)} versus optimized ${pct(opt.optimized.annualVolatility)}. This is an in-sample comparison, not a realized improvement.`);
  if(!s.walkforward)actions.push({id:'walkforward',text:'Run Walk-forward to check how the allocation rule behaved on later, held-out historical windows.'});
 }else if(historicalValid){actions.push({id:'optimization',text:'Calculate constrained allocations and inspect concentration and downside estimates.'});}
 const wf=s.walkforward;
 if(wf&&historicalValid&&Array.isArray(wf.symbols)&&wf.symbols.join('|')===history.symbols.join('|')&&
    ok(wf.optimized?.metrics?.change)&&ok(wf.benchmark?.metrics?.change)){
  const a=wf.optimized.metrics.change,b=wf.benchmark.metrics.change;
  facts.push(`Historical rolling evaluation: strategy ${pct(a)} vs equal-weight benchmark ${pct(b)} after modeled fees, over the tested windows. Neither result predicts future returns.`);
  if(ok(wf.optimized.metrics.maxDrawdown))facts.push(`Largest modeled strategy drawdown in those windows: ${pct(wf.optimized.metrics.maxDrawdown)}.`);
  if(opt&&ok(opt.equal?.annualVolatility)&&ok(opt.optimized?.annualVolatility)){
   if(opt.optimized.annualVolatility<opt.equal.annualVolatility&&a<b){
    warnings.push('The allocation model reduced fitted volatility in-sample, but its later-window compounded return was below the equal-weight benchmark. These are different measures: lower estimated risk did not mean better tested return.');
   }else if(a>b){
    warnings.push('The strategy finished ahead of the benchmark in these past test windows, but that alone does not establish persistent superiority or justify a trade.');
   }
  }
  warnings.push('Look for sensitivity to trading costs, tested dates, and selection bias before placing weight on backtest results.');
 }else if(historicalValid){actions.push({id:'walkforward',text:'Run the walk-forward comparison; review both strategies on identical historical periods.'});}
 const screening=s.screening;
 if(screening&&Array.isArray(screening.comparisons)&&screening.comparisons.length){
  facts.push(`Investment screening: ${screening.comparisons.length} candidates compared under a selected historical scoring lens. A ranking describes the chosen inputs and is not an estimate of future profit.`);
  if(Array.isArray(screening.warnings)&&screening.warnings.length){
   warnings.push('Screening quality checks raised '+screening.warnings.length+' warning(s); inspect the screening report before comparing ranks.');
  }
 }else actions.push({id:'ideas',text:'Run Investment screening to compare candidates before reviewing an individual company.'});
 const allocation=s.purchaseImpact;
 if(allocation&&ok(allocation.proposedBudget)&&allocation.after&&allocation.before){
  facts.push(`Hypothetical purchase impact was calculated for ${dollars(allocation.proposedBudget)}. The virtual account was not changed.`);
  if(ok(allocation.before.largest?.weight)&&ok(allocation.after.largest?.weight)){
   facts.push(`Largest holding share: ${pct(allocation.before.largest.weight)} before versus ${pct(allocation.after.largest.weight)} after the proposed purchase.`);
  }
 }else if(entries.length){actions.push({id:'home',text:'Use Proposed purchase impact to compare concentration before recording any virtual transaction.'});}
 if(s.robustness){facts.push('A walk-forward robustness report was calculated. Review how changing fees and evaluation windows changes the comparison before trusting the result.');}
 else if(wf)actions.push({id:'walkforward',text:'After walk-forward, run the benchmark and cost-sensitivity checks.'});
 if(s.forecast){facts.push('A hypothetical multi-year company cash-flow scenario was calculated. Growth, discount, margin, and terminal assumptions materially affect its value; it is not a per-share price target.');}
 const company=s.company;
 if(company&&Array.isArray(company.annual)&&company.annual.length){
  const latest=company.annual[0],m=latest?.metrics||{};
  const name=String(company.name||company.symbol||'Selected company').slice(0,90);
  const fiscal=String(latest?.fiscal_end||'unknown period');
  if(ok(m.revenue_usd))facts.push(`${name}: reported revenue ${dollars(m.revenue_usd)} for fiscal year ending ${fiscal}. Business revenue is not an investment return.`);
  if(ok(m.free_cash_flow_usd))facts.push(`Reported-cash-flow-derived FCF proxy: ${dollars(m.free_cash_flow_usd)}; this is not free cash flow to the firm or equity valuation.`);
  else warnings.push(`Comparable cash-flow proxy is unavailable for ${name}. Valuation conclusions should not fill missing inputs.`);
  actions.push({id:'valuation',text:'Review SEC filing dates and vary cash-flow assumptions; do not interpret the discounted proxy as a stock price target.'});
 }else actions.push({id:'valuation',text:'Choose a company in Valuation and load SEC statements to assess its business finances.'});
 if(s.horizon==='short')warnings.push('You indicated a near-term need for the money. Stock and cryptocurrency prices can fall before you need cash; consider your actual liquidity requirements separately from this simulated portfolio.');
 if(s.horizon==='unknown')actions.push({id:'home',text:'Identify when you might need the money before comparing investment risk.'});
 if(s.comfort==='low')warnings.push('You indicated that a substantial loss would be difficult to tolerate. Historical drawdowns are only examples of what can go wrong, not worst-case limits.');
 if(!actions.length)actions.push({id:'home',text:'Review the dates, assumptions, uncertainty, and saved research before making any decision.'});
 notes.push('The report describes evidence and missing information. It cannot determine whether to buy, hold, or sell, and it does not know your debts, emergency savings, taxes, full finances, or personal suitability.');
 notes.push('This report is generated locally from the current signed-in browser session. It is not a chat model, and no portfolio data is sent to an AI provider.');
 return {title:'Your research, explained',facts,warnings,actions:actions.slice(0,7),notes,createdAt:s.now&&isDate(s.now)?s.now:null};
}
const api={analyze};if(typeof module!=='undefined'&&module.exports)module.exports=api;
if(root)root.QFPrivateGuideV79=api;
})(typeof window!=='undefined'?window:null);
