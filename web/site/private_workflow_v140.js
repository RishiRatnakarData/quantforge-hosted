/* V14.0: Pure, fail-closed private workflow readiness. No external I/O or trading. */
(function(root){
'use strict';
const ticker=s=>typeof s==='string'&&/^[A-Z0-9.\-]{1,15}$/.test(s);
const date=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;
const missing=(key,label,route,detail)=>({key,label,route,ready:false,detail});
const success=(key,label,route,detail)=>({key,label,route,ready:true,detail});
function assess({authenticated=false,selection,history,archive,brief,integrity}={}){
 const selected=Array.isArray(selection)?selection:[];
 const validSelection=selected.length>=2&&selected.length<=5&&selected.every(ticker)&&new Set(selected).size===selected.length;
 const steps=[authenticated?
  success('session','Private research session','decision','Authenticated workspace session present; MFA flow requires a separate live browser test.'):
  missing('session','Private research session','decision','Sign in and complete the authenticator flow.')];
 steps.push(validSelection?
  success('selection','Selected investments','decision',`${selected.length} distinct investments selected.`):
  missing('selection','Selected investments','decision','Choose 2–5 distinct companies by name in Research Hub.'));
 const syms=history?.symbols,days=history?.dates,closes=history?.closes;
 const validHistory=validSelection&&authenticated&&Array.isArray(syms)&&syms.length===selected.length&&
  syms.every(ticker)&&new Set(syms).size===syms.length&&selected.every(x=>syms.includes(x))&&
  Array.isArray(days)&&days.length>=64&&days.every(date)&&days.every((d,i)=>i===0||d>days[i-1])&&
  closes&&typeof closes==='object'&&syms.every(s=>Array.isArray(closes[s])&&closes[s].length===days.length&&
   closes[s].every(v=>typeof v==='number'&&Number.isFinite(v)&&v>0));
 steps.push(validHistory?success('history','Loaded and matched price history','research',`${syms.length} companies · ${days.length} aligned dated observations.`):
  missing('history','Loaded and matched price history','research','Load verified historical prices for the exact current company selection.'));
 const archived=!!(authenticated&&archive&&typeof archive==='object'&&Array.isArray(archive.issuers)&&archive.issuers.length>0);
 // Archive evidence is optional. Its absence must not be misrepresented as an authenticated or complete historical evaluation.
 const evidence={key:'archive',label:'Optional historical SEC archive',route:'decision',ready:archived,
  optional:true,detail:archived?'Local filing archive present for this browser session.':'Import the locally validated SEC archive if testing historical filing evidence.'};
 const universe=brief?.universe;
 const matchedBrief=validHistory&&brief?.schema==='quantforge.research-brief.v9.3'&&ticker(brief.symbol)&&
  Array.isArray(universe)&&universe.length===selected.length&&new Set(universe.map(u=>u?.symbol)).size===selected.length&&
  universe.every(u=>selected.includes(u.symbol))&&selected.includes(brief.symbol)&&
  Array.isArray(brief.models)&&typeof brief.readiness==='string';
 steps.push(matchedBrief?success('assessment','Current linked research assessment','decision',
  `Assessment for ${brief.symbol} matches the loaded investment universe.`):
  missing('assessment','Current linked research assessment','decision','Run a new Research Hub assessment after matching market history is loaded.'));
 const completeIntegrity=matchedBrief&&integrity?.schema==='quantforge.integrity-console.v13.0'&&
  integrity.ready===true&&integrity.candidate===brief.symbol&&
  ['blocked','evidence-limited','evidence-complete'].includes(integrity.classification);
 steps.push(completeIntegrity?success('review','Connected research evidence review','settings',
  `Integrity classification: ${integrity.classification}. This is not a forecast score.`):
  missing('review','Connected research evidence review','settings','Inspect the linked research evidence and its documented limitations.'));
 const first=steps.find(s=>!s.ready);
 const completed=steps.filter(s=>s.ready).length;
 let state='research-review-ready';
 if(!authenticated)state='sign-in-required';
 else if(!validSelection)state='select-companies';
 else if(!validHistory)state='load-history';
 else if(!matchedBrief)state='run-research';
 else if(!completeIntegrity)state='review-unavailable';
 else if(integrity.classification==='blocked')state='assessment-blocked';
 else if(integrity.classification==='evidence-limited')state='evidence-limited';
 const next=first?{route:first.route,label:first.label,detail:first.detail}:
  {route:'settings',label:'Review linked research briefing',detail:'Read limitations and evaluate evidence before making an independent decision.'};
 return {schema:'quantforge.workflow-readiness.v14.0',state,ready:completeIntegrity,
  completed,total:steps.length,steps,evidence,next,
  limitation:'Workflow readiness is not provider uptime verification, MFA flow acceptance, a prediction score or an instruction to trade.'};
}
function exportSafe(result){
 if(result?.schema!=='quantforge.workflow-readiness.v14.0')return {schema:'quantforge.workflow-export.v14.0',ready:false};
 return {schema:'quantforge.workflow-export.v14.0',ready:result.ready,state:result.state,
  completed:result.completed,total:result.total,steps:result.steps.map(x=>({key:x.key,ready:x.ready})),
  optionalArchivePresent:result.evidence.ready,limitation:result.limitation};
}
const api=Object.freeze({assess,exportSafe});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateWorkflowV140=api;
})(typeof window!=='undefined'?window:globalThis);
