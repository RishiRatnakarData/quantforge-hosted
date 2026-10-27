/* QuantForge private Decision Brief v7.2: pure, observed-data research, no calls/trades/storage. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
function dailyReturns(prices){
 if(!Array.isArray(prices)||prices.length<126||prices.length>800||prices.some(x=>!finite(x)||x<=0))throw Error('Invalid historical prices');
 return prices.slice(1).map((x,i)=>x/prices[i]-1);
}
function correlation(first,second){
 if(!Array.isArray(first)||!Array.isArray(second)||first.length!==second.length||first.length<30) return null;
 if(first.some(x=>!finite(x))||second.some(x=>!finite(x)))return null;
 const n=first.length,ax=first.reduce((a,b)=>a+b,0)/n,bx=second.reduce((a,b)=>a+b,0)/n;
 let xx=0,yy=0,xy=0;
 for(let i=0;i<n;i++){const a=first[i]-ax,b=second[i]-bx;xx+=a*a;yy+=b*b;xy+=a*b;}
 if(xx<=1e-20||yy<=1e-20)return null;
 const value=xy/Math.sqrt(xx*yy);
 return finite(value)?Math.max(-1,Math.min(1,value)):null;
}
function sameSessions(a,b){
 const d=a.dates,e=b.dates;
 if(!Array.isArray(d)||!Array.isArray(e)||d.length!==a.prices.length||e.length!==b.prices.length||d.length!==e.length||d.length<126)return false;
 return d.every((date,i)=>typeof date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(date)&&date===e[i]&&(i===0||date>d[i-1]));
}
function correlations(rows){
 if(!Array.isArray(rows)||rows.length<2)throw Error('At least two investments required');
 const pairs=[];let notAligned=0,undefinedVolatility=0;
 for(let i=0;i<rows.length;i++)for(let j=i+1;j<rows.length;j++){
  const a=rows[i],b=rows[j];
  if(!sameSessions(a,b)){notAligned++;continue;}
  const value=correlation(dailyReturns(a.prices),dailyReturns(b.prices));
  if(value===null){undefinedVolatility++;continue;}
  pairs.push({a:a.symbol,b:b.symbol,value,sessions:a.prices.length-1});
 }
 return {pairs:pairs.sort((a,b)=>b.value-a.value||a.a.localeCompare(b.a)||a.b.localeCompare(b.b)),notAligned,undefinedVolatility};
}
function virtualExposure(holdings,quotes,cash){
 if(!holdings||typeof holdings!=='object'||Array.isArray(holdings))return {held:[],complete:false,positions:[],note:'Virtual portfolio not loaded.'};
 const held=Object.keys(holdings).filter(s=>finite(Number(holdings[s]))&&Number(holdings[s])>0);
 let total=finite(cash)&&cash>=0?cash:0;let incomplete=!finite(cash)||cash<0;
 const positions=[];
 for(const symbol of held){
  const qty=Number(holdings[symbol]),price=quotes?.[symbol]?.price;
  if(!finite(price)||price<=0){incomplete=true;continue;}
  const value=qty*price;if(!finite(value)){incomplete=true;continue;}
  positions.push({symbol,value});total+=value;
 }
 // We cannot infer a reliable percentage if a held quote is missing.
 return {held,complete:!incomplete&&total>0,positions:!incomplete&&total>0?positions.map(x=>({symbol:x.symbol,weight:x.value/total})):[],note:incomplete?'Some virtual quotes are missing; position percentages are unavailable.':'Prices reflect observations, not executable quotes.'};
}
function build(rows,lens='balanced',fundamentals={},holdings={},quotes={},cash=0){
 const Ideas=root.QFPrivateIdeas;
 if(!Ideas||typeof Ideas.rank!=='function')throw Error('Research scoring module not available');
 if(!Array.isArray(rows)||rows.length<2||rows.length>10)throw Error('Choose 2–10 candidates');
 if(!['balanced','growth','defensive'].includes(lens))throw Error('Unknown research lens');
 const distinct=new Set(rows.map(x=>x.symbol));if(distinct.size!==rows.length)throw Error('Duplicate candidates');
 const all={};for(const perspective of ['balanced','growth','defensive'])all[perspective]=Ideas.rank(rows,perspective);
 const order=all[lens];const marketCorrelation=correlations(rows);const virtual=virtualExposure(holdings,quotes,cash);
 const comparisons=order.map((r,i)=>{
  const ranks=['balanced','growth','defensive'].map(p=>all[p].findIndex(x=>x.symbol===r.symbol)+1);
  const related=marketCorrelation.pairs.filter(p=>p.a===r.symbol||p.b===r.symbol);
  const strongest=related.length?related.reduce((a,b)=>Math.abs(b.value)>Math.abs(a.value)?b:a):null;
  const sec=fundamentals[r.symbol]||null;
  const cautions=[];
  if(r.metrics.annualVol>.40)cautions.push('Elevated historical volatility');
  if(r.metrics.maxDrawdown<-.25)cautions.push('Historical drawdown greater than 25%');
  if(r.metrics.quarterReturn<0)cautions.push('Recent price momentum is negative');
  if(strongest&&strongest.value>.80)cautions.push('Highly correlated with '+(strongest.a===r.symbol?strongest.b:strongest.a)+' in aligned history');
  if(sec&&finite(sec.fcfMargin)&&sec.fcfMargin<0)cautions.push('Negative reported FCF proxy margin');
  if(!sec)cautions.push('SEC business fundamentals not loaded or unavailable');
  const existing=virtual.held.includes(r.symbol);
  if(existing)cautions.push('Already present in virtual holdings');
  const concentration=virtual.positions.find(p=>p.symbol===r.symbol);
  if(concentration&&concentration.weight>.25)cautions.push('Virtual position already exceeds 25% of observed total');
  return {symbol:r.symbol,score:r.score,position:i+1,rankSpread:Math.max(...ranks)-Math.min(...ranks),rankRange:[Math.min(...ranks),Math.max(...ranks)],metrics:r.metrics,sec:sec?{revenueGrowth:sec.revenueGrowth,fcfMargin:sec.fcfMargin,fiscalEnd:sec.fiscalEnd,source:sec.source}:null,highestPair:strongest?{other:strongest.a===r.symbol?strongest.b:strongest.a,correlation:strongest.value,sessions:strongest.sessions}:null,held:existing,concentration:concentration?.weight??null,cautions};
 });
 const top= comparisons.slice(0,3).map(r=>r.symbol);
 const warnings=[];
 if(marketCorrelation.notAligned)warnings.push(marketCorrelation.notAligned+' pair(s) lack identical observed dates; cross-asset correlations were omitted.');
 if(marketCorrelation.undefinedVolatility)warnings.push('Some comparisons had zero/undefined return variability.');
 if(!virtual.complete&&virtual.held.length)warnings.push('Virtual position concentration is incomplete because a quote is unavailable.');
 warnings.push('Scores rank historical evidence within your selected universe; they do not estimate expected returns, intrinsic value, or an optimal buy time.');
 warnings.push('Prices exclude dividends; some equity histories use IEX-only coverage. SEC filings may lag market conditions.');
 return {lens,selected:rows.map(r=>r.symbol),top,comparisons,correlations:marketCorrelation,portfolio:virtual,warnings};
}
function report(brief,source,period){
 if(!brief||!Array.isArray(brief.comparisons)||!brief.comparisons.length)throw Error('No decision brief to export');
 const research=brief.comparisons.map(r=>({symbol:r.symbol,score:r.score,rank:r.position,rankRange:r.rankRange,rankSpread:r.rankSpread,metrics:r.metrics,sec:r.sec,mostCorrelated:r.highestPair,cautions:r.cautions.filter(x=>!x.toLowerCase().includes('virtual'))}));
 return {schema:'quantforge.decision-brief.v1',type:'historical-research-screen',historicalOnly:true,source:String(source||'Historical market observations'),requestedPeriod:String(period),selected:brief.selected,lens:brief.lens,topResearchPriorities:brief.top,results:research,correlationPairs:brief.correlations.pairs,unalignedPairs:brief.correlations.notAligned,limitations:brief.warnings.filter(x=>!x.toLowerCase().includes('virtual position')) .concat(['This export excludes virtual holdings, cash, account notes, credentials, raw licensed prices, and personally identifying information.','No valuations versus current market price, sector normalization, total-return data, expected returns, or investment suitability assessment.'])};
}
root.QFPrivateDecision=Object.freeze({dailyReturns,correlation,sameSessions,correlations,virtualExposure,build,report});
if(typeof module!=='undefined'&&module.exports)module.exports=root.QFPrivateDecision;
})(typeof window!=='undefined'?window:globalThis);
