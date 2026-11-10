/* Adapters for preserved numerical engines. No network, persistence or account mutations. */
(function(root){
'use strict';
function run(input,E=root){
 const {history,snapshot,symbol,company,origin,archive=null,factors=null}=input;
 const profiles={company:['value','comparative','portfolioValidation','unified','simple','history','peers','optimization','walkforward','robustness','candidate','proxy','policy','intelligence','integrity'],valuation:['value','forecast','history'],strategy:['history','optimization','walkforward','robustness'],factors:['history','candidate','proxy','french'],portfolio:['history','optimization','simulation'],data:['history','candidate','filing','coverage','archive','archiveQuality','historical','historicalRobustness','attribution','policy','intelligence','integrity']};
 const enabled=profiles[input.scope];
 const out={schema:'quantforge.shared-research.v25',symbol,origin,results:{}};
 const call=(key,job)=>{if(enabled&&!enabled.includes(key)){out.results[key]={ready:false,reason:'This method belongs to a different scoped research view.'};return out.results[key];}try{const value=job();out.results[key]=value?.ready===false?value:{...value,ready:true};}catch(e){out.results[key]={ready:false,reason:String(e.message||'Eligible inputs are unavailable.').slice(0,220)};}return out.results[key];};
 const selection=history?.symbols||[];
 const common={history,snapshot,selection,candidate:symbol,archive,train:126,step:21,feeBps:5,maxDrawdown:.25};
 call('history',()=>{E.QFPrivateOptimizer.prepare(history);return {first:history.dates[0],last:history.dates.at(-1),observations:history.dates.length};});
 call('peers',()=>E.QFPublicSECPeers.compare(snapshot,symbol,{sectorOnly:true}));
 const optimized=call('optimization',()=>E.QFPrivateOptimizer.run(history,{objective:'minimum',maxWeight:.6}));
 const walk=call('walkforward',()=>E.QFPrivateWalkforward.run(history,{train:126,step:21,feeBps:5,cap:.6}));
 call('robustness',()=>{if(!walk.ready)throw Error(walk.reason);return E.QFPrivateRobustness.analyze(history,walk);});
 call('simulation',()=>{
  if(!optimized.ready)throw Error(optimized.reason);
  const data=E.QFPrivateOptimizer.prepare(history);
  const weights=input.weights?selection.map(s=>input.weights[s]||0):optimized.chosen;
  if(weights.some(w=>!Number.isFinite(w)||w<0)||weights.reduce((a,b)=>a+b,0)>1+1e-9)throw Error('Invalid simulation weights.');
  return {...E.QFModel.monteCarlo(weights,data.rawCovariance,10000,9821,1800,21),days:21,paths:1800,weights,assumption:'Seeded zero-drift Gaussian daily returns with fixed sample covariance; independent sessions; cash has zero return. Scenario sensitivity, not a calibrated future confidence interval.'};
 });
 call('forecast',()=>E.QFPrivateForecast.run(company,{years:5,growth:input.growth??.06,fcfMargin:input.margin??.12,discount:.10,terminal:.02}));
 const value=call('value',()=>{if(origin!=='market'||!input.capital||!input.quote)throw Error('Observed-price ratios need authenticated quotes and independently sourced SEC capital data.');const result=E.QFPrivateValueV73.build(company,input.capital,input.quote,input.asOf);return result.valid?result:{...result,ready:false,reason:result.warnings.join(' ')};});
 const candidate=call('candidate',()=>E.QFPrivateCandidateV85.evaluate({history,selection,symbol,company,value:value.ready?value:null,portfolio:input.portfolio,quotes:input.quotes,now:input.asOf||new Date().toISOString()}));
 call('proxy',()=>E.QFPrivateFactorScenariosV86.assess({history,selection,symbol,benchmark:symbol==='SPY'?'VTI':'SPY',proxies:['IWM','IVE'].filter(s=>s!==symbol&&selection.includes(s)),years:1}));
 call('french',()=>E.QFPrivateFrenchFactorsV87.assess({history,selection,symbol,factors}));
 call('filing',()=>E.QFPrivatePointInTimeV97.replay(common));
 call('coverage',()=>E.QFPrivateSECCoverageV98.run(common));
 call('archive',()=>E.QFPrivateArchivedSECValidationV99.run(common));
 call('archiveQuality',()=>E.QFPrivateArchiveQualityV100.inspect({archive,snapshot,selection}));
 const panel=call('historical',()=>E.QFPrivateHistoricalPanelV110.study(common));
 const sensitivity=call('historicalRobustness',()=>E.QFPrivateHistoricalRobustnessV120.analyze(common));
 const attribution=call('attribution',()=>E.QFPrivateHistoricalAttributionV130.study(panel));
 const intelligence=call('intelligence',()=>E.QFPrivateResearchIntelligenceV96.build({...common,symbol,asOf:input.asOf||new Date().toISOString(),portfolio:input.portfolio,quotes:input.quotes,limit:.25}));
 call('policy',()=>{
  const O=E.QFPrivateResearchOrchestratorV91;
  const plan=O.plan({history,selection,symbol,train:126,step:21,cap:.6,frenchImported:!!factors});
  let ledger=O.ledger(plan);
  for(const m of ledger){
   const key=m.key==='backtest'?'robustness':m.key,result=out.results[key];
   const ready=m.status==='pending'&&result?.ready===true;
   ledger=O.mark(ledger,m.key,ready?'completed':'ineligible',ready?'Calculated on the stated common-date input.':result?.reason||'Required eligible inputs are unavailable.');
  }
  const raw=E.QFPrivateResearchOSV90.assess({symbol,selection,history:origin==='market'?history:null,dossier:candidate,quote:origin==='market'?input.quote:null,portfolio:origin==='market'?input.portfolio:null,asOf:input.asOf||new Date().toISOString(),walkforward:walk.ready?walk:null});
  const assessment=O.reconcile(raw,ledger),review=E.QFPrivateDecisionReviewV92.review(assessment,history,selection);
  const brief=E.QFPrivateResearchBriefV93.summarize(assessment,review,{},selection);
  out.brief=brief;
  return {assessment,review,brief,ledger};
 });
 const integrity=call('integrity',()=>E.QFPrivateDecisionIntegrityV130.assess({brief:out.brief,historical:panel,robustness:sensitivity,attribution,portfolio:intelligence?.allocation}));
 call('comparative',()=>E.QFPrivateInvestmentIntelligenceV94.build({brief:out.brief,snapshot,selection,history,variants:['conservative','balanced','growth'].map(risk=>E.QFPrivateResearchOSV90.assess({symbol,selection,history:origin==='market'?history:null,dossier:candidate,quote:origin==='market'?input.quote:null,portfolio:origin==='market'?input.portfolio:null,asOf:input.asOf,walkforward:walk.ready?walk:null,risk})),asOf:input.asOf}));
 call('portfolioValidation',()=>E.QFPrivatePortfolioValidationV95.build({...common,symbol,portfolio:input.portfolio,quotes:input.quotes,asOf:input.asOf,maxWeight:.2}));
 call('unified',()=>E.QFPrivateUnifiedDecisionV160.summarize({brief:out.brief,integrity}));
 call('simple',()=>{
  const rows=selection.map(s=>{const dossier=E.QFPrivateCandidateV85.evaluate({history,selection,symbol:s,company:snapshot.companies.find(c=>c.symbol===s),now:input.asOf});const assessment=E.QFPrivateResearchOSV90.assess({symbol:s,selection,history:origin==='market'?history:null,dossier,asOf:input.asOf,quote:input.quotes?.[s],portfolio:input.portfolio});return {...assessment,name:snapshot.companies.find(c=>c.symbol===s)?.name||s};});
  return E.QFPrivateSimpleResearchV170.prepare({rows,selected:selection,comparison:out.results.policy?.review?.comparison,asOf:input.asOf});
 });
 return out;
}
const api=Object.freeze({run});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFDeepResearch25=api;
})(typeof window!=='undefined'?window:globalThis);
