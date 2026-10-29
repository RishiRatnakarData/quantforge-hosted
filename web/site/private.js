/* Hosted private mode, same Cloudflare website. No credentials or provider keys in source. */
(function () {
'use strict';
const $=id=>document.getElementById(id);
let guideReportV79=null, linkedResearchBriefV93=null;
let privateDecisionCenterV84=null;
let researchOSRunV90=0, researchOSInternalLoadV90=false;
let candidateDossierV90=null,candidateQuoteV90=null,candidateFactorV91=null;
function clearResearchOSV90(){
 linkedResearchBriefV93=null;
 if(typeof refreshConnectedResearchV93==='function')refreshConnectedResearchV93();
 researchOSRunV90++;
 candidateDossierV90=null;candidateQuoteV90=null;candidateFactorV91=null;
 const button=$('private-v90-run');if(button)button.disabled=false;
 const report=$('private-v90-report');
 if(report)report.textContent='Research inputs changed. Run complete research to rebuild an evidence-linked assessment.';
}
function refreshResearchOSChoicesV90(){
 const picker=$('private-v90-candidate');if(!picker)return;
 const prior=picker.value;
 picker.innerHTML='<option value="">Select a candidate</option>'+researchSelection.map(s=>
  '<option value="'+safe(s)+'">'+safe(assetNames[s]||s)+' ('+safe(s)+')</option>').join('');
 if(researchSelection.includes(prior))picker.value=prior;
 else if(researchSelection.length)picker.value=researchSelection[0];
 const note=$('private-v90-selection');
 if(note)note.textContent=researchSelection.length?
  'Research universe: '+researchSelection.map(s=>assetNames[s]||s).join(' · ')+' · '+researchSelection.length+' selected. Company assessment uses the chosen candidate; portfolio strategies use the complete selection.':
  'Choose 2–5 investments with Browse companies by name; select the candidate from the list.';
}
function renderResearchOSV90(result){
 const out=$('private-v90-report');if(!out)return;
 const review=window.QFPrivateDecisionReviewV92.review(result,historySeries,researchSelection);
 linkedResearchBriefV93=window.QFPrivateResearchBriefV93.summarize(result,review,assetNames,researchSelection);
 refreshConnectedResearchV93();
 const list=(xs,empty)=>'<ul class="qf-v92-list">'+(xs.length?xs:[empty]).map(x=>'<li>'+safe(x)+'</li>').join('')+'</ul>';
 const label=s=>({supports:'Supports',cautions:'Caution',mixed:'Mixed',available:'Available',unavailable:'Unavailable'})[s]||'Unavailable';
 const cells=review.coverage.map(e=>'<article class="qf-v92-evidence"><div class="qf-v92-row"><strong>'+safe(e.name)+'</strong><span class="qf-v92-tag qf-v92-state-'+safe(e.status)+'">'+safe(label(e.status))+'</span></div><div class="tiny">'+safe(e.scope)+'</div><p>'+safe(e.detail)+'</p><small class="tiny">Source: '+safe(e.source)+'</small></article>').join('');
 const models=result.orchestration?.models||[];
 const modelRows=models.map(m=>'<article class="qf-v9-evidence"><strong>'+safe(m.title)+'</strong><span class="tiny"> · '+safe(m.status)+' · '+safe(m.scope)+'</span><p>'+safe(m.detail)+'</p><small class="tiny">'+safe(m.source)+(m.period?' · '+safe(m.period.start)+' to '+safe(m.period.end)+' · '+safe(m.period.sessions)+' observations':'')+'</small></article>').join('');
 const cmp=review.comparison;
 const table=cmp.ready?'<div class="table-wrap"><table class="qf-v92-table"><caption>Matched-window observed price change and worst peak-to-trough decline; no dividends, forecast or overall investment ranking.</caption><thead><tr><th scope="col">Investment</th><th scope="col">Price change</th><th scope="col">Maximum drawdown (0–60% scale)</th></tr></thead><tbody>'+
  cmp.rows.map(r=>{const dd=Math.abs(100*r.maxDrawdown);const bar=(Math.min(60,dd)/60*100).toFixed(1);
   return '<tr><th scope="row">'+safe(assetNames[r.symbol]||r.symbol)+' <span class="tiny">('+safe(r.symbol)+')</span></th><td>'+safe((100*r.totalChange).toFixed(1))+'%</td><td><span class="qf-v92-bar"><span style="width:'+bar+'%"></span></span><span class="qf-v92-barvalue">'+safe(dd.toFixed(1))+'%</span></td></tr>';}).join('')+'</tbody></table></div><p class="tiny">'+safe(cmp.period.start)+' to '+safe(cmp.period.end)+' · '+safe(cmp.period.observations)+' shared sessions · '+safe(cmp.period.source)+'. Bars are capped at 60% visually; printed values are exact to one decimal place. These are past price-only observations, not fair-value estimates.</p>':
  '<p class="tiny">'+safe(cmp.reason)+' This comparison is withheld rather than filled with estimates.</p>';
 const caution=review.con.length?review.con:review.flags;
 out.innerHTML='<section class="qf-v92-report" aria-label="Investment research assessment">'+
  '<div class="qf-v92-hero"><div class="qf-v92-row"><span class="eyebrow">V9.3 · LINKED INVESTMENT RESEARCH</span><span class="qf-v92-readiness">'+safe(review.readiness)+'</span></div><h3>'+safe(review.action)+'</h3><p>'+safe(review.reason)+'</p><p class="tiny">'+safe(review.symbol)+' · Research as of '+safe(review.asOf||'unavailable')+' · '+safe(review.policy)+' · No automatic trades</p></div>'+
  '<div class="qf-v92-metrics" aria-label="Evidence summary"><div><strong>'+review.observed+' / '+review.total+'</strong><span>Evidence areas available</span></div><div><strong>'+safe(result.orchestration?.completed??0)+' / '+safe(result.orchestration?.total??0)+'</strong><span>Models completed</span></div><div><strong>'+review.dimensionConcerns+'</strong><span>Areas with cautions</span></div><div><strong>'+safe(result.orchestration?.failed??0)+'</strong><span>Model failures</span></div></div>'+
  '<div class="qf-v92-twin"><section class="qf-v92-panel"><h4>Evidence in favor</h4>'+list(review.pro,'No favorable company-specific research screens verified.')+'</section><section class="qf-v92-panel"><h4>Risks and objections</h4>'+list(caution,'No completed screen crossed its caution threshold; unmeasured risks remain.')+'</section></div>'+
  '<div class="qf-v92-core"><section><div class="qf-v92-heading"><h4>How the evidence lines up</h4><span class="tiny">Company vs portfolio sources are identified separately</span></div><div class="qf-v92-evidence-grid">'+cells+'</div></section>'+
  '<section><div class="qf-v92-heading"><h4>Compare the investments you selected</h4><span class="tiny">Identical observed sample · historical risk only</span></div>'+table+'</section></div>'+
  '<details class="qf-v92-more"><summary>What might change this assessment?</summary>'+list(review.next,'Reassess price and filing freshness, concentration limits and business-specific valuation assumptions.')+'</details>'+
  '<details class="qf-v92-more"><summary>Evidence conflicts and decision rules</summary>'+list(review.flags,'No specific detected conflict; this is not evidence of investment safety.')+'<p class="tiny">Hard constraints and unavailable required inputs can block action. Other evidence is interpreted by source and scope, never counted as independent votes or calibrated probabilities. Portfolio strategy results do not establish single-company returns.</p></details>'+
  '<details class="qf-v92-more"><summary>V9.1 model execution and data provenance</summary><p class="tiny">'+safe(result.orchestration?.completed??0)+' of '+safe(result.orchestration?.total??0)+' methods completed · '+safe(result.orchestration?.failed??0)+' failed · '+safe(result.orchestration?.unavailable??0)+' unavailable.</p><div class="qf-v9-grid">'+modelRows+'</div></details>'+
  '<details class="qf-v92-more"><summary>Policy assumptions and important limitations</summary><p class="tiny">Risk approach: '+safe(review.constraints.risk)+' · Horizon: '+safe(review.constraints.horizon)+' · Single-name limit: '+(100*review.constraints.maxWeight).toFixed(0)+'% · Drawdown screen: '+(100*review.constraints.maxDrawdown).toFixed(0)+'%</p>'+list(review.limitations,'No further limitations recorded.')+'</details>'+
  '<div class="qf-v93-related"><strong>One assessment, connected research</strong><p>Open the linked briefing for a readable report, or inspect the original model calculations in the Research Lab. Both refer to this assessment and its dated input universe.</p><div class="controls"><button type="button" class="btn primary" data-private-tab="settings">Read linked research briefing</button><button type="button" class="btn" data-private-tab="lab">Explore completed models</button><button type="button" class="btn" data-private-tab="trade">Hypothetical portfolio impact</button></div></div>'+
  '</section>';
}

function refreshConnectedResearchV93(){
 const packet=linkedResearchBriefV93;
 const title=$('qf-v93-ribbon-title'),detail=$('qf-v93-ribbon-detail'),brief=$('qf-v93-ribbon-brief');
 if(title)title.textContent=packet?'Completed research · '+packet.candidate+' ('+packet.symbol+')':'Research workflow · No current assessment';
 if(detail)detail.textContent=packet?packet.universe.length+' investments · '+packet.modelCoverage.completed+'/'+packet.modelCoverage.total+' methods completed · '+packet.readiness:
  'Select investments and run a new assessment. Previous results are not reused after inputs change.';
 if(brief)brief.disabled=!packet;
 const status=$('qf-v93-brief-status');if(status)status.textContent=packet?
  'Connected to '+packet.candidate+' · '+packet.universe.map(s=>s.name).join(', ')+' · '+packet.modelCoverage.completed+' completed methods.':
  'No current linked assessment. Run the Research Hub workflow first.';
 for(const id of ['qf-v93-brief-refresh','qf-v93-brief-export']){const button=$(id);if(button)button.disabled=!packet;}
 const report=$('qf-v93-briefing');if(report&&!packet)report.textContent='No current briefing. Run investment research to generate a linked report; changing its inputs invalidates the previous briefing.';
 const lab=$('qf-v93-lab-status');
 if(lab){
  if(!packet){lab.innerHTML='<strong>Connected research methods</strong><p class="tiny">No current assessment. The Research Lab remains available independently, but a new Research Hub run is needed to link all eligible methods.</p>';}
  else{
   const relevant=packet.models.map(m=>'<div class="qf-v93-lab-tag"><strong>'+safe(m.name)+'</strong><small>'+safe(m.status)+' · '+safe(m.scope)+'</small><button class="text-link" type="button" data-v93-method="'+safe(m.route)+'">Open method</button></div>').join('');
   lab.innerHTML='<strong>Methods from the current Research Hub assessment</strong><p class="tiny">'+safe(packet.candidate)+' · '+safe(packet.readiness)+' · '+packet.modelCoverage.completed+'/'+packet.modelCoverage.total+' completed. Open any method to review or revise its calculations.</p><div class="qf-v93-lab-tags">'+relevant+'</div>';
  }
 }
}
function renderConnectedBriefV93(){
 const report=$('qf-v93-briefing'),packet=linkedResearchBriefV93;
 if(!report||!packet)return;
 const items=(arr,empty)=>'<ul>'+((arr&&arr.length?arr:[empty]).map(t=>'<li>'+safe(t)+'</li>').join(''))+'</ul>';
 const section=(title,itemsList,empty)=>'<section class="qf-v93-brief-section"><h4>'+safe(title)+'</h4>'+items(itemsList,empty)+'</section>';
 const methods=packet.models.map(m=>'<div class="qf-v93-method"><strong>'+safe(m.name)+'</strong> · '+safe(m.status)+
  (m.required?' · Required':' · Optional')+'<small>'+safe(m.scope)+' · '+safe(m.source)+(m.period?' · '+safe(m.period.start)+' to '+safe(m.period.end):'')+'</small><button class="text-link" type="button" data-v93-method="'+safe(m.route)+'">Inspect method</button></div>').join('');
 const evidence=packet.evidence.map(e=>'<div class="qf-v93-method"><strong>'+safe(e.name)+'</strong> · '+safe(e.status)+'<small>'+safe(e.detail)+' · '+safe(e.source)+'</small><button class="text-link" type="button" data-v93-method="'+safe(e.route)+'">Explore evidence</button></div>').join('');
 const cmp=packet.comparison?'<p class="tiny">'+safe(packet.comparison.period.start)+' to '+safe(packet.comparison.period.end)+' · '+safe(packet.comparison.period.observations)+' matched sessions. Price-only, no dividends or forecasts.</p>'+displayTable(['Investment','Observed change','Worst drawdown'],packet.comparison.assets.map(a=>[a.name,a.priceChangePercent.toFixed(2)+'%',a.maxDrawdownPercent.toFixed(2)+'%'])):
  '<p class="tiny">Comparable dated price history is unavailable. No values have been imputed.</p>';
 report.innerHTML='<div class="qf-v93-report-top"><span class="eyebrow">VERIFIED SESSION · '+safe(packet.readiness)+'</span><h4>'+safe(packet.action)+'</h4><p>'+safe(packet.reason)+'</p><p class="tiny">'+safe(packet.candidate)+' ('+safe(packet.symbol)+') · '+safe(packet.asOf||'Research date unavailable')+' · '+safe(packet.policy)+' · No automatic trades</p></div>'+
  '<div class="qf-v93-brief-grid">'+section('Evidence supporting the assessment',packet.favorable,'No favorable evidence was established.')+
  section('Risks and objections',packet.cautions,'No threshold violation was measured; unobserved risks remain.')+
  section('Conflicts and mandatory constraints',packet.conflicts.concat(packet.mandatoryMissing.map(m=>'Required method incomplete: '+m)), 'No specific model conflict was identified; missing evidence may still matter.')+
  section('Important next research steps',packet.next,'Revalidate data dates and assumptions before acting.')+'</div>'+
  '<section class="qf-v93-brief-section"><h4>Selected investments · matched historical context</h4>'+cmp+'</section>'+
  '<div class="qf-v93-brief-grid"><section class="qf-v93-brief-section"><h4>Evidence coverage and sources</h4>'+evidence+'</section><section class="qf-v93-brief-section"><h4>Research method execution</h4><p class="tiny">'+packet.modelCoverage.completed+' completed · '+packet.modelCoverage.failed+' failed · '+packet.modelCoverage.ineligible+' ineligible · '+packet.modelCoverage.total+' total</p>'+methods+'</section></div>'+
  section('Assumptions and limitations',packet.limitations,'Research depends on data quality, sample windows, scenario assumptions and personal risk tolerance.')+
  '<p class="tiny">This briefing describes observed and simulated model output, not guaranteed investment performance, investment suitability or a brokerage instruction. It contains no account balance or raw provider price series.</p>';
}

async function runResearchOSV90(){
 if(!privateState){message('Sign in with MFA before running research.');return;}
 const status=$('private-v90-report'),button=$('private-v90-run');
 let selected=[...researchSelection];
 if(selected.length<2){
  const held=Object.entries(privateState.holdings||{}).filter(([,qty])=>finite(qty)&&qty>0).map(([sym])=>sym).slice(0,5);
  if(held.length>=2){researchSelection=held;renderResearchSelection();selected=[...researchSelection];}
 }
 if(selected.length<2||selected.length>5){
  status.textContent='Choose 2–5 investments and select one company to assess. No decision has been generated.';
  return;
 }
 let sym=$('private-v90-candidate').value;
 if(!selected.includes(sym))sym=selected[0];
 $('private-v90-candidate').value=sym;
 const id=++researchOSRunV90,session=privateState;
 let activeHistory=null;
 const preferences=['private-v90-risk','private-v90-horizon','private-v90-maxweight','private-v90-maxdrawdown','private-v90-days'].map(x=>$(x).value).join('|');
 const current=()=>id===researchOSRunV90&&privateState===session&&
  (!activeHistory||historySeries===activeHistory)&&selected.join(',')===researchSelection.join(',')&&$('private-v90-candidate').value===sym&&
  preferences===['private-v90-risk','private-v90-horizon','private-v90-maxweight','private-v90-maxdrawdown','private-v90-days'].map(x=>$(x).value).join('|');
 const engine=window.QFPrivateResearchOrchestratorV91;
 let plan=null,results=null;
 const record=(key,state,detail)=>{results=engine.mark(results,key,state,detail);};
 button.disabled=true;
 status.textContent='Stage 1/4: loading matching and dated observations…';
 try{
  $('private-history-days').value=$('private-v90-days').value;
  researchOSInternalLoadV90=true;
  try{await loadHistory();}finally{researchOSInternalLoadV90=false;}
  if(!current())return;
  activeHistory=historySeries;
  plan=engine.plan({selection:selected,symbol:sym,history:historySeries,
   train:Number($('private-wf-train').value),step:Number($('private-wf-step').value),
   cap:Number($('private-wf-cap').value),frenchImported:!!frenchFactorsV87});
  results=engine.ledger(plan);
  const eligible=key=>plan.models.find(x=>x.key===key).eligible;
  if(eligible('history'))record('history','completed',`${plan.period.sessions} dated closes from ${plan.period.start} to ${plan.period.end}; ${plan.period.source}.`);
  else record('history','ineligible',plan.models[0].reason||'History could not be validated.');
  if(eligible('optimization')){
   status.textContent='Stage 2/4: optimizing observed multi-asset allocations…';
   try{runOptimization();if(!current())return;
    record('optimization',optimizerResult?.symbols?.length===selected.length&&optimizerResult?.periodEnd===plan.period.end?'completed':'failed',
     optimizerResult?.periodEnd===plan.period.end?'Computed constrained in-sample allocation; not an investment forecast.':'Optimizer did not produce a matching allocation. Inspect Research Lab.');
   }catch(e){record('optimization','failed','Optimization was unavailable; review its settings in Research Lab.');}
  }
  if(eligible('backtest')){
   status.textContent='Stage 2/4: comparing historical buy-and-hold and monthly rebalancing…';
   try{privateBacktest();if(!current())return;
    const success=!!$('private-backtest-output').querySelector('table');
    record('backtest',success?'completed':'failed',success?
     'Historical equal-weight buy-and-hold and rebalancing comparison generated in Research Lab.':'Historical comparison did not complete; check capital and fee assumptions.');
   }catch(e){record('backtest','failed','Historical comparison could not be evaluated.');}
  }
  if(eligible('walkforward')){
   status.textContent='Stage 2/4: evaluating past-only, non-overlapping strategy windows…';
   try{runWalkforward();if(!current())return;
    record('walkforward',walkforwardResult?.end===plan.period.end&&walkforwardResult?.windows?.length>=2?'completed':'failed',
     walkforwardResult?.end===plan.period.end?`${walkforwardResult.windows.length} evaluated test windows; selected multi-asset universe.`:'Walk-forward did not produce eligible, matching test windows.');
   }catch(e){record('walkforward','failed','Chronological evaluation failed; review Research Lab.');}
  }
  if(walkforwardResult?.windows?.length>=3&&results.find(x=>x.key==='walkforward').status==='completed'){
   status.textContent='Stage 2/4: testing robustness and model sensitivities…';
   try{runV68Robustness();if(!current())return;
    record('robustness',robustnessResultV68?.windowCount>=3?'completed':'failed',
     robustnessResultV68?.windowCount>=3?'Sensitivity analyses and leave-one-window-out checks completed.':'Robustness calculations did not produce validated results.');
   }catch(e){record('robustness','failed','Robustness verification was unavailable.');}
  }else record('robustness','ineligible','Requires a successfully evaluated walk-forward with three or more test windows.');
  if(eligible('candidate')){
   status.textContent='Stage 3/4: retrieving company SEC evidence, observed quotes and downside statistics…';
   try{
    refreshCandidateChoicesV85();$('private-candidate-select-v85').value=sym;
    await runCandidateDossierV85();
    if(!current())return;
    record('candidate',candidateDossierV90?.ready&&candidateDossierV90.symbol===sym?'completed':'failed',
     candidateDossierV90?.ready?'Candidate risk and available SEC data reconciled with loaded history.':'Company dossier incomplete; required evidence may be unavailable.');
    if(candidateFactorV91?.ready&&candidateFactorV91.symbol===sym){
     const p=candidateFactorV91;
     record('proxy','completed',p.market?.ready?'Market ETF regression available; ETF proxies are not official FF3 factors.':
      'Candidate historical rolling risk assessed; ETF benchmark regression was unavailable.');
    }else record('proxy','failed','Candidate proxy and rolling-risk assessment were not produced.');
   }catch(e){
    if(!current())return;
    record('candidate','failed','Company evidence acquisition or evaluation failed; review Research Lab.');
    record('proxy','skipped','Candidate computation did not complete.');
    $('private-candidate-run-v85').disabled=false;
   }
  }
  let ff=null;
  if(eligible('french')){
   try{ff=window.QFPrivateFrenchFactorsV87.assess({history:historySeries,selection:researchSelection,symbol:sym,factors:frenchFactorsV87});
    record('french',ff?.ready?'completed':'ineligible',ff?.ready?
     `${ff.aligned} exactly aligned imported factor observations; not an investable forecast.`:ff?.reason||'Imported factor data did not match market observations.');
   }catch(e){record('french','failed','Imported factor estimates could not be validated.');}
  }
  if(!current())return;
  status.textContent='Stage 4/4: reconciling actual model outcomes and applying research policy…';
  const assessment=window.QFPrivateResearchOSV90.assess({
   asOf:new Date().toISOString(),symbol:sym,selection:researchSelection,history:historySeries,
   dossier:candidateDossierV90,quote:candidateQuoteV90||quoted[sym]||null,
   portfolio:privateState,optimizer:optimizerResult,walkforward:walkforwardResult,
   robustness:robustnessResultV68,french:ff,
   risk:$('private-v90-risk').value,horizon:$('private-v90-horizon').value,
   maxWeight:Number($('private-v90-maxweight').value),maxDrawdown:Number($('private-v90-maxdrawdown').value)
  });
  if(!current())return;
  renderResearchOSV90(engine.reconcile(assessment,results));
  message('Automated evidence review completed. Partial failures are disclosed; no trade was placed.');
 }catch(e){
  if(current())status.textContent='Research stopped without a new decision: '+String(e.message||e).slice(0,240)+'. Please inspect the Research Lab.';
 }finally{if(current())button.disabled=false;}
}

function clearDecisionCenterV84(){
 privateDecisionCenterV84=null;
 const out=$('private-decision-result-v84');
 if(out)out.textContent='Inputs or analysis may have changed. Assess current evidence to generate a new summary.';
}
function runDecisionCenterV84(){
 if(!privateState){message('Complete sign-in and MFA before reviewing private research.');return;}
 const symbol=$('private-valuation-company').value;
 const result=window.QFPrivateDecisionCenterV84.evaluate({
  portfolio:privateState,quotes:quoted,selection:researchSelection,history:historySeries,
  optimizer:optimizerResult,walkforward:walkforwardResult,robustness:robustnessResultV68,
  screening:ideaDecisionBrief,company:valuationCompanies[symbol]||null,
  purchaseImpact:allocationResultV74,horizon:$('private-guide-horizon-v79').value,
  comfort:$('private-guide-comfort-v79').value,now:new Date().toISOString()
 });
 privateDecisionCenterV84=result;
 const list=(items)=>'<ul class="tiny">'+items.map(x=>'<li>'+safe(x)+'</li>').join('')+'</ul>';
 const evidence=result.details.map(d=>'<div class="qf-v84-evidence"><strong>'+safe(d.label)+'</strong><span class="'+(d.available?'qf-v84-yes':'qf-v84-no')+'">'+(d.available?'Completed':'Needs work')+'</span><p class="tiny">'+safe(d.detail)+'</p><button class="text-link" type="button" data-v84-go="'+safe(d.route)+'">Open analysis</button></div>').join('');
 const next=result.steps.map(x=>'<li>'+safe(x.text)+' <button class="text-link" type="button" data-v84-go="'+safe(x.route)+'">Open</button></li>').join('');
 $('private-decision-result-v84').innerHTML='<div class="qf-v84-summary"><span class="eyebrow">EVIDENCE REVIEW</span><h3>'+safe(result.status)+'</h3><p>'+result.coverage.available+' of '+result.coverage.total+' analysis areas have usable results.</p>'+
  '<p class="tiny">'+(result.dataset?'Loaded investments: '+safe(result.dataset.symbols.map(x=>assetNames[x]||x).join(' · '))+' · '+safe(result.dataset.start)+' to '+safe(result.dataset.end):'No validated shared investment history is loaded.')+'</p></div>'+
  '<div class="qf-v84-next"><strong>Most useful next step</strong><p>'+safe(result.nextAction.text)+'</p><button class="btn sm" type="button" data-v84-go="'+safe(result.nextAction.route)+'">Open this research step</button></div>'+
  '<h3>What the calculations show</h3>'+list(result.findings.length?result.findings:['No completed calculations are currently available for comparison.'])+
  '<h3>Contradictions and cautions</h3>'+list(result.conflicts.length?result.conflicts:['No conflicting evidence identified in the completed checks. Missing analyses can still change the conclusion.'])+
  '<h3>Evidence coverage</h3><div class="qf-v84-evidence-grid">'+evidence+'</div>'+
  '<h3>Next research steps</h3><ol class="tiny">'+(next||'<li>Review research assumptions and data dates before considering any transaction.</li>')+'</ol>'+
  '<h3>Options to examine</h3>'+list(result.alternatives.map(x=>x.title+': '+x.text))+
  '<p class="tiny">'+safe(result.limits.join(' '))+'</p>';
 message('Decision Center updated from current local research results. No trades or external AI calls.');
}

/* V8.7 official research-factor file stays in this browser's MFA session only. */
let frenchFactorsV87=null,frenchImportSequenceV87=0;
function clearImportedFrenchV87(){
 frenchImportSequenceV87++;
 frenchFactorsV87=null;
 const input=$('private-v87-factor-file');if(input)input.value='';
 const status=$('private-v87-factor-status');if(status)status.textContent='No independently sourced factor file imported.';
 const out=$('private-v87-factor-output');if(out)out.textContent='';
}
async function importFrenchV87(){
 const file=$('private-v87-factor-file')?.files?.[0];
 const seq=++frenchImportSequenceV87,session=privateState;
 frenchFactorsV87=null;
 const status=$('private-v87-factor-status');
 const out=$('private-v87-factor-output');if(out)out.textContent='';
 if(!session){status.textContent='Sign in with MFA before importing factors.';return;}
 if(!file){status.textContent='Choose an extracted CSV first.';return;}
 if(file.size>3000000||file.size===0||!(/\.(csv|txt)$/i.test(file.name))){status.textContent='Choose an extracted CSV/TXT file smaller than 3 MB.';return;}
 try{
  const csv=await file.text();
  if(seq!==frenchImportSequenceV87||session!==privateState||!privateState)return;
  const parsed=window.QFPrivateFrenchFactorsV87.parseDailyCsv(csv);
  frenchFactorsV87=parsed;
  status.textContent='Local factor file loaded: '+parsed.available+' daily observations, '+parsed.from+' through '+parsed.to+'. '+parsed.missing+' missing rows excluded. Imported source is not independently authenticated.';
 }catch(err){if(seq===frenchImportSequenceV87&&session===privateState)status.textContent='Import rejected: '+String(err.message||err);}
}
function renderFrenchV87(r){
 const out=$('private-v87-factor-output');if(!out)return;
 if(!r.ready){out.innerHTML='<p class="notice">'+safe(r.reason)+'</p>';return;}
 const pct=x=>finite(x)?(100*x).toFixed(2)+'%':'Unavailable';
 const num=x=>finite(x)?x.toFixed(3):'Unavailable';
 const m=r.model,o=r.holdout;
 out.innerHTML='<div class="qf-v87-results"><h4>Observed excess-return factor exposures</h4>'+
  '<p class="tiny">'+safe(r.symbol)+' · '+safe(r.aligned)+' matched daily returns · '+safe(r.from)+' to '+safe(r.to)+'. Exact-date join; '+safe(r.excludedPrices)+' unmatched price-return dates omitted. Source: '+safe(r.source)+'</p>'+
  displayTable(['Daily FF3 regression','Estimated coefficient / result'],[
   ['Alpha, approximate annualized (252 × daily)',pct(m.alphaAnnualApprox)],
   ['Alpha approximate 95% HAC interval',pct(m.alphaAnnualCi95[0])+' to '+pct(m.alphaAnnualCi95[1])],
   ['Market excess-return loading',num(m.factorBetas[0])],
   ['Small-minus-big loading',num(m.factorBetas[1])],
   ['High-minus-low loading',num(m.factorBetas[2])],
   ['Market / SMB / HML HAC standard errors',m.factorHacSe.map(num).join(' / ')],
   ['In-sample R²',pct(m.r2)],['Adjusted R²',pct(m.adjustedR2)],
   ['Annualized regression residual volatility',pct(m.residualAnnualVolatility)]])+
  '<h4>Chronological coefficient-stability check</h4>'+
  displayTable(['Held-out observations','Result'],[
   ['Training observations',String(o.train)+' through '+safe(o.trainThrough)],
   ['Later holdout dates',safe(o.testFrom)+' to '+safe(o.testThrough)+' ('+o.test+' observations)'],
   ['Holdout excess-return fit R² versus training-mean baseline',pct(o.r2)],
   ['Holdout error (RMSE, daily returns)',pct(o.rmse)],
   ['Training-mean baseline error (RMSE)',pct(o.baselineRmse)]])+
  '<p class="tiny"><strong>Interpretation:</strong> '+safe(o.interpretation)+' R² may be negative. Full-sample coefficients and confidence intervals are descriptive; holdout metrics use coefficients fitted only on earlier observations.</p>'+
  '<h4>Methods and limitations</h4><ul class="tiny">'+r.limitations.map(x=>'<li>'+safe(x)+'</li>').join('')+'</ul></div>';
}
function runFrenchV87(){
 if(!privateState){message('Sign in with MFA first.');return;}
 const symbol=$('private-candidate-select-v85').value;
 const result=window.QFPrivateFrenchFactorsV87.assess({history:historySeries,selection:researchSelection,symbol,factors:frenchFactorsV87});
 renderFrenchV87(result);
 if(result.ready)message('Research factor study computed locally; no trade or account changes.');
}

/* V8.5 single-candidate dossier, explicitly invoked after MFA sign-in. */
let candidateRequestV85=0;
function clearCandidateDossierV85(){
 candidateRequestV85++;
 candidateDossierV90=null;candidateQuoteV90=null;candidateFactorV91=null;
 const supplemental=$('private-v86-output');if(supplemental)supplemental.textContent='';
 const official=$('private-v87-factor-output');if(official)official.textContent='';
 const out=$('private-candidate-output-v85');
 if(out)out.textContent='Research inputs may have changed. Run the candidate analysis again.';
 const button=$('private-candidate-run-v85');if(button)button.disabled=false;
}
function refreshCandidateChoicesV85(){
 const picker=$('private-candidate-select-v85');if(!picker)return;
 const prev=picker.value;
 const matched=historySeries&&Array.isArray(historySeries.symbols)&&
  researchSelection.length===historySeries.symbols.length&&
  researchSelection.every(sym=>historySeries.symbols.includes(sym));
 const choices=matched?historySeries.symbols:[];
 picker.innerHTML='<option value="">'+(matched?'Choose a loaded investment':'Load matching market history first')+'</option>'+
  choices.map(sym=>'<option value="'+safe(sym)+'">'+safe(assetNames[sym]||sym)+' ('+safe(sym)+')</option>').join('');
 if(choices.includes(prev))picker.value=prev;
 refreshFactorChoicesV86();
}
const MARKET_ETFS_V86=['SPY','VTI','VOO','IVV'];
const PROXY_ETFS_V86=['IWM','IWD','IVE','IWF','IWO','QQQ','VTV','VUG','VB','VBR'];
function refreshFactorChoicesV86(){
 const symbols=historySeries?.symbols||[];
 const candidate=$('private-candidate-select-v85')?.value||'';
 for(const [id,allowed,empty] of [
  ['private-v86-benchmark',MARKET_ETFS_V86,'No loaded market ETF'],
  ['private-v86-proxy1',PROXY_ETFS_V86,'None'],
  ['private-v86-proxy2',PROXY_ETFS_V86,'None']]){
  const select=$(id);if(!select)continue;
  const old=select.value;
  const found=symbols.filter(s=>s!==candidate&&allowed.includes(s));
  select.innerHTML='<option value="">'+safe(empty)+'</option>'+found.map(s=>
   '<option value="'+safe(s)+'">'+safe(assetNames[s]||s)+' ('+safe(s)+')</option>').join('');
  if(found.includes(old))select.value=old;
 }
}
function renderFactorScenariosV86(r){
 const out=$('private-v86-output');if(!out)return;
 if(!r.ready){out.textContent=r.reason;return;}
 const pct=n=>finite(n)?(n*100).toFixed(2)+'%':'Unavailable';
 const num=n=>finite(n)?n.toFixed(3):'Unavailable';
 const money=n=>finite(n)?'$'+n.toFixed(2):'Unavailable';
 const m=r.market,d=r.risk,v=r.valuation;
 const note=txt=>'<p class="tiny">'+safe(txt)+'</p>';
 const labels=(m.ready?'<p>'+safe(m.benchmark)+' benchmark · '+safe(m.observations)+' shared daily returns · '+safe(m.from)+' to '+safe(m.to)+'</p>'+displayTable(
   ['Market comparison','Observed measure'],[
    ['Broad-market ETF beta',num(m.singleBeta)],['Return correlation',num(m.marketCorrelation)],
    ['Single-benchmark R²',pct(m.singleR2)],['Candidate period price change',pct(m.candidatePeriodReturn)],
    ['Market ETF period price change',pct(m.marketPeriodReturn)]
   ])+(m.multi.ready?'<h4>Additional ETF proxy regression</h4>'+displayTable(['Regressor','Estimated return sensitivity'],
    m.multi.predictorLabels.map((x,i)=>[x,num(m.multi.coefficients[i])]))+
    displayTable(['Model diagnostic','Result'],[['Adjusted R²',pct(m.multi.adjustedR2)],
    ['Annualized residual volatility',pct(m.multi.residualAnnualVolatility)],
    ['Raw-return daily intercept (not CAPM alpha)',pct(m.multi.rawDailyIntercept)]]):note(m.multi.reason)):
   '<p class="notice">'+safe(m.reason)+'</p>');
 let risk='';
 if(d.ready){
  const points=d.rollingPoints;
  let graph='';
  if(points.length>=2){
   const top=Math.max(.001,...points.map(p=>p.value));
   const poly=points.map((p,i)=>(32+i*500/(points.length-1)).toFixed(1)+','+(149-p.value/top*120).toFixed(1)).join(' ');
   graph='<figure><svg class="qf-v86-risk-chart" viewBox="0 0 570 184" role="img" aria-label="Rolling 63-session annualized historical volatility in chronological order"><line x1="32" y1="149" x2="532" y2="149" stroke="#bacfc2"/><polyline points="'+poly+'" fill="none" stroke="#1b7462" stroke-width="3"/><text x="32" y="173" font-size="12">'+safe(points[0].date)+'</text><text x="532" y="173" text-anchor="end" font-size="12">'+safe(points.at(-1).date)+'</text></svg><figcaption class="tiny">Sampled 63-session rolling annualized volatility, 252 equity sessions per year; not a volatility forecast.</figcaption></figure>';
  }
  risk=displayTable(['Observed historical downside','Result'],[
   ['Maximum peak-to-trough drawdown',pct(d.maxDrawdown)],
   ['Drawdown peak → trough',d.drawdownPeak+' → '+d.drawdownTrough],
   ['Longest underwater spell (sessions)',String(d.longestUnderwaterSessions)],
   ['Current underwater spell (sessions)',String(d.underwaterNow)],
   ['Latest rolling 63-session volatility',pct(d.latestRolling63Volatility)],
   ['Highest rolling 63-session volatility',pct(d.highestRolling63Volatility)],
   ['Worst observed 20-session change',pct(d.worst20?.change)],
   ['Worst 20-session window',d.worst20?d.worst20.from+' → '+d.worst20.to:'Unavailable']
  ])+graph;
 }else risk='<p class="notice">'+safe(d.reason)+'</p>';
 let valuation='';
 if(v.ready){
  valuation=note('Observed quote '+v.quoteTime+' · observed P/S '+num(v.observedPS)+'× · scenario horizon '+v.years+' year(s). Multipliers below are percentages of the current P/S multiple, not assumed absolute P/S values.')+
   displayTable(['Annual revenue growth','Terminal P/S / current P/S','Conditional price change','Conditional implied price'],
   v.scenarios.map(x=>[pct(x.growth),num(x.multipleRatio)+'×',pct(x.priceChange),money(x.impliedPrice)]))+
   note(v.assumptions);
 }else valuation='<p class="notice">'+safe(v.reason)+'</p>';
 out.innerHTML='<div class="qf-v86-report"><span class="eyebrow">DEEPER CANDIDATE RESEARCH · V8.6</span><h3>Market exposures, rolling downside and valuation sensitivity</h3>'+note('All figures below are descriptive, session-local, and use the currently loaded candidate; no model here places or proposes a trade.')+
  '<h4>Explicit broad-market ETF comparison</h4>'+labels+'<h4>Historical downside diagnostics</h4>'+risk+
  '<h4>Observed-price valuation sensitivity (not fair value)</h4>'+valuation+
  '<h4>Methods and limitations</h4><ul class="tiny">'+r.limitations.map(x=>'<li>'+safe(x)+'</li>').join('')+'</ul></div>';
}
function candidateChartV85(d){
 const data=d.graph;if(!data||!data.candidate?.length)return '';
 const all=[...data.candidate,...data.peers];
 if(all.some(x=>!finite(x)))return '';
 const mn=Math.min(...all),mx=Math.max(...all),spread=mx-mn||1;
 const path=series=>series.map((v,i)=>(i?'L':'M')+(48+i*510/(series.length-1)).toFixed(1)+' '+(181-(v-mn)/spread*144).toFixed(1)).join(' ');
 const start=safe(data.dates[0]),end=safe(data.dates.at(-1));
 return '<figure style="margin:15px 0"><svg class="qf-v85-chart" viewBox="0 0 600 220" role="img" aria-label="Indexed historical candidate and equal-weight peer basket price returns on the same dates">'+
  '<line x1="48" y1="181" x2="558" y2="181" stroke="#b4c7bd"/>'+
  '<line x1="48" y1="37" x2="48" y2="181" stroke="#b4c7bd"/>'+
  '<path d="'+path(data.peers)+'" fill="none" stroke="#a5672b" stroke-width="2.3"/>'+
  '<path d="'+path(data.candidate)+'" fill="none" stroke="#146e5f" stroke-width="2.6"/>'+
  '<text x="48" y="203" fill="#425e50" font-size="12">'+start+'</text><text x="558" y="203" text-anchor="end" fill="#425e50" font-size="12">'+end+'</text></svg>'+
  '<div class="qf-v85-key"><span><i class="line"></i>'+safe(d.symbol)+'</span><span><i class="line peer"></i>Equal-weight selected peers</span></div>'+
  '<figcaption class="tiny">Recent aligned sessions; both series rebased to their common chart starting observation. Price-only. Read the numerical statistics below for full-period measures.</figcaption></figure>';
}
function renderCandidateDossierV85(d){
 const out=$('private-candidate-output-v85');
 if(!d.ready){out.innerHTML='<p class="notice">'+safe(d.reason)+'</p>';return;}
 const pct=n=>finite(n)?(n*100).toFixed(2)+'%':'Unavailable';
 const num=n=>finite(n)?n.toFixed(2)+'×':'Unavailable';
 const coef=n=>finite(n)?n.toFixed(2):'Unavailable';
 const metric=(name,value)=>'<div class="qf-v85-metric"><span class="tiny">'+safe(name)+'</span><strong>'+safe(value)+'</strong></div>';
 const m=d.metrics,f=d.fundamentals,v=d.valuation,p=d.portfolioImpact;
 const impacts=p?[
  ['Existing position weight',pct(p.currentWeight)],
  ['Candidate -20%: current portfolio effect',pct(p.existingCandidateShock20)],
  ['Add 5% of portfolio from cash, then -20%',pct(p.additional5)],
  ['Add 10% of portfolio from cash, then -20%',pct(p.additional10)],
  ['Current virtual cash share',pct(p.cashWeight)]
 ]:[];
 const cautions=[...d.cautions,...v.warnings];
 const list=items=>'<ul class="tiny">'+items.map(x=>'<li>'+safe(x)+'</li>').join('')+'</ul>';
 out.innerHTML='<div class="qf-v84-summary"><span class="eyebrow">CANDIDATE DOSSIER</span><h3>'+safe(assetNames[d.symbol]||d.symbol)+' ('+safe(d.symbol)+')</h3>'+
  '<p class="tiny">'+safe(d.history.observations)+' observed daily returns · '+safe(d.history.start)+' through '+safe(d.history.end)+' · '+safe(d.history.peerCount)+' other selected investments in peer comparison</p></div>'+
  '<h3>Observed return and downside profile</h3><div class="qf-v85-metric-grid">'+
  metric('Loaded-period price change',pct(m.periodReturn))+metric('Last 63-session price change',pct(m.trailing63Return))+
  metric('Historical annualized volatility',pct(m.annualVolatility))+metric('Worst observed drawdown',pct(m.maxDrawdown))+
  metric('One-day historical 95% VaR (loss)',pct(m.dailyVaR95))+metric('One-day historical 95% expected shortfall',pct(m.dailyES95))+'</div>'+
  candidateChartV85(d)+'<h3>Peer-relative sensitivity (not broad-market beta)</h3>'+
  displayTable(['Descriptive measure','Candidate / other selected investments'],[
   ['Candidate period change',pct(m.periodReturn)],['Equal-weight peers period change',pct(m.peerPeriodReturn)],
   ['Candidate annualized volatility',pct(m.annualVolatility)],['Peer annualized volatility',pct(m.peerAnnualVolatility)],
   ['Candidate daily return correlation with peers',coef(m.peerCorrelation)],
   ['Candidate regression sensitivity to peers',coef(m.peerBeta)],
   ['In-sample explanatory R²',pct(m.peerR2)]])+
  '<p class="tiny">Peer sensitivity = covariance(candidate daily returns, equal-weight daily returns of other selected investments) / variance(peer returns). The peer set is selected by the user, not an external market or economic factor benchmark. In-sample only.</p>'+
  '<h3>SEC operating evidence and observed-price valuation</h3>'+
  displayTable(['Measure','Reported / calculated'],[
   ['Latest SEC annual period',f.fiscalEnd||'Not loaded / not applicable'],
   ['Comparable annual revenue growth',pct(f.revenueGrowth)],['Operating profit margin',pct(f.operatingMargin)],
   ['Free-cash-flow proxy / revenue',pct(f.freeCashFlowMargin)],
   ['Observed quote timestamp',v.priceTime||'Unavailable'],['SEC share-count period',v.sharesTime||'Unavailable'],
   ['Price / sales',num(v.pSales)],['Price / positive FCF proxy',num(v.pFcf)],
   ['Annual FCF proxy yield',pct(v.fcfYield)]])+
  '<p class="tiny">Negative cash flow is not converted to a positive P/FCF multiple. Missing or stale share counts, annual filings and quotes suppress market-cap-based ratios. These ratios are not a DCF, fair-value estimate, or price target.</p>'+
  '<h3>Virtual portfolio impact — hypothetical downside</h3>'+
  (p?displayTable(['Scenario','Portfolio result'],impacts):'<p class="notice">Incomplete priced holdings or missing virtual cash balance; current-account stress effects are withheld.</p>')+
  '<p class="tiny">The assumed -20% isolated candidate shock applies to the position weight after each illustrated cash-funded allocation. It is not a return prediction; no trades or changes to virtual holdings take place.</p>'+
  '<h3>Flags and limitations</h3>'+list(cautions.length?cautions:['No numerical review thresholds triggered; this does not mean risk is low.'])+
  list([...d.valuation.limitations,...d.limitations])+
  '<div class="controls"><button class="btn sm" type="button" data-v85-go="valuation">Open company valuation</button><button class="btn sm" type="button" data-v85-go="trade">Open purchase-impact calculator</button></div>';
}
async function runCandidateDossierV85(){
 if(!privateState){message('Sign in with MFA before requesting candidate research.');return;}
 const sym=$('private-candidate-select-v85').value;
 if(!sym||!historySeries?.symbols?.includes(sym)){message('Choose an investment from the loaded market history.');return;}
 clearCandidateDossierV85();
 const id=candidateRequestV85,session=privateState,h=historySeries,selected=researchSelection.join(','),out=$('private-candidate-output-v85');
 $('private-candidate-run-v85').disabled=true;
 out.textContent='Combining observed historical data with available SEC filings and private observed-price context…';
 const companyPromise=valuationCompanies[sym]?Promise.resolve(valuationCompanies[sym]):api('private/sec/company?symbol='+encodeURIComponent(sym));
 const [companyResult,capitalResult,quoteResult]=await Promise.allSettled([
  companyPromise,api('private/valuation-capital?symbol='+encodeURIComponent(sym)),
  api('private/quotes?symbols='+encodeURIComponent(sym))
 ]);
 if(id!==candidateRequestV85||session!==privateState||h!==historySeries||selected!==researchSelection.join(',')||$('private-candidate-select-v85').value!==sym)return;
 const company=companyResult.status==='fulfilled'&&companyResult.value?.symbol===sym?companyResult.value:null;
 if(company)valuationCompanies[sym]=company;
 const capital=capitalResult.status==='fulfilled'?capitalResult.value:null;
 const q=quoteResult.status==='fulfilled'?(quoteResult.value?.quotes||[]).find(item=>item.symbol===sym):null;
 let value=null;
 if(company&&capital&&q){try{value=window.QFPrivateValueV73.build(company,capital,q,new Date().toISOString());}catch(_){/* Valuation withheld when issuer or dates disagree. */}}
 const dossier=window.QFPrivateCandidateV85.evaluate({symbol:sym,selection:researchSelection,history:h,company,value,portfolio:session,quotes:quoted,now:new Date().toISOString()});
 candidateDossierV90=dossier;candidateQuoteV90=q||quoted[sym]||null;
 renderCandidateDossierV85(dossier);
 const proxyChoices=[$('private-v86-proxy1').value,$('private-v86-proxy2').value].filter(Boolean);
 const factorResult=window.QFPrivateFactorScenariosV86.assess({
  history:h,selection:researchSelection,symbol:sym,benchmark:$('private-v86-benchmark').value,
  proxies:proxyChoices,value,years:Number($('private-v86-years').value)
 });
 renderFactorScenariosV86(factorResult);
 candidateFactorV91=factorResult;
 $('private-candidate-run-v85').disabled=false;
 message('Private candidate analysis calculated. No portfolio changes or broker orders.');
}
function clearGuideV79(){
 guideReportV79=null;
 clearDecisionCenterV84();
 clearCandidateDossierV85();
 const out=$('private-guide-result-v79'),btn=$('private-guide-export-v79');
 if(out)out.textContent='Research changed. Generate a new summary to use the latest results.';
 if(btn)btn.disabled=true;
}
function runGuideV79(){
 if(!privateState){message('Sign in and complete authenticator verification first.');return;}
 const symbol=$('private-valuation-company').value;
 const report=window.QFPrivateGuideV79.analyze({
  cash:privateState.cash,holdings:privateState.holdings,quotes:quoted,
  selected:researchSelection,history:historySeries,optimizer:optimizerResult,
  walkforward:walkforwardResult,company:valuationCompanies[symbol]||null,
  screening:ideaDecisionBrief,purchaseImpact:allocationResultV74,
  robustness:robustnessResultV68,forecast:forecastResultV66,
  horizon:$('private-guide-horizon-v79').value,comfort:$('private-guide-comfort-v79').value,
  now:new Date().toISOString()
 });
 guideReportV79=report;
 const ul=items=>'<ul class="tiny">'+items.map(item=>'<li>'+safe(item)+'</li>').join('')+'</ul>';
 const actions=report.actions.map(a=>'<li>'+safe(a.text)+' <button class="text-link" type="button" data-guide-go-v79="'+safe(a.id)+'">Open '+safe(({trade:'Virtual trades',ideas:'Investment screening',research:'Market data',optimization:'Optimization',walkforward:'Walk-forward',valuation:'Valuation',home:'Overview'})[a.id]||'Overview')+'</button></li>').join('');
 $('private-guide-result-v79').innerHTML='<h4>What the available evidence says</h4>'+ul(report.facts.length?report.facts:['No completed research calculations are available yet.'])+
  '<h4>Important risks and limits</h4>'+ul(report.warnings.length?report.warnings:['No numerical risk conclusion can be drawn without verified market observations.'])+
  '<h4>What to check next</h4><ol class="tiny">'+actions+'</ol><h4>How to use this report</h4>'+ul(report.notes)+
  '<p class="tiny">Generated on request; results are not automatically updated. No real trades or data transfers took place.</p>';
 $('private-guide-export-v79').disabled=false;
 message('Research summary generated locally. No trades or external AI calls.');
}

const M=window.QFModel;
let privateState=null, version=0, quoted={}, mfaFactorId=null;
let researchSelection=[];
let valuationCompanies={};
let assetNames={};
const browserState={mode:'trade',category:'popular',letter:'',query:'',page:0,pages:1};
let browserRequest=0, browserDebounce;

const usd=n=>Number(n).toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2});
const safe=s=>String(s).replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
function message(msg){$('private-message').textContent=msg;}
async function api(path, body){
  const init={credentials:'same-origin',cache:'no-store'};
  if(body!==undefined){init.method='POST';init.headers={'Content-Type':'application/json','X-QF-Action':'1'};init.body=JSON.stringify(body);}
  const r=await fetch('/api/'+path,init);
  let data;try{data=await r.json();}catch(_){throw Error('Service unavailable. Free hosting may be waking up.');}
  if(!r.ok)throw Error(data.detail || data.error || ('HTTP '+r.status));
  return data;
}
function showStep(step){
  $('private-login').hidden=step!=='login';
  $('private-mfa').hidden=step!=='mfa';
  $('private-signed').hidden=step!=='ready';
  if(step!=='ready')clearAllocationV74();else allocationChoicesV74();
  if(step!=='ready'){valueBridgeRequestV73++;const bridge=$('private-value-output-v73');if(bridge)bridge.textContent='';}
  $('private-status').textContent=step==='ready'?'Private · Signed in with MFA':
    step==='mfa'?'Private · Verification required':'Private · Sign in required';
}
function clearMFA(){
  mfaFactorId=null;
  $('private-mfa-code').value='';
  $('private-mfa-qr').removeAttribute('src');
  $('private-mfa-qr-wrap').hidden=true;
  $('private-mfa-setup-actions').hidden=true;
}
async function handleAuthState(state){
  if(state.signed_in){clearMFA();showStep('ready');await loadState();privateTab('decision');privatePeers();return;}
  if(!state.mfa_required){clearMFA();showStep('login');return;}
  showStep('mfa');
  if(state.mfa_setup){
    $('private-mfa-title').textContent='Set up your authenticator';
    $('private-mfa-instructions').textContent='Scan this private QR code in an authenticator app, then enter its six-digit code.';
    if(!mfaFactorId){$('private-mfa-setup-actions').hidden=false;}
    // Enrollment is a user action, never a GET/session side effect. Keep any
    // existing QR visible during an in-progress enrollment in this tab.
  }else{
    clearMFA();
    const factors=await api('auth/mfa/factors');
    mfaFactorId=factors.factor_id;
    $('private-mfa-title').textContent='Verify your authenticator';
    $('private-mfa-instructions').textContent='Enter the current code from your enrolled authenticator app.';
  }
}
async function loadState(){
  clearAllocationV74();
  clearResearchOSV90();
  clearGuideV79();
  const d=await api('private/state');privateState=d.portfolio;version=d.version;
  quoted={}; // Never carry fictional quotes across a private session.
  const symbols=Object.keys(privateState.holdings || {});
  if(symbols.length){
    try{const q=await api('private/quotes?symbols='+encodeURIComponent(symbols.join(',')));
      for(const item of q.quotes) quoted[item.symbol]=item;
    }catch(e){message('Portfolio loaded, but market prices are unavailable: '+e.message);}
  }
  render();
}
function render(){
  if(!privateState)return;
  const holdings=privateState.holdings||{};let valued=0, incomplete=false;
  const rows=Object.entries(holdings).map(([sym,qty])=>{
    const q=quoted[sym],v=q?qty*q.price:null;
    if(v===null)incomplete=true;else valued+=v;
    return '<tr><td>'+safe(M.bySymbol[sym]?.name||sym)+' ('+safe(sym)+')</td><td>'+Number(qty).toFixed(6)+'</td><td>'+
        (q?usd(q.price):'Unavailable')+'</td><td>'+(v===null?'Unavailable':usd(v))+'</td><td>'+
        (q?safe(q.venue)+' · '+safe(q.timestamp):'—')+'</td></tr>';
  });
  $('private-cash').textContent=usd(privateState.cash);
  $('private-invested').textContent=incomplete?'Incomplete':usd(valued);
  $('private-total').textContent=incomplete?'Incomplete':usd(privateState.cash+valued);
  $('private-positions').innerHTML='<div class="table-wrap"><table><thead><tr><th>Investment</th><th>Units</th><th>Observed price</th><th>Value</th><th>Source / time</th></tr></thead><tbody>'+
    (rows.join('')||'<tr><td colspan="5">No virtual holdings yet.</td></tr>')+'</tbody></table></div>';
  $('private-watchlist').textContent=(privateState.watchlist||[]).join(', ')||'None';
  const entries=Object.entries(holdings),worth=privateState.cash+valued;
  $('private-concentration').innerHTML=entries.length?entries.map(([symbol,units])=>{const weight=quoted[symbol]?units*quoted[symbol].price/worth:null;return '<div class="row"><span>'+safe(symbol)+'</span><strong>'+(weight===null?'Quote unavailable':percent(weight))+'</strong></div>';}).join(''):'No virtual holdings yet. Open Virtual trades to add one.';
  $('private-notes').innerHTML=(privateState.notes||[]).map((n,i)=>'<div class="saved-note"><div class="saved-note-body"><p>'+safe(n.text)+'</p><span class="tiny">'+safe(n.at||'Saved note')+'</span></div><button class="btn sm" type="button" data-note-delete="'+i+'" aria-label="Delete note '+(i+1)+'">Delete</button></div>').join('')||'<p class="tiny">No notes saved.</p>';
}
async function login(){
  message('Signing in…');
  try{
    const state=await api('auth/login',{email:$('private-email').value.trim(),password:$('private-password').value});
    $('private-password').value='';await handleAuthState(state);
    message(state.signed_in?'Signed in.':'Password accepted. Authenticator verification required.');
  }catch(e){message(e.message);}
}
async function startMFASetup(){
  message('Starting authenticator setup…');
  try{
    const enroll=await api('auth/mfa/enroll',{});
    mfaFactorId=enroll.factor_id;
    $('private-mfa-setup-actions').hidden=true;
    // Supabase provides SVG markup. Show it as an image, never inject HTML.
    $('private-mfa-qr').src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(enroll.qr_svg);
    $('private-mfa-qr-wrap').hidden=false;
    message('Scan the QR, then verify the current code. Keep this page open until setup is complete.');
  }catch(e){message(e.message);}
}
async function verifyMFA(){
  const code=$('private-mfa-code').value.trim();
  if(!/^[0-9]{6}$/.test(code)){message('Enter the six-digit code.');return;}
  message('Verifying authenticator…');
  try{
    const data=await api('auth/mfa/verify',{factor_id:mfaFactorId||undefined,code});
    await handleAuthState(data);message('Authenticator verified. Your private workspace is unlocked.');
  }catch(e){message(e.message);}
}
async function logout(){
  clearResearchOSV90();
  try{await api('auth/logout',{});}catch(_){ /* Clear visible private content regardless */ }
  ideasRunSequence++;ideaData=[];ideaFundamentals={};$('ideas-results').textContent='';$('ideas-run').disabled=false;clearDecisionBrief();
  clearImportedFrenchV87();clearGuideV79();clearMFA();showStep('login');privateState=null;quoted={};historyLoadSequence++;historySeries=null;closeAssetBrowser();researchSelection=[];$('private-symbol').value='';$('private-selected-asset').textContent='No investment selected';renderResearchSelection();
  optimizerResult=null;$('private-opt-export').disabled=true;$('private-opt-output').textContent='Load market history to begin.';$('private-opt-risk').textContent='';
  $('private-history-chart').textContent='Load a historical series to begin.';$('private-risk-results').textContent='';$('private-backtest-output').textContent='';$('private-valuation-output').textContent='';$('private-peers').textContent='';$('private-concentration').textContent='';$('private-positions').textContent='';
  $('private-wf-output').textContent='Load price history in Market data to begin.';$('private-wf-export').disabled=true;walkforwardResult=null;clearV66Walkforward();clearV66Forecast();
  $('private-fc-output').textContent='Load SEC statements for a selected company first.';
  $('private-total').textContent='—';$('private-invested').textContent='—';
  $('private-cash').textContent='—';$('private-notes').textContent='';valuationCompanies={};$('private-valuation-company').value='';$('private-valuation-selected').textContent='No company selected';message('Signed out.');privateTab('home');
}
async function currentQuote(){
  message('Retrieving private market observation…');
  const symbol=$('private-symbol').value.trim().toUpperCase();
  if(!symbol){message('Choose an investment with Browse investments first.');return;}
  try{
    const r=await api('private/quotes?symbols='+encodeURIComponent(symbol));
    const q=r.quotes[0];quoted[symbol]=q;
    $('private-quote').textContent=usd(q.price)+' · '+q.venue+' · '+q.timestamp+' (last trade, not executable price)';
    message('Quote loaded.');if(privateState)render();
  }catch(e){$('private-quote').textContent='Unavailable';message(e.message);}
}
async function trade(){
  if(!privateState){message('Sign in first.');return;}
  if(!$('private-symbol').value){message('Choose an investment before trading.');return;}
  message('Validating virtual trade…');
  try{
    const r=await api('private/trade',{symbol:$('private-symbol').value.trim().toUpperCase(),side:$('private-side').value,
      amount:$('private-amount').value,expected_version:version});
    privateState=r.portfolio;version=r.version;await loadState();
    message('Virtual transaction recorded. No brokerage order sent.');
  }catch(e){message(e.message);}
}
async function addNote(){
  if(!privateState)return;
  const t=$('private-note').value.trim();if(!t)return;
  const notes=[{text:t,at:new Date().toISOString(),symbol:$('private-symbol').value},...(privateState.notes||[])].slice(0,100);
  try{
    const d=await api('private/notes',{expected_version:version,watchlist:privateState.watchlist||[],notes});
    privateState=d.portfolio;version=d.version;$('private-note').value='';render();message('Private note saved.');
  }catch(e){message(e.message);}
}
async function deleteNote(index){
 if(!privateState || !Number.isInteger(index))return;
 const previous=privateState.notes||[];
 if(index<0||index>=previous.length)return;
 if(!window.confirm('Delete this saved research note? This cannot be undone.'))return;
 const notes=previous.filter((_,i)=>i!==index);
 try{
  const d=await api('private/notes',{expected_version:version,watchlist:privateState.watchlist||[],notes});
  privateState=d.portfolio;version=d.version;render();message('Selected note deleted.');
 }catch(e){message('Note was not deleted: '+e.message);}
}
$('private-notes').addEventListener('click',e=>{
 const button=e.target.closest('[data-note-delete]');
 if(button&&$('private-notes').contains(button))deleteNote(Number(button.dataset.noteDelete));
});
async function checkSession(){
  try{const s=await api('auth/session');await handleAuthState(s);}
  catch(e){message('Private authentication needs attention: '+e.message);}
}
function updateMode(){
 // Public page labels belong to app.js navigation; never overwrite them.
 const active=document.querySelector('.tabpage.active')?.id==='page-private';
 if(!active)return;
 const badge=document.querySelector('.topbar .badge');
 if(badge)badge.textContent='PRIVATE WORKSPACE';
 const eyebrow=document.querySelector('.topbar .eyebrow');
 if(eyebrow)eyebrow.textContent='Your portfolio · Personal use';
}
$('private-login-submit').addEventListener('click',login);
$('private-mfa-submit').addEventListener('click',verifyMFA);
$('private-mfa-start').addEventListener('click',startMFASetup);
$('private-mfa-logout').addEventListener('click',logout);
$('private-logout').addEventListener('click',logout);
$('private-quote-submit').addEventListener('click',currentQuote);
$('private-trade-submit').addEventListener('click',trade);
$('private-note-submit').addEventListener('click',addNote);
document.addEventListener('click',e=>{const b=e.target.closest('[data-page],[data-go]');if(b){queueMicrotask(updateMode);if(b.dataset.page==='private')checkSession();}});
// Investment names come from private Alpaca asset discovery after MFA.
// Do not contact the private API from the public-only pages.
/* Private asset directory: click-to-select. Name search is optional. */
function renderResearchSelection(){
 const target=$('private-history-selection');
 refreshResearchOSChoicesV90();
 $('private-history-symbols').value=researchSelection.join(',');
 if(!researchSelection.length){target.textContent='Choose investments to compare.';return;}
 target.innerHTML=researchSelection.map(symbol=>'<button type="button" class="asset-chip" data-research-remove="'+safe(symbol)+'" aria-label="Remove '+safe(symbol)+'">'+safe(assetNames[symbol]||symbol)+' ('+safe(symbol)+') ×</button>').join('');
}
function closeAssetBrowser(){
 browserRequest++;
 const dialog=$('private-asset-browser');
 if(dialog)dialog.hidden=true;
}
async function openAssetBrowser(mode){
 if(!privateState){message('Sign in and verify your authenticator first.');return;}
 browserState.mode=mode;
 browserState.category='popular';browserState.letter='';browserState.query='';browserState.page=0;
 $('asset-browser-search').value='';
 $('private-asset-browser').hidden=false;
 $('asset-browser-letters').innerHTML=['All',...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'].map(letter=>'<button type="button" data-asset-letter="'+(letter==='All'?'':letter)+'">'+letter+'</button>').join('');
 await loadBrowserPage();
 $('asset-browser-close').focus();
}
function browserParams(){
 return 'private/assets?'+new URLSearchParams({category:browserState.category,letter:browserState.letter,query:browserState.query,page:String(browserState.page)});
}
async function loadBrowserPage(){
 const id=++browserRequest;
 $('asset-browser-status').textContent='Loading investments…';
 $('asset-browser-results').textContent='';
 try{
  const data=await api(browserParams());
  if(id!==browserRequest||$('private-asset-browser').hidden||!privateState)return;
  browserState.pages=data.pages;
  $('asset-browser-status').textContent=data.total+' available investments · '+data.source;
  $('asset-browser-results').innerHTML=data.items.length?data.items.map(a=>'<button class="picker-item" type="button" data-asset-select="'+safe(a.symbol)+'" data-asset-kind="'+safe(a.asset_class)+'" data-asset-name="'+safe(a.name)+'"><strong>'+safe(a.name)+'</strong><span>'+safe(a.symbol)+' · '+safe(a.exchange||a.asset_class)+'</span></button>').join(''):'<p>No investments found for this filter. Choose another letter or category.</p>';
  $('asset-browser-page').textContent='Page '+(data.page+1)+' of '+data.pages;
  $('asset-browser-prev').disabled=!data.has_previous;
  $('asset-browser-next').disabled=!data.has_next;
  document.querySelectorAll('[data-asset-category]').forEach(b=>b.classList.toggle('active',b.dataset.assetCategory===browserState.category));
  document.querySelectorAll('[data-asset-letter]').forEach(b=>b.classList.toggle('active',b.dataset.assetLetter===browserState.letter));
 }catch(e){if(id===browserRequest)$('asset-browser-status').textContent=e.message;}
}
function chooseAsset(symbol,name,kind){
 if(!privateState)return;
 assetNames[symbol]=name;
 if(browserState.mode==='ideas'){
  if(ideaChoose(symbol,name,kind))closeAssetBrowser();
  return;
 }
 if(browserState.mode==='valuation'){
  if(kind==='crypto'){message('Crypto assets do not have SEC corporate financial statements.');return;}
  $('private-valuation-company').value=symbol;
  $('private-valuation-selected').textContent=name+' ('+symbol+')';
   valueBridgeRequestV73++;$('private-value-output-v73').textContent='';
  $('private-valuation-output').textContent='Select Run scenario to load available SEC filings.';
  $('private-fc-output').textContent='Load SEC statements for the newly selected company first.';clearV66Forecast();
  message('Selected '+name+'. SEC statements will be checked when you run the scenario.');
 }else if(browserState.mode==='trade'){
  $('private-symbol').value=symbol;
  $('private-selected-asset').textContent=name+' ('+symbol+')';
  $('private-quote').textContent='Get market price to inspect the current observation.';
  message('Selected '+name+'. No trade has been placed.');
 }else{
  if(!researchSelection.includes(symbol)){
   if(researchSelection.length>=5){message('You can compare up to five investments. Remove one first.');return;}
   researchSelection.push(symbol);
  }
  renderResearchSelection();invalidateResearchHistory('Selection changed. Load the updated historical series first.');
  message('Added '+name+' to your historical research selection.');
 }
 closeAssetBrowser();
}
$('private-browse-trade').addEventListener('click',()=>openAssetBrowser('trade'));
$('private-browse-research').addEventListener('click',()=>openAssetBrowser('research'));
$('private-browse-valuation').addEventListener('click',()=>openAssetBrowser('valuation'));
$('asset-browser-close').addEventListener('click',closeAssetBrowser);
$('asset-browser-prev').addEventListener('click',()=>{if(browserState.page>0){browserState.page--;loadBrowserPage();}});
$('asset-browser-next').addEventListener('click',()=>{if(browserState.page+1<browserState.pages){browserState.page++;loadBrowserPage();}});
$('asset-browser-search').addEventListener('input',()=>{
 clearTimeout(browserDebounce);
 browserDebounce=setTimeout(()=>{browserState.query=$('asset-browser-search').value;browserState.page=0;loadBrowserPage();},220);
});
$('private-asset-browser').addEventListener('click',e=>{
 if(e.target.id==='private-asset-browser'){closeAssetBrowser();return;}
 const cat=e.target.closest('[data-asset-category]');
 if(cat){browserState.category=cat.dataset.assetCategory;browserState.letter='';browserState.page=0;loadBrowserPage();return;}
 const letter=e.target.closest('[data-asset-letter]');
 if(letter){browserState.letter=letter.dataset.assetLetter;browserState.page=0;loadBrowserPage();return;}
 const asset=e.target.closest('[data-asset-select]');
 if(asset){chooseAsset(asset.dataset.assetSelect,asset.dataset.assetName,asset.dataset.assetKind);}
});
$('private-history-selection').addEventListener('click',e=>{
 const b=e.target.closest('[data-research-remove]');
 if(!b)return;
 researchSelection=researchSelection.filter(s=>s!==b.dataset.researchRemove);
 renderResearchSelection();invalidateResearchHistory('Selection changed. Load the updated historical series first.');
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('private-asset-browser').hidden)closeAssetBrowser();});
renderResearchSelection();

