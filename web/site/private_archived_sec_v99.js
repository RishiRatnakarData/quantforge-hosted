/* QuantForge V9.9: local, revision-aware SEC filing archive point-in-time validation.
 * User-imported archive is never fetched, transmitted, persisted or used to trade.
 * This is a restricted historical rule, not a complete decision-engine backtest. */
(function(root){
'use strict';
const FIELDS=['revenue_usd','operating_cash_flow_usd','capex_usd'];
const TAGS=Object.freeze({
 revenue_usd:['RevenueFromContractWithCustomerExcludingAssessedTax','RevenueFromContractWithCustomerIncludingAssessedTax','Revenues','SalesRevenueNet'],
 operating_cash_flow_usd:['NetCashProvidedByUsedInOperatingActivities','NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'],
 capex_usd:['PaymentsToAcquirePropertyPlantAndEquipment']
});
const isDate=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&!Number.isNaN(Date.parse(x))&&new Date(x).toISOString().slice(0,10)===x;
const symbol=x=>typeof x==='string'&&/^[A-Z0-9.\-]{1,15}$/.test(x);
const accession=x=>typeof x==='string'&&/^\d{10}-\d{2}-\d{6}$/.test(x);
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const today=()=>new Date().toISOString().slice(0,10);
const dayDiff=(a,b)=>(Date.parse(b)-Date.parse(a))/86400000;
const fix=x=>finite(x)?Number(x.toFixed(6)):null;
const bounded=x=>String(x||'Unavailable').slice(0,160);
function validateArchive(input,snapshot){
 const fail=reason=>({ready:false,reason,archive:null});
 if(!input||input.schema!=='quantforge.sec.filing-revisions.v9.8'||!isDate(input.as_of)||input.as_of>today()||
   !Array.isArray(input.companies)||input.companies.length<1||input.companies.length>100||
   !Array.isArray(snapshot?.companies)||snapshot.companies.length>500||new Set(snapshot.companies.map(c=>c.symbol)).size!==snapshot.companies.length)
  return fail('Archive schema, cutoff, size, or SEC reference snapshot is invalid.');
 const registry=new Map(snapshot.companies.map(c=>[c.symbol,c.cik]));
 const seen=new Set();let totalVersions=0;
 for(const issuer of input.companies){
  if(!symbol(issuer?.symbol)||seen.has(issuer.symbol)||!Number.isSafeInteger(issuer.cik)||issuer.cik<=0||
   registry.get(issuer.symbol)!==issuer.cik||!Array.isArray(issuer.annual)||
   issuer.annual.length<1||issuer.annual.length>25)return fail('Duplicate, unsupported, or CIK-mismatched archive issuer.');
  seen.add(issuer.symbol);
  const periodSet=new Set();
  for(const period of issuer.annual){
   if(!isDate(period?.fiscal_end)||period.fiscal_end>input.as_of||periodSet.has(period.fiscal_end)||
     !period.revisions||typeof period.revisions!=='object')return fail('Duplicate or invalid annual filing period.');
   periodSet.add(period.fiscal_end);
   for(const field of FIELDS){
    const entries=period.revisions[field];
    if(!Array.isArray(entries)||entries.length>500)return fail('Missing or excessive filing revisions.');
    totalVersions+=entries.length;
    if(totalVersions>250000)return fail('Archive exceeds safe source-row limit.');
    const duplicate=new Map();
    for(const version of entries){
     if(!isDate(version?.start)||!isDate(version.filed)||version.filed>input.as_of||
       version.filed<period.fiscal_end||dayDiff(version.start,period.fiscal_end)<330||
       dayDiff(version.start,period.fiscal_end)>400||!accession(version.accession)||
       typeof version.tag!=='string'||!TAGS[field].includes(version.tag)||
       !Number.isInteger(version.tag_priority)||version.tag_priority!==TAGS[field].indexOf(version.tag)||
       !finite(version.value)||Math.abs(version.value)>=1e16||
       (field==='capex_usd'&&version.value<0))return fail('Invalid source lineage, period, or SEC annual value.');
     const key=[version.start,version.filed,version.accession,version.tag].join('|');
     if(duplicate.has(key)&&duplicate.get(key)!==version.value)return fail('Conflicting duplicate source facts.');
     duplicate.set(key,version.value);
    }
   }
  }
 }
 return {ready:true,reason:null,archive:input,issuerCount:seen.size,versionCount:totalVersions,asOf:input.as_of};
}
function choose(entries,period,asOf){
 const eligible=entries.filter(x=>x.filed<=asOf&&x.filed>=period&&
    dayDiff(x.start,period)>=330&&dayDiff(x.start,period)<=400);
 if(!eligible.length)return null;
 const last=eligible.reduce((a,x)=>x.filed>a?x.filed:a,'0000-00-00');
 const latest=eligible.filter(x=>x.filed===last);
 const priority=Math.min(...latest.map(x=>x.tag_priority));
 const preferred=latest.filter(x=>x.tag_priority===priority);
 if(new Set(preferred.map(x=>x.value)).size!==1)return null;
 return {value:preferred[0].value,filed:last,source:preferred[0].accession,
  revised:eligible.some(x=>x.filed<last)};
}
function auditAt(issuer,asOf){
 const fail=reason=>({ready:false,reason});
 if(!isDate(asOf)||!issuer||!Array.isArray(issuer.annual))return fail('Missing archival filing evidence.');
 const annual=[];
 for(const period of issuer.annual){
  if(period.fiscal_end>asOf)continue;
  const found=Object.fromEntries(FIELDS.map(field=>[field,choose(period.revisions[field],period.fiscal_end,asOf)]));
  if(FIELDS.some(field=>!found[field]))continue;
  if(found.revenue_usd.value<=0||found.capex_usd.value<0)continue;
  annual.push({fiscalEnd:period.fiscal_end,revenue:found.revenue_usd.value,
   cashFlow:found.operating_cash_flow_usd.value-found.capex_usd.value,
   latestFiled:FIELDS.map(f=>found[f].filed).sort().at(-1),
   laterVersion:FIELDS.some(f=>found[f].revised)});
 }
 annual.sort((a,b)=>b.fiscalEnd.localeCompare(a.fiscalEnd));
 if(annual.length<2)return fail('Two fully filed fiscal years are not available by this decision date.');
 const latest=annual[0],previous=annual[1];
 const spacing=dayDiff(previous.fiscalEnd,latest.fiscalEnd);
 if(spacing<300||spacing>430)return fail('The two most recent available annual periods are not consecutive.');
 if(dayDiff(latest.fiscalEnd,asOf)>800)return fail('Most recent available fiscal year is too old.');
 const growth=latest.revenue/previous.revenue-1,margin=latest.cashFlow/latest.revenue;
 if(!finite(growth)||!finite(margin))return fail('Invalid point-in-time financial ratios.');
 return {ready:true,period:latest.fiscalEnd,previousPeriod:previous.fiscalEnd,
  latestFiled:latest.latestFiled>previous.latestFiled?latest.latestFiled:previous.latestFiled,
  revenueGrowth:fix(growth),fcfMargin:fix(margin),usedLaterVersion:latest.laterVersion||previous.laterVersion};
}
function trailingDrawdown(values){let p=values[0],worst=0;for(const x of values){p=Math.max(p,x);worst=Math.min(worst,x/p-1);}return worst;}
function run({archive,snapshot,history,selection,candidate,train=126,step=21,maxDrawdown=.25,feeBps=10}={}){
 const fail=reason=>({ready:false,reason,counts:{scheduled:0,completeUniverse:0,withheld:0},
  issuers:[],performance:{ready:false,reason:'Historical evaluation unavailable.'}});
 const validated=validateArchive(archive,snapshot);
 if(!validated.ready)return fail(validated.reason);
 const pit=root.QFPrivatePointInTimeV97;
 if(!pit||!pit.validatePrice(history,candidate)||!Array.isArray(selection)||selection.length<2||selection.length>5||
   new Set(selection).size!==selection.length||selection.some(s=>!symbol(s)||!history.symbols.includes(s))||
   selection.length!==history.symbols.length||!selection.includes(candidate))return fail('Select and load the exact dated 2–5-investment research universe.');
 if(!Number.isInteger(train)||train<63||train>504||!Number.isInteger(step)||step<5||step>63||
   !finite(maxDrawdown)||maxDrawdown<=0||maxDrawdown>=1||!finite(feeBps)||feeBps<0||feeBps>100)
  return fail('Invalid historical screening configuration.');
 const bySymbol=new Map(archive.companies.map(x=>[x.symbol,x]));
 const dates=history.dates;
 const boundaries=[];
 for(let end=train-1;end+step<dates.length&&boundaries.length<80;end+=step)boundaries.push(end);
 if(boundaries.length<2)return fail('At least two historical evaluation windows are required.');
 const coverage=new Map(selection.map(s=>[s,{symbol:s,scheduled:boundaries.length,eligible:0,withheld:0,
  laterRevisionWindows:0,firstEligible:null,lastEligible:null,primaryGap:null,_gaps:new Map()}]));
 let full=0,wealth=1,passive=1,priorExposure=0,changes=0,accepted=0;
 const windows=[];
 for(const end of boundaries){
  const decision=dates[end];const eligible=new Map();
  for(const s of selection){
   const issuer=bySymbol.get(s);
   const evidence=issuer&&decision<=archive.as_of?auditAt(issuer,decision):
    {ready:false,reason:issuer?'Decision date is after local archive source cutoff.':'Issuer is absent from the imported filing archive.'};
   const row=coverage.get(s);
   if(evidence.ready){row.eligible++;eligible.set(s,evidence);
    if(evidence.usedLaterVersion)row.laterRevisionWindows++;
    if(!row.firstEligible)row.firstEligible=decision;
    row.lastEligible=decision;
   }else{row.withheld++;const reason=bounded(evidence.reason);
    row._gaps.set(reason,(row._gaps.get(reason)||0)+1);}
  }
  if(eligible.size!==selection.length)continue;
  full++;
  const point=eligible.get(candidate),prices=history.closes[candidate];
  const dd=trailingDrawdown(prices.slice(end-train+1,end+1));
  const exposure=point.revenueGrowth>0&&point.fcfMargin>0&&dd>=-maxDrawdown?1:0;
  const gross=prices[end+step]/prices[end+1]-1;
  const cost=Math.abs(exposure-priorExposure)*feeBps/10000;
  const net=(1-cost)*(1+exposure*gross)-1;
  if(!finite(gross)||!finite(net)||net<=-1)return fail('Invalid observed evaluation returns.');
  wealth*=1+net;passive*=1+gross;
  if(windows.length===0)passive*=1-feeBps/10000;
  accepted+=exposure;changes+=Math.abs(exposure-priorExposure);priorExposure=exposure;
  windows.push({decisionDate:decision,executionDate:dates[end+1],testThrough:dates[end+step],
   fiscalYear:point.period,exposure,observedGrossReturn:fix(gross),observedRuleReturn:fix(net)});
 }
 const rows=selection.map(s=>{
  const r=coverage.get(s),gap=[...r._gaps].sort((a,b)=>b[1]-a[1])[0];
  return {symbol:s,scheduled:r.scheduled,eligible:r.eligible,withheld:r.withheld,
   coveragePct:fix(100*r.eligible/r.scheduled),laterRevisionWindows:r.laterRevisionWindows,
   firstEligible:r.firstEligible,lastEligible:r.lastEligible,primaryGap:gap?{reason:gap[0],count:gap[1]}:null};
 });
 const complete=full===boundaries.length;
 return {ready:true,reason:null,archiveAsOf:archive.as_of,archivedIssuers:validated.issuerCount,
  sourceVersions:validated.versionCount,counts:{scheduled:boundaries.length,completeUniverse:full,withheld:boundaries.length-full},
  issuers:rows,performance:complete?{ready:true,
   policy:'Filing-date-eligible revenue growth > 0, FCF margin > 0, and trailing drawdown inside threshold',
   ruleReturn:fix(wealth-1),passiveReturn:fix(passive-1),investedWindows:accepted,
   cashWindows:windows.length-accepted,weightChanges:changes,feeBps,maxDrawdown,
   testedFrom:windows[0].executionDate,testedThrough:windows.at(-1).testThrough,
   windows:windows.slice(-8)}:{ready:false,reason:'Cumulative historical returns withheld because one or more scheduled decision windows lacks full issuer coverage.',
   availableWindows:full,requiredWindows:boundaries.length},
  limitations:[
   'SEC Company Facts may omit original superseded filing versions; archival completeness cannot be assumed.',
   'Historical companies were selected today; this is not a survivorship-bias-free point-in-time universe.',
   'Only a restricted historical rule is replayed, not the full contemporary Research Hub model.',
   'Price-only next-close returns exclude dividends, corporate actions, spread, slippage, taxes and market impact.',
   'The archive is imported locally and kept only in browser memory; no automatic brokerage transactions.'
  ]};
}
function exportSafe(result){
 if(!result||result.ready!==true)return {schema:'quantforge.archived-sec-evidence.v9.9',ready:false,reason:bounded(result?.reason)};
 return {schema:'quantforge.archived-sec-evidence.v9.9',ready:true,archiveAsOf:result.archiveAsOf,
  archivedIssuers:result.archivedIssuers,counts:{...result.counts},
  issuers:result.issuers.map(r=>({symbol:r.symbol,scheduled:r.scheduled,eligible:r.eligible,withheld:r.withheld,
   coveragePct:r.coveragePct,laterRevisionWindows:r.laterRevisionWindows})),
  performance:result.performance.ready?{ready:true,ruleReturn:result.performance.ruleReturn,
   passiveReturn:result.performance.passiveReturn,feeBps:result.performance.feeBps,
   testedFrom:result.performance.testedFrom,testedThrough:result.performance.testedThrough}:
   {ready:false,reason:bounded(result.performance.reason)},limitations:result.limitations.slice(0,5)};
}
const api=Object.freeze({validateArchive,auditAt,run,exportSafe});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateArchivedSECValidationV99=api;
})(typeof window!=='undefined'?window:globalThis);
