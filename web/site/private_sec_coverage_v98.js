/* QuantForge V9.8: pure evidence coverage and revision-risk audit.
 * Existing SEC snapshot is a limited cutoff view, NOT a complete as-of archive. */
(function(root){
'use strict';
const validSymbol=s=>typeof s==='string'&&/^[A-Z0-9.\-]{1,15}$/.test(s);
const validDate=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;
const maxReason=s=>String(s||'Unknown evidence gap').slice(0,160);
const days=(a,b)=>Math.round((Date.parse(b)-Date.parse(a))/86400000);
function run({snapshot,history,selection,candidate,train=126,step=21}={}){
 const fail=reason=>({ready:false,reason,universe:[],counts:{scheduled:0,eligible:0,withheld:0},rows:[],coverage:'unavailable',limitations:[
  'Snapshot annual facts can reflect a later-restated or survivor-selected company universe; not a complete historical as-of database.'
 ]});
 const pit=root.QFPrivatePointInTimeV97;
 if(!pit||typeof pit.auditOne!=='function'||!pit.validatePrice(history,candidate))return fail('Load validated, aligned market history before reviewing historical filing coverage.');
 if(!Array.isArray(selection)||selection.length<2||selection.length>5||new Set(selection).size!==selection.length||
  !selection.every(validSymbol)||!selection.includes(candidate)||selection.length!==history.symbols.length||
  selection.some(s=>!history.symbols.includes(s)))return fail('Selected companies must exactly match the loaded historical investments.');
 if(!Number.isInteger(train)||train<63||train>504||!Number.isInteger(step)||step<5||step>63)
  return fail('Historical sampling configuration unavailable.');
 if(!validDate(snapshot?.as_of)||!Array.isArray(snapshot?.companies)||snapshot.companies.length>500||
  new Set(snapshot.companies.map(c=>c?.symbol)).size!==snapshot.companies.length||
  snapshot.companies.some(c=>!validSymbol(c?.symbol)))return fail('SEC snapshot has invalid metadata or duplicated issuers.');
 const lookup=new Map(snapshot.companies.map(c=>[c.symbol,c]));
 const dates=history.dates;
 const boundaries=[];
 for(let end=train-1;end+step<dates.length&&boundaries.length<80;end+=step)boundaries.push(dates[end]);
 if(!boundaries.length)return fail('Insufficient historic evaluation windows for filing coverage.');
 const rows=[];let eligibleAll=0;
 const issues=new Map();
 for(const symbol of selection){
  const company=lookup.get(symbol);
  const cutoff=company?.as_of||snapshot.as_of;
  let eligible=0,withheld=0,latestPeriod=null,firstEligible=null,lastEligible=null;
  const lags=[];const reasons=new Map();
  for(const decisionDate of boundaries){
   // Do not infer SEC availability after this issuer's source snapshot was captured.
   const result=company&&validDate(cutoff)&&cutoff>=decisionDate
    ?pit.auditOne(company,decisionDate)
    :{ready:false,reason:company?'Decision date is beyond this issuer’s published snapshot cutoff.':'No SEC record for this selected security.'};
   if(result.ready){
    eligible++;latestPeriod=result.period;
    if(!firstEligible)firstEligible=decisionDate;
    lastEligible=decisionDate;
    if(validDate(result.maxFiled)&&validDate(result.period))lags.push(days(result.period,result.maxFiled));
   }else{
    withheld++;
    const reason=maxReason(result.reason);
    reasons.set(reason,(reasons.get(reason)||0)+1);
    issues.set(reason,(issues.get(reason)||0)+1);
   }
  }
  // This is a coverage analysis, NOT a cross-company investment ranking.
  const lag=lags.length?lags.sort((a,b)=>a-b)[Math.floor((lags.length-1)/2)]:null;
  rows.push({symbol,scheduled:boundaries.length,eligible,withheld,coveragePct:Number((100*eligible/boundaries.length).toFixed(1)),
   sourceCutoff:validDate(cutoff)?cutoff:null,mostRecentEligibleFiscalPeriod:latestPeriod,
   firstEligible,lastEligible,medianFilingLagDays:lag,
   gaps:[...reasons].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,3).map(([reason,count])=>({reason,count}))});
 }
 for(let i=0;i<boundaries.length;i++){
  const date=boundaries[i];
  if(selection.every(symbol=>{
   const company=lookup.get(symbol),cutoff=company?.as_of||snapshot.as_of;
   return !!company&&validDate(cutoff)&&cutoff>=date&&pit.auditOne(company,date).ready;
  }))eligibleAll++;
 }
 return {ready:true,reason:null,candidate,snapshotAsOf:snapshot.as_of,
  coverage:'limited cutoff snapshot; cannot establish full historical revision completeness',
  counts:{scheduled:boundaries.length,eligible:eligibleAll,withheld:boundaries.length-eligibleAll},
  period:{first:boundaries[0],last:boundaries.at(-1)},rows,
  primaryGaps:[...issues].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,4).map(([reason,count])=>({reason,count})),
  limitations:[
   'This is an issuer-by-issuer evidence coverage diagnostic, not a multi-issuer backtest, recommendation, or return forecast.',
   'Snapshot annual facts may omit earlier originally filed values later replaced by amendments; coverage is not proof of a complete filing archive.',
   'The company universe is currently selected, not a survivorship-bias-free historical universe.',
   'Median filing lag is observed fiscal-end to latest contributing SEC filing, not the regulator’s original disclosure lag.'
  ]};
}
function exportSafe(r){
 if(!r||r.ready!==true)return {schema:'quantforge.sec-evidence-coverage.v9.8',ready:false,reason:maxReason(r?.reason)};
 return {schema:'quantforge.sec-evidence-coverage.v9.8',ready:true,
  coverage:r.coverage,counts:{...r.counts},period:{...r.period},
  issuers:r.rows.map(x=>({symbol:x.symbol,scheduled:x.scheduled,eligible:x.eligible,withheld:x.withheld,
   coveragePct:x.coveragePct,sourceCutoff:x.sourceCutoff,medianFilingLagDays:x.medianFilingLagDays})),
  limitations:r.limitations.slice(0,4)};
}
const api=Object.freeze({run,exportSafe});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateSECCoverageV98=api;
})(typeof window!=='undefined'?window:globalThis);
