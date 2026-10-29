/* V9.4: private, pure cross-investment evidence and policy sensitivity.
 * Uses published SEC annual observations and already-loaded authenticated history.
 * It cannot fetch, save, mutate portfolios or issue broker orders. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const bounded=x=>String(x??'').slice(0,180);
const validDate=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;
const pct=x=>finite(x)?Math.round(x*10000)/100:null;
const returns=prices=>prices.slice(1).map((p,i)=>Math.log(p/prices[i]));
function correlation(a,b){
 if(a.length!==b.length||a.length<63)return null;
 const n=a.length,ma=a.reduce((s,v)=>s+v,0)/n,mb=b.reduce((s,v)=>s+v,0)/n;
 let xy=0,xx=0,yy=0;
 for(let i=0;i<n;i++){const x=a[i]-ma,y=b[i]-mb;xy+=x*y;xx+=x*x;yy+=y*y;}
 return xx>1e-14&&yy>1e-14?Math.max(-1,Math.min(1,xy/Math.sqrt(xx*yy))):null;
}
function compareSEC(snapshot,selection,asOf){
 if(!Array.isArray(selection)||selection.length<2||selection.length>5||new Set(selection).size!==selection.length)throw Error('Invalid investment selection.');
 const date=String(asOf||'').slice(0,10),snapshotDate=snapshot?.as_of;
 const validSnapshot=validDate(date)&&validDate(snapshotDate)&&snapshotDate<=date&&Date.parse(date)-Date.parse(snapshotDate)<=730*86400000&&Array.isArray(snapshot?.companies);
 const lookup=new Map(validSnapshot?snapshot.companies.map(c=>[c.symbol,c]):[]);
 const rows=selection.map(symbol=>{
  const c=lookup.get(symbol),a=c?.annual?.[0],prior=c?.annual?.[1];
  const fiscal=a?.fiscal_end,older=prior?.fiscal_end;
  const valid=!!c&&validDate(fiscal)&&validDate(older)&&older<fiscal&&fiscal<=date&&
   Date.parse(date)-Date.parse(fiscal)<=800*86400000&&
   (Date.parse(fiscal)-Date.parse(older))/86400000>=300&&
   (Date.parse(fiscal)-Date.parse(older))/86400000<=430;
  const cur=valid?a.metrics||{}:{},prev=valid?prior.metrics||{}:{};
  const rev=finite(cur.revenue_usd)&&cur.revenue_usd>0?cur.revenue_usd:null;
  const yoy=rev!==null&&finite(prev.revenue_usd)&&prev.revenue_usd>0?cur.revenue_usd/prev.revenue_usd-1:null;
  const op=rev!==null&&finite(cur.operating_income_usd)?cur.operating_income_usd/rev:null;
  const fcf=rev!==null&&finite(cur.free_cash_flow_usd)?cur.free_cash_flow_usd/rev:null;
  const observed=[yoy,op,fcf].filter(finite).length;
  return {symbol:bounded(symbol),name:bounded(c?.name||symbol),status:valid?(observed?'reported':'incomplete'):'unavailable',
   fiscalEnd:valid?fiscal:null,filingCutoff:valid?snapshotDate:null,
   revenueUsd:rev,yearlyGrowthPercent:pct(yoy),operatingMarginPercent:pct(op),freeCashFlowMarginPercent:pct(fcf),
   coverage:observed,source:valid?bounded(c.source_url):null};
 });
 const fiscalYears=new Set(rows.filter(r=>r.fiscalEnd).map(r=>r.fiscalEnd.slice(0,4)));
 return {rows,available:rows.filter(r=>r.status==='reported').length,asOf:validSnapshot?snapshotDate:null,
  note:!validSnapshot?'The published SEC snapshot is missing, invalid or too old for this assessment.':
   'SEC annual reporting periods differ across issuers; fiscal year comparisons are not synchronized. Public SEC snapshot is separate from authenticated private company research.',
  mismatchedFiscalYears:fiscalYears.size>1};
}
function comovement(history,selection){
 const failure=reason=>({ready:false,reason,rows:[],period:null,averagePairCorrelation:null});
 if(!Array.isArray(selection)||selection.length<2||selection.length>5||new Set(selection).size!==selection.length||
  !history||!Array.isArray(history.symbols)||history.symbols.length!==selection.length||
  !history.symbols.every(s=>selection.includes(s))||!Array.isArray(history.dates)||history.dates.length<64||history.dates.length>2500||
  history.dates.some((d,i)=>!validDate(d)||(i&&history.dates[i-1]>=d)))return failure('Aligned market observations are unavailable.');
 const series={};
 for(const s of selection){
  const ps=history.closes?.[s];
  if(!Array.isArray(ps)||ps.length!==history.dates.length||ps.some(x=>!finite(x)||x<=0))return failure('Invalid or incomplete observed prices.');
  series[s]=returns(ps);
 }
 const pairs=[];
 for(let i=0;i<selection.length;i++)for(let j=i+1;j<selection.length;j++){
  const value=correlation(series[selection[i]],series[selection[j]]);
  if(value===null)return failure('At least one selected return series has no measurable variance.');
  pairs.push({a:selection[i],b:selection[j],value});
 }
 const rows=selection.map(symbol=>({symbol:bounded(symbol),averagePeerCorrelation:Math.round(1000*
  (pairs.filter(p=>p.a===symbol||p.b===symbol).reduce((sum,p)=>sum+p.value,0)/(selection.length-1)))/1000}));
 const mean=pairs.reduce((sum,p)=>sum+p.value,0)/pairs.length;
 return {ready:true,reason:null,rows,averagePairCorrelation:Math.round(1000*mean)/1000,
  period:{start:history.dates[0],end:history.dates.at(-1),sessions:history.dates.length},
  caveat:'Historical correlations describe co-movement within this selected research universe, not holdings-weighted portfolio diversification or future correlation.'};
}
function sensitivity(variants,base){
 if(!Array.isArray(variants)||variants.length!==3||!base||typeof base.action!=='string')
  throw Error('Three comparable policy variants and original decision required.');
 const labels=['Conservative','Balanced','Growth-oriented'];
 const rows=variants.map((v,i)=>{
  if(!v||typeof v.decision!=='string'||typeof v.readiness!=='string'||v.symbol!==base.symbol)
   throw Error('Incompatible policy sensitivity input.');
  return {risk:labels[i],action:bounded(v.decision),readiness:bounded(v.readiness)};
 });
 return {rows,sameAction:rows.every(r=>r.action===rows[0].action),baselineAction:bounded(base.action),
  note:'Counterfactual screen settings reuse the same dated evidence. Differences reflect policy assumptions, not calibrated forecast probabilities or historical policy backtesting.'};
}
function build({brief,snapshot,selection,history,variants,asOf}={}){
 if(brief?.schema!=='quantforge.research-brief.v9.3'||!Array.isArray(selection)||!selection.includes(brief.symbol)||
  selection.length!==brief.universe.length||!selection.every((s,i)=>s===brief.universe[i]?.symbol))
  throw Error('Current V9.3 briefing and selected investment universe must match.');
 const sec=compareSEC(snapshot,selection,asOf);
 const movement=comovement(history,selection);
 const policies=sensitivity(variants,brief);
 return {schema:'quantforge.investment-intelligence.v9.4',symbol:brief.symbol,selection:[...selection],asOf:String(asOf||'').slice(0,10),
  baselineAction:brief.action,sec,comovement:movement,policies,
  coverage:{issuersWithMetrics:sec.available,selected:selection.length,historyAligned:movement.ready},
  boundaries:['SEC annual fiscal periods differ and may be stale.','Not all selected investments have SEC company statements (for example ETFs or crypto).',
   'Risk correlation is historical and equally compares selected securities, not the authenticated account holdings.',
   'Policy sensitivity is not forward-looking model validation or trading advice.','Detailed private-company policy still evaluates the selected focus candidate, not all issuers.']};
}
const api=Object.freeze({build,compareSEC,comovement,sensitivity});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateInvestmentIntelligenceV94=api;
})(typeof window!=='undefined'?window:globalThis);