/* V7.0 investment ideas are owner-only and never modify virtual holdings. */
const initialIdeas=[['AAPL','Apple'],['MSFT','Microsoft'],['NVDA','NVIDIA'],['GOOGL','Alphabet'],['AMZN','Amazon'],['JPM','JPMorgan Chase'],['WMT','Walmart'],['VOO','Vanguard S&P 500 ETF']];
let ideaUniverse=initialIdeas.map(x=>x[0]),ideaData=[],ideaFundamentals={},ideasRunSequence=0,ideaSource='';
for(const [s,n] of initialIdeas)assetNames[s]=n;
function ideaStatus(value){$('ideas-status').textContent=value;}
function ideaSelectionRender(){
 $('ideas-count').textContent=ideaUniverse.length+' selected (maximum 10)';
 $('ideas-selected').innerHTML=ideaUniverse.map(symbol=>'<button type="button" class="asset-chip" data-ideas-remove="'+safe(symbol)+'">'+safe(assetNames[symbol]||symbol)+' ('+safe(symbol)+') ×</button>').join('')||'No investments selected.';
}
function invalidateIdeaResults(){ideasRunSequence++;ideaData=[];ideaFundamentals={};ideaSource='';$('ideas-results').textContent='';clearDecisionBrief();ideaStatus('Selection changed. Compare investments to refresh the research ranking.');}
function ideaChoose(symbol,name,kind){
 if(kind==='crypto'){message('This stock and ETF screen does not compare 24/7 crypto trading with equity-session risk. Use Market data for cryptocurrency.');return false;}
 if(ideaUniverse.includes(symbol)){message(name+' is already in your shortlist.');return true;}
 if(ideaUniverse.length>=10){message('Choose up to ten investments. Remove one before adding another.');return false;}
 ideaUniverse.push(symbol);assetNames[symbol]=name;ideaSelectionRender();invalidateIdeaResults();message('Added '+name+' to your investment shortlist.');return true;
}
function ideaPct(n){return typeof n==='number'&&Number.isFinite(n)?(100*n).toFixed(1)+'%':'Unavailable';}
let ideaDecisionBrief=null;
function clearDecisionBrief(){
 ideaDecisionBrief=null;
 $('ideas-brief').hidden=true;
 $('ideas-brief-output').textContent='';
 $('ideas-brief-export').disabled=true;
}
function renderDecisionBrief(){
 clearDecisionCenterV84();
 if(!privateState||!ideaData.length){clearDecisionBrief();return;}
 const model=window.QFPrivateDecision;
 const brief=model.build(ideaData,$('ideas-lens').value,ideaFundamentals,privateState.holdings||{},quoted,privateState.cash);
 ideaDecisionBrief=brief;
 const top=brief.comparisons.slice(0,3);
 const paired=brief.correlations.pairs.filter(x=>x.value>=.8).slice(0,3);
 const selectedLens={balanced:'Balanced',growth:'Growth',defensive:'Risk-aware'}[brief.lens];
 const topCards=top.map(r=>'<div class="decision-tile"><span>RESEARCH PRIORITY '+r.position+'</span><strong>'+safe(assetNames[r.symbol]||r.symbol)+'</strong><span>'+safe(r.symbol)+' · '+r.score+'/100 score · rank '+r.rankRange[0]+'–'+r.rankRange[1]+' across perspectives</span><p class="tiny">'+safe(r.cautions.length?r.cautions.slice(0,2).join('; '):'No threshold flags triggered in this dataset')+'</p></div>').join('');
 const held=brief.comparisons.filter(x=>x.held);
 const heldSummary=held.length?held.map(x=>{const weight=x.concentration==null?'unavailable weight':ideaPct(x.concentration)+' of virtual account';return safe(x.symbol)+' ('+safe(weight)+')';}).join(', '):'No selected candidate overlaps your virtual holdings.';
 const corrSummary=paired.length?paired.map(p=>safe(p.a)+' / '+safe(p.b)+' ('+(p.value*100).toFixed(0)+'% historical daily-return correlation)').join('; '):'No pair above 0.80 among comparable histories.';
 const cautions=brief.warnings.map(x=>'<li>'+safe(x)+'</li>').join('');
 $('ideas-brief-output').innerHTML='<p class="tiny"><strong>'+safe(selectedLens)+' perspective · '+safe(ideaSource)+'</strong>. Relative rankings for the '+brief.selected.length+' selected securities; not predicted returns or trade recommendations.</p>'+
  '<div class="decision-grid">'+topCards+'</div>'+
  '<h4>Historical correlation between candidates</h4><p class="tiny">'+corrSummary+' '+(brief.correlations.notAligned?' '+brief.correlations.notAligned+' pair(s) omitted because dates did not match.':'')+'</p>'+
  '<h4>Existing virtual portfolio exposure</h4><p class="tiny">'+heldSummary+' '+safe(brief.portfolio.note)+'</p>'+
  '<h4>Before using real money</h4><ul class="tiny"><li>Compare the current market price with a defensible business valuation; SEC FCF proxies alone are not per-share values.</li><li>Check earnings, competitive risks, sector exposure, taxes, fees, personal time horizon, and potential loss of principal.</li>'+cautions+'</ul>';
 $('ideas-brief').hidden=false;
 $('ideas-brief-export').disabled=false;
}
function renderIdeas(){
 if(!ideaData.length){$('ideas-results').textContent='No comparable observations were returned.';clearDecisionBrief();return;}
 const mode=$('ideas-lens').value;
 const ordered=window.QFPrivateIdeas.rank(ideaData,mode);
 const rows=ordered.map((x,i)=>{
  const m=x.metrics,sec=ideaFundamentals[x.symbol];
  const fundamentalsText=sec?'<p class="ideas-brief">SEC reported context: revenue growth '+ideaPct(sec.revenueGrowth)+', FCF / revenue '+ideaPct(sec.fcfMargin)+' · fiscal end '+safe(sec.fiscalEnd||'unavailable')+'</p>':'<p class="ideas-brief">SEC company fundamentals: unavailable or not comparable for this security.</p>';
  const why=x.notes.map(n=>'<li>'+safe(n)+'</li>').join('');
  return '<article class="ideas-card"><div class="row"><div><span class="eyebrow">RESEARCH PRIORITY '+(i+1)+'</span><h3>'+safe(assetNames[x.symbol]||x.symbol)+' <span class="tiny">'+safe(x.symbol)+'</span></h3></div><div><div class="ideas-score">'+x.score+'<span class="tiny">/100</span></div><span class="tiny">Heuristic score</span></div></div>'+
   '<div class="ideas-meta"><span>Period price return: '+ideaPct(m.periodReturn)+'</span><span>Recent 63-session return: '+ideaPct(m.quarterReturn)+'</span><span>Annualized volatility: '+ideaPct(m.annualVol)+'</span><span>Maximum drawdown: '+ideaPct(m.maxDrawdown)+'</span></div>'+
   '<ul class="ideas-brief">'+why+'</ul>'+fundamentalsText+'<div class="controls"><button class="btn sm" type="button" data-ideas-valuation="'+safe(x.symbol)+'">Review SEC valuation</button><button class="btn sm" type="button" data-ideas-trade="'+safe(x.symbol)+'">Inspect virtual trade</button></div></article>';
 }).join('');
 $('ideas-results').innerHTML='<div class="notice">'+safe(ideaSource)+' · Price-only returns; no dividends, future forecasts, or current executable quote. A 100/100 score is not a 100% success probability. SEC figures are context and do not affect this market-risk ranking.</div>'+rows;
 renderDecisionBrief();
}
async function compareIdeas(){
 if(!privateState){ideaStatus('Authenticate first.');return;}
 const selection=[...ideaUniverse];
 if(selection.length<2||selection.length>10){ideaStatus('Choose between 2 and 10 investments.');return;}
 const period=$('ideas-period').value,request=++ideasRunSequence,rows=[],sources=new Set(),dates=[];
 const chunks=[];
 for(let i=0;i<selection.length;i+=5)chunks.push(selection.slice(i,i+5));
 if(chunks.at(-1).length===1)chunks.at(-1).unshift(selection[0]);
 ideaData=[];ideaFundamentals={};$('ideas-results').textContent='';clearDecisionBrief();$('ideas-run').disabled=true;
 try{
  for(let i=0;i<chunks.length;i++){
   ideaStatus('Loading observed market history · group '+(i+1)+' of '+chunks.length+'…');
   const data=await api('private/history?symbols='+encodeURIComponent(chunks[i].join(','))+'&days='+period);
   if(!privateState||request!==ideasRunSequence)return;
   sources.add(data.source||'Alpaca private daily market bars');dates.push(data.as_of||'');
   for(const symbol of chunks[i]){
    if(rows.some(x=>x.symbol===symbol))continue;
    const prices=data.closes?.[symbol];
    if(!prices||prices.length<126)throw Error('Insufficient history for '+symbol+'. Choose another candidate.');
    rows.push({symbol,prices,dates:Array.isArray(data.dates)?data.dates.slice():null,annual:data.sessions_per_year});
   }
  }
  if(sources.size>1)throw Error('The selected groups used different market feeds. Reduce the shortlist so comparisons use one consistent source.');
  if(new Set(dates).size>1)throw Error('Historical observations have different as-of dates. Retry for comparable data.');
  ideaData=rows;ideaSource=[...sources][0]+' · as of '+dates[0];
  renderIdeas();
  ideaStatus('Compared '+rows.length+' investments using observed historical market data.');
  if($('ideas-sec').checked){
   const info=[];
   for(const x of rows){
    if(!privateState||request!==ideasRunSequence)return;
    if(['VOO','SPY','QQQ','VTI','IVV'].includes(x.symbol))continue;
    try{
     const sec=await api('private/sec/company?symbol='+encodeURIComponent(x.symbol));
     const view=window.QFPrivateIdeas.fundamentals(sec);
     if(view)ideaFundamentals[x.symbol]=view;
    }catch(_){info.push(x.symbol);}
   }
   if(!privateState||request!==ideasRunSequence)return;
   renderIdeas();
   ideaStatus('Market observations and available SEC fundamentals loaded. Missing SEC figures remain unavailable'+(info.length?' ('+info.length+' issuer(s) unavailable).':'.'));
  }
 }catch(e){if(request===ideasRunSequence){ideaData=[];$('ideas-results').textContent='';clearDecisionBrief();ideaStatus('Unable to compare: '+e.message);}}
 finally{if(request===ideasRunSequence)$('ideas-run').disabled=false;}
}
$('ideas-brief-export').addEventListener('click',()=>{
 if(!privateState||!ideaDecisionBrief){message('Load your current investment research before exporting.');return;}
 const result=window.QFPrivateDecision.report(ideaDecisionBrief,ideaSource,$('ideas-period').value);
 downloadResearchJSON('quantforge-investment-decision-brief.json',result);
 message('Historical decision brief downloaded. Your account positions and raw market prices were excluded.');
});
$('ideas-browse').addEventListener('click',()=>openAssetBrowser('ideas'));
$('ideas-reset').addEventListener('click',()=>{ideaUniverse=initialIdeas.map(x=>x[0]);ideaSelectionRender();invalidateIdeaResults();});
$('ideas-run').addEventListener('click',compareIdeas);
$('ideas-lens').addEventListener('change',()=>{if(ideaData.length)renderIdeas();});
$('ideas-period').addEventListener('change',invalidateIdeaResults);
$('ideas-sec').addEventListener('change',invalidateIdeaResults);
$('ideas-selected').addEventListener('click',e=>{const b=e.target.closest('[data-ideas-remove]');if(!b)return;ideaUniverse=ideaUniverse.filter(x=>x!==b.dataset.ideasRemove);ideaSelectionRender();invalidateIdeaResults();});
$('ideas-results').addEventListener('click',e=>{
 const valuation=e.target.closest('[data-ideas-valuation]'),trade=e.target.closest('[data-ideas-trade]');
 if(!privateState||(!valuation&&!trade))return;
 const sym=(valuation||trade).dataset[valuation?'ideasValuation':'ideasTrade'];
 if(valuation){$('private-valuation-company').value=sym;$('private-valuation-selected').textContent=(assetNames[sym]||sym)+' ('+sym+')';$('private-valuation-output').textContent='Run scenario to load reported SEC filings.';clearV66Forecast();privateTab('valuation');}
 else{$('private-symbol').value=sym;$('private-selected-asset').textContent=(assetNames[sym]||sym)+' ('+sym+')';$('private-quote').textContent='Retrieve a private observation before considering a virtual transaction.';privateTab('trade');}
});
ideaSelectionRender();

