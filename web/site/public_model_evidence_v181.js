/* Public reproducible validation exhibit. Synthetic prices; actual private model. */
(function(root){
'use strict';
function fixture(n=355){
 const dates=[],prices=[];
 for(let i=0;i<n;i++){
  dates.push(new Date(Date.UTC(2023,0,1+i)).toISOString().slice(0,10));
  prices.push(100*Math.exp(i*0.00024+0.018*Math.sin(i/11)+0.008*Math.sin(i/3)));
 }
 return {symbols:['DEMO'],dates,closes:{DEMO:prices},asset_classes:{DEMO:'us_equity'},source:'Deterministic, synthetic prices; not market observations'};
}
function summary(result){
 if(!result||!result.ready)return {ready:false,message:'The synthetic model evaluation could not be completed.'};
 const accurate=x=>Math.round(Math.max(0,Math.min(1,x))*100);
 const brier=x=>x.toFixed(3);
 return {ready:true,windows:result.testWindows,start:result.firstTestDate,end:result.lastTestDate,
  modelAccuracy:accurate(result.evaluatedAccuracy),baselineAccuracy:accurate(result.baselineAccuracy),
  modelBrier:brier(result.evaluatedBrier),baselineBrier:brier(result.baselineBrier),
  conclusion:result.qualified?'The model cleared its internal baseline screen on this generated series. This is not evidence of market predictability.':'The model did not clear its internal baseline screen on this generated series.'};
}
function render(){
 if(typeof document==='undefined')return;
 const host=document.getElementById('qf-v181-evidence');if(!host)return;
 const ml=root.QFPrivatePredictiveMLV180;
 const r=summary(ml?ml.analyze(fixture(),'DEMO'):null);
 if(!r.ready){host.textContent=r.message;return;}
 const bar=(label,value,extra)=>'<div class="qf-v181-bar '+extra+'"><strong>'+label+'</strong><div class="qf-v181-track"><span style="width:'+value+'%"></span></div><strong>'+value+'%</strong></div>';
 host.innerHTML='<p class="qf-v181-scope">Generated prices only · '+r.windows+' disjoint five-session held-out windows · '+r.start+' to '+r.end+'</p>'+
  '<div class="qf-v181-bars" role="img" aria-label="Synthetic evaluation: model directional accuracy '+r.modelAccuracy+' percent; simple baseline '+r.baselineAccuracy+' percent">'+bar('Classifier',r.modelAccuracy,'model')+bar('Baseline',r.baselineAccuracy,'baseline')+'</div>'+
  '<div class="qf-v181-scores"><div class="qf-v181-score"><strong>'+r.modelBrier+'</strong><span>Model Brier score · smaller is better</span></div><div class="qf-v181-score"><strong>'+r.baselineBrier+'</strong><span>Historical-frequency baseline Brier score</span></div></div><p>'+r.conclusion+'</p>';
}
const api=Object.freeze({fixture,summary});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPublicModelEvidenceV181=api;
if(typeof window!=='undefined')window.addEventListener('load',render);
})(typeof window!=='undefined'?window:globalThis);
