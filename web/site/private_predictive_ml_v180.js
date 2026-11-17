/* Price-history ML experiment. Expanding past-only logistic regression; no network or trades. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const symbol=x=>typeof x==='string'&&/^[A-Z][A-Z0-9.]{0,9}$/.test(x);
const H=5, MIN_DAYS=185, FIRST=65;
const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
const sig=z=>z>=0?1/(1+Math.exp(-Math.min(z,60))):Math.exp(Math.max(z,-60))/(1+Math.exp(Math.max(z,-60)));
const clamp=(x,l,h)=>Math.max(l,Math.min(h,x));
function features(prices,t){
 if(t<FIRST||t>=prices.length)return null;
 const r=(a,b)=>Math.log(prices[a]/prices[b]);
 const returns=[];for(let i=t-19;i<=t;i++)returns.push(r(i,i-1));
 const m=mean(returns),sd=Math.sqrt(mean(returns.map(v=>(v-m)**2)));
 const hi=Math.max(...prices.slice(t-39,t+1));
 return [r(t,t-5),r(t,t-20),r(t,t-60),sd,prices[t]/hi-1];
}
function prepare(history,sym){
 if(!symbol(sym)||!history||!Array.isArray(history.dates)||!Array.isArray(history.symbols)||
  !history.symbols.includes(sym)||!history.closes||!Array.isArray(history.closes[sym]))return null;
 const prices=history.closes[sym],dates=history.dates;
 if(prices.length!==dates.length||prices.length<MIN_DAYS||prices.length>2500||
  prices.some(x=>!finite(x)||x<=0)||dates.some((d,i)=>!/^\d{4}-\d{2}-\d{2}$/.test(d)||
   !finite(Date.parse(d))||(i>0&&d<=dates[i-1])))return null;
 if(history.asset_classes&&history.asset_classes[sym]&&history.asset_classes[sym]!=='us_equity')return null;
 return {prices,dates};
}
function fit(rows){
 const p=rows[0].x.length,n=rows.length,mu=Array(p).fill(0),scale=Array(p).fill(1);
 for(let j=0;j<p;j++){
  mu[j]=mean(rows.map(v=>v.x[j]));
  scale[j]=Math.sqrt(mean(rows.map(v=>(v.x[j]-mu[j])**2)));
  if(scale[j]<1e-8)scale[j]=1;
 }
 const weights=Array(p+1).fill(0);
 const prior=clamp(rows.reduce((v,r)=>v+r.y,0)/n,0.05,0.95);
 weights[0]=Math.log(prior/(1-prior));
 for(let k=0;k<260;k++){
  const gradient=Array(p+1).fill(0);
  for(const row of rows){
   const x=row.x.map((v,j)=>clamp((v-mu[j])/scale[j],-5,5));
   let z=weights[0];for(let j=0;j<p;j++)z+=weights[j+1]*x[j];
   const diff=sig(z)-row.y;gradient[0]+=diff;
   for(let j=0;j<p;j++)gradient[j+1]+=diff*x[j];
  }
  weights[0]-=0.085*gradient[0]/n;
  for(let j=1;j<=p;j++)weights[j]-=0.085*(gradient[j]/n+0.16*weights[j]);
 }
 return {weights,mu,scale,prior};
}
function score(model,x){
 let z=model.weights[0];
 for(let j=0;j<x.length;j++)z+=model.weights[j+1]*clamp((x[j]-model.mu[j])/model.scale[j],-5,5);
 return sig(z);
}
function diagnostics(samples){
 const unavailable=reason=>({state:'insufficient',reason,minimumPerPeriod:12});
 if(!Array.isArray(samples)||samples.length>400||samples.some((r,i)=>!Number.isInteger(r?.t)||
  !Number.isFinite(Date.parse(r.date))||![0,1].includes(r.y)||
  !finite(r.prediction)||r.prediction<0||r.prediction>1||!finite(r.baseline)||r.baseline<0||r.baseline>1||
  (i>0&&(r.t-samples[i-1].t<H||r.date<=samples[i-1].date))))return unavailable('Matching, disjoint chronological held-out outcomes are required.');
 const cut=Math.floor(samples.length/2),early=samples.slice(0,cut),recent=samples.slice(cut);
 if(early.length<12||recent.length<12)return unavailable('At least 12 matured test windows in both the early and recent periods are needed.');
 const period=rows=>{const model=mean(rows.map(r=>(r.prediction-r.y)**2)),base=mean(rows.map(r=>(r.baseline-r.y)**2));return {windows:rows.length,first:rows[0].date,last:rows.at(-1).date,modelBrier:model,baselineBrier:base,pairedLossDifference:model-base};};
 const before=period(early),after=period(recent),deteriorating=before.pairedLossDifference<-.005&&after.pairedLossDifference>.005;
 return {schema:'quantforge.chronological-model-review.v34',state:deteriorating?'deteriorating':'no-clear-deterioration',early:before,recent:after,minimumPerPeriod:12,
  interpretation:deteriorating?'The earlier Brier advantage reversed in the recent held-out period. The direction screen is withheld.':'These two descriptive periods do not show the defined reversal; that does not establish future stability.',
  limitation:'A predeclared descriptive 0.005 Brier-difference review rule on existing matured chronological tests. Not a significance test, calibrated future probability or investment-performance backtest.'};
}
function analyze(history,sym){
 const input=prepare(history,sym);
 const unavailable=reason=>({ready:false,symbol:sym,reason});
 if(!input)return unavailable('At least 185 valid, dated, aligned equity sessions are needed.');
 const {prices,dates}=input,n=prices.length;
 const rows=[];
 for(let t=FIRST;t+H<n;t++){
  const x=features(prices,t),future=prices[t+H]/prices[t]-1;
  if(x)rows.push({t,x,y:future>0?1:0,realized:future});
 }
 if(rows.length<100)return unavailable('Not enough chronological examples to train and evaluate this model.');
 // Hold out the last quarter of feature dates; test in non-overlapping 5-session windows.
 // At each test date, a training label is used only if its complete future return is already observed.
 const firstTest=Math.max(FIRST+120,Math.floor(n*0.75));
 const tests=[];
 for(let t=firstTest;t+H<n;t+=H){
  const train=rows.filter(r=>r.t+H<=t);
  if(train.length<100)continue;
  const fx=features(prices,t);if(!fx)continue;
  const model=fit(train);
  const y=prices[t+H]>prices[t]?1:0;
  const prediction=score(model,fx);
  const baseline=model.prior;
  tests.push({t,date:dates[t],prediction,baseline,y});
 }
 if(tests.length<7)return unavailable('Not enough non-overlapping out-of-sample test windows.');
 const brier=a=>mean(tests.map(v=>(v[a]-v.y)**2));
 const accuracy=a=>mean(tests.map(v=>(v[a]>=0.5?1:0)===v.y?1:0));
 const modelBrier=brier('prediction'),baseBrier=brier('baseline');
 const train=rows.filter(r=>r.t+H<n);
 const model=fit(train),current=score(model,features(prices,n-1));
 // The Brier improvement alone is not sufficient: check directional accuracy too.
 // Screens are deliberately conservative and remain exploratory, not statistical proof.
 const modelAccuracy=accuracy('prediction'),baseAccuracy=accuracy('baseline');
 // Three coarse reliability groups are shown as descriptive holdout diagnostics, not
 // calibrated future-return probabilities (small test counts may be very noisy).
 const calibration=[0,1,2].map(bin=>{
  const group=tests.filter(v=>Math.min(2,Math.floor(v.prediction*3))===bin);
  return {range:[bin/3,(bin+1)/3],count:group.length,
   mean_prediction:group.length?mean(group.map(v=>v.prediction)):null,
   observed_positive:group.length?mean(group.map(v=>v.y)):null};
 });
 const testPositiveRate=mean(tests.map(v=>v.y));
 const diagnostic=diagnostics(tests);
 const qualified=modelBrier<baseBrier-0.005&&modelAccuracy>=baseAccuracy&&tests.length>=12&&diagnostic.state!=='deteriorating';
 const status=diagnostic.state==='deteriorating'?'Recent held-out deterioration; direction withheld':qualified?'Exploratory signal (limited validation)':'No consistent advantage over the simple baseline';
 const direction=current>=0.55?'Upward tilt':current<=0.45?'Downward tilt':'No clear direction';
 const reasons=diagnostic.state==='deteriorating'?'Earlier held-out Brier advantage reversed in the recent descriptive period. The direction screen is withheld; this is not a significance test.':qualified?
  'The model improved the Brier score and matched or exceeded baseline directional accuracy across held-out windows. This remains exploratory, not statistical proof.':
  'Held-out Brier error, directional accuracy, or sample size did not clear the conservative baseline screen.';
 return {ready:true,symbol:sym,asOf:dates[n-1],forecastHorizon:H,
  model:'L2-regularized logistic regression',features:['5-session return','20-session return','60-session return','20-session volatility','40-session drawdown'],
  trainingExamples:train.length,testWindows:tests.length,firstTestDate:tests[0].date,lastTestDate:tests.at(-1).date,
  evaluatedAccuracy:modelAccuracy,baselineAccuracy:baseAccuracy,
  evaluatedBrier:modelBrier,baselineBrier:baseBrier,
  testPositiveRate,calibration,diagnostics:diagnostic,validation:{horizon:H,first:tests[0].date,last:tests.at(-1).date,
   disjoint_test_windows:tests.length,baseline:'Expanding historical positive-outcome frequency',
   label_maturity:'Training labels end no later than each test feature date',
   calibration_limit:'Three descriptive score bins; no post-hoc probability recalibration or claimed future calibration'},
  qualified,status,direction:qualified?direction:'Not validated',rawModelScore:current,
  explanation:reasons,source:String(history.source||'authenticated historical prices').slice(0,100),
  limitations:'Exploratory 5-session price-direction classification. Price-only bars omit dividends, spread and taxes. Market regimes can change. The score is uncalibrated, not a probability of future profit.'};
}
function all(history,selection){
 if(!Array.isArray(selection)||selection.length<2||selection.length>5||new Set(selection).size!==selection.length||
  selection.some(s=>!symbol(s)))return {ready:false,reason:'Choose 2–5 eligible companies.'};
 return {ready:true,rows:selection.map(s=>analyze(history,s))};
}
const api=Object.freeze({analyze,all,prepare,features,diagnostics});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivatePredictiveMLV180=api;
})(typeof window!=='undefined'?window:globalThis);
