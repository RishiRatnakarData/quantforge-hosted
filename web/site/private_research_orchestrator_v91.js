/* QuantForge V9.1: pure research planning, evidence ledger, and coverage reconciliation.
 * No IO, storage, model execution, provider calls, or trading. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const date=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;
const MODELS=Object.freeze([
 {key:'history',title:'Aligned market history',scope:'selected universe',source:'Authenticated history provider',required:true},
 {key:'optimization',title:'Constrained portfolio optimization',scope:'selected universe',source:'QFPrivateOptimizer',required:false},
 {key:'backtest',title:'Historical allocation comparison',scope:'selected universe',source:'V5 multi-asset buy-and-hold / rebalance',required:false},
 {key:'walkforward',title:'Chronological strategy evaluation',scope:'selected universe',source:'QFPrivateWalkforward',required:false},
 {key:'robustness',title:'Out-of-sample sensitivity',scope:'selected universe',source:'QFPrivateRobustness',required:false},
 {key:'candidate',title:'Company financials and downside',scope:'selected candidate',source:'QFPrivateCandidateV85 / SEC / observed quotes',required:true},
 {key:'proxy',title:'Market and ETF proxy analysis',scope:'selected candidate',source:'QFPrivateFactorScenariosV86',required:false},
 {key:'french',title:'User-imported independent FF3',scope:'selected candidate',source:'QFPrivateFrenchFactorsV87',required:false}
]);
function checkHistory(selection,history){
 if(!Array.isArray(selection)||selection.length<2||selection.length>5||new Set(selection).size!==selection.length||
  selection.some(s=>typeof s!=='string'||!s))return 'Choose two to five distinct investments.';
 if(!history||!Array.isArray(history.symbols)||history.symbols.length!==selection.length||
  new Set(history.symbols).size!==selection.length||!history.symbols.every(s=>selection.includes(s)))
  return 'Loaded history must match the currently selected investments.';
 const ds=history.dates;
 if(!Array.isArray(ds)||ds.length<64||ds.length>2500||
  ds.some((d,i)=>!date(d)||(i>0&&ds[i-1]>=d)))return 'Historical session dates are missing, unordered, or too short.';
 if(!history.closes||history.symbols.some(s=>!Array.isArray(history.closes[s])||
  history.closes[s].length!==ds.length||history.closes[s].some(p=>!finite(p)||p<=0)))
  return 'Observed price series are incomplete, inconsistent, or nonpositive.';
 return null;
}
function plan({selection=[],symbol='',history=null,train=126,step=21,cap=.6,frenchImported=false}={}){
 const reason=checkHistory(selection,history);
 const historyOK=!reason;
 const candidateOK=historyOK&&selection.includes(symbol);
 const count=historyOK?history.dates.length:0;
 const feasible=finite(cap)&&cap>0&&cap<=1&&cap*selection.length>=1-1e-10;
 const canWF=historyOK&&Number.isInteger(train)&&train>=63&&train<=504&&
  Number.isInteger(step)&&step>=10&&step<=90&&feasible&&count-train>=2*step;
 const reasons={
  history:reason,
  optimization:!historyOK?'Requires matching price history.':!feasible?'Configured weight cap is infeasible for the selection.':null,
  backtest:!historyOK?'Requires matching price history.':null,
  walkforward:!canWF?'Requires sufficient history, feasible constraints and two complete out-of-sample windows.':null,
  robustness:'Requires a successful walk-forward run with at least three windows.',
  candidate:!candidateOK?'Requires matching history with the candidate in the selected universe.':null,
  proxy:!candidateOK?'Requires eligible candidate history; benchmark and ETF models have additional data requirements.':null,
  french:!candidateOK?'Requires eligible candidate history.':!frenchImported?'Official daily FF3 data must be voluntarily imported for this session.':null
 };
 const decisions={history:historyOK,optimization:historyOK&&feasible,backtest:historyOK,walkforward:canWF,
  robustness:false,candidate:candidateOK,proxy:candidateOK,french:candidateOK&&frenchImported};
 return {schema:'quantforge.orchestration.v9.1',universe:historyOK?[...history.symbols]:[...selection],
  symbol,period:historyOK?{start:history.dates[0],end:history.dates.at(-1),sessions:count,source:String(history.source||'Market history').slice(0,160)}:null,
  models:MODELS.map(m=>({...m,eligible:!!decisions[m.key],reason:reasons[m.key]||null}))};
}
function ledger(plan){
 if(plan?.schema!=='quantforge.orchestration.v9.1')throw Error('Invalid research plan.');
 return plan.models.map(m=>({key:m.key,title:m.title,scope:m.scope,source:m.source,required:m.required,
  status:m.eligible?'pending':'ineligible',detail:m.reason||'Eligible; execution not yet completed.',
  period:plan.period?{...plan.period}:null}));
}
function mark(items,key,status,detail){
 if(!Array.isArray(items)||!['completed','failed','ineligible','skipped'].includes(status))throw Error('Invalid model outcome.');
 if(typeof detail!=='string')throw Error('A bounded, human-readable outcome is required.');
 if(!items.some(x=>x.key===key)||items.filter(x=>x.key===key).length!==1)throw Error('Unknown research model.');
 return items.map(m=>m.key===key?{...m,status,detail:detail.slice(0,360)}:{...m});
}
function reconcile(assessment,items){
 if(!assessment||!Array.isArray(assessment.evidence)||!Array.isArray(items))throw Error('Incomplete assessment.');
 if(items.some(x=>!['completed','failed','ineligible','skipped'].includes(x.status)))
  throw Error('Research execution has unfinished modules.');
 const completed=items.filter(x=>x.status==='completed');
 const failed=items.filter(x=>x.status==='failed');
 const absent=items.filter(x=>x.status==='ineligible'||x.status==='skipped');
 const mandatoryMissing=items.some(x=>x.required&&x.status!=='completed');
 const limitations=[...assessment.limitations];
 if(failed.length)limitations.push(`${failed.length} eligible research method(s) failed; no missing results were replaced with estimates.`);
 if(mandatoryMissing)limitations.push('A required acquisition or company-research step did not complete; no positive action is permitted.');
 const withheld=mandatoryMissing&&assessment.decision!=='Insufficient evidence';
 return {...assessment,decision:withheld?'Insufficient evidence':assessment.decision,
  reason:withheld?'Required research did not complete. Review the execution ledger and refresh the unavailable evidence.':assessment.reason,
  readiness:withheld?'withheld':assessment.readiness,limitations,
  orchestration:{schema:'quantforge.orchestration.v9.1',completed:completed.length,failed:failed.length,
   unavailable:absent.length,total:items.length,models:items.map(m=>({...m,period:m.period?{...m.period}:null}))}};
}
const api=Object.freeze({plan,ledger,mark,reconcile,checkHistory});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateResearchOrchestratorV91=api;
})(typeof window!=='undefined'?window:globalThis);
