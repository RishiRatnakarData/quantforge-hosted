/* QuantForge V10.0: read-only, imported SEC history readiness diagnostics.
 * No raw SEC facts, browser storage, network access, or trading interfaces. */
(function(root){
'use strict';
const valid=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&!Number.isNaN(Date.parse(x))&&new Date(x).toISOString().slice(0,10)===x;
const validSymbol=x=>typeof x==='string'&&/^[A-Z0-9.\-]{1,15}$/.test(x);
const fail=reason=>({ready:false,reason:String(reason).slice(0,180)});
function checkpoints(asOf,startYear=2011){
 if(!valid(asOf)||!Number.isInteger(startYear)||startYear<2009||startYear>2100)return [];
 const cutoff=Number(asOf.slice(0,4)),out=[];
 for(let year=startYear;year<=cutoff;year++)for(const half of ['01-01','07-01']){
  const day=year+'-'+half;if(day<=asOf)out.push(day);
 }
 return out.slice(-40);
}
function inspect({archive,snapshot,selection=[],startYear=2011}={}){
 const pit=root.QFPrivateArchivedSECValidationV99;
 if(!pit||typeof pit.validateArchive!=='function'||typeof pit.auditAt!=='function')return fail('SEC archive validator is unavailable.');
 const validated=pit.validateArchive(archive,snapshot);
 if(!validated.ready)return fail(validated.reason);
 if(!Array.isArray(selection)||selection.length>5||selection.some(s=>!validSymbol(s))||new Set(selection).size!==selection.length)
  return fail('Selected research companies are invalid.');
 const dates=checkpoints(archive.as_of,startYear);
 if(!dates.length)return fail('No historical checkpoints within source cutoff.');
 const sources=new Map(archive.companies.map(c=>[c.symbol,c]));
 const symbols=selection.length?selection:archive.companies.slice(0,5).map(c=>c.symbol);
 const rows=symbols.map(symbol=>{
  const issuer=sources.get(symbol),eligible=[],reasons=new Map();
  for(const day of dates){
   const r=issuer?pit.auditAt(issuer,day):{ready:false,reason:'Issuer absent from local SEC archive.'};
   if(r.ready)eligible.push(day);
   else reasons.set(String(r.reason||'Missing').slice(0,110),(reasons.get(r.reason)||0)+1);
  }
  const gap=[...reasons].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]))[0];
  return {symbol,eligible:eligible.length,scheduled:dates.length,
   coveragePct:Number((100*eligible.length/dates.length).toFixed(1)),
   firstEligible:eligible[0]||null,lastEligible:eligible.at(-1)||null,
   primaryGap:gap?{reason:gap[0],count:gap[1]}:null};
 });
 const complete=dates.filter(day=>symbols.every(s=>{
  const issuer=sources.get(s);return !!issuer&&pit.auditAt(issuer,day).ready;
 }));
 return {ready:true,asOf:archive.as_of,archivedIssuers:archive.companies.length,
  referenceIssuers:snapshot.companies.length,sourceFacts:validated.versionCount,
  selectedCount:symbols.length,selectedMode:selection.length?'selection':'sample',
  dates:{first:dates[0],last:dates.at(-1),scheduled:dates.length,complete:complete.length,
   firstComplete:complete[0]||null,lastComplete:complete.at(-1)||null},
  rows,notes:[
   'Checks Jan 1 and Jul 1 reporting eligibility by source filing date, independent of market price availability.',
   'Only complete, consecutive reported annual periods qualify; missing issuers remain in the denominator.',
   'SEC Company Facts may not preserve all superseded original filings; current selection has survivor bias.',
   'This is a filing evidence audit, not a historical investment performance or return forecast.'
  ]};
}
function exportSafe(r){
 if(!r||!r.ready)return {schema:'quantforge.sec-archive-readiness.v10.0',ready:false,reason:String(r?.reason||'Unavailable').slice(0,160)};
 return {schema:'quantforge.sec-archive-readiness.v10.0',ready:true,asOf:r.asOf,
  archivedIssuers:r.archivedIssuers,referenceIssuers:r.referenceIssuers,sourceFacts:r.sourceFacts,
  selectedMode:r.selectedMode,dates:{...r.dates},
  rows:r.rows.map(x=>({symbol:x.symbol,scheduled:x.scheduled,eligible:x.eligible,coveragePct:x.coveragePct})),
  notes:r.notes.slice(0,4)};
}
const api=Object.freeze({checkpoints,inspect,exportSafe});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateArchiveQualityV100=api;
})(typeof window!=='undefined'?window:globalThis);
