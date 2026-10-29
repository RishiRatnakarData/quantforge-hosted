/* V8.4: private, session-only evidence synthesis. No network, storage, trades or external AI. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const pct=x=>(x*100).toFixed(1)+'%';
const same=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((x,i)=>x===b[i]);
const asDate=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&!Number.isNaN(Date.parse(x));
function evaluate(input){
 const s=input&&typeof input==='object'?input:{};
 const details=[],findings=[],conflicts=[],steps=[];
 function check(id,label,ok,detail,route){details.push({id,label,available:!!ok,detail,route});}
 function step(route,text){if(!steps.some(x=>x.route===route&&x.text===text))steps.push({route,text});}
 const state=s.portfolio,holdings=state?.holdings,quotes=s.quotes||{};
 const validPortfolio=!!state&&finite(state.cash)&&state.cash>=0&&holdings&&typeof holdings==='object'&&!Array.isArray(holdings);
 let portfolioComplete=validPortfolio,largest=null,largestWeight=null;
 if(validPortfolio){
  let total=state.cash;
  for(const [symbol,qty] of Object.entries(holdings)){
   if(!finite(qty)||qty<0||!finite(quotes[symbol]?.price)||quotes[symbol].price<=0){portfolioComplete=false;break;}
   const value=qty*quotes[symbol].price;
   if(!finite(value)){portfolioComplete=false;break;}
   total+=value;if(qty>0&&(!largest||value>largest.value))largest={symbol,value};
  }
  if(portfolioComplete&&total>0&&largest)largestWeight=largest.value/total;
 }
 check('portfolio','Virtual portfolio and priced positions',portfolioComplete,
   portfolioComplete?'Current virtual account values are available.':'A virtual position or cash balance is missing a valid quote; concentration is withheld.','home');
 if(portfolioComplete&&largestWeight!==null){
  findings.push(`Largest priced holding: ${largest.symbol}, ${pct(largestWeight)} of virtual portfolio value.`);
  if(largestWeight>.35)conflicts.push('Concentration exceeds the 35% screening threshold; this is a review flag, not an allocation target.');
 }else if(!portfolioComplete)step('trade','Refresh missing market observations before comparing portfolio exposure.');
 const h=s.history,selection=Array.isArray(s.selection)?s.selection:[];
 const hValid=h&&Array.isArray(h.symbols)&&h.symbols.length>=2&&h.symbols.length<=5&&new Set(h.symbols).size===h.symbols.length&&
  Array.isArray(h.dates)&&h.dates.length>=31&&h.dates.every((d,i)=>asDate(d)&&(!i||d>h.dates[i-1]))&&
  h.closes&&h.symbols.every(sym=>Array.isArray(h.closes[sym])&&h.closes[sym].length===h.dates.length&&h.closes[sym].every(x=>finite(x)&&x>0));
 const aligned=!!hValid&&(!selection.length||(selection.length===h.symbols.length&&new Set(selection).size===selection.length&&selection.every(x=>h.symbols.includes(x))));
 const coverage=aligned?{start:h.dates[0],end:h.dates.at(-1),count:h.dates.length,symbols:[...h.symbols]}:null;
 check('history','Aligned historical market observations',aligned,
   aligned?`${coverage.count} sessions, ${coverage.start} to ${coverage.end}.`:'Load price histories matching the current selected investments.','research');
 if(aligned)findings.push(`Historical analysis covers ${coverage.symbols.join(', ')} from ${coverage.start} to ${coverage.end}; results are price-only.`);
 else {step('research','Load matching historical market observations.');if(hValid&&selection.length)conflicts.push('Selected investments differ from the loaded historical universe. Previous model results are not comparable.');}
 const o=s.optimizer;
 const optValid=aligned&&o&&same(o.symbols,h.symbols)&&finite(o.equal?.annualVolatility)&&finite(o.optimized?.annualVolatility)&&
  o.equal.annualVolatility>=0&&o.optimized.annualVolatility>=0;
 check('optimization','Constrained portfolio optimization',optValid,
   optValid?'In-sample model comparison completed for the loaded investments.':'Recalculate allocations for the loaded investment history.','optimization');
 if(optValid){
  findings.push(`Fitted annualized volatility: ${pct(o.equal.annualVolatility)} equal weight vs ${pct(o.optimized.annualVolatility)} modeled allocation (in-sample).`);
  if(o.optimized.annualVolatility>o.equal.annualVolatility+1e-10)conflicts.push('The chosen allocation model does not reduce fitted volatility against equal weights.');
 }else if(aligned)step('optimization','Compare constrained allocations with an equal-weight baseline.');
 const w=s.walkforward;
 const wfValid=aligned&&w&&same(w.symbols,h.symbols)&&Array.isArray(w.windows)&&w.windows.length>=1&&
  finite(w.optimized?.metrics?.change)&&finite(w.benchmark?.metrics?.change)&&asDate(w.start)&&asDate(w.end)&&w.end>=w.start&&
  h.dates.includes(w.start)&&h.dates.includes(w.end);
 check('walkforward','Past-only walk-forward evaluation',wfValid,
   wfValid?`${w.windows.length} historical evaluation windows ending ${w.end}.`:'Run a walk-forward evaluation for the loaded historical universe.','walkforward');
 if(wfValid){
  const active=w.optimized.metrics.change-w.benchmark.metrics.change;
  findings.push(`Historical rolling strategy: ${pct(w.optimized.metrics.change)} vs ${pct(w.benchmark.metrics.change)} equal-weight benchmark (difference ${active>=0?'+':''}${pct(active)}).`);
  if(active<0)conflicts.push('The evaluated strategy underperformed equal weights on the tested dates.');
  else conflicts.push('Observed outperformance does not establish predictive skill or statistical significance.');
  if(optValid&&o.optimized.annualVolatility<o.equal.annualVolatility&&active<0)
    conflicts.push('Lower fitted in-sample volatility did not translate to a higher compounded historical return.');
 }else if(aligned)step('walkforward','Test the allocation on held-out historical windows.');
 const r=s.robustness;
 const robustValid=wfValid&&r?.schema==='quantforge.robustness.v1'&&same(r.symbols,h.symbols)&&
  r.dates?.start===w.start&&r.dates?.end===w.end&&finite(r.summary?.fullActivePp)&&Array.isArray(r.strategyCases)&&r.strategyCases.length>=1;
 check('robustness','Strategy sensitivity and robustness',robustValid,
   robustValid?'Fixed-window cost, allocation and omitted-window checks available.':'Review transaction costs, allocation assumptions and sensitivity to test windows.','walkforward');
 if(robustValid&&r.summary.windowDependentSign)conflicts.push('Strategy-versus-benchmark sign reverses after omitting a test window; results depend on the chosen period.');
 if(wfValid&&!robustValid)step('walkforward','Run robustness checks on the existing walk-forward result.');
 const sc=s.screening;
 const screeningValid=!!sc&&Array.isArray(sc.comparisons)&&sc.comparisons.length>=2&&sc.comparisons.every(x=>typeof x.symbol==='string'&&finite(x.score));
 check('screening','Historical candidate screening',screeningValid,
   screeningValid?'Comparative ranking from observed prices; scores are not return probabilities.':'Compare investment candidates using the available market history.','ideas');
 if(screeningValid){
  const first=sc.comparisons[0];
  findings.push(`Under the ${sc.lens||'selected'} screening lens, ${first.symbol} ranked first of ${sc.comparisons.length} candidates (${first.score}/100 descriptive score).`);
  if(first.cautions?.length)conflicts.push(`Top-screened candidate ${first.symbol} has ${first.cautions.length} flagged consideration(s); inspect the screening evidence.`);
 }else step('ideas','Compare candidates and inspect the reasons behind the ranking.');
 const company=s.company;
 const annual=company&&Array.isArray(company.annual)?company.annual:[];
 const companyValid=annual.some(a=>a&&asDate(a.fiscal_end)&&a.metrics&&finite(a.metrics.revenue_usd));
 check('fundamentals','Company filings and valuation context',companyValid,
   companyValid?'SEC financial statements available for the selected issuer; forecast assumptions remain separate.':'Load SEC statements for a company before making valuation claims.','valuation');
 if(companyValid){
  const period=annual.find(a=>a&&asDate(a.fiscal_end)&&a.metrics&&finite(a.metrics.revenue_usd));
  findings.push(`SEC revenue is available for ${company.symbol||company.name||'the selected issuer'} through fiscal ${period.fiscal_end}.`);
  if(!finite(period.metrics.free_cash_flow_usd))conflicts.push('Comparable free-cash-flow proxy is unavailable for the reported company period.');
 }else step('valuation','Review current filings, cash flow and valuation assumptions for the candidate.');
 const p=s.purchaseImpact;
 const scenarioValid=!!p&&finite(p.proposedBudget)&&p.proposedBudget>0&&p.before&&p.after;
 check('impact','Hypothetical purchase and concentration impact',scenarioValid,
   scenarioValid?'Before-and-after virtual portfolio scenario calculated.':'Compare cash and concentration before recording any virtual change.','trade');
 if(!scenarioValid)step('trade','Run the proposed purchase impact calculator before considering a change.');
 if(s.now&&Number.isFinite(Date.parse(s.now))&&validPortfolio){
  const stale=Object.keys(holdings).filter(sym=>holdings[sym]>0&&quotes[sym]&&Number.isFinite(Date.parse(quotes[sym].timestamp))&&Date.parse(s.now)-Date.parse(quotes[sym].timestamp)>7*86400000);
  if(stale.length)conflicts.push('Last observed quotes for '+stale.join(', ')+' are more than seven calendar days old; refresh before estimating a transaction.');
 }
 if(s.horizon==='short')conflicts.push('Near-term cash needs may be inconsistent with substantial exposure to volatile securities.');
 if(s.comfort==='low')conflicts.push('A large temporary loss may exceed the risk tolerance selected in the research guide.');
 const available=details.filter(x=>x.available).length;
 let assessment='Build the evidence first';
 if(aligned&&wfValid&&companyValid&&portfolioComplete&&robustValid)
  assessment='Core evidence assembled — review tradeoffs';
 else if(aligned&&(wfValid||screeningValid||optValid))
  assessment='Partial evidence — resolve the gaps';
 const nextAction=steps.length?{...steps[0]}:{route:'valuation',text:'Review price-versus-business-value assumptions, observed dates and contrary evidence before any investment decision.'};
 const alternatives=[
  {title:'Research further',text:'Resolve missing filings, stale histories, and disagreement between models before evaluating a transaction.',route:'valuation'},
  {title:'Compare the current portfolio',text:'Inspect concentration and portfolio exposure without making a transaction.',route:'home'},
  {title:'Evaluate a hypothetical change',text:'Use the purchase-impact calculator to compare potential exposure, cash use and risk.',route:'trade'}
 ];
 return {schema:'quantforge.private-decision-center.v1',status:assessment,coverage:{available,total:details.length},
  dataset:coverage,details,findings,conflicts,steps:steps.slice(0,7),nextAction,alternatives,
  limits:['Historical rankings and backtests do not forecast future returns or establish a statistically significant trading edge.',
    'Price-only histories can omit dividends, spreads, slippage, taxes and current market changes.',
    'This assessment cannot determine personal investment suitability or authorize any transaction.']};
}
const api=Object.freeze({evaluate});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateDecisionCenterV84=api;
})(typeof window!=='undefined'?window:globalThis);
