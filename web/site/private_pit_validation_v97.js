/* QuantForge V9.7. Pure, filing-date-aware subset of the investment policy.
 * Does not simulate the entire Research Hub, trade, fetch, or store private data. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const sym=x=>typeof x==='string'&&/^[A-Z0-9.\-]{1,15}$/.test(x);
const date=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&
 !Number.isNaN(Date.parse(x))&&new Date(x).toISOString().slice(0,10)===x;
const accession=x=>typeof x==='string'&&/^\d{10}-\d{2}-\d{6}$/.test(x);
const fix=(x,n=5)=>finite(x)?Number(x.toFixed(n)):null;
const DAY=86400000;
function auditOne(company,asOf){
 const fail=reason=>({ready:false,reason,period:null,provenance:[]});
 if(!sym(company?.symbol)||!date(asOf)||!Array.isArray(company.annual))return fail('Issuer or filing metadata unavailable.');
 const annual=company.annual;
 const validRow=r=>r&&date(r.fiscal_end)&&r.fiscal_end<=asOf&&r.metrics&&r.sources;
 // The source snapshot includes only a recent subset of annual filings; do NOT extrapolate missing years.
 const eligible=annual.filter(validRow).map(row=>{
  const rev=row.metrics.revenue_usd,ocf=row.metrics.operating_cash_flow_usd,capex=row.metrics.capex_usd;
  const fields=['revenue_usd','operating_cash_flow_usd','capex_usd'];
  const evidence=fields.map(k=>({field:k,filed:row.sources[k]?.filed,accession:row.sources[k]?.accession,tag:row.sources[k]?.tag}));
  const reliable=fields.every((field,i)=>finite(row.metrics[field])&&date(evidence[i].filed)&&
    evidence[i].filed>=row.fiscal_end&&evidence[i].filed<=asOf&&accession(evidence[i].accession)&&
    typeof evidence[i].tag==='string'&&evidence[i].tag.length>1);
  const maxFiled=reliable?evidence.map(x=>x.filed).sort().at(-1):null;
  const fcf=reliable&&capex>=0?ocf-capex:null;
  // Cross-check the derived cash flow against the value embedded in the source snapshot.
  const consistent=fcf!==null&&finite(row.metrics.free_cash_flow_usd)&&
   Math.abs(fcf-row.metrics.free_cash_flow_usd)<=Math.max(1,Math.abs(fcf)*1e-8);
  return {end:row.fiscal_end,revenue:reliable&&rev>0?rev:null,fcf:consistent?fcf:null,
   maxFiled:reliable?maxFiled:null,provenance:evidence,valid:reliable&&consistent&&rev>0};
 }).filter(r=>r.valid&&r.maxFiled<=asOf).sort((a,b)=>b.end.localeCompare(a.end));
 if(eligible.length<2)return fail('At least two complete, dated, filing-supported annual reports were not publicly available.');
 const [latest,previous]=eligible;
 const separation=(Date.parse(latest.end)-Date.parse(previous.end))/DAY;
 if(separation<300||separation>430)return fail('Annual fiscal periods cannot be compared consistently.');
 if((Date.parse(asOf)-Date.parse(latest.end))/DAY>800)return fail('Most recent eligible annual financial statement is too old.');
 if(latest.maxFiled<=latest.end||previous.maxFiled<=previous.end)return fail('Publication evidence does not follow the fiscal period.');
 const growth=latest.revenue/previous.revenue-1;
 const margin=latest.fcf/latest.revenue;
 if(!finite(growth)||!finite(margin))return fail('Financial ratios are invalid.');
 return {ready:true,reason:null,period:latest.end,previousPeriod:previous.end,
  maxFiled:latest.maxFiled>previous.maxFiled?latest.maxFiled:previous.maxFiled,
  revenueGrowth:fix(growth),fcfMargin:fix(margin),
  provenance:[...latest.provenance,...previous.provenance].map(e=>({field:e.field,filed:e.filed,accession:e.accession,tag:e.tag}))};
}
function validatePrice(history,candidate){
 if(!sym(candidate)||!history||!Array.isArray(history.symbols)||history.symbols.length<2||history.symbols.length>5||
  new Set(history.symbols).size!==history.symbols.length||!history.symbols.includes(candidate)||
  !Array.isArray(history.dates)||history.dates.length<180||history.dates.length>2500||
  history.dates.some((d,i)=>!date(d)||(i>0&&d<=history.dates[i-1]))||
  history.dates.at(-1)>new Date().toISOString().slice(0,10)||
  !history.symbols.every(s=>sym(s)&&Array.isArray(history.closes?.[s])&&
   history.closes[s].length===history.dates.length&&history.closes[s].every(x=>finite(x)&&x>0)))return false;
 return true;
}
function drawdown(xs){let peak=xs[0],worst=0;for(const x of xs){peak=Math.max(peak,x);worst=Math.min(worst,x/peak-1);}return worst;}
function replay({snapshot,history,candidate,selection,train=126,step=21,maxDrawdown=.25,feeBps=10}={}){
 const fail=(reason,extra={})=>({ready:false,reason,counts:{planned:0,eligible:0,withheld:0},windows:[],summary:null,...extra});
 if(!Array.isArray(selection)||selection.length<2||selection.length>5||new Set(selection).size!==selection.length||
  !selection.every(sym)||!selection.includes(candidate)||!validatePrice(history,candidate)||
  selection.length!==history.symbols.length||selection.some(s=>!history.symbols.includes(s)))return fail('Load the exact current 2–5 company historical universe with aligned, finite prices.');
 if(!Number.isInteger(train)||train<63||train>504||!Number.isInteger(step)||step<5||step>63||
  !finite(maxDrawdown)||maxDrawdown<=0||maxDrawdown>=1||!finite(feeBps)||feeBps<0||feeBps>100)
  return fail('The historical rule or evaluation window is invalid.');
 if(!date(snapshot?.as_of)||!Array.isArray(snapshot?.companies)||snapshot.companies.length>500||
   snapshot.companies.some(c=>!sym(c?.symbol))||new Set(snapshot.companies.map(c=>c.symbol)).size!==snapshot.companies.length||
   !snapshot.companies.some(c=>c?.symbol===candidate))
  return fail('A valid SEC filing snapshot covering the tested market dates is not available.');
 const company=snapshot.companies.find(c=>c.symbol===candidate);
 const cutoff=company?.as_of||snapshot.as_of;
 if(!date(cutoff)||cutoff>new Date().toISOString().slice(0,10))return fail('SEC snapshot cutoff is missing or future dated.');
 const prices=history.closes[candidate],dates=history.dates;
 const windows=[];let planned=0,withheld=0,wealth=1,passive=1,weight=0,entries=0;
 const limitedReasons=new Set();
 for(let end=train-1;end+step<dates.length&&planned<80;end+=step){
  planned++;
  const point=dates[end]>cutoff?{ready:false,reason:'Decision date is after this issuer’s SEC snapshot cutoff.'}:auditOne(company,dates[end]);
  const next=dates[end+1],last=dates[end+step];
  if(!point.ready){withheld++;limitedReasons.add(point.reason);continue;}
  const dd=drawdown(prices.slice(end-train+1,end+1));
  const positive=point.revenueGrowth>0&&point.fcfMargin>0&&dd>=-maxDrawdown;
  const newWeight=positive?1:0;
  // Signal calculated at end-session close. Idealized execution at NEXT close; no same-bar fill.
  const gross=prices[end+step]/prices[end+1]-1;
  const fee=Math.abs(newWeight-weight)*feeBps/10000;
  const net=(1-fee)*(1+newWeight*gross)-1;
  if(!finite(gross)||!finite(net)||net<=-1)return fail('Invalid test-period return; all performance withheld.');
  wealth*=1+net;passive*=1+gross;
  if(windows.length===0)passive*=1-feeBps/10000;
  entries+=Math.abs(newWeight-weight);
  windows.push({decisionDate:dates[end],executionDate:next,testThrough:last,
   fiscalPeriod:point.period,latestFiled:point.maxFiled,
   revenueGrowth:point.revenueGrowth,fcfMargin:point.fcfMargin,
   trailingDrawdown:fix(dd),eligible:true,exposure:newWeight,
   observedTestReturn:fix(gross),observedAfterCosts:fix(net),
   sourceAccessions:[...new Set(point.provenance.map(s=>s.accession))].slice(0,6)});
  weight=newWeight;
 }
 if(!planned)return fail('Not enough nonoverlapping training and evaluation windows.');
 const counts={planned,eligible:windows.length,withheld};
 // Partial windows produce an evidence inventory, never a performance claim, because omissions induce sample bias.
 if(withheld||windows.length<2)return fail('No complete historical replay: missing or publication-ineligible statements in one or more scheduled windows.',{
  counts,windows:windows.slice(-12),withheldReasons:[...limitedReasons].slice(0,3),
  coverage:'partial; no cumulative return claimed'});
 const accepted=windows.filter(w=>w.exposure===1).length;
 return {ready:true,reason:null,counts,coverage:'all scheduled windows eligible',
  period:{from:windows[0].decisionDate,to:windows.at(-1).testThrough},
  policy:{train,step,maxDrawdown,feeBps,rule:'Positive annual revenue growth, positive FCF margin, and past-only drawdown no worse than threshold'},
  summary:{netRuleReturn:fix(wealth-1),netPassiveReturn:fix(passive-1),
   acceptedWindows:accepted,cashWindows:windows.length-accepted,weightChanges:entries},
  windows:windows.slice(-12),
  limitations:[
   'Only a restricted SEC filing-date-gated rule is reconstructed, not the complete current Research Hub decision engine.',
   'The source snapshot keeps only selected recent annual facts and can contain later restatements; historical coverage may be incomplete.',
   'Chosen investments, thresholds, and filing universe can reflect hindsight or survivorship; these results do not establish forecast skill.',
   'Next-close idealized execution, 10-K reporting lag, no dividends, financing, taxes, market impact, slippage or corporate-action adjustment.',
   'Independent evaluation windows can omit boundary returns; comparison uses identical observed test intervals for both strategies.'
  ]};
}
function safeSummary(x){
 const v=x||{};
 return {schema:'quantforge.filing-audit.v9.7',ready:v.ready===true,
  coverage:v.counts?{planned:v.counts.planned,eligible:v.counts.eligible,withheld:v.counts.withheld}:null,
  period:v.ready?v.period:null,policy:v.ready?v.policy:null,
  summary:v.ready?v.summary:null,reason:v.ready?null:String(v.reason||'Unavailable').slice(0,220),
  limitations:v.ready?v.limitations:[]};
}
const api=Object.freeze({auditOne,replay,safeSummary,validatePrice});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivatePointInTimeV97=api;
})(typeof window!=='undefined'?window:globalThis);
