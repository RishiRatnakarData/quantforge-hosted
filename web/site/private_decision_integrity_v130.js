/* V13.0 - fail-closed evidence integrity synthesis. Never instructs brokerage actions. */
(function(root){
'use strict';
const safe=x=>String(x??'').slice(0,160);
const key=x=>typeof x==='string'&&/^[A-Z0-9.\-]{1,15}$/.test(x);
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const gates=['linkedModelEvidence','requiredMethods','historicalFilingCoverage','historicalSensitivity','portfolioRiskEvidence'];
const missing=reason=>({schema:'quantforge.integrity-console.v13.0',ready:false,classification:'unavailable',
 reason:safe(reason),gates:[],followUps:['Run a fresh authenticated Research Hub assessment.']});
function assess({brief,historical,robustness,attribution,portfolio}={}){
 if(!brief||brief.schema!=='quantforge.research-brief.v9.3'||!key(brief.symbol)||
  !Array.isArray(brief.universe)||brief.universe.length<2||brief.universe.length>5||
  !Array.isArray(brief.models)||!Array.isArray(brief.mandatoryMissing)||!brief.modelCoverage||
  !brief.universe.some(u=>u.symbol===brief.symbol)||new Set(brief.universe.map(u=>u.symbol)).size!==brief.universe.length)
  return missing('A complete current Research Hub assessment and selected company universe are required.');
 const rows=[];
 const add=(name,status,detail)=>rows.push({key:name,status,detail:safe(detail)});
 const total=brief.models.length,completed=brief.models.filter(m=>m.status==='completed').length;
 const blocked=brief.blocked===true||brief.mandatoryMissing.length>0;
 add('linkedModelEvidence',total>=1&&completed===total?'covered':'limited',
  completed+' of '+total+' linked methods completed.');
 add('requiredMethods',blocked?'blocked':'covered',blocked?
  'Original assessment is blocked or mandatory methods are incomplete.':'Original assessment has no reported mandatory-method block.');
 const covered=!!(historical?.ready&&historical.coverage?.scheduled>=2&&
  historical.coverage.complete===historical.coverage.scheduled&&historical.performance?.ready);
 add('historicalFilingCoverage',covered?'covered':'limited',covered?
  historical.coverage.complete+' / '+historical.coverage.scheduled+' dates have complete historical SEC evidence.':
  'Historical cross-company replay is missing, withheld or incomplete.');
 const hasRobust=!!(robustness?.ready&&robustness.scenarioCount===18&&
  robustness.eligibleScenarios===18&&robustness.fullComparisonReady===true);
 add('historicalSensitivity',hasRobust?'covered':'limited',hasRobust?
  'All 18 prespecified sensitivity scenarios have complete evidence.':
  'One or more fixed sensitivity scenarios cannot support a full comparison.');
 const hasPortfolio=portfolio?.schema==='quantforge.portfolio-validation.v9.5'&&
  portfolio.symbol===brief.symbol&&portfolio.portfolio?.ready===true;
 add('portfolioRiskEvidence',hasPortfolio?'covered':'limited',hasPortfolio?
  'Authenticated portfolio risk analysis is available in the private workspace.':
  'Current authenticated portfolio-weighted risk is unavailable or does not match the candidate.');
 if(rows.map(r=>r.key).join('|')!==gates.join('|'))throw Error('Internal integrity gate mismatch.');
 const gaps=rows.filter(g=>g.status!=='covered');
 const reasons=[...(brief.conflicts||[]),...(brief.cautions||[])].filter(x=>typeof x==='string').slice(0,8).map(safe);
 const followUps=[];
 if(blocked)followUps.push('Resolve the original blocked decision or mandatory method evidence before interpreting any research conclusion.');
 if(!covered)followUps.push('Import the dated SEC archive and verify every scheduled decision window.');
 if(!hasRobust)followUps.push('Compare all fixed historical sensitivity settings without choosing the best observed case.');
 if(!hasPortfolio)followUps.push('Review current authenticated portfolio exposure and provider-data freshness.');
 if(!followUps.length)followUps.push('Review source dates, assumptions and limitations before any independent decision.');
 let classification='evidence-complete';
 if(blocked)classification='blocked';
 else if(gaps.length)classification='evidence-limited';
 // Even a complete set of gates does not establish investability or forecast confidence.
 const attr=attribution?.ready&&covered&&attribution.windowsEvaluated===historical.coverage.scheduled?
  {available:true,windows:attribution.windowsEvaluated,outperform:attribution.outcomes.outperform,
   underperform:attribution.outcomes.underperform,modelMaxDrawdown:attribution.outcomes.modelMaxDrawdown,
   benchmarkMaxDrawdown:attribution.outcomes.benchmarkMaxDrawdown,concentration:attribution.outcomes.exposureConcentration}:null;
 return {schema:'quantforge.integrity-console.v13.0',ready:true,candidate:brief.symbol,
  researchDate:brief.asOf||null,classification,originalAction:safe(brief.action),
  modelCoverage:{total,completed},gates:rows,coveredGates:rows.filter(r=>r.status==='covered').length,
  flaggedRisks:reasons,followUps:followUps.slice(0,5),attribution:attr,
  statement:'This is an evidence-quality audit, not a confidence score, automated investment recommendation or order instruction.',
  limitations:['A complete checklist does not validate forecast accuracy or economic value.',
   'SEC Company Facts history and present-day issuer selection cannot establish bias-free investability.',
   'Risk calculations and historical policies are separate from the original candidate assessment.']};
}
function exportSafe(result){
 if(!result?.ready)return {schema:'quantforge.integrity-export.v13.0',ready:false,classification:'unavailable',reason:safe(result?.reason)};
 return {schema:'quantforge.integrity-export.v13.0',ready:true,candidate:result.candidate,
  classification:result.classification,originalAction:result.originalAction,coveredGates:result.coveredGates,
  gates:result.gates.map(g=>({key:g.key,status:g.status,detail:g.detail})),
  attribution:result.attribution?{...result.attribution}:null,
  flaggedRisks:result.flaggedRisks.slice(),followUps:result.followUps.slice(),
  statement:result.statement,limitations:result.limitations.slice()};
}
const api=Object.freeze({assess,exportSafe});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateDecisionIntegrityV130=api;
})(typeof window!=='undefined'?window:globalThis);
