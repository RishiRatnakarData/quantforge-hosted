/* V13.0 - historical observation attribution; descriptive, no provider, account or trading access. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const fix=x=>finite(x)?Number(x.toFixed(6)):null;
const safe=x=>String(x||'Unavailable').slice(0,160);
const unready=reason=>({ready:false,reason:safe(reason)});
function study(panel){
 if(!panel||panel.ready!==true||(!Number.isInteger(panel.coverage?.scheduled)||panel.coverage.scheduled<2)||panel.coverage.complete!==panel.coverage.scheduled||
    panel.performance?.ready!==true||!Array.isArray(panel.performance.rows)||
    panel.performance.rows.length!==panel.coverage.scheduled)
  return unready('Complete filing-covered, non-overlapping price observations are required.');
 const rows=panel.performance.rows;
 let rw=1,bw=1,peakR=1,peakB=1,worstR=0,worstB=0;
 let outperform=0,underperform=0,ties=0,nonCash=0,excesses=[];
 const perSymbol=new Map(),windows=[];
 let priorEnd=null;
 for(const row of rows){
  const {decisionDate,executionDate,testThrough,rulePeriodReturn:r,benchmarkPeriodReturn:b,selected}=row;
  const iso=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&!Number.isNaN(Date.parse(x))&&new Date(x).toISOString().slice(0,10)===x;
  if(!iso(decisionDate)||!iso(executionDate)||!iso(testThrough)||
    !(decisionDate<executionDate&&executionDate<=testThrough)||
    (priorEnd!==null&&priorEnd>=executionDate)||!finite(r)||!finite(b)||r<=-1||b<=-1||
    (selected!==null&&!(typeof selected==='string'&&/^[A-Z0-9.\-]{1,15}$/.test(selected))))
   return unready('Historical window boundaries, exposure labels or after-fee returns are inconsistent.');
  priorEnd=testThrough;
  rw*=1+r;bw*=1+b;peakR=Math.max(peakR,rw);peakB=Math.max(peakB,bw);
  worstR=Math.min(worstR,rw/peakR-1);worstB=Math.min(worstB,bw/peakB-1);
  const excess=r-b;excesses.push(excess);
  if(excess>1e-10)outperform++;else if(excess< -1e-10)underperform++;else ties++;
  if(selected){nonCash++;perSymbol.set(selected,(perSymbol.get(selected)||0)+1);}
  windows.push({decisionDate,executionDate,testThrough,selection:selected||'Cash',excess:fix(excess),
   cumulativeModel:fix(rw-1),cumulativeBenchmark:fix(bw-1)});
 }
 const max=Math.max(...perSymbol.values(),0);
 const comparison=fix(rw-bw);
 return {ready:true,windowsEvaluated:rows.length,start:rows[0].executionDate,end:rows.at(-1).testThrough,
  outcomes:{modelReturn:fix(rw-1),benchmarkReturn:fix(bw-1),wealthDifference:comparison,
   modelMaxDrawdown:fix(worstR),benchmarkMaxDrawdown:fix(worstB),
   outperform,underperform,ties,cashWindows:rows.length-nonCash,
   exposureConcentration:nonCash?fix(max/nonCash):null,
   distinctSelectedCompanies:perSymbol.size},
  windows,limitations:[
   'Describes observed, non-overlapping evaluation intervals; no statistical independence or significance claim.',
   'Compounded return and drawdown use only the sampled evaluation windows; omitted boundary sessions are not represented.',
   'Company selection uses today\'s supported universe; delisted securities and distributions are absent.',
   'The screen and fee conventions are predefined; this is not a live investing track record.'
  ]};
}
function exportSafe(r){
 if(!r?.ready)return {schema:'quantforge.historical-attribution.v13.0',ready:false,reason:safe(r?.reason)};
 return {schema:'quantforge.historical-attribution.v13.0',ready:true,windowsEvaluated:r.windowsEvaluated,
  start:r.start,end:r.end,outcomes:{...r.outcomes},limitations:r.limitations.slice()};
}
const api=Object.freeze({study,exportSafe});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateHistoricalAttributionV130=api;
})(typeof window!=='undefined'?window:globalThis);
