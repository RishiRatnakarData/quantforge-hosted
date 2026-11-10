const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const {run}=require('../site/research_deep_v25.js');
function engines(){
 const E={console,Date,Math,window:null};E.window=E;
 const context=vm.createContext(E);
 for(const file of ['model','sec_peer_model','private_optimizer','private_walkforward_v65','private_integrity_v67','private_robustness_v68','private_forecast_v65','private_value_v73','private_investment_intelligence_v94','private_portfolio_validation_v95','private_unified_decision_v160','private_simple_research_v170','private_candidate_v85','private_factor_scenarios_v86','private_french_factors_v87','private_research_orchestrator_v91','private_research_os_v90','private_decision_review_v92','private_research_brief_v93','private_research_intelligence_v96','private_pit_validation_v97','private_sec_coverage_v98','private_archived_sec_v99','private_archive_quality_v100','private_historical_panel_v110','private_robustness_v120','private_historical_attribution_v130','private_decision_integrity_v130'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../site',file+'.js'),'utf8'),context);
 return E;
}
function input(){
 const snap=JSON.parse(fs.readFileSync(path.join(__dirname,'../site/sec_snapshot.json'),'utf8'));
 const dates=Array.from({length:300},(_,i)=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10));
 return {symbol:'MSFT',origin:'synthetic',company:snap.companies.find(c=>c.symbol==='MSFT'),snapshot:snap,history:{symbols:['MSFT','SPY','IWM','IVE'],dates,closes:Object.fromEntries(['MSFT','SPY','IWM','IVE'].map((s,j)=>[s,dates.map((_,i)=>100*Math.exp(.0002*i+.05*Math.sin(i/(8+j))+.02*Math.cos(i/(3+j))))])),sessions_per_year:252},asOf:'2026-11-10T12:00:00Z'};
}
test('all retained engines execute through shared adapters and absent archives remain withheld',()=>{
 const r=run(input(),engines());
 for(const key of ['peers','optimization','walkforward','robustness','simulation','forecast','candidate','proxy','coverage','policy','integrity','comparative','portfolioValidation','unified','simple'])assert.equal(r.results[key].ready,true,key+': '+r.results[key].reason);
 assert.equal(r.results.archive.ready,false);assert.equal(r.results.french.ready,false);
 assert.equal(r.results.policy.assessment.decision,'Insufficient evidence');
 assert.equal(r.results.simulation.paths,1800);
});
test('adapter is immutable and never turns invalid history or missing SEC coverage into a result',()=>{
 const data=input(),before=JSON.stringify(data),E=engines();run(data,E);assert.equal(JSON.stringify(data),before);
 data.history.closes.MSFT[3]=-1;
 const r=run(data,E);assert.equal(r.results.history.ready,false);assert.equal(r.results.simulation.ready,false);
 assert.equal(r.results.candidate.ready,false);
});
test('model scenarios remain deterministic and price changes invalidate their measured outcome',()=>{
 const E=engines(),data={...input(),scope:'portfolio'};const a=run(data,E),b=run(data,E);assert.deepEqual(a.results.simulation,b.results.simulation);
 data.history.closes.MSFT[200]*=.7;const c=run(data,E);assert.notEqual(a.results.simulation.low,c.results.simulation.low);
});
