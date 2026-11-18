/* One current research assessment. Pure calculations; no account writes or orders. */
(function(root){
'use strict';
const finite=Number.isFinite;
const dayAge=(value,now)=>{const a=Date.parse(value),b=Date.parse(now);return finite(a)&&finite(b)&&b>=a?(b-a)/86400000:null;};
const percent=v=>(v*100).toFixed(1)+'%';
const policyVersion='research-conditions-2026-11-18';
function policy(raw={}){
 raw=raw&&typeof raw==='object'&&!Array.isArray(raw)?raw:{};
 const out={},errors=[];
 for(const [key,low,high] of [['maxWeight',.01,1],['maxDrawdown',.01,.99],['maxPfcf',1,500],['amount',1,1000000],['maxCorrelation',0,1]]){
  const value=raw[key];
  if(value===undefined||value===null||value===''){out[key]=null;continue;}
  if(!finite(value)||value<low||value>high){errors.push('Choose a valid '+key+' condition.');out[key]=null;}else out[key]=value;
 }
 return {...out,errors,version:policyVersion};
}
function comparable(financial){
 const row=financial?.annual?.find(r=>r.fiscal_end===financial?.source?.period),prior=financial?.annual?.filter(r=>r.fiscal_end<financial.source.period).sort((a,b)=>b.fiscal_end.localeCompare(a.fiscal_end))[0];
 if(!row)return {valid:false,reason:'Reported annual source lineage is unavailable.'};
 const keys=['revenue_usd','operating_income_usd','operating_cash_flow_usd','capex_usd'],sources=keys.map(k=>row.sources?.[k]);
 if(sources.some(s=>!s?.accession)||new Set(sources.map(s=>s.accession)).size!==1)return {valid:false,reason:'Financial-filter inputs require matching filing accessions; missing lineage is not agreement.'};
 if(sources.some(s=>s.end&&s.end!==row.fiscal_end)||new Set(sources.map(s=>s.start).filter(Boolean)).size>1)return {valid:false,reason:'Annual inputs have incompatible source periods.'};
 if(!prior?.sources?.revenue_usd?.tag||prior.sources.revenue_usd.tag!==row.sources.revenue_usd.tag)return {valid:false,reason:'Annual revenue growth requires a consistent disclosed revenue concept.'};
 const m=financial.metrics||{};
 if(m.operating_margin>1||(m.revenue_usd>0&&m.free_cash_flow_usd/m.revenue_usd>1))return {valid:false,reason:'Operating or cash-flow proxy margin exceeds 100%; inspect revenue-concept coverage and unusual transactions before comparison. Raw facts remain available.'};
 return {valid:true,reason:'Matched annual filing inputs and consistent revenue concept; this does not independently establish total-revenue completeness or cross-industry comparability.'};
}
function deterioration(prediction){
 const d=prediction?.diagnostics;
 const valid=p=>p&&Number.isInteger(p.windows)&&p.windows>=12&&[p.modelBrier,p.baselineBrier,p.pairedLossDifference].every(finite)&&p.modelBrier>=0&&p.modelBrier<=1&&p.baselineBrier>=0&&p.baselineBrier<=1&&Math.abs(p.modelBrier-p.baselineBrier-p.pairedLossDifference)<1e-10&&finite(Date.parse(p.first))&&finite(Date.parse(p.last))&&p.first<=p.last;
 return prediction?.ready===true&&d?.schema==='quantforge.chronological-model-review.v34'&&d.state==='deteriorating'&&valid(d.early)&&valid(d.recent)&&d.early.last<d.recent.first&&d.early.pairedLossDifference<-.005&&d.recent.pairedLossDifference>.005;
}

// Evidence coverage is independent of the investment disposition. No new scoring policy.
function researchCoverage(input={},report={coverage:[]}){
 const now=input.asOf||new Date().toISOString(),v=input.valuation;
 const expired=(date,days)=>{const age=dayAge(date,now);return age!==null&&age>days;};
 const gaps=(report.coverage||[]).filter(r=>r.status!=='covered').map(row=>{
  let cause='missing',detail=row.detail,action='Inspect the missing source requirements; a different verified source may be needed.';
  if(row.domain==='Company financials'||row.domain==='Financial health'){
   if(expired(input.financial?.source?.period,550)){cause='stale';detail='Financial evidence exceeds the 550-day review policy.';action='Load a newer eligible annual filing.';}
  }
  if(row.domain==='Observed market risk'&&expired(input.risk?.last,7)){cause='stale';detail='Observed market history exceeds the seven-day research review policy.';action='Refresh observed market history.';}
  if(row.domain==='Observed-price valuation'){
   const outdated=expired(v?.priceTime,7)||expired(v?.sharesTime,550);
   cause=outdated?'stale':'missing';
   detail=outdated?'Price or reported-share evidence exceeds its research review window.':
    (v?.warnings?.length?v.warnings.join(' '):v?.reason||'Compatible price, reported shares and annual financial evidence are unavailable through the current source.');
   if(!outdated&&v?.symbol&&v.symbol!==input.financial?.symbol)detail='Returned valuation evidence belongs to a different issuer; it cannot support this company assessment.';
   else if(!outdated&&v?.fiscalEnd&&v.fiscalEnd!==input.financial?.source?.period)detail='Price/share evidence and the selected annual financial period do not match.';
   action=outdated?'Refresh dated price/share evidence and check the fiscal bridge.':'Inspect price, reported-share dates and filing compatibility. A missing capital input may require another verified source; waiting alone may not resolve it.';
  }
  if(row.domain==='Requested source refresh'){const contractOnly=(input.readFailures||[]).every(k=>input.readIssueKinds?.[k]==='incompatible');cause=contractOnly?'incompatible':'unavailable';detail=(contractOnly?'Returned evidence did not match the required company or data contract: ':'Required evidence requests could not be completed: ')+(input.readFailures||[]).join(', ')+'. Available results are retained.';action=contractOnly?'Inspect the returned company identifier and source contract before using these inputs.':'Retry the failed source requests when access is available; inspect service status if the problem persists.';}
  return {...row,cause,detail,action};
 });
 const unavailable=gaps.find(r=>r.cause==='unavailable'),stale=gaps.find(r=>r.cause==='stale');
 const state=unavailable?'Provider unavailable':stale?'Outdated evidence':gaps.length?'Partial coverage':'Complete coverage';
 const primary=unavailable||stale||gaps[0];
 return {state,upstreamCause:'unclassified',complete:gaps.length===0,gaps,reason:primary?.detail||'All required supported evidence domains are available. Coverage does not establish investment quality.',next:primary?.action||'Inspect the research disposition and its assumptions.'};
}

function assess(input={},guide=root.QFResearchGuide30){
 if(!guide?.decisionSummary)throw Error('The existing research assessment engine is unavailable.');
 const result=guide.decisionSummary(input),rules=policy(input.rules),now=input.asOf||new Date().toISOString();
 const conditions=[],missing=[],breaches=[];
 const f=input.financial?.metrics||{},value=input.valuation,impact=input.portfolioImpact;
 const quoteAge=dayAge(value?.priceTime,now),quoteFresh=quoteAge!==null&&quoteAge*86400<=(input.financial?.symbol?.includes('/')?300:900);
 const weight=finite(impact?.currentWeight)&&impact.currentWeight>=0&&impact.currentWeight<=1?impact.currentWeight:null,drawdown=finite(input.risk?.max_drawdown)&&input.risk.max_drawdown<=0&&input.risk.max_drawdown>=-1?input.risk.max_drawdown:null;
 const observed=input.observed===true;
 if(rules.maxWeight!==null){
  conditions.push({id:'single-name-limit',selected:rules.maxWeight,measured:finite(weight)?weight:null});
  if(!finite(weight))missing.push('Complete dated holding marks to test the selected concentration limit.');
  else if(weight>rules.maxWeight+1e-10)breaches.push('Marked single-name weight '+percent(weight)+' exceeds your '+percent(rules.maxWeight)+' limit.');
 }
 if(rules.maxDrawdown!==null){
  conditions.push({id:'historical-drawdown-limit',selected:rules.maxDrawdown,measured:finite(drawdown)?-drawdown:null});
  if(!observed||!finite(drawdown))missing.push('Observed historical risk is needed for the selected drawdown rule.');
  else if(-drawdown>rules.maxDrawdown)breaches.push('Observed drawdown exceeded your '+percent(rules.maxDrawdown)+' review boundary. This is not a maximum future loss.');
 }
 if(rules.maxPfcf!==null){
  const measured=value?.valid&&finite(value.pFcf)&&value.pFcf>0?value.pFcf:null;
  conditions.push({id:'price-cash-flow-limit',selected:rules.maxPfcf,measured});
  if(measured===null)missing.push('Positive, dated price / cash-flow evidence is needed for the selected valuation rule.');
  else if(measured>rules.maxPfcf)breaches.push('Observed price / cash-flow proxy '+measured.toFixed(1)+'× exceeds your '+rules.maxPfcf.toFixed(1)+'× ceiling. This ceiling is your assumption, not intrinsic value.');
 }
 if(rules.maxCorrelation!==null){
  const others=Object.entries(input.portfolio?.holdings||{}).filter(([symbol,units])=>symbol!==input.financial?.symbol&&finite(units)&&units>0).map(([symbol])=>symbol);
  const pairs=(input.overlap||[]).filter(r=>others.includes(r.symbol)&&finite(r.correlation)&&r.correlation>=-1&&r.correlation<=1&&r.observations>=60);
  conditions.push({id:'observed-held-correlation-limit',selected:rules.maxCorrelation,measured:pairs.length?Math.max(...pairs.map(r=>r.correlation)):null});
  if(others.some(symbol=>!pairs.some(r=>r.symbol===symbol)))missing.push('Historical overlap does not cover every other holding; the selected correlation limit is untested.');
  if(pairs.some(r=>r.correlation>rules.maxCorrelation))breaches.push('Observed overlap exceeds your selected correlation limit. Historical correlation does not prove future diversification.');
 }
 let scenario=null;
 if(rules.amount!==null){
  const cash=input.portfolio?.cash,cashWeight=impact?.cashWeight;
  if(!finite(cash)||!finite(cashWeight)||cashWeight<=0||cashWeight>1||cash<0||!finite(weight))missing.push('Complete dated cash and holding marks are required for a hypothetical allocation.');
  else if(rules.amount>cash)breaches.push('The hypothetical amount exceeds available virtual cash.');
  else{
   const total=cash/cashWeight,gross=rules.amount/1.0005,fee=rules.amount-gross;
   if(finite(total)&&total>fee){
    const proposed=(total*weight+gross)/(total-fee);
    scenario={amount:rules.amount,assumedFee:fee,proposedWeight:proposed,assumption:'Illustrative cash-funded allocation using dated marks and the existing 5-basis-point fee assumption. Exact units, fee and freshness must be revalidated in the server preview.'};
    if(rules.maxWeight!==null&&proposed>rules.maxWeight+1e-10)breaches.push('The hypothetical addition would exceed your selected concentration limit.');
   }
  }
 }
 if(Array.isArray(input.readFailures)&&input.readFailures.length){result.coverage.push({domain:'Requested source refresh',status:'incomplete',detail:'Incomplete evidence requests: '+input.readFailures.join(', ')});missing.push('Refresh the incomplete source requests before treating this as a complete assessment.');}
 const incomplete=result.coverage.filter(r=>r.status!=='covered').map(r=>r.domain);
 const comparableEvidence=comparable(input.financial);
 const financialPositive=[f.revenue_growth,f.operating_margin,f.free_cash_flow_usd].every(finite)&&f.revenue_growth>=0&&f.operating_margin>0&&f.free_cash_flow_usd>0&&!(finite(input.healthRow?.metrics?.equity_usd)&&input.healthRow.metrics.equity_usd<0);
 const explicitEntry=rules.maxWeight!==null&&rules.maxDrawdown!==null&&rules.maxPfcf!==null&&rules.amount!==null;
 const oldMarks=impact?.transactionQualityMarks!==true;
 let label='Investigate',code='research-further',reason='Review the strengths, opposing evidence and assumptions before considering a position.';
 if(rules.errors.length){label='Check research conditions';code='invalid-conditions';reason=rules.errors.join(' ');}
 else if(breaches.length){label=input.held&&finite(weight)&&rules.maxWeight!==null&&weight>rules.maxWeight?'Consider reducing an exposure under your selected rule':'Avoid adding under current risk rules';code='selected-rule-breach';reason=breaches[0];}
 else if(incomplete.length||missing.length){label='Wait for evidence';code='evidence-incomplete';reason=missing[0]||'The current assessment is incomplete: '+incomplete.join(', ')+'. Historical facts remain inspectable.';}
 else if(deterioration(input.prediction)&&input.preferences?.horizon!=='long'){label='Watch model deterioration';code='model-deterioration';reason='Recent held-out error lost its baseline advantage. Reassess the model before relying on its direction.';}
 else if(!comparableEvidence.valid){label='Investigate source comparability';code='financial-comparability';reason=comparableEvidence.reason;}
 else if(!financialPositive){label='Watch';code='financial-cautions';reason='The covered growth, profitability and cash-generation measures do not all support the selected positive-business case.';}
 else if(explicitEntry&&(!quoteFresh||oldMarks)){label='Wait for a current observation';code='execution-observation-stale';reason='Current transaction-quality observations are unavailable. Historical research remains useful; a fresh server preview is required before any virtual transaction.';}
 else if(explicitEntry&&scenario&&observed){label='Consider an entry under specified conditions';code='conditions-met';reason='The dated evidence meets the explicitly selected financial, valuation, drawdown, cash and concentration rules. This is conditional research, not proof of investment merit or an instruction to trade.';}
 const modelLimited=!input.prediction?.ready||input.prediction.qualified!==true||deterioration(input.prediction);
 result.model+=' A five-session classifier is supplementary evidence; it cannot independently justify a multi-year entry or exit.';
 if(deterioration(input.prediction))result.model+=' Recent chronological diagnostics are deteriorating; do not rely on this direction signal.';
 const research=researchCoverage(input,result);
 if(code==='evidence-incomplete'){reason=incomplete.length?research.reason:missing[0];}
 if(code==='research-further')reason=financialPositive?'Reported growth, profitability and cash generation support further research. An attractive purchase price is not established; test valuation assumptions and portfolio limits.':reason;
 const selectedInvalidation=breaches.length?'Reassess after the breached condition is resolved using compatible dated evidence.':incomplete.length?'Reassess when the listed missing domains are supplied and pass their source/date checks.':explicitEntry?'Reassess if the selected valuation, drawdown, cash or concentration conditions stop passing, or new filings weaken the business case.':'Reassess after a new filing, weaker cash generation, a material price change or a portfolio-exposure change. No scheduled monitoring is implied.';
 const next=(code==='evidence-incomplete'&&incomplete.length?research.next:null)||missing.find(x=>!x.startsWith('Refresh the incomplete source'))||({
  'invalid-conditions':'Correct the highlighted optional research conditions and calculate again.',
  'selected-rule-breach':'Inspect the breached condition in detailed evidence, then test a smaller hypothetical allocation or compare another issuer. No transaction has been prepared.',
  'evidence-incomplete':research.next,
  'model-deterioration':'Open Models → Prediction → Evaluation and compare recent held-out Brier error with the baseline before using the model.',
  'financial-comparability':'Open the financial-source lineage and reconcile revenue concepts, filing accessions and fiscal periods before comparing ratios.',
  'financial-cautions':'Inspect the latest annual revenue, operating profit and cash-generation trends; read the relevant filing for the weakest reported measure.',
  'execution-observation-stale':'Refresh the dated observations. Any later virtual transaction still needs its own fresh server preview.',
  'conditions-met':'Stress-test growth and discount-rate assumptions, and compare a peer before making an independent investment decision.'
 }[code]||'Inspect the observed-price ratios, then select a valuation ceiling and portfolio limits before testing a hypothetical addition.');

 return {...result,researchCoverage:research,next,invalidation:selectedInvalidation,authoritative:true,schema:'quantforge.current-assessment.v34',policyVersion,
  snapshot:{symbol:input.financial?.symbol||'',asOf:now,financialPeriod:input.financial?.source?.period||null,marketThrough:input.risk?.last||null,priceTime:value?.priceTime||null,ownerVersion:input.ownerVersion??null,revision:input.revision??null},
  proposal:{label,code,reason,conditions,missing,breaches,scenario,explicitEntry,modelLimited,quoteFresh},
  evidenceKinds:['Observed facts','Derived calculations','Statistical estimates','Scenarios','Research judgment'],
  financialComparability:comparableEvidence,investmentPerformanceProven:false};
}
function screen({snapshot,health,eligible,filters={},asOf=new Date().toISOString(),limit=5}={},engines={core:root.QFResearchCore20,guide:root.QFResearchGuide30}){
 if(eligible?.schema!=='quantforge.research-universe.v34'||eligible.licensed_private!==true||!Array.isArray(eligible.items))return {ready:false,reason:'Load the owner-verified eligible universe first.',rows:[],shortlist:[]};
 if(!Array.isArray(snapshot?.companies)||!engines.core?.financialSummary)throw Error('The reported financial engine is unavailable.');
 const identifiers=eligible.items.map(r=>r?.symbol);
 if(identifiers.some(s=>typeof s!=='string'||!/^[A-Z0-9.\-]{1,15}$/.test(s))||new Set(identifiers).size!==identifiers.length)throw Error('The eligible research universe has invalid or duplicate identifiers.');
 if(filters.minGrowth!==undefined&&filters.minGrowth!==null&&!finite(filters.minGrowth))throw Error('Select a numeric annual growth filter.');
 const order=['cashMargin','growth','margin'].includes(filters.order)?filters.order:'cashMargin';
 const minGrowth=finite(filters.minGrowth)?filters.minGrowth:0;
 if(minGrowth<-.5||minGrowth>2)throw Error('Select a bounded annual growth filter.');
 const rows=[],excluded=[];
 for(const item of eligible.items){
  const company=snapshot.companies.find(c=>c.symbol===item.symbol);
  if(!company){excluded.push({symbol:item.symbol,reason:'No compatible cached issuer financials.'});continue;}
  const f=engines.core.financialSummary(company,asOf),m=f.metrics||{},age=dayAge(f.source?.period,asOf);
  const balanceRow=(health?.companies?.[item.symbol]?.annual||[]).find(r=>r.fiscal_end===f.source?.period);
  const balance=engines.guide?.health(balanceRow),missing=['revenue_growth','operating_margin','free_cash_flow_usd','revenue_usd'].filter(k=>!finite(m[k]));
  if(age===null||age>550||missing.length||!(m.revenue_usd>0)){excluded.push({symbol:item.symbol,reason:age===null||age>550?'Financial evidence is missing or beyond the disclosed 550-day review policy.':'Required reported profitability, growth or cash-flow inputs are missing.'});continue;}
  const lineage=comparable(f);if(!lineage.valid){excluded.push({symbol:item.symbol,reason:lineage.reason});continue;}
  if(m.revenue_growth<minGrowth||m.operating_margin<=0||m.free_cash_flow_usd<=0){excluded.push({symbol:item.symbol,reason:'Does not meet the disclosed positive-profit/cash and minimum-growth filters.'});continue;}
  const equity=balanceRow?.metrics?.equity_usd;
  if(finite(equity)&&equity<0){excluded.push({symbol:item.symbol,reason:'Negative reported equity requires separate financial-health review.'});continue;}
  rows.push({symbol:item.symbol,name:company.name,sector:company.sector||'Not reported',growth:m.revenue_growth,margin:m.operating_margin,cashMargin:m.free_cash_flow_usd/m.revenue_usd,fiscalEnd:f.source.period,filingCutoff:company.as_of||snapshot.as_of||null,
   currentRatio:balance?.current_ratio??null,liabilitiesToAssets:balance?.liabilities_to_assets??null,
   action:'Investigate',reason:'Positive covered operating profit and cash-flow proxy; annual growth meets the selected filter.',risk:'Market downside, current valuation, portfolio overlap and model evidence still require individual research.',valuation:'Not screened from these annual financials alone.',model:'Not evaluated in this financial screen.',invalidate:'Reassess if filings, valuation, market risk or your portfolio conditions change.'});
 }
 rows.sort((a,b)=>b[order]-a[order]||a.symbol.localeCompare(b.symbol));
 return {ready:true,schema:'quantforge.financial-shortlist.v34',rows,shortlist:rows.slice(0,Math.min(5,Math.max(0,limit))),excluded,
  universe:eligible.items.map(x=>x.symbol),eligibleCount:eligible.items.length,passed:rows.length,asOf,order,
  conditions:{minGrowth,positiveOperatingMargin:true,positiveCashFlowProxy:true,financialReviewDays:550},
  explanation:'A transparent financial filter over the stated eligible SEC coverage, ordered by '+({cashMargin:'cash-flow proxy / revenue',growth:'annual revenue growth',margin:'operating margin'}[order])+'. This is not a score, whole-market ranking or investment recommendation.'};
}
function briefing({portfolio,valuation,notes=[],rules={},asOf=new Date().toISOString()}={},guide=root.QFResearchGuide30){
 const selected=policy(rules),actions=[],positions=Object.entries(portfolio?.holdings||{}).filter(([,u])=>finite(u)&&u>0);
 const marked=valuation&&valuation.total_value>0&&finite(valuation.total_value)?valuation:null;
 if(selected.maxWeight!==null&&marked){for(const position of marked.quotes||[]){const w=position.market_value/marked.total_value;if(w>selected.maxWeight)actions.push({kind:'concentration',symbol:position.symbol,label:'Review concentration',detail:'Marked weight '+percent(w)+' exceeds your selected '+percent(selected.maxWeight)+' limit. Consider a reduction scenario; no transaction has been prepared.'});}}
 const latest=new Map();
 for(const note of notes){const thesis=guide?.decode(note.text);if(!thesis)continue;const key=note.symbol+'|'+thesis.id,old=latest.get(key);if(!old||thesis.revision>old.thesis.revision)latest.set(key,{note,thesis});}
 for(const {note,thesis} of latest.values()){if(thesis.review&&dayAge(thesis.review,asOf)!==null)actions.push({kind:'review-due',symbol:note.symbol,label:'Revisit your thesis',detail:'Your chosen review date '+thesis.review+' has arrived. Inspect new evidence; earlier records remain unchanged.'});}
 if(!marked&&positions.length)actions.unshift({kind:'marks-missing',label:'Refresh dated holding marks',detail:'Current portfolio exposure cannot be inferred from cash and units alone. No values or gains have been fabricated.'});
 return {schema:'quantforge.owner-briefing.v34',actions:actions.slice(0,3),positionCount:positions.length,savedTheses:latest.size,asOf,continuousMonitoring:false,accountWrites:0};
}
const api=Object.freeze({policy,assess,screen,briefing,comparable,researchCoverage,policyVersion});
root.QFDecision34=api;if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
