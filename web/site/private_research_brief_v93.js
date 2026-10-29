/* QuantForge V9.3: connected evidence briefing built exclusively from an existing
 * validated V9.1/V9.2 research run. No I/O, persistence, trading, AI provider, or portfolio balances. */
(function(root){
'use strict';
const STR= x=>String(x??'').slice(0,350);
const texts=(xs,limit)=>Array.isArray(xs)?xs.filter(x=>typeof x==='string'&&x.trim()).slice(0,limit).map(STR):[];
const routes=Object.freeze({history:'research',fundamentals:'candidate',downside:'candidate',valuation:'valuation',portfolio:'trade',walkforward:'walkforward',factors:'candidate',optimization:'optimization',backtest:'backtest',robustness:'walkforward',french:'candidate',candidate:'candidate'});
const statuses=new Set(['completed','failed','ineligible','skipped']);
function summarize(assessment,review,names={},selected=[]){
 if(!assessment||!review||review.schema!=='quantforge.decision-review.v9.2'||!Array.isArray(review.coverage)||
  !Array.isArray(assessment.orchestration?.models)||!Array.isArray(selected)||
  assessment.symbol!==review.symbol||!selected.includes(review.symbol))
  throw Error('A complete linked research assessment is required.');
 const universe=selected.slice(0,5).map(sym=>({symbol:STR(sym),name:STR(names[sym]||sym)}));
 const models=assessment.orchestration.models.map(m=>({
  key:STR(m.key),name:STR(m.title),status:statuses.has(m.status)?m.status:'ineligible',
  required:m.required===true,scope:STR(m.scope),detail:STR(m.detail),source:STR(m.source),
  period:m.period?{start:STR(m.period.start),end:STR(m.period.end),sessions:Number.isFinite(m.period.sessions)?m.period.sessions:null}:null,
  route:routes[m.key]||'lab'
 }));
 const evidence=review.coverage.map(e=>({key:STR(e.key),name:STR(e.name),status:STR(e.status),
  scope:STR(e.scope),detail:STR(e.detail),source:STR(e.source),route:routes[e.key]||'lab'}));
 const comparison=review.comparison?.ready?{
  basis:'Matched historical closing prices, no dividends or investment ranking',
  period:{start:STR(review.comparison.period.start),end:STR(review.comparison.period.end),observations:review.comparison.period.observations},
  assets:review.comparison.rows.map(r=>({symbol:STR(r.symbol),name:STR(names[r.symbol]||r.symbol),
   priceChangePercent:Number((r.totalChange*100).toFixed(2)),maxDrawdownPercent:Number((r.maxDrawdown*100).toFixed(2))}))
 }:null;
 const gaps=evidence.filter(e=>e.status==='unavailable');
 const blocks=review.blocked===true;
 const mandatory=models.filter(m=>m.required&&m.status!=='completed');
 const claims=Object.freeze({
  title:'Linked investment research briefing',schema:'quantforge.research-brief.v9.3',
  symbol:STR(review.symbol),candidate:STR(names[review.symbol]||review.symbol),universe,
  action:STR(review.action),readiness:STR(review.readiness),blocked:blocks,
  reason:STR(review.reason),asOf:review.asOf?STR(review.asOf):null,policy:STR(review.policy),
  modelCoverage:{total:models.length,completed:models.filter(m=>m.status==='completed').length,
   failed:models.filter(m=>m.status==='failed').length,ineligible:models.filter(m=>m.status==='ineligible').length},
  evidence,models,comparison,
  favorable:texts(review.pro,8),cautions:texts(review.con,8),conflicts:texts(review.flags,10),
  missing:gaps.map(g=>g.name),mandatoryMissing:mandatory.map(m=>m.name),
  next:texts(review.next,8),limitations:texts(review.limitations,12),
  assumptions:{risk:STR(review.constraints?.risk),horizon:STR(review.constraints?.horizon),
   maxWeight:Number.isFinite(review.constraints?.maxWeight)?review.constraints.maxWeight:null,
   maxDrawdown:Number.isFinite(review.constraints?.maxDrawdown)?review.constraints.maxDrawdown:null},
  description:'Conditional research based on dated observations and user-selected constraints; not an investment forecast or automatic trade.'
 });
 // Exports deliberately omit the original account state, raw quotes, holdings, price arrays and credentials.
 return claims;
}
const api=Object.freeze({summarize,routes});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateResearchBriefV93=api;
})(typeof window!=='undefined'?window:globalThis);
