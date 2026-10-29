/* QuantForge V9.6: pure historical risk-policy validation, financial statement
 * comparison, hypothetical allocation stress, and authenticated-note archive codec.
 * No network, browser storage, credentials or brokerage operations in this file. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const validDate=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;
const round=(v,n=4)=>finite(v)?Number(v.toFixed(n)):null;
const TAG='QF96|';
const symbol=s=>typeof s==='string'&&/^[A-Z0-9.\-]{1,15}$/.test(s);
function historyValid(h,s){
 return !!h&&Array.isArray(h.symbols)&&h.symbols.length>=2&&h.symbols.length<=5&&
  new Set(h.symbols).size===h.symbols.length&&h.symbols.includes(s)&&
  Array.isArray(h.dates)&&h.dates.length>=175&&h.dates.length<=2500&&
  h.dates.every((d,i)=>validDate(d)&&(!i||d>h.dates[i-1]))&&
  h.symbols.every(k=>symbol(k)&&Array.isArray(h.closes?.[k])&&
   h.closes[k].length===h.dates.length&&h.closes[k].every(p=>finite(p)&&p>0));
}
function maxDrawdown(xs){
 let peak=xs[0],worst=0;
 for(const x of xs){peak=Math.max(peak,x);worst=Math.min(worst,x/peak-1);}
 return worst;
}
function futureRiskScreen({history,symbol:focus,limit=.25,train=126,step=21,feeBps=10}={}){
 const fail=reason=>({ready:false,reason,windows:[],summary:null});
 if(!symbol(focus)||!historyValid(history,focus))return fail('Load matched historical data for the selected candidate before validating a rule.');
 if(!finite(limit)||limit<=0||limit>=1||!Number.isInteger(train)||train<63||train>504||
  !Number.isInteger(step)||step<5||step>63||!finite(feeBps)||feeBps<0||feeBps>100||
  history.dates.length<train+step*2)return fail('Risk rule, transaction cost, or evaluation window is invalid or insufficient.');
 if(history.dates.at(-1)>String(new Date().toISOString()).slice(0,10))return fail('Future-dated price observations are not permitted.');
 const p=history.closes[focus],windows=[];
 let model=1,passive=1,priorWeight=0,turnover=0;
 // Each window decision uses closes only through its training boundary.
 // First out-of-sample interval starts on the *next* daily close (decision-execution
 // timing is an idealized prior-close fill). Fees charged at weight changes.
 for(let end=train-1;end+step<p.length&&windows.length<80;end+=step){
  const trailing=maxDrawdown(p.slice(end-train+1,end+1));
  const allowed=trailing>=-limit,weight=allowed?1:0;
  const gross=p[end+step]/p[end]-1;
  const trading=Math.abs(weight-priorWeight)*feeBps/10000;
  const net=(1-trading)*(1+weight*gross)-1;
  if(!finite(net)||net<=-1||!finite(gross)||gross<=-1)return fail('A period contains an invalid historical return.');
  model*=1+net;
  // Buy-and-hold benchmark pays the same one-time entry fee, not recurrent fees.
  passive*=1+gross;
  if(!windows.length)passive*=1-feeBps/10000;
  turnover+=Math.abs(weight-priorWeight);
  windows.push({trainThrough:history.dates[end],outOfSampleFrom:history.dates[end+1],outOfSampleThrough:history.dates[end+step],
   trailingDrawdown:round(trailing),riskScreenPassed:allowed,modelWeight:weight,
   observedPeriodReturn:round(gross),netModelReturn:round(net),modelWealth:round(model),passiveWealth:round(passive)});
  priorWeight=weight;
 }
 if(windows.length<2||!finite(model)||!finite(passive)||model<=0||passive<=0)return fail('Insufficient complete, finite out-of-sample windows.');
 const risk=windows.filter(w=>!w.riskScreenPassed).length;
 const curve=xs=>Math.min(0,maxDrawdown([1,...xs]));
 return {ready:true,reason:null,symbol:focus,period:{firstTrainThrough:windows[0].trainThrough,
  testStart:windows[0].outOfSampleFrom,testEnd:windows.at(-1).outOfSampleThrough,
  windows:windows.length,observations:windows.length*step},
  summary:{netScreenReturn:round(model-1),netPassiveReturn:round(passive-1),
   screenMaxDrawdown:round(curve(windows.map(w=>w.modelWealth))),
   passiveMaxDrawdown:round(curve(windows.map(w=>w.passiveWealth))),
   blockedWindows:risk,investedWindows:windows.length-risk,turnover:round(turnover),feeBps},
  windows:windows.slice(-10),
  limitations:['Past-only drawdown rule with idealized boundary fills and one-way transaction costs; not a historically reconstructed SEC/valuation decision policy.',
   'No dividends, financing, taxes, slippage, cash yield, corporate actions or survivorship correction. Reported drawdowns are measured at evaluation-window ends; intra-window declines can be larger.',
   'The rule and investment universe were chosen with hindsight; these out-of-sample windows do not independently establish forecast skill.']};
}
function financialBridge({snapshot,selection,asOf}={}){
 const fail=reason=>({ready:false,reason,rows:[]});
 if(!Array.isArray(selection)||selection.length<2||selection.length>5||new Set(selection).size!==selection.length||!selection.every(symbol))return fail('Choose two to five valid issuers.');
 const now=String(asOf||'').slice(0,10),stamp=snapshot?.as_of;
 if(!validDate(now)||!validDate(stamp)||stamp>now||Date.parse(now)-Date.parse(stamp)>730*86400000||!Array.isArray(snapshot?.companies))return fail('An eligible dated SEC company snapshot is unavailable.');
 const map=new Map(snapshot.companies.filter(x=>symbol(x?.symbol)).map(x=>[x.symbol,x]));
 const rows=selection.map(s=>{
  const company=map.get(s),all=company?.annual;
  const current=all?.[0],last=all?.[1];
  const end=current?.fiscal_end,prior=last?.fiscal_end;
  const eligible=validDate(end)&&validDate(prior)&&prior<end&&end<=now&&
   (Date.parse(now)-Date.parse(end))/86400000<=800&&
   (Date.parse(end)-Date.parse(prior))/86400000>=300&&
   (Date.parse(end)-Date.parse(prior))/86400000<=430;
  if(!eligible)return {symbol:s,status:'unavailable',fiscalEnd:null,netIncome:null,fcf:null,fcfGrowth:null,fcfMargin:null,capexIntensity:null,cfoCoverage:null,source:null};
  const a=current.metrics||{},b=last.metrics||{};
  const rev=finite(a.revenue_usd)&&a.revenue_usd>0?a.revenue_usd:null;
  const fcf=finite(a.free_cash_flow_usd)?a.free_cash_flow_usd:null;
  const old=finite(b.free_cash_flow_usd)?b.free_cash_flow_usd:null;
  const cash=finite(a.operating_cash_flow_usd)?a.operating_cash_flow_usd:null;
  const capex=finite(a.capex_usd)?a.capex_usd:null;
  const netIncome=finite(a.net_income_usd)?a.net_income_usd:null;
  return {symbol:s,status:fcf!==null?'reported':'incomplete',fiscalEnd:end,netIncome,
   fcf,fcfGrowth:fcf!==null&&fcf>0&&old!==null&&old>0?round(fcf/old-1):null,
   fcfMargin:fcf!==null&&rev!==null?round(fcf/rev):null,
   capexIntensity:capex!==null&&rev!==null?round(Math.abs(capex)/rev):null,
   cfoCoverage:cash!==null&&netIncome!==null&&netIncome>0?round(cash/netIncome):null,
   source:typeof company.source_url==='string'&&company.source_url.startsWith('https://data.sec.gov/')?company.source_url:null};
 });
 return {ready:true,reason:null,snapshotDate:stamp,rows,coverage:rows.filter(x=>x.status==='reported').length,
  note:'Reported fiscal periods can differ. These observations are business cash-flow quality indicators, not equity values, normalized industry rankings, investment returns or stock-price targets.'};
}
function allocationStress({portfolio,quotes,history,asOf,symbol:focus,steps=[.02,.05,.10]}={}){
 const fail=reason=>({ready:false,reason,rows:[]});
 if(!symbol(focus)||!Array.isArray(steps)||steps.length!==3||steps.some((x,i)=>!finite(x)||x<=0||x>.2||(i&&x<=steps[i-1])))return fail('The candidate or scenario sizes are invalid.');
 const base=root.QFPrivatePortfolioValidationV95?.portfolioRisk({portfolio,quotes,history,asOf,symbol:focus,maxWeight:1});
 if(!base?.ready||!base.baseline||!base.period||!base.allocation)return fail(base?.reason||'Complete matched account history is required for weighted portfolio stress.');
 if(!history.symbols.includes(focus))return fail('The candidate is not in the fully loaded portfolio history.');
 const positions=base.allocation.positions;
 const total=portfolio.cash+positions.reduce((sum,x)=>sum+portfolio.holdings[x.symbol]*quotes[x.symbol].price,0);
 if(!finite(total)||total<=0)return fail('Validated portfolio total is unavailable.');
 const weights=Object.fromEntries(positions.map(x=>[x.symbol,portfolio.holdings[x.symbol]*quotes[x.symbol].price/total]));
 const cash=portfolio.cash/total;
 const ret=Object.fromEntries(history.symbols.map(s=>[s,history.closes[s].slice(1).map((x,i)=>x/history.closes[s][i]-1)]));
 const daily=(w)=>ret[focus].map((_,i)=>Object.entries(w).reduce((t,[s,p])=>t+p*ret[s][i],0));
 const metrics=(w)=>{
  const series=daily(w),n=series.length,mean=series.reduce((a,b)=>a+b,0)/n;
  const varr=series.reduce((a,b)=>a+(b-mean)**2,0)/(n-1);
  const order=[...series].sort((a,b)=>a-b),threshold=order[Math.floor(.05*(n-1))],tail=order.filter(x=>x<=threshold);
  let wealth=1,peak=1,dd=0;
  for(const x of series){wealth*=1+x;if(!finite(wealth)||wealth<=0)return null;peak=Math.max(peak,wealth);dd=Math.min(dd,wealth/peak-1);}
  return {annualVolatility:round(Math.sqrt(varr)*Math.sqrt(history.sessions_per_year===365?365:252)),
   dailyES95:round(Math.max(0,-tail.reduce((a,b)=>a+b,0)/tail.length)),maxDrawdown:round(dd)};
 };
 const before=metrics(weights);
 if(!before)return fail('Cannot validate historical stress outcomes.');
 const rows=steps.map(share=>{
  if(share>cash+1e-6)return {additionalCashPercent:round(100*share,1),ready:false,reason:'Insufficient virtual cash for this scenario.'};
  const adjusted={...weights,[focus]:(weights[focus]||0)+share},after=metrics(adjusted);
  if(!after)return {additionalCashPercent:round(100*share,1),ready:false,reason:'Historical scenario is numerically invalid.'};
  return {ready:true,additionalCashPercent:round(100*share,1),newCandidateWeight:round(adjusted[focus]),
   newCashWeight:round(cash-share),annualVolatility:after.annualVolatility,deltaVolatility:round(after.annualVolatility-before.annualVolatility),
   dailyES95:after.dailyES95,maxDrawdown:after.maxDrawdown};
 });
 return {ready:true,reason:null,base:before,period:base.period,rows,
  note:'Constant current weights over historical price-only returns; cash-funded hypothetical positions do not place trades. Risk is sample-dependent and may understate future losses.'};
}
function archiveRecord(brief,when){
 if(brief?.schema!=='quantforge.research-brief.v9.3'||!symbol(brief.symbol)||
  !validDate(String(when||'').slice(0,10))||typeof brief.action!=='string'||
  !Array.isArray(brief.universe)||brief.universe.length<2||brief.universe.length>5)throw Error('A current completed, valid assessment is required.');
 const payload={v:1,date:String(when).slice(0,10),symbol:brief.symbol,
  action:brief.action.slice(0,95),readiness:String(brief.readiness||'').slice(0,50),
  covered:Math.min(99,Math.max(0,Number(brief.modelCoverage?.completed)||0)),
  universe:brief.universe.map(x=>x.symbol).filter(symbol).slice(0,5),
  policy:String(brief.policy||'').slice(0,55)};
 if(payload.universe.length!==brief.universe.length||!payload.universe.includes(payload.symbol))throw Error('Invalid investment universe.');
 return {text:TAG+JSON.stringify(payload),symbol:payload.symbol,at:String(when)};
}
function readArchive(note){
 if(!note||typeof note.text!=='string'||!note.text.startsWith(TAG))return null;
 if(note.text.length>1100)return null;
 try{
  const x=JSON.parse(note.text.slice(TAG.length));
  if(x.v!==1||!validDate(x.date)||!symbol(x.symbol)||typeof x.action!=='string'||x.action.length>95||
   typeof x.readiness!=='string'||x.readiness.length>50||!Number.isInteger(x.covered)||x.covered<0||x.covered>99||
   !Array.isArray(x.universe)||x.universe.length<2||x.universe.length>5||!x.universe.every(symbol)||
   !x.universe.includes(x.symbol)||typeof x.policy!=='string'||x.policy.length>55)return null;
  return {date:x.date,symbol:x.symbol,action:x.action,readiness:x.readiness,covered:x.covered,universe:[...x.universe],policy:x.policy};
 }catch(_){return null;}
}
function safeSummary(packet){
 if(packet?.schema!=='quantforge.intelligence.v9.6')throw Error('Unexpected assessment diagnostics.');
 return {schema:'quantforge.intelligence-summary.v9.6',asOf:packet.asOf,
  historicalRiskScreenAvailable:packet.historical.ready,
  secCompanyCoverage:packet.financial.ready?packet.financial.coverage:0,
  weightedPortfolioStressAvailable:packet.allocation.ready,
  limitations:['Account balances, positions, position weights, prices, historical series and provider credentials are not exported.',
   'Historical risk screens are not an end-to-end investment policy validation.']};
}
function build({history,symbol:focus,snapshot,selection,portfolio,quotes,asOf,limit,feeBps=10}={}){
 const historical=futureRiskScreen({history,symbol:focus,limit,feeBps});
 const financial=financialBridge({snapshot,selection,asOf});
 const allocation=allocationStress({portfolio,quotes,history,asOf,symbol:focus});
 return {schema:'quantforge.intelligence.v9.6',asOf:String(asOf||'').slice(0,10),historical,financial,allocation};
}
const api=Object.freeze({build,futureRiskScreen,financialBridge,allocationStress,archiveRecord,readArchive,safeSummary,TAG});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateResearchIntelligenceV96=api;
})(typeof window!=='undefined'?window:globalThis);
