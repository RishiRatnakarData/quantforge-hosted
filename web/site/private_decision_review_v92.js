/* QuantForge V9.2: pure investment evidence review and same-window historical comparison.
 * Descriptive, not expected returns, probability estimates, suitability or order execution. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const date=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;
const required=['history','fundamentals','downside','portfolio'];
const groups=Object.freeze([
 {key:'fundamentals',name:'Business health',scope:'Company filings'},
 {key:'valuation',name:'Valuation',scope:'Observed quotes and statements'},
 {key:'downside',name:'Downside risk',scope:'Candidate price history'},
 {key:'portfolio',name:'Portfolio fit',scope:'Hypothetical exposure'},
 {key:'walkforward',name:'Strategy validation',scope:'Multi-asset backtest'},
 {key:'factors',name:'Factor exposure',scope:'Independent factors (optional)'},
 {key:'history',name:'Market observations',scope:'Aligned dated history'}
]);
function historicalComparison(history,selection){
 const failure=(reason)=>({ready:false,reason,rows:[],period:null});
 if(!Array.isArray(selection)||selection.length<2||selection.length>5||new Set(selection).size!==selection.length||
  selection.some(s=>typeof s!=='string'||!s))return failure('Choose two to five distinct investments.');
 if(!history||!Array.isArray(history.symbols)||history.symbols.length!==selection.length||
  new Set(history.symbols).size!==selection.length||!history.symbols.every(s=>selection.includes(s))||
  !Array.isArray(history.dates)||history.dates.length<64||history.dates.length>2500||
  history.dates.some((d,i)=>!date(d)||(i>0&&history.dates[i-1]>=d)))
  return failure('The selected investments do not share a validated chronological price sample.');
 const n=history.dates.length;
 if(!history.closes||history.symbols.some(s=>!Array.isArray(history.closes[s])||history.closes[s].length!==n||
  history.closes[s].some(p=>!finite(p)||p<=0)))return failure('One or more investments has missing or invalid observed closing prices.');
 const rows=selection.map(symbol=>{
  const prices=history.closes[symbol];let peak=prices[0],maxDrawdown=0;
  for(const price of prices){peak=Math.max(peak,price);maxDrawdown=Math.min(maxDrawdown,price/peak-1);}
  const totalChange=prices[n-1]/prices[0]-1;
  return {symbol,totalChange,maxDrawdown,observations:n};
 });
 if(rows.some(r=>!finite(r.totalChange)||!finite(r.maxDrawdown)))return failure('Historical price changes could not be calculated safely.');
 return {ready:true,reason:null,rows,period:{start:history.dates[0],end:history.dates[n-1],observations:n,
  source:String(history.source||'Authenticated historical market observations').slice(0,120)}};
}
function review(assessment,history,selection){
 if(!assessment||typeof assessment!=='object'||!Array.isArray(assessment.evidence)||
  !Array.isArray(assessment.pro)||!Array.isArray(assessment.con)||!Array.isArray(assessment.gaps)||
  !Array.isArray(assessment.steps)||!Array.isArray(assessment.limitations)||!assessment.constraints||
  typeof assessment.decision!=='string')throw Error('V9.2 requires a complete reconciled research assessment.');
 const lookup=new Map(assessment.evidence.map(e=>[e.key,e]));
 const coverage=groups.map(g=>{
  const e=lookup.get(g.key);
  const status=e&&['supports','mixed','cautions','available','unavailable'].includes(e.state)?e.state:'unavailable';
  return {...g,status,detail:typeof e?.detail==='string'?e.detail:'Analysis not available.',source:typeof e?.source==='string'?e.source:'No verified source.'};
 });
 const missingRequired=required.filter(key=>lookup.get(key)?.state==='unavailable'||!lookup.has(key));
 const mandatoryModels=Array.isArray(assessment.orchestration?.models)?assessment.orchestration.models.filter(m=>m.required&&m.status!=='completed'):[];
 const blocked=assessment.readiness==='withheld'||assessment.decision==='Insufficient evidence'||missingRequired.length>0||mandatoryModels.length>0;
 const positive=/^Consider a small position/.test(assessment.decision);
 const blockedOrPositiveInconsistent=blocked&&positive;
 let action=blockedOrPositiveInconsistent?'Insufficient evidence':assessment.decision;
 const flags=[];
 if(missingRequired.length)flags.push('Required evidence is incomplete: '+missingRequired.join(', ')+'.');
 if(mandatoryModels.length)flags.push('Required model execution was incomplete.');
 if(assessment.con.length&&assessment.pro.length)flags.push('Supporting and cautionary evidence coexist; do not treat the assessment as a unanimous model vote.');
 if(assessment.orchestration?.failed>0)flags.push('One or more research methods failed; the missing results were not imputed.');
 const drawdown=lookup.get('downside');
 const portfolio=lookup.get('portfolio');
 if(drawdown?.state==='cautions')flags.push('Observed downside risk breaches at least one chosen screen.');
 if(portfolio?.state==='cautions')flags.push('Portfolio concentration or hypothetical allocation breaches a chosen limit.');
 if(lookup.get('valuation')?.state==='unavailable')flags.push('Valuation evidence is incomplete; an attractive price cannot be established.');
 if(lookup.get('walkforward')?.state==='cautions')flags.push('Multi-asset historical evaluation underperformed its comparator; this is not a candidate forecast.');
 const readiness=blocked?'Evidence blocked':flags.length?'Conditional / caution':'Screening inputs available';
 const comparison=historicalComparison(history,selection);
 const observed=coverage.filter(e=>e.status!=='unavailable').length;
 const dimensionConcerns=coverage.filter(e=>e.status==='cautions').length;
 const next=[...assessment.steps].filter(x=>typeof x==='string'&&x.trim()).slice(0,6);
 if(!comparison.ready)next.push('Reload matching observed price history before comparing investments.');
 return {schema:'quantforge.decision-review.v9.2',action,readiness,blocked,
  reason:blockedOrPositiveInconsistent?'Required data is incomplete, so a positive assessment is withheld.':assessment.reason,
  asOf:assessment.asOf||null,symbol:assessment.symbol||'',coverage,observed,total:coverage.length,
  dimensionConcerns,flags,pro:[...assessment.pro],con:[...assessment.con],next,
  comparison,orchestration:assessment.orchestration||null,limitations:[...assessment.limitations],
  constraints:{...assessment.constraints},policy:assessment.policy||'explicit-screens.v1',
  summary:assessment.summary||''};
}
const api=Object.freeze({historicalComparison,review});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateDecisionReviewV92=api;
})(typeof window!=='undefined'?window:globalThis);
