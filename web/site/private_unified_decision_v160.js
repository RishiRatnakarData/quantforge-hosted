/* V16.0 - evidence-grounded, explainable screening dashboard. Pure; no trades or I/O. */
(function(root){
'use strict';
const SYMBOL=/^[A-Z0-9.\-]{1,15}$/;
const str=(v,n=180)=>String(v??'').slice(0,n);
const domains=Object.freeze([
 {key:'fundamentals',name:'Business health',weight:25,description:'Reported growth, operating margin and cash generation'},
 {key:'valuation',name:'Valuation context',weight:25,description:'Observed-price financial ratios, not a fair-value target'},
 {key:'downside',name:'Downside risk',weight:20,description:'Historical drawdown and loss-tail screens'},
 {key:'portfolio',name:'Portfolio fit',weight:20,description:'Virtual exposure and chosen position-size limits'},
 {key:'walkforward',name:'Strategy resilience',weight:10,description:'Past-only strategy/benchmark evidence for the whole selection'}
]);
const labels=Object.freeze({supports:'Supportive',mixed:'Mixed',cautions:'Caution',available:'Measured',unavailable:'Unavailable'});
function empty(reason){return {schema:'quantforge.decision-center.v16.0',ready:false,signal:'unavailable',reason:str(reason),alignment:null,coverage:null,domains:[],comparison:[],next:[],notes:[],action:'Run a complete research assessment',methodology:'No score without eligible, matching evidence.'};}
function summarize({brief,integrity,workflow}={}){
 if(!brief||brief.schema!=='quantforge.research-brief.v9.3'||!SYMBOL.test(brief.symbol)||
  !Array.isArray(brief.universe)||brief.universe.length<2||brief.universe.length>5||
  !brief.universe.every(u=>SYMBOL.test(u?.symbol))||
  new Set(brief.universe.map(u=>u.symbol)).size!==brief.universe.length||
  !brief.universe.some(u=>u.symbol===brief.symbol)||!Array.isArray(brief.evidence)||
  !Array.isArray(brief.models)||!Array.isArray(brief.mandatoryMissing)||!brief.modelCoverage||
  typeof brief.action!=='string')return empty('No valid linked assessment for the current company selection.');
 if(!integrity||integrity.schema!=='quantforge.integrity-console.v13.0'||!integrity.ready||
  integrity.candidate!==brief.symbol||!Array.isArray(integrity.gates))return empty('The linked evidence review is missing or does not match the candidate.');
 if(workflow?.schema==='quantforge.workflow-readiness.v14.0'&&
  !['research-review-ready','assessment-blocked','evidence-limited'].includes(workflow.state))
  return empty('Current selection or loaded observations do not match this assessment.');
 const unique=new Map();
 for(const e of brief.evidence){
  if(typeof e?.key==='string'&&!unique.has(e.key))unique.set(e.key,e);
 }
 const results=domains.map(d=>{
  const e=unique.get(d.key),status=Object.hasOwn(labels,e?.status)?e.status:'unavailable';
  return {key:d.key,name:d.name,weight:d.weight,description:d.description,status,
   label:labels[status],detail:str(e?.detail||'The current model did not produce eligible directional evidence.'),
   source:str(e?.source||'Not measured',100)};
 });
 const required=['history','fundamentals','downside','portfolio'];
 const requiredMissing=required.filter(k=>!unique.has(k)||unique.get(k).status==='unavailable');
 const mandatoryMissing=brief.mandatoryMissing.length>0||brief.blocked===true||integrity.classification==='blocked';
 const blocked=mandatoryMissing||requiredMissing.length>0;
 const directional=results.filter(r=>['supports','mixed','cautions'].includes(r.status));
 const observedWeight=directional.reduce((s,r)=>s+r.weight,0);
 // This is a deterministic descriptive screening rubric, NOT empirical accuracy or predicted returns.
 const totalPoints=directional.reduce((s,r)=>s+r.weight*(r.status==='supports'?1:r.status==='mixed'?.5:0),0);
 const alignment=blocked||observedWeight<40?null:Math.round(100*totalPoints/observedWeight);
 const count=brief.models.length,completed=brief.models.filter(m=>m.status==='completed').length;
 const coverage=count?Math.round(100*completed/count):null;
 const comparable=brief.comparison?.assets;
 const comparison=Array.isArray(comparable)?comparable.slice(0,5).filter(a=>
  SYMBOL.test(a?.symbol)&&Number.isFinite(a.priceChangePercent)&&Number.isFinite(a.maxDrawdownPercent)).map(a=>({
   symbol:a.symbol,name:str(a.name||a.symbol,70),change:a.priceChangePercent,drawdown:a.maxDrawdownPercent
  })):[];
 let signal='amber';
 if(blocked)signal='red';
 else if(alignment!==null&&alignment<35)signal='red';
 else if(alignment!==null&&alignment>=70&&results.every(r=>['supports','mixed','cautions'].includes(r.status)))signal='green';
 const decision=str(brief.action,160);
 const reasons=[...(brief.cautions||[]),...(brief.conflicts||[])].filter(x=>typeof x==='string').slice(0,4).map(x=>str(x));
 const next=[];
 if(blocked)next.push('Complete required, current financial and portfolio evidence before interpreting a recommendation.');
 if(integrity.classification!=='evidence-complete')next.push('Historical filing completeness or other checks are limited; treat results as preliminary.');
 for(const item of brief.next||[]){
  if(typeof item==='string'&&!/(upload|import|file|archive)/i.test(item)&&!next.includes(str(item)))next.push(str(item));
  if(next.length>=3)break;
 }
 if(!next.length)next.push('Inspect the dated evidence, valuation assumptions and concentration limits before making an independent investment decision.');
 const notes=[];
 if(alignment===null)notes.push('The directional alignment score is withheld because required evidence is absent or too few directional screens are eligible.');
 else notes.push('Evidence alignment is a transparent weighted screening index, not a probability, prediction, stock rating, or investment performance statistic.');
 if(integrity.classification!=='evidence-complete')notes.push('Some extended historical SEC and robustness evidence is unavailable; this is not a green-light for investing.');
 notes.push('Company statements use SEC-derived data when present; market figures are observed-price studies, and scenario outputs are modeled.');
 return {schema:'quantforge.decision-center.v16.0',ready:true,signal,alignment,coverage,
  scoreLabel:'Observed evidence alignment',candidate:brief.symbol,candidateName:str(brief.candidate||brief.symbol,80),
  asOf:str(brief.asOf||'Date unavailable',32),action:decision,reason:str(brief.reason,300),
  blocked,classification:integrity.classification,universe:brief.universe.length,
  completed,total:count,domains:results,comparison,reasons,next,notes,
  requiredMissing,methodology:'Predeclared weights: fundamentals 25%, valuation 25%, downside 20%, portfolio fit 20%, multi-asset strategy 10%. Supports=100%, mixed=50%, cautions=0%; unavailable/available-only screens do not enter the directional denominator. Score withheld if core evidence is blocked or less than 40 weight-points are directional. Model coverage is completed/total, measured separately. A green screening light requires no mandatory block, all five directional categories, and alignment >=70; extended integrity is displayed separately and may still be limited. Neither index measures forecast accuracy or suitability.'};
}
function exportSafe(r){
 if(!r?.ready)return {schema:'quantforge.decision-center-export.v16.0',ready:false};
 return {schema:'quantforge.decision-center-export.v16.0',ready:true,candidate:r.candidate,
  asOf:r.asOf,action:r.action,signal:r.signal,alignment:r.alignment,coverage:r.coverage,
  classification:r.classification,domains:r.domains.map(d=>({key:d.key,status:d.status,weight:d.weight})),
  completed:r.completed,total:r.total,notes:r.notes.slice(),methodology:r.methodology};
}
const api=Object.freeze({summarize,exportSafe,domains});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateUnifiedDecisionV160=api;
})(typeof window!=='undefined'?window:globalThis);