/* V6: authenticated research tools. No Alpaca credentials or private data in public code. */
let optimizerResult=null;
let historySeries=null;
let historyLoadSequence=0;
function researchCompanyLabel(symbol){return (assetNames[symbol]||symbol)+' ('+symbol+')';}
function refreshResearchContext(){
 const chosen=$('private-research-selected'),loaded=$('private-research-loaded'),status=$('private-research-state');
 if(!chosen||!loaded||!status)return;
 chosen.textContent=researchSelection.length?researchSelection.length+' selected: '+researchSelection.map(researchCompanyLabel).join(' · '):'None selected';
 const d=historySeries;
 if(d&&Array.isArray(d.symbols)&&Array.isArray(d.dates)&&d.dates.length){
  loaded.textContent=d.symbols.length+' loaded: '+d.symbols.map(researchCompanyLabel).join(' · ')+
   ' | '+d.dates[0]+' to '+d.dates[d.dates.length-1];
  status.textContent='History loaded: Optimization, Backtests and Walk-forward use these '+d.symbols.length+' investments. Changing the selection or period requires reloading.';
 }else{
  loaded.textContent='No historical data loaded';
  status.textContent=researchSelection.length>=2?'Not loaded yet. Click Load market history before running the analysis tools.':'Choose 2–5 investments and load history to begin.';
 }
}
function invalidateResearchHistory(reason){
 if(!researchOSInternalLoadV90)clearResearchOSV90();
 clearGuideV79();
 historyLoadSequence++;
 historySeries=null;optimizerResult=null;walkforwardResult=null;clearV66Walkforward();
 $('private-opt-export').disabled=true;$('private-wf-export').disabled=true;
 $('private-history-source').textContent='';
 $('private-history-chart').textContent='Load market history for the selected investments.';
 $('private-risk-results').textContent='';$('private-opt-risk').textContent='';
 $('private-opt-output').textContent=reason;$('private-backtest-output').textContent='';
 $('private-wf-output').textContent=reason;
 refreshResearchContext();
}
const finite=n=>typeof n==='number'&&Number.isFinite(n);
const percent=n=>finite(n)?(n*100).toFixed(2)+'%':'Unavailable';
const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
function sampleStdev(a){if(a.length<2)return 0;const m=mean(a);return Math.sqrt(a.reduce((x,y)=>x+(y-m)*(y-m),0)/(a.length-1));}
function maxDD(values){let high=0,deep=0;for(const v of values){high=Math.max(high,v);if(high)deep=Math.min(deep,v/high-1);}return deep;}
function displayTable(headers,rows){return '<div class="table-wrap"><table><thead><tr>'+headers.map(h=>'<th>'+safe(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(v=>'<td>'+safe(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function privateTab(tab){
 if(tab==='decision')clearDecisionCenterV84();
 if(tab==='decision')refreshCandidateChoicesV85();
 if(tab==='decision')refreshResearchOSChoicesV90();
 if(tab==='settings')renderConnectedBriefV93();
 if(tab==='lab')refreshConnectedResearchV93();
 const shared=$('private-research-dataset');if(shared)shared.hidden=!['research','optimization','backtest','walkforward'].includes(tab);
 refreshResearchContext();
 document.querySelectorAll('[data-private-view]').forEach(p=>p.hidden=p.dataset.privateView!==tab);
 document.querySelectorAll('.private-nav [data-private-tab]').forEach(b=>b.classList.toggle('active',b.dataset.privateTab===tab));
 const activeButton=document.querySelector('.private-nav [data-private-tab].active');const group=typeof activeButton?.closest==='function'?activeButton?.closest('details.private-nav-group'):null;if(group)group.open=true;
}
function normalizedSeries(series){
 const rows=series.symbols.map(s=>series.closes[s]);
 if(rows.some(a=>!Array.isArray(a)||a.length!==series.dates.length||a.some(x=>!finite(x)||x<=0)))throw Error('Incomplete historical price series.');
 return rows;
}
function svgIndexChart(series){
 const rows=normalizedSeries(series);const n=series.dates.length;
 const tracks=rows.map(a=>a.map(x=>x/a[0]*100));
 const all=tracks.flat();let lo=Math.min(...all),hi=Math.max(...all);const pad=(hi-lo)||1;lo-=pad*.08;hi+=pad*.08;
 const colors=['#0a6658','#c78a39','#386eac','#874ba0','#b85850'];
 const plots=tracks.map((track,i)=>{
  const points=track.map((v,k)=>`${(15+k*570/(n-1)).toFixed(2)},${(205-(v-lo)/(hi-lo)*185).toFixed(2)}`).join(' ');
  return `<polyline fill="none" stroke="${colors[i%colors.length]}" stroke-width="2" points="${points}"/>`;
 }).join('');
 return '<svg viewBox="0 0 600 245" role="img" aria-label="Historical prices indexed to 100; '+safe(series.symbols.join(', '))+'"><line x1="14" y1="210" x2="588" y2="210" stroke="#cad9d2"/>'+plots+'<text x="14" y="235" fill="#5f746e" font-size="11">'+safe(series.dates[0])+'</text><text x="475" y="235" fill="#5f746e" font-size="11">'+safe(series.dates[n-1])+'</text></svg>'+
 '<div class="controls tiny">'+series.symbols.map((s,i)=>'<span style="color:'+colors[i%colors.length]+'">● '+safe(s)+'</span>').join(' ')+'</div>';
}
function equalReturns(series){
 const rows=normalizedSeries(series), len=series.dates.length;const changes=[];
 for(let t=1;t<len;t++)changes.push(mean(rows.map(a=>a[t]/a[t-1]-1)));
 return changes;
}
function privateRisk(series){
 const ret=equalReturns(series),wealth=[100];for(const r of ret)wealth.push(wealth.at(-1)*(1+r));
 const sorted=[...ret].sort((a,b)=>a-b),bottom=Math.max(1,Math.ceil(.05*sorted.length));
 const var95=Math.max(0,-sorted[bottom-1]),es=Math.max(0,-mean(sorted.slice(0,bottom)));
 const annual=series.sessions_per_year===365?365:252;
 const sdev=sampleStdev(ret)*Math.sqrt(annual),total=wealth.at(-1)/wealth[0]-1;
 const rows=[['Aligned observed days',String(ret.length)],['Annualization convention',annual+' observations/year'],['Equal-weight daily average return',percent(mean(ret))],['Annualized historical volatility',percent(sdev)],['5% historical daily VaR',percent(var95)],['5% historical daily expected shortfall',percent(es)],['Worst historical drawdown',percent(maxDD(wealth))],['Compounded indexed change',percent(total)]];
 return '<h3 style="margin:18px 0 10px">Historical return statistics</h3>'+displayTable(['Measure','Result'],rows)+'<p class="tiny">Equal-weight daily return series with simple arithmetic returns. VaR/ES are empirical one-day historical statistics, not forward forecasts. Equity prices exclude dividends; mixed portfolios use common observed equity-session dates without filling crypto weekends.</p>';
}
function privateCrossAsset(series){
 const report=window.QFPrivateMultiMarket.analyze(series);
 const diagnostics=displayTable(['Investment','Asset class','Period change','Annualized volatility','Max drawdown','Worst aligned day'],report.assets.map(a=>[
  (assetNames[a.symbol]||a.symbol)+' ('+a.symbol+')',a.kind==='crypto'?'Cryptocurrency':'Stock / ETF',
  percent(a.observedChange),percent(a.annualVolatility),percent(a.maxDrawdown),percent(a.worstDay)
 ]));
 const stress=displayTable(['Hypothetical one-day event','Equal-weight impact'],report.stress.map(row=>[row.name,percent(row.change)]));
 return '<h3 style="margin:20px 0 8px">Multi-asset comparison</h3>'+diagnostics+
  '<h3 style="margin:20px 0 8px">What-if stress scenarios</h3>'+stress+
  '<p class="tiny">Stress events are user-independent fixed assumptions, not historical observations or likelihood estimates: broad shock = stocks −10%, crypto −20%; crypto selloff = crypto −35%; equity selloff = stocks −20%. Equal-weight one-day impact only, with no rebalancing, fees or volatility forecast. '+safe(report.calendar)+' · '+report.annual+' observations/year annualization.</p>';
}
async function loadHistory(){
 const raw=researchSelection.join(',');
 const syms=researchSelection;
 const period=$('private-history-days').value;
 if(syms.length<2||syms.length>5){message('Select 2–5 investments by name using Browse investments.');return;}
 invalidateResearchHistory('Loading market history…');
 const request=historyLoadSequence;
 message('Retrieving private market history…');
 try{
  const d=await api('private/history?symbols='+encodeURIComponent(raw)+'&days='+encodeURIComponent(period));
  // A pending fetch may finish after sign-out or a changed investment selection.
  if(!privateState || researchSelection.join(',')!==raw || $('private-history-days').value!==period || request!==historyLoadSequence)return;
  optimizerResult=null;$('private-opt-export').disabled=true;
  $('private-opt-output').textContent='Historical observations loaded for portfolio calculations.';
  $('private-opt-risk').textContent='Risk diagnostics appear after an allocation is calculated.';
  historySeries=d;walkforwardResult=null;$('private-wf-export').disabled=true;$('private-wf-output').textContent='History loaded. Run walk-forward evaluation when ready.';refreshResearchContext();
  $('private-history-chart').innerHTML=svgIndexChart(d);
  $('private-history-source').textContent=d.source+' · through '+d.as_of+' · '+d.calendar;
  $('private-risk-results').innerHTML=privateRisk(d)+privateCrossAsset(d);
  message('Historical market research loaded.');
 }catch(e){if(request!==historyLoadSequence)return;optimizerResult=null;$('private-opt-export').disabled=true;historySeries=null;walkforwardResult=null;$('private-wf-export').disabled=true;$('private-wf-output').textContent='Load history again to continue.';message(e.message);$('private-history-chart').textContent='Market history unavailable.';$('private-risk-results').textContent='';$('private-backtest-output').textContent='';refreshResearchContext();}
}
function wealthStats(values){let out=values.at(-1)/values[0]-1;return [percent(out),percent(maxDD(values))];}
function privateBacktest(){
 if(!historySeries){message('Load historical market research first.');privateTab('research');return;}
 const dollars=Number($('private-test-capital').value),fee=Number($('private-test-fee').value)/10000;
 if(!finite(dollars)||dollars<100||dollars>1_000_000||!finite(fee)||fee<0||fee>.01){message('Check starting balance and fee.');return;}
 const d=historySeries,a=normalizedSeries(d),N=a.length,T=d.dates.length;
 const holdUnits=a.map(b=>dollars/N/b[0]);const hold=[];
 for(let t=0;t<T;t++)hold.push(holdUnits.reduce((v,u,k)=>v+u*a[k][t],0));
 let units=[...holdUnits],equity=[],paid=0;
 for(let t=0;t<T;t++){
  let values=units.map((u,k)=>u*a[k][t]),total=values.reduce((x,y)=>x+y,0);
  if(t>0&&d.dates[t].slice(0,7)!==d.dates[t-1].slice(0,7)){
   const target=total/N;
   const turnover=values.reduce((s,v)=>s+Math.abs(v-target),0);
   const commission=turnover*fee;paid+=commission;
   const newEach=(total-commission)/N;
   units=units.map((u,k)=>newEach/a[k][t]);total-=commission;
  }
  equity.push(total);
 }
 const holdStats=wealthStats(hold),rebalanceStats=wealthStats(equity);
 $('private-backtest-output').innerHTML=displayTable(['Measure','Buy & hold','Monthly rebalance'],[
  ['Ending virtual capital',usd(hold.at(-1)),usd(equity.at(-1))],
  ['Period return',holdStats[0],rebalanceStats[0]],
  ['Maximum drawdown',holdStats[1],rebalanceStats[1]],
  ['Rebalancing costs',usd(0),usd(paid)]
 ])+'<p class="tiny">Equal-weight initial allocation, monthly close rebalances, '+safe($('private-test-fee').value)+' bps on gross dollar turnover. No slippage, dividends, taxes or corporate-action forecasts. Historical illustration only; no brokerage orders.</p>';
 message('Backtest comparison calculated.');
}
async function privateValuation(){
 clearGuideV79();
 const symbol=$('private-valuation-company').value;
 if(!symbol){message('Choose a company with Browse companies first.');return;}
 $('private-valuation-output').textContent='Loading available SEC annual filings…';
 let company=valuationCompanies[symbol];
 if(!company){
  try{
   company=await api('private/sec/company?symbol='+encodeURIComponent(symbol));
   if(!privateState)return;
   valuationCompanies[symbol]=company;
  }catch(e){$('private-valuation-output').textContent='No comparable SEC figures were loaded. '+e.message;message(e.message);return;}
 }
 const metrics=company.annual?.[0]?.metrics||{},raw=metrics.free_cash_flow_usd;
 const companyName=company.name+' ('+company.symbol+')';
 const rows=[['Issuer',companyName],['SEC annual period ending',company.annual?.[0]?.fiscal_end||'Unavailable'],
 ['Revenue',metrics.revenue_usd==null?'Unavailable':usd(metrics.revenue_usd)],
 ['Operating income',metrics.operating_income_usd==null?'Unavailable':usd(metrics.operating_income_usd)],
 ['Operating cash flow',metrics.operating_cash_flow_usd==null?'Unavailable':usd(metrics.operating_cash_flow_usd)],
 ['Cash PP&E purchases',metrics.capex_usd==null?'Unavailable':usd(metrics.capex_usd)],
 ['Free-cash-flow proxy',raw==null?'Unavailable':usd(raw)]];
 const source=/^https:\/\/data\.sec\.gov\/api\/xbrl\/companyfacts\/CIK[0-9]{10}\.json$/.test(company.source_url||'')?company.source_url:'';
 const provenance='<p class="tiny">Source: '+safe(company.source||'SEC EDGAR')+' · Data cutoff: '+safe(company.as_of||'unknown')+
  ' · CIK '+safe(company.cik||'unknown')+' · SEC Company Facts / 10-K annual disclosures. '+(source?'<a href="'+safe(source)+'" target="_blank" rel="noopener noreferrer">Inspect SEC facts</a>':'')+'</p>';
 let output='<h3 style="margin:17px 0 10px">Reported financials</h3>'+displayTable(['Measure','Reported / derived'],rows)+provenance;
 const fcf=Number(raw),rate=Number($('private-valuation-wacc').value)/100,
  growth=Number($('private-valuation-growth').value)/100,
  terminal=Number($('private-valuation-terminal').value)/100;
 if(raw==null||!finite(fcf)||fcf<=0){
  output+='<p class="notice">A positive comparable cash-flow proxy is unavailable for this issuer. The reported values above remain useful, but no valuation scenario was calculated.</p>';
 }else if(![rate,growth,terminal].every(finite)||rate<=terminal||rate<.02||rate>.30||growth<-.30||growth>.4||terminal<-.05||terminal>.08){
  output+='<p class="error">Check assumptions: discount rate must exceed terminal growth and all values must remain within their limits.</p>';
 }else{
  let discounted=0,fcfNext=fcf;
  for(let year=1;year<=5;year++){fcfNext*=1+growth;discounted+=fcfNext/(1+rate)**year;}
  const terminalValue=(fcfNext*(1+terminal)/(rate-terminal))/(1+rate)**5;
  output+='<h3 style="margin:18px 0 10px">Hypothetical sensitivity</h3>'+displayTable(['Calculation','Scenario'],[
   ['Reported-period FCF proxy',usd(fcf)],['Five-year discounted proxy',usd(discounted)],
   ['Discounted terminal component',usd(terminalValue)],
   ['Illustrative present value',usd(discounted+terminalValue)]])+
   '<p class="tiny">FCF proxy = operating cash flow minus cash PP&E purchases, not unlevered FCFF. This is not per-share fair value. Debt, cash, taxes, other adjustments, and terminal-model uncertainty are excluded.</p>';
 }
 // Do not allow late fetches from a prior selection to replace the current issuer.
 if($('private-valuation-company').value!==symbol)return;
 $('private-valuation-output').innerHTML=output;
 $('private-fc-output').textContent='Statements loaded. Set projection assumptions and run a forecast.';clearV66Forecast();
 privatePeers();message('SEC filings loaded for '+companyName+'.');
}
function privatePeers(){
 const rows=Object.values(valuationCompanies).slice(-8).map(company=>{
  const m=company.annual?.[0]?.metrics||{},rev=m.revenue_usd,inc=m.operating_income_usd;
  return [company.name+' ('+company.symbol+')',company.annual?.[0]?.fiscal_end||'Unavailable',
   rev==null?'Unavailable':usd(rev),inc==null||!rev?'Unavailable':percent(inc/rev),
   m.free_cash_flow_usd==null?'Unavailable':usd(m.free_cash_flow_usd)];
 });
 $('private-peers').innerHTML=rows.length?displayTable(['Company','Fiscal year end','Revenue','Operating margin','FCF proxy'],rows)+
  '<p class="tiny">Selected-company comparisons use different fiscal periods and accounting practices; not sector-normalized rankings.</p>':
  '<p class="tiny">Company comparison values appear after the corresponding SEC annual scenarios are loaded.</p>';
}
async function changeCapital(){
 if(!privateState)return;
 const action=$('private-capital-action').value,amount=$('private-capital-amount').value;
 if(!Number.isFinite(Number(amount))||Number(amount)<1||Number(amount)>1_000_000){message('Enter virtual capital between $1 and $1,000,000.');return;}
 let confirmation='';
 if(action==='reset'){
  if(!window.confirm('Clear your virtual trades and positions? Private research notes will remain.'))return;
  confirmation=window.prompt('Type RESET to confirm resetting the virtual portfolio.','')||'';
  if(confirmation!=='RESET'){message('Reset cancelled.');return;}
 }
 try{
  const data=await api('private/capital',{action,amount,confirmation,expected_version:version});
  privateState=data.portfolio;version=data.version;await loadState();
  message('Virtual account updated. No real funds were moved.');privateTab('home');
 }catch(e){message(e.message);}
}

/* V6.3: purely historical owner-only optimization; never invokes /trade or /capital. */
function optPct(x){return typeof x==='number'&&Number.isFinite(x)?(100*x).toFixed(2)+'%':'Unavailable';}
function optSvgFrontier(points, equal, optimized){
 // A tight or degenerate volatility range is common when position caps bind.
 // Never divide by an arbitrary fallback denominator that pins the plot to the left.
 const candidates=[...points.map(p=>({risk:p.risk,mean:p.historicalMean,kind:'candidate'}))];
 if(equal)candidates.push({risk:equal.annualVolatility,mean:equal.annualHistoricalMean,kind:'equal'});
 if(optimized)candidates.push({risk:optimized.annualVolatility,mean:optimized.annualHistoricalMean,kind:'optimized'});
 if(!candidates.length||candidates.some(p=>!Number.isFinite(p.risk)||!Number.isFinite(p.mean))){
  return '<p class="tiny">Historical portfolio comparison is unavailable for these observations.</p>';
 }
 const xs=candidates.map(p=>p.risk),ys=candidates.map(p=>p.mean);
 const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
 const spanX=xmax-xmin,spanY=ymax-ymin;
 const dx=Math.max(spanX*1.18,0.006),dy=Math.max(spanY*1.18,0.015);
 const mx=(xmin+xmax)/2,my=(ymin+ymax)/2;
 const domainX=[mx-dx/2,mx+dx/2],domainY=[my-dy/2,my+dy/2];
 const left=80,right=565,top=27,bottom=219;
 const xscale=x=>left+(right-left)*(x-domainX[0])/dx;
 const yscale=y=>bottom-(bottom-top)*(y-domainY[0])/dy;
 const percent=x=>(100*x).toFixed(2)+'%';
 const xTicks=[domainX[0],mx,domainX[1]].map(t=>
  '<line x1="'+xscale(t).toFixed(2)+'" y1="'+top+'" x2="'+xscale(t).toFixed(2)+'" y2="'+bottom+'" stroke="#e5ece8"/>'+
  '<text x="'+xscale(t).toFixed(2)+'" y="240" text-anchor="middle" font-size="11" fill="#526a60">'+percent(t)+'</text>').join('');
 const yTicks=[domainY[0],my,domainY[1]].map(t=>
  '<line x1="'+left+'" y1="'+yscale(t).toFixed(2)+'" x2="'+right+'" y2="'+yscale(t).toFixed(2)+'" stroke="#e5ece8"/>'+
  '<text x="73" y="'+(yscale(t)+4).toFixed(2)+'" text-anchor="end" font-size="11" fill="#526a60">'+percent(t)+'</text>').join('');
 // Duplicate parameter settings may generate the same constrained weights.
 const distinct=[];
 for(const p of candidates.filter(p=>p.kind==='candidate')){
  if(!distinct.some(q=>Math.abs(p.risk-q.risk)<1e-9&&Math.abs(p.mean-q.mean)<1e-9))distinct.push(p);
 }
 const circles=distinct.map(p=>'<circle cx="'+xscale(p.risk).toFixed(2)+'" cy="'+yscale(p.mean).toFixed(2)+'" r="4" fill="#196c58"><title>Scenario · volatility '+percent(p.risk)+' · historical mean '+percent(p.mean)+'</title></circle>').join('');
 const special=candidates.filter(p=>p.kind!=='candidate').map(p=>
  '<circle cx="'+xscale(p.risk).toFixed(2)+'" cy="'+yscale(p.mean).toFixed(2)+'" r="6" fill="'+(p.kind==='equal'?'#d48b31':'#ffffff')+'" stroke="'+(p.kind==='equal'?'#b67628':'#135c4b')+'" stroke-width="2"><title>'+(p.kind==='equal'?'Equal-weight':'Selected optimized')+' · volatility '+percent(p.risk)+' · historical mean '+percent(p.mean)+'</title></circle>').join('');
 const near=spanX<0.0005;
 const note=near?'Candidate portfolios have almost identical volatility with these assets and weight constraints. The points may overlap.':
  'Dots represent in-sample portfolio candidates, not a predictive efficient frontier.';
 return '<div class="opt-frontier-chart"><svg viewBox="0 0 640 280" width="100%" role="img" aria-label="Annualized historical mean versus volatility for portfolio candidates">'+
  xTicks+yTicks+'<path d="M'+left+' '+top+' V'+bottom+' H'+right+'" fill="none" stroke="#849f92" stroke-width="1.5"/>'+
  circles+special+'<text x="322" y="265" text-anchor="middle" font-size="12" fill="#526a60">Annualized historical volatility</text>'+
  '<text x="80" y="15" font-size="12" fill="#526a60">Historical annual mean (not a forecast)</text></svg>'+
  '<p class="tiny">'+note+' Orange: equal-weight. Outlined: selected allocation.</p></div>';
}
function optimizationTable(res){
 const risks=res.optimized.riskContributions;
 return displayTable(['Investment','Equal weight','Optimized','Variance contribution'],res.symbols.map((sym,i)=>[
  (assetNames[sym]||sym)+' ('+sym+')',optPct(res.equalWeights[i]),optPct(res.chosen[i]),optPct(risks[i])]));
}
function optimizerDiagnostics(res){
 const eq=res.equal,op=res.optimized;
 const comparison=displayTable(['Measure','Equal-weight','Optimized'],[
  ['Annualized historical volatility',optPct(eq.annualVolatility),optPct(op.annualVolatility)],
  ['Historical arithmetic annual mean',optPct(eq.annualHistoricalMean),optPct(op.annualHistoricalMean)],
  ['Historical compounded change',optPct(eq.compoundChange),optPct(op.compoundChange)],
  ['Maximum drawdown',optPct(eq.maxDrawdown),optPct(op.maxDrawdown)],
  ['One-day 95% historical VaR',optPct(eq.dailyVaR),optPct(op.dailyVaR)],
  ['One-day 95% historical expected shortfall',optPct(eq.dailyES),optPct(op.dailyES)],
  ['Worst rolling five-session change',optPct(eq.worst5),optPct(op.worst5)],
  ['Worst rolling 20-session change',optPct(eq.worst20),optPct(op.worst20)],
  ['Effective number of holdings',eq.effectiveHoldings.toFixed(2),op.effectiveHoldings.toFixed(2)]
 ]);
 const matrix=displayTable(['Investment',...res.symbols],res.symbols.map((sym,i)=>[
  sym,...res.correlation[i].map(x=>x===null?'Unavailable':x.toFixed(3))]));
 return '<h3>Equal-weight versus optimized</h3>'+comparison+'<h3 style="margin:20px 0 8px">Historical correlation matrix</h3>'+matrix+
  '<h3 style="margin:20px 0 8px">In-sample risk–return trade-off</h3>'+optSvgFrontier(res.frontier, res.equal, res.optimized)+
  '<p class="tiny">All statistics use the same observed period. A portfolio selected using these data is in-sample; the displayed historical result is not an out-of-sample backtest. Daily rebalancing is assumed when compounding weighted returns. No dividends, borrow costs, slippage, or brokerage orders are included. Variance contributions may be negative for hedging assets.</p>';
}
function runOptimization(){
 clearGuideV79();
 if(!privateState){message('Sign in to run private portfolio research.');return;}
 if(!historySeries){message('Go to Market data and load 2–5 investments first.');privateTab('research');return;}
 $('private-opt-output').textContent='Calculating historical allocation…';
 try{
  const result=window.QFPrivateOptimizer.run(historySeries,{
   objective:$('private-opt-objective').value,maxWeight:Number($('private-opt-cap').value)});
  optimizerResult=result;
  $('private-opt-export').disabled=false;
  $('private-opt-output').innerHTML='<p class="tiny">'+safe(result.periodStart)+' to '+safe(result.periodEnd)+' · '+result.observations+' aligned return sessions · '+safe(result.source)+'</p>'+optimizationTable(result)+
   '<p class="tiny">Allocation constraints: no shorts or leverage, each position limited to '+optPct(result.maxWeight)+'. Weights sum to 100%. Calculations do not alter your virtual holdings.</p>';
  $('private-opt-risk').innerHTML=optimizerDiagnostics(result);
  message('Historical portfolio optimization completed; no transactions were placed.');
 }catch(e){optimizerResult=null;$('private-opt-export').disabled=true;$('private-opt-output').textContent=e.message;$('private-opt-risk').textContent='';message(e.message);}
}
function exportOptimization(){
 if(!privateState||!optimizerResult)return;
 const result=optimizerResult;
 const clean=s=>{let v=String(s).replace(/"/g,'""');if(/^[=+@\-]/.test(v))v="'"+v;return '"'+v+'"';};
 const head=['symbol','company','equal_weight','optimized_weight','variance_contribution','period_start','period_end','objective','price_source'];
 const lines=[head.join(',')];
 for(let i=0;i<result.symbols.length;i++){
  const sym=result.symbols[i];lines.push([sym,assetNames[sym]||sym,result.equalWeights[i],result.chosen[i],result.optimized.riskContributions[i],result.periodStart,result.periodEnd,result.objective,result.source].map(clean).join(','));
 }
 const blob=new Blob([lines.join('\r\n')+'\r\n'],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download='quantforge-private-optimized-allocations.csv';document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
 message('Historical allocation CSV exported locally. No data was uploaded.');
}
$('private-opt-run').addEventListener('click',runOptimization);
$('private-opt-export').addEventListener('click',exportOptimization);
for(const id of ['private-opt-objective','private-opt-cap'])$(id).addEventListener('change',()=>{optimizerResult=null;$('private-opt-export').disabled=true;$('private-opt-output').textContent='Settings changed. Calculate allocations to update the results.';$('private-opt-risk').textContent='';});


/* V6.5: SEC scenario projections and past-only walk-forward evaluations. */
let walkforwardResult=null;
/* V6.6: derived reports are ephemeral, not stored with virtual positions. */
let forecastResultV66=null,forecastDiagnosticsV66=null,walkforwardDiagnosticsV66=null;
/* V6.8: derived robustness scenarios are ephemeral and never alter saved portfolios. */
let robustnessResultV68=null;
function clearV66Walkforward(){
 walkforwardDiagnosticsV66=null;
 $('private-wf-diagnostics').hidden=true;
 $('private-wf-diagnostics-content').textContent='';
 $('private-wf-robustness-output').textContent='';
 $('private-wf-report').disabled=true;
 $('private-wf-robustness').disabled=true;
 robustnessResultV68=null;
 $('private-wf-v68-run').disabled=true;
 $('private-wf-v68-export').disabled=true;
 $('private-wf-v68-output').textContent='Run Walk-forward before sensitivity checks.';
}
function clearV66Forecast(){
 forecastResultV66=null;forecastDiagnosticsV66=null;
 $('private-fc-diagnostics').hidden=true;
 $('private-fc-diagnostics-content').textContent='';
 $('private-fc-report').disabled=true;
}
function downloadResearchJSON(filename,data){
 if(!privateState)throw Error('Sign in to export a private research report.');
 const blob=new Blob([JSON.stringify(data,null,2)+'\n'],{type:'application/json;charset=utf-8'});
 const url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download=filename;document.body.appendChild(link);link.click();link.remove();
 URL.revokeObjectURL(url);
}
function showV66ForecastDiagnostics(d,company,opts){
 const grid=window.QFPrivateDiagnostics.forecastSensitivity(company,opts);
 forecastResultV66=d;forecastDiagnosticsV66=grid;
 const header=['Discount / revenue growth',...grid.growthRates.map(percent)];
 const rows=grid.discountRates.map((rate,i)=>[percent(rate),...grid.cells[i].map(v=>v==null?'Unavailable':usd(v))]);
 $('private-fc-diagnostics-content').innerHTML='<p class="tiny">Sensitivity of the <strong>hypothetical discounted FCF proxy</strong> to annual revenue growth (columns) and discount rate (rows). FCF margin, horizon, and terminal growth remain unchanged. Not a share price or market forecast.</p>'+displayTable(header,rows)+
  '<p class="tiny">'+grid.historicalPeriods+' SEC annual periods · observed annual revenue growth range: '+
  (grid.observedGrowthMin==null?'Unavailable':percent(grid.observedGrowthMin)+' to '+percent(grid.observedGrowthMax))+'. Past growth is not a forecast or an estimate of predictive accuracy. Unavailable cells fail the modeling limits.</p>';
 const exposure=window.QFPrivateIntegrity.forecastRisk(d);
 const base=exposure.scenarios.find(x=>x.scenario==='Base case');
 const fmtShare=base?.terminalShare==null?'Unavailable':percent(base.terminalShare);
 $('private-fc-diagnostics-content').insertAdjacentHTML('afterbegin',
  '<h4 style="margin:12px 0 8px">Model risk and SEC baseline</h4>'+displayTable(['Diagnostic','Value'],[
   ['Observed latest FCF proxy / revenue',exposure.observedFcfMargin===null?'Unavailable':percent(exposure.observedFcfMargin)],
   ['Assumed base FCF / revenue',exposure.modelFcfMargin===null?'Unavailable':percent(exposure.modelFcfMargin)],
   ['Base-case discounted terminal share',fmtShare],
   ['Reported SEC fiscal years',String(exposure.reportedFiscalYears)]])+
   '<p class="tiny"><strong>Terminal-value dependence:</strong> '+safe(exposure.warnings.join(' '))+
   ' SEC baseline and scenario assumptions are captured in the downloaded research manifest.</p>');
 $('private-fc-diagnostics').hidden=false;$('private-fc-report').disabled=false;
}
function showV66WalkforwardDiagnostics(d){
 const result=window.QFPrivateDiagnostics.summarizeWalkforward(d);
 walkforwardDiagnosticsV66=result;
 const rows=result.rows.map(w=>[String(w.index),w.testStart+' to '+w.testEnd,
  percent(w.optimizedReturn),percent(w.benchmarkReturn),percent(w.activeReturn),
  usd(w.optimizedFees),usd(w.benchmarkFees)]);
 $('private-wf-diagnostics-content').innerHTML='<p class="tiny">Each row compares <strong>two portfolios containing all '+d.symbols.length+' selected investments</strong>. Returns are compounded within each non-overlapping evaluation window, including modeled rebalance fees.</p>'+
  displayTable(['Window','Unseen test dates','Optimized return','Equal-weight return','Difference (pp)','Optimized fees','Benchmark fees'],rows)+
  displayTable(['Stability and accounting','Result'],[
   ['Windows outperforming equal-weight',result.positiveActiveWindows+' / '+result.windowsCount],
   ['Mean allocation change between fits',percent(result.meanWeightChange)],
   ['Maximum allocation change between fits',percent(result.maxWeightChange)],
   ['Windows where maximum weight cap binds',result.capBindingWindows+' / '+result.windowsCount],
   ['Optimized total fee reconciliation',usd(result.totalFees[0])],
   ['Equal-weight total fee reconciliation',usd(result.totalFees[1])]])+
  '<p class="tiny">Allocation change = half the absolute difference between consecutive fitted weight vectors; it is <strong>not</strong> transaction-dollar turnover. Positive window differences do not imply statistical significance. This is a historical simulation with selected assets and assumptions.</p>';
 const manifest=window.QFPrivateIntegrity.marketManifest(historySeries,d,$('private-history-days').value);
 const count=d.dates.length-1;
 $('private-wf-diagnostics-content').insertAdjacentHTML('afterbegin',
  '<h4 style="margin:12px 0 8px">Data integrity and evaluation coverage</h4>'+displayTable(['Check','Value'],[
   ['Selected investments',d.symbols.map(x=>safe(researchCompanyLabel(x))).join(' · ')],
   ['Aligned market-data observations',String(manifest.data.observationCount)],
   ['Observed coverage',safe(manifest.data.observedStart)+' to '+safe(manifest.data.observedEnd)],
   ['Evaluation coverage',d.windows.length+' windows; '+count+' evaluated observations'],
   ['SHA-256 data fingerprint',safe(manifest.data.fingerprint.slice(0,16))+'…']])+
   '<p class="tiny">'+(d.windows.length<6||count<126?'<strong>Limited sample:</strong> Only '+d.windows.length+' windows / '+count+' observations were evaluated. ':'')+
   'This fingerprint identifies the exact aligned price arrays used in this session; it does not prove source authenticity or allow a full replay without the licensed original bars. Asset and parameter selection can bias historical results.</p>');
 $('private-wf-diagnostics').hidden=false;$('private-wf-report').disabled=false;$('private-wf-robustness').disabled=false;
 $('private-wf-robustness-output').textContent='';
 robustnessResultV68=null;
 $('private-wf-v68-run').disabled=false;
 $('private-wf-v68-export').disabled=true;
 $('private-wf-v68-output').textContent='Run robustness checks to compare strategies over the same evaluation dates.';
}
function runV66CostSensitivity(){
 if(!privateState||!walkforwardResult||!historySeries){message('Run Walk-forward with loaded historical investments first.');return;}
 try{
  const rows=window.QFPrivateDiagnostics.costSensitivity(historySeries,walkforwardResult);
  $('private-wf-robustness-output').innerHTML='<h4 style="margin:14px 0 8px">Transaction-cost sensitivity</h4>'+displayTable(
   ['Fee (bps)','Optimized net change','Equal-weight net change','Difference (pp)','Optimized fees'],
   rows.map(r=>[String(r.feeBps),percent(r.optimizedChange),percent(r.benchmarkChange),percent(r.activeChange),usd(r.optimizedFees)]))+
   '<p class="tiny">The same assets, training boundaries, objective and cap are used in every scenario. Only the fee assumption changes. These are historical counterfactuals, not execution-quality estimates.</p>';
 }catch(e){$('private-wf-robustness-output').textContent=e.message;message(e.message);}
}

/* V6.8: comparative evaluation over identical dates, plus passive benchmark. */
function runV68Robustness(){
 if(!privateState||!walkforwardResult||!historySeries){message('Load investments and run Walk-forward before robustness checks.');return;}
 try{
  const r=window.QFPrivateRobustness.analyze(historySeries,walkforwardResult);
  robustnessResultV68=r;
  const passive=r.passive,base=r.strategyCases[0];
  const scenarios=r.strategyCases.map(x=>[x.label,
   x.objective==='minimum'?'Min volatility':x.objective==='inverse'?'Inverse volatility':'Return tilt',
   percent(x.cap),String(x.feeBps),percent(x.optimizedReturn),
   percent(x.equalWeightReturn),x.activeDifferencePp.toFixed(2)+' pp',usd(x.fees)]);
  const omitted=r.leaveOneOut.map(w=>[String(w.excludedWindow),w.excludedDates,
   percent(w.strategyReturn),percent(w.benchmarkReturn),w.differencePp.toFixed(2)+' pp']);
  $('private-wf-v68-output').innerHTML=
   '<h4 style="margin:14px 0 8px">Evaluation coverage</h4>'+
   displayTable(['Measure','Result'],[
    ['Underlying investments',r.symbols.map(researchCompanyLabel).join(' · ')],
    ['Common out-of-sample period',r.dates.start+' to '+r.dates.end],
    ['Evaluated sessions',String(r.evaluationSessions)],
    ['Non-overlapping test windows',String(r.windowCount)],
    ['Loaded market source',r.source]])+
   (r.evaluationSessions<126||r.windowCount<6?'<p class="notice"><strong>Short evaluation:</strong> The current observation window contains limited out-of-sample coverage; longer eligible history may produce more test windows.</p>':'')+
   '<h4 style="margin:14px 0 8px">Passive benchmark (one initial purchase)</h4>'+
   displayTable(['Portfolio','Compounded historical return','Volatility','Max drawdown','Modeled fees'],[
    ['Selected rolling allocation',percent(base.optimizedReturn),percent(walkforwardResult.optimized.metrics.annualVol),percent(walkforwardResult.optimized.metrics.maxDrawdown),usd(walkforwardResult.optimized.fees)],
    ['Equal-weight rebalanced',percent(base.equalWeightReturn),percent(walkforwardResult.benchmark.metrics.annualVol),percent(walkforwardResult.benchmark.metrics.maxDrawdown),usd(walkforwardResult.benchmark.fees)],
    ['Equal-weight buy and hold',percent(passive.change),percent(passive.annualVol),percent(passive.maxDrawdown),usd(passive.fee)]])+
   '<p class="tiny">The passive benchmark buys the same investments at the first evaluation close, includes its initial entry fee, and does not rebalance afterward. All three use the same price-only evaluation dates.</p>'+
   '<h4 style="margin:14px 0 8px">Allocation-rule and constraint sensitivity</h4>'+
   displayTable(['Case','Rule','Max weight','Fee (bps)','Rolling return','Rebalanced equal weight','Difference','Modeled rolling fees'],scenarios)+
   '<p class="tiny">All scenario allocations refit using the same training and evaluation boundaries. Only the rule, position cap, or trading fee changes. These are preselected checks, not a competition to choose the highest historical return.</p>'+
   '<h4 style="margin:14px 0 8px">Leave-one-window-out sensitivity</h4>'+
   displayTable(['Excluded window','Removed evaluation dates','Rolling return','Rebalanced benchmark','Difference'],omitted)+
   '<p class="tiny">Full-sample benchmark-relative difference: '+r.summary.fullActivePp.toFixed(2)+' pp. '+
   'After excluding each test window in turn, the difference ranges from '+r.summary.looMinActivePp.toFixed(2)+
   ' to '+r.summary.looMaxActivePp.toFixed(2)+' pp. '+
   (r.summary.windowDependentSign?'<strong>The sign changes when at least one window is omitted.</strong> ':'')+
   'Remaining periods are not refitted; this measures result concentration, not statistically independent validation.</p>'+
   '<p class="tiny">Historical evaluation only; prices exclude dividends and transaction modeling omits spreads, slippage, and taxes. No investment advice or actual trades.</p>';
  $('private-wf-v68-export').disabled=false;
  message('Robustness comparisons calculated locally. No trades placed.');
 }catch(e){robustnessResultV68=null;$('private-wf-v68-export').disabled=true;
  $('private-wf-v68-output').textContent=e.message;message(e.message);}
}
function exportV68Robustness(){
 if(!privateState||!historySeries||!walkforwardResult||!robustnessResultV68)return;
 try{
  const manifest=window.QFPrivateIntegrity.marketManifest(historySeries,walkforwardResult,$('private-history-days').value);
  if(!window.QFPrivateIntegrity.verifyMarketFingerprint(historySeries,manifest))throw Error('Historical price integrity verification failed.');
  downloadResearchJSON('quantforge-walkforward-robustness.json',window.QFPrivateRobustness.report(robustnessResultV68,manifest));
  message('Historical robustness report downloaded locally.');
 }catch(e){message('Robustness report unavailable: '+e.message);}
}
$('private-wf-v68-run').addEventListener('click',runV68Robustness);
$('private-wf-v68-export').addEventListener('click',exportV68Robustness);

const fcMoney=x=>finite(x)?usd(x):'Unavailable';
function runFinancialForecast(){
 clearGuideV79();
 if(!privateState){message('Sign in first.');return;}
 const symbol=$('private-valuation-company').value,company=valuationCompanies[symbol];
 if(!company){message('Load SEC annual statements for a selected company first.');return;}
 try{
  const d=window.QFPrivateForecast.run(company,{
   years:Number($('private-fc-years').value),growth:Number($('private-fc-growth').value)/100,
   fcfMargin:Number($('private-fc-margin').value)/100,
   discount:Number($('private-fc-discount').value)/100,
   terminal:Number($('private-fc-terminal').value)/100});
  const hist=displayTable(['Reported fiscal end','SEC revenue','SEC FCF proxy','Revenue change'],d.historic.map(x=>[
   x.date,fcMoney(x.revenue),fcMoney(x.fcf),x.revenueGrowth===null?'—':percent(x.revenueGrowth)]));
  const projected=displayTable(['Scenario','Forward year','Modeled revenue','Modeled FCF proxy'],d.scenarios.flatMap(s=>s.projection.map(x=>[
   s.name,'Year '+x.year,fcMoney(x.revenue),fcMoney(x.fcf)])));
  const valuation=displayTable(['Assumption','Conservative','Base case','Optimistic'],[
   ['Revenue growth',...d.scenarios.map(s=>percent(s.growth))],
   ['FCF/revenue',...d.scenarios.map(s=>percent(s.margin))],
   ['Discounted FCF-plus-terminal proxy',...d.scenarios.map(s=>fcMoney(s.proxy))]]);
  $('private-fc-output').innerHTML='<p class="tiny">'+safe(d.name)+' ('+safe(d.symbol)+') · last SEC fiscal period '+safe(d.fiscalEnd)+' · '+safe(d.source)+' · as-of '+safe(d.asOf)+'</p>'+hist+
   '<h3 style="margin:16px 0 8px">Hypothetical projections</h3>'+projected+
   '<h3 style="margin:16px 0 8px">Scenario sensitivity</h3>'+valuation+
   '<p class="tiny">Forecasts are assumptions, not observed SEC values. Revenue is compounded from the latest reported year. FCF is projected using an assumed FCF-to-revenue margin. '+
   (d.baseMargin===null?'Reported FCF margin unavailable; FCF valuation is suppressed.':'Latest reported FCF proxy/revenue: '+percent(d.baseMargin)+'.')+
   ' The discounted total is a simplified cash-flow proxy, NOT company equity value, enterprise value, price target, or per-share valuation. Cash, debt and other capital adjustments are not modeled; historical data may be restated.</p>';
  showV66ForecastDiagnostics(d,company,{years:d.years,growth:Number($('private-fc-growth').value)/100,fcfMargin:Number($('private-fc-margin').value)/100,discount:d.discount,terminal:d.terminal});
  message('Financial scenarios calculated. No trades placed.');
 }catch(e){clearV66Forecast();$('private-fc-output').textContent=e.message;message(e.message);}
}
function wfChart(d){
 const a=d.optimized.wealth,b=d.benchmark.wealth,len=a.length;
 const all=[...a,...b],min=Math.min(...all),max=Math.max(...all),span=Math.max(max-min,1),lo=min-span*.08,hi=max+span*.08;
 function path(values){return values.map((v,i)=>(i?'L':'M')+(26+560*i/(len-1)).toFixed(1)+' '+(201-170*(v-lo)/(hi-lo)).toFixed(1)).join(' ');}
 return '<svg viewBox="0 0 620 245" width="100%" role="img" aria-label="Out-of-sample virtual wealth for optimized and equal-weight portfolios">'+
  '<path d="'+path(a)+'" stroke="#0c7660" stroke-width="2" fill="none"/>'+
  '<path d="'+path(b)+'" stroke="#c58b31" stroke-width="2" fill="none"/>'+
  '<text x="26" y="232" font-size="11" fill="#526a60">'+safe(d.start)+'</text><text x="493" y="232" font-size="11" fill="#526a60">'+safe(d.end)+'</text></svg>'+
  '<p class="tiny"><strong>'+d.symbols.length+' investments are combined into two portfolio lines:</strong> '+d.symbols.map(s=>safe(researchCompanyLabel(s))).join(' · ')+'</p>'+
  '<p class="tiny">Green: optimized portfolio (all selected investments). Orange: equal-weight benchmark (the same investments). These are two strategies, not one line per company. To view prices for each investment, open Market data. Trading costs included; prices observed historically.</p>';
}
function runWalkforward(){
 clearGuideV79();
 if(!privateState){message('Sign in first.');return;}
 if(!historySeries){message('Load investment history in Market data first.');privateTab('research');return;}
 try{
  const d=window.QFPrivateWalkforward.run(historySeries,{
   train:Number($('private-wf-train').value),step:Number($('private-wf-step').value),
   objective:$('private-wf-mode').value,cap:Number($('private-wf-cap').value),
   feeBps:Number($('private-wf-fee').value),capital:Number($('private-wf-capital').value)});
  walkforwardResult=d;$('private-wf-export').disabled=false;
  const om=d.optimized.metrics,bm=d.benchmark.metrics;
  const comparison=displayTable(['Metric','Rolling allocation','Equal-weight benchmark'],[
   ['Out-of-sample compounded return',percent(om.change),percent(bm.change)],
   ['Annualized historical volatility',percent(om.annualVol),percent(bm.annualVol)],
   ['Maximum drawdown',percent(om.maxDrawdown),percent(bm.maxDrawdown)],
   ['Daily 95% historical VaR',percent(om.var95),percent(bm.var95)],
   ['Daily 95% historical expected shortfall',percent(om.expectedShortfall),percent(bm.expectedShortfall)],
   ['Modeled transaction fees',usd(d.optimized.fees),usd(d.benchmark.fees)],
   ['Final hypothetical wealth',usd(d.optimized.wealth.at(-1)),usd(d.benchmark.wealth.at(-1))]]);
  const windows=displayTable(['Fitted through','Unseen evaluation dates','Rolling weights'],d.windows.map(w=>[
   w.trainingEnd,w.testStart+' to '+w.testEnd,
   w.weights.map((p,i)=>d.symbols[i]+': '+percent(p)).join(' · ')]));
  $('private-wf-output').innerHTML='<p class="tiny">'+d.windows.length+' non-overlapping test windows · '+safe(d.start)+' to '+safe(d.end)+' · '+
   d.train+' prior training observations per fit · '+d.step+' test observations · '+d.annual+' annualization observations/year · '+safe(d.source)+'</p>'+wfChart(d)+comparison+
   '<h3 style="margin:16px 0 8px">Training and evaluation boundaries</h3>'+windows+
   '<p class="tiny">Each allocation is fitted only through the training-end date shown and held until its next scheduled rebalance. Rebalance fees are charged to both strategies on absolute traded notional, including initial deployment. Trades are assumed at the observed rebalance-date closing price, without bid–ask spreads or slippage. This is a retrospective simulation, not a live or guaranteed out-of-sample trading record. Symbol selection, date selection and model choice can introduce selection bias.</p>';
  showV66WalkforwardDiagnostics(d);
  message('Walk-forward historical evaluation completed. No trades placed.');
 }catch(e){walkforwardResult=null;clearV66Walkforward();$('private-wf-export').disabled=true;$('private-wf-output').textContent=e.message;message(e.message);}
}
function exportWalkforward(){
 if(!privateState||!walkforwardResult)return;
 const d=walkforwardResult,cell=v=>{let s=String(v).replace(/"/g,'""');if(/^[=+@-]/.test(s))s="'"+s;return '"'+s+'"';};
 const rows=[['training_start','training_end','test_start','test_end','symbol','fitted_weight','period_source'].map(cell).join(',')];
 for(const w of d.windows)for(let i=0;i<d.symbols.length;i++)rows.push([
  w.trainingStart,w.trainingEnd,w.testStart,w.testEnd,d.symbols[i],w.weights[i],d.source].map(cell).join(','));
 const blob=new Blob([rows.join('\r\n')+'\r\n'],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download='quantforge-walkforward-historical-windows.csv';document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
 message('Historical walk-forward windows exported locally.');
}
$('private-fc-run').addEventListener('click',runFinancialForecast);
$('private-wf-run').addEventListener('click',runWalkforward);
$('private-wf-export').addEventListener('click',exportWalkforward);
$('private-wf-robustness').addEventListener('click',runV66CostSensitivity);
$('private-wf-report').addEventListener('click',()=>{
 if(!privateState||!walkforwardResult||!walkforwardDiagnosticsV66)return;
 try{
  const base=window.QFPrivateDiagnostics.report('walkforward',walkforwardResult,walkforwardDiagnosticsV66);
  const report=window.QFPrivateIntegrity.attachWalkforward(base,historySeries,walkforwardResult,$('private-history-days').value);
  if(!window.QFPrivateIntegrity.verifyMarketFingerprint(historySeries,report.manifest))throw Error('Price-series integrity check failed.');
  downloadResearchJSON('quantforge-walkforward-research.json',report);
 }catch(e){message('Research export unavailable: '+e.message);}
});
$('private-fc-report').addEventListener('click',()=>{
 if(!privateState||!forecastResultV66||!forecastDiagnosticsV66)return;
 try{
  const base=window.QFPrivateDiagnostics.report('forecast',forecastResultV66,forecastDiagnosticsV66);
  downloadResearchJSON('quantforge-sec-forecast-research.json',window.QFPrivateIntegrity.attachForecast(base,forecastResultV66));
 }catch(e){message('Research export unavailable: '+e.message);}
});
for(const id of ['private-wf-train','private-wf-step','private-wf-mode','private-wf-cap','private-wf-fee','private-wf-capital']){
 $(id).addEventListener('change',()=>{clearResearchOSV90();walkforwardResult=null;clearV66Walkforward();$('private-wf-export').disabled=true;
  $('private-wf-output').textContent='Settings changed. Re-run walk-forward evaluation.';});
}
for(const id of ['private-fc-years','private-fc-growth','private-fc-margin','private-fc-discount','private-fc-terminal']){
 $(id).addEventListener('change',()=>{clearV66Forecast();$('private-fc-output').textContent='Assumptions changed. Re-run company forecast.';});
}

document.querySelectorAll('[data-private-tab]').forEach(b=>b.addEventListener('click',()=>privateTab(b.dataset.privateTab)));
$('qf-v93-ribbon-assess').addEventListener('click',()=>privateTab('decision'));
$('qf-v93-ribbon-brief').addEventListener('click',()=>privateTab('settings'));
$('qf-v93-brief-refresh').addEventListener('click',renderConnectedBriefV93);
$('qf-v93-brief-export').addEventListener('click',()=>{
 if(!privateState||!linkedResearchBriefV93)return;
 downloadResearchJSON('quantforge-v93-linked-research-briefing.json',linkedResearchBriefV93);
});
for(const id of ['qf-v93-briefing','qf-v93-lab-status'])$(id).addEventListener('click',e=>{
 const b=e.target.closest('[data-v93-method]');
 if(b&&privateState&&['research','candidate','valuation','trade','walkforward','backtest','optimization','lab'].includes(b.dataset.v93Method))privateTab(b.dataset.v93Method);
});
$('private-v90-browse').addEventListener('click',()=>openAssetBrowser('research'));
$('private-v90-run').addEventListener('click',runResearchOSV90);
$('private-v90-report').addEventListener('click',e=>{const b=e.target.closest('[data-private-tab]');if(b&&privateState&&['lab','trade','research','candidate','settings'].includes(b.dataset.privateTab))privateTab(b.dataset.privateTab);});
for(const id of ['private-v90-candidate','private-v90-risk','private-v90-horizon','private-v90-maxweight','private-v90-maxdrawdown','private-v90-days'])
 $(id).addEventListener('change',clearResearchOSV90);

$('private-decision-run-v84').addEventListener('click',runDecisionCenterV84);
$('private-candidate-run-v85').addEventListener('click',runCandidateDossierV85);
$('private-v87-factor-file').addEventListener('change',importFrenchV87);
$('private-v87-factor-run').addEventListener('click',runFrenchV87);
$('private-v87-factor-clear').addEventListener('click',clearImportedFrenchV87);
$('private-candidate-select-v85').addEventListener('change',()=>{refreshFactorChoicesV86();clearCandidateDossierV85();});
for(const id of ['private-v86-benchmark','private-v86-proxy1','private-v86-proxy2','private-v86-years'])
 $(id).addEventListener('change',clearCandidateDossierV85);
$('private-candidate-output-v85').addEventListener('click',e=>{
 const b=e.target.closest('[data-v85-go]');
 if(b&&privateState&&['valuation','trade'].includes(b.dataset.v85Go))privateTab(b.dataset.v85Go);
});
$('private-decision-result-v84').addEventListener('click',e=>{
 const b=e.target.closest('[data-v84-go]');
 if(!b||!privateState)return;
 const route=b.dataset.v84Go;
 if(['home','trade','ideas','research','optimization','walkforward','valuation','candidate','lab'].includes(route))privateTab(route);
});
$('private-guide-run-v79').addEventListener('click',runGuideV79);
$('private-guide-export-v79').addEventListener('click',()=>{
 if(!privateState||!guideReportV79)return;
 downloadResearchJSON('quantforge-private-research-explanation.json',guideReportV79);
});
$('private-guide-result-v79').addEventListener('click',e=>{
 const b=e.target.closest('[data-guide-go-v79]');
 if(!b||!privateState)return;
 const id=b.dataset.guideGoV79;
 if(['home','trade','ideas','research','optimization','backtest','walkforward','valuation','settings'].includes(id))privateTab(id);
});

$('private-history-load').addEventListener('click',loadHistory);
$('private-history-days').addEventListener('change',()=>invalidateResearchHistory('Historical period changed. Load the new date range first.'));
$('private-backtest-run').addEventListener('click',privateBacktest);
/* V7.3: owner-only price/filing comparison; never calls brokerage order endpoints. */
let valueBridgeRequestV73=0;
async function loadValueBridgeV73(){
 const symbol=$('private-valuation-company').value;
 const out=$('private-value-output-v73');
 if(!privateState){out.textContent='Sign in to load private valuation context.';return;}
 if(!symbol){out.textContent='Choose a company by name first.';return;}
 const company=valuationCompanies[symbol];
 if(!company){out.textContent='Run scenario first to load this company’s SEC annual financials.';return;}
 const state=privateState,seq=++valueBridgeRequestV73;
 $('private-value-run-v73').disabled=true;
 out.textContent='Loading SEC shares, balance-sheet disclosures and private market quote…';
 try{
  const [capital,quotes]=await Promise.all([
   api('private/valuation-capital?symbol='+encodeURIComponent(symbol)),
   api('private/quotes?symbols='+encodeURIComponent(symbol))
  ]);
  if(seq!==valueBridgeRequestV73||privateState!==state||$('private-valuation-company').value!==symbol)return;
  const quote=(quotes.quotes||[]).find(q=>q.symbol===symbol);
  if(!quote)throw Error('Observed price unavailable for this company.');
  const result=window.QFPrivateValueV73.build(company,capital,quote,new Date().toISOString());
  const num=(n)=>typeof n==='number'&&Number.isFinite(n)?n.toLocaleString('en-US',{maximumFractionDigits:2}):'Unavailable';
  const money=n=>typeof n==='number'&&Number.isFinite(n)?usd(n):'Unavailable';
  const pct=n=>typeof n==='number'&&Number.isFinite(n)?(n*100).toFixed(2)+'%':'Unavailable';
  const multiple=n=>typeof n==='number'&&Number.isFinite(n)?n.toFixed(2)+'×':'Unavailable';
  const rows=[
   ['Alpaca observed market price',money(result.price)],
   ['Quote source / timestamp',safe(result.venue)+' / '+safe(result.priceTime||'Unavailable')],
   ['SEC common shares outstanding',num(result.shares)],
   ['Shares reported period',safe(result.sharesTime||'Unavailable')],
   ['Estimated market capitalization',money(result.marketCap)],
   ['Annual FCF proxy fiscal period',safe(result.fiscalEnd||'Unavailable')],
   ['Annual reported FCF proxy',money(result.reportedFcf)],
   ['Price / annual FCF proxy',multiple(result.pFcf)],
   ['Annual FCF proxy yield',pct(result.fcfYield)],
   ['Market capitalization / annual revenue',multiple(result.pSales)],
   ['Indicative EV (partial components)',money(result.approximateEV)]
  ];
  const notes=[...result.warnings,...result.limitations].map(x=>'<li>'+safe(x)+'</li>').join('');
  const facts=/^https:\/\/data\.sec\.gov\/api\/xbrl\/companyfacts\/CIK[0-9]{10}\.json$/.test(result.secUrl||'')?result.secUrl:null;
  out.innerHTML='<p class="tiny"><strong>Historical filing data and observed market quote—not an intrinsic-value target or investment recommendation.</strong></p>'+
   displayTable(['Measure','Observed / calculated'],rows)+
   '<p class="tiny">Source: '+safe(result.source)+' · '+(facts?'<a href="'+safe(facts)+'" target="_blank" rel="noopener noreferrer">Inspect SEC filing facts</a>':'SEC facts unavailable')+'</p>'+
   '<h4>Interpretation and missing information</h4><ul class="tiny">'+notes+'</ul>';
  message('Observed-price research loaded for '+symbol+'. No trades were placed.');
 }catch(e){
  if(seq===valueBridgeRequestV73&&privateState===state&&$('private-valuation-company').value===symbol){
   out.textContent='Price and SEC comparison unavailable: '+e.message;
   message(e.message);
  }
 }finally{
  if(seq===valueBridgeRequestV73)$('private-value-run-v73').disabled=false;
 }
}
$('private-value-run-v73').addEventListener('click',loadValueBridgeV73);

/* V7.4 owner-only virtual allocation what-if: read-only; no write API calls. */
let allocationTokenV74=0,allocationResultV74=null,allocationRiskV74=null;
function clearAllocationV74(){
 allocationTokenV74++;allocationResultV74=null;allocationRiskV74=null;
 const out=$('private-allocation-results-v74');if(out)out.textContent='';
 const exp=$('private-allocation-export-v74');if(exp)exp.disabled=true;
 const go=$('private-allocation-run-v74');if(go)go.disabled=false;
}
function allocationChoicesV74(){
 const picker=$('private-allocation-symbol-v74');if(!picker)return;
 const previous=picker.value;
 const holdings=Object.keys(privateState?.holdings||{});
 const suggested=typeof ideaUniverse!=='undefined'&&Array.isArray(ideaUniverse)?ideaUniverse:[];
 const all=[...new Set([...suggested,...holdings])].filter(s=>/^[A-Z0-9][A-Z0-9.\/-]{0,19}$/.test(s)).sort();
 picker.innerHTML='<option value="">Choose an investment</option>'+all.map(s=>'<option value="'+safe(s)+'">'+safe(assetNames[s]||s)+' ('+safe(s)+')</option>').join('');
 if(all.includes(previous))picker.value=previous;
 $('private-allocation-selection-v74').textContent=all.length?'Choose from your screened investments or holdings. Add companies in Investment screening.':'Select companies by name in Investment screening, then return here.';
}
function renderAllocationV74(plan,risk){
 const pct=n=>typeof n==='number'&&Number.isFinite(n)?(n*100).toFixed(2)+'%':'Unavailable';
 const rows=[...new Set([...plan.before.positions.map(p=>p.symbol),...plan.after.positions.map(p=>p.symbol)])].sort();
 const weights=rows.map(s=>{const a=plan.before.positions.find(p=>p.symbol===s)?.weight||0;
  const b=plan.after.positions.find(p=>p.symbol===s)?.weight||0;
  return [safe(assetNames[s]||s)+' ('+safe(s)+')',pct(a),pct(b),pct(b-a)];});
 weights.push(['Virtual cash',pct(plan.before.cashWeight),pct(plan.after.cashWeight),pct(plan.after.cashWeight-plan.before.cashWeight)]);
 const lines=[
  ['Observed purchase price',usd(plan.observedPrice)],
  ['Quote provenance',safe(plan.source)+' / '+safe(plan.priceTime)],
  ['Proposed virtual spending',usd(plan.proposedBudget)],
  ['Hypothetical units added',plan.unitsBought.toFixed(6)],
  ['Cash before / after',usd(plan.cashBefore)+' / '+usd(plan.cashAfter)],
  ['Total virtual portfolio value (unchanged)',usd(plan.totalAfter)],
  ['Invested share of total (before / after)',pct(plan.before.investedWeight)+' / '+pct(plan.after.investedWeight)],
  ['Largest position as share of total (before / after)',pct(plan.before.largest?.weight||0)+' / '+pct(plan.after.largest?.weight||0)],
  ['Largest position as share of invested assets', (plan.before.largestInvestedWeight===null?'Not applicable':pct(plan.before.largestInvestedWeight))+' / '+(plan.after.largestInvestedWeight===null?'Not applicable':pct(plan.after.largestInvestedWeight))],
  ['Invested-only HHI (before / after)',(plan.before.investmentHhi===null?'Not applicable':plan.before.investmentHhi.toFixed(4))+' / '+(plan.after.investmentHhi===null?'Not applicable':plan.after.investmentHhi.toFixed(4))],
  ['Cash-inclusive allocation HHI (not a risk measure)',plan.before.hhi.toFixed(4)+' / '+plan.after.hhi.toFixed(4)]
 ];
 const riskView=risk?.available?
  '<h4>Aligned-history volatility sensitivity</h4>'+displayTable(['Measure','Before','After'],[
   ['Annualized historical volatility',pct(risk.annualizedVolBefore),pct(risk.annualizedVolAfter)],
   ['Aligned observations',String(risk.sessions),String(risk.sessions)]])+
   '<p class="tiny">'+safe(risk.firstDate)+' to '+safe(risk.lastDate)+' · '+safe(risk.note)+'</p>':
   '<p class="notice">Historical volatility comparison unavailable: '+safe(risk?.reason||'Historical data not loaded.')+' The cash and concentration comparison remains available.</p>';
 $('private-allocation-results-v74').innerHTML='<p class="tiny"><strong>Hypothetical only: no portfolio balances or holdings were changed.</strong> All amounts use observed historical/last-trade quotes, not executable prices.</p>'+
   displayTable(['Metric','What-if result'],lines)+'<p class="tiny">Cash-inclusive HHI treats all virtual cash as one allocation bucket. It can fall when cash is invested even as stock-market volatility rises. Invested-only HHI excludes cash, and is unavailable for an all-cash portfolio.</p>'+'<h4>Before vs. after allocations</h4>'+displayTable(['Investment','Before','After','Change'],weights)+riskView+
   '<h4>Assumptions and cautions</h4><ul class="tiny">'+plan.warnings.map(w=>'<li>'+safe(w)+'</li>').join('')+'</ul>';
 $('private-allocation-export-v74').disabled=false;
}
async function runAllocationV74(){
 clearAllocationV74();
 if(!privateState){message('Sign in and load your virtual portfolio first.');return;}
 const symbol=$('private-allocation-symbol-v74').value;
 const budget=Number($('private-allocation-budget-v74').value);
 const target=$('private-allocation-results-v74');
 if(!symbol){target.textContent='Choose an investment from your shortlist first.';return;}
 const state=privateState,token=allocationTokenV74;
 $('private-allocation-run-v74').disabled=true;
 target.textContent='Fetching fresh private market observations for all current positions…';
 try{
  const symbols=[...new Set([...Object.entries(state.holdings||{}).filter(([s,n])=>Number(n)>0).map(([s])=>s),symbol])];
  if(symbols.length>60)throw Error('Too many virtual positions to compare.');
  const quotes={};
  for(let i=0;i<symbols.length;i+=8){
   const data=await api('private/quotes?symbols='+encodeURIComponent(symbols.slice(i,i+8).join(',')));
   for(const q of data.quotes||[])if(symbols.includes(q.symbol))quotes[q.symbol]=q;
   if(token!==allocationTokenV74||privateState!==state)return;
  }
  const plan=window.QFPrivateAllocationV74.scenario({holdings:state.holdings,cash:state.cash,quotes,symbol,budget,nowISO:new Date().toISOString()});
  const aligned=Array.isArray(ideaData)?ideaData:[];
  const risk=window.QFPrivateAllocationV74.matchedRisk(plan,aligned,252);
  if(token!==allocationTokenV74||privateState!==state)return;
  allocationResultV74=plan;allocationRiskV74=risk;
  renderAllocationV74(plan,risk);
  message('Hypothetical allocation analyzed. No trades were placed.');
 }catch(e){if(token===allocationTokenV74&&privateState===state){target.textContent='Unable to calculate: '+e.message;message(e.message);}}
 finally{if(token===allocationTokenV74)$('private-allocation-run-v74').disabled=false;}
}
$('private-allocation-choices-v74').addEventListener('click',()=>{clearAllocationV74();allocationChoicesV74();});
$('private-allocation-symbol-v74').addEventListener('change',clearAllocationV74);
$('private-allocation-budget-v74').addEventListener('input',clearAllocationV74);
$('private-allocation-run-v74').addEventListener('click',runAllocationV74);
$('private-allocation-export-v74').addEventListener('click',()=>{
 if(!privateState||!allocationResultV74){message('Calculate the scenario before exporting.');return;}
 const report=window.QFPrivateAllocationV74.exportResearch(allocationResultV74,allocationRiskV74,{source:ideaSource,period:$('ideas-period').value});
 downloadResearchJSON('quantforge-allocation-research.json',report);
 message('Allocation research exported without private account balances, positions, purchase amounts or raw prices.');
});

$('private-valuation-run').addEventListener('click',privateValuation);
$('private-valuation-run').addEventListener('click',()=>{valueBridgeRequestV73++;$('private-value-output-v73').textContent='';});
$('private-capital-submit').addEventListener('click',changeCapital);
privatePeers();

})();
