/* QuantForge V7.4 — read-only virtual portfolio allocation and risk counterfactual. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const round=x=>Math.round((x+Number.EPSILON)*1e10)/1e10;
function dateAgeDays(then,now){
 if(typeof then!=='string'||typeof now!=='string'||!then.includes('T'))return null;
 const a=Date.parse(then),b=Date.parse(now);
 if(!Number.isFinite(a)||!Number.isFinite(b)||a>b)return null;
 return (b-a)/86400000;
}
function scenario(input){
 const {holdings,cash,quotes,symbol,budget,nowISO}=input||{};
 if(!holdings||typeof holdings!=='object'||Array.isArray(holdings)||!quotes||typeof quotes!=='object'||Array.isArray(quotes))throw Error('Portfolio or quotes unavailable.');
 if(!finite(cash)||cash<0)throw Error('Virtual cash balance unavailable.');
 if(typeof symbol!=='string'||!(/^[A-Z0-9][A-Z0-9.\/-]{0,19}$/).test(symbol))throw Error('Choose a valid investment from the list.');
 if(!finite(budget)||budget<1||budget>1e9)throw Error('Enter a purchase budget between $1 and $1 billion.');
 if(budget>cash)throw Error('Proposed purchase exceeds available virtual cash.');
 const units={},values={},warnings=[];
 let invested=0;
 for(const [ticker,raw] of Object.entries(holdings)){
  if(!(/^[A-Z0-9][A-Z0-9.\/-]{0,19}$/).test(ticker))throw Error('Unrecognized holding symbol.');
  const qty=Number(raw);
  if(!finite(qty)||qty<0)throw Error('Invalid holding quantity for '+ticker+'.');
  if(qty===0)continue;
  units[ticker]=qty;
 }
 const required=[...new Set([...Object.keys(units),symbol])];
 if(required.length>60)throw Error('Too many holdings to evaluate.');
 for(const ticker of required){
  const q=quotes[ticker];
  const age=dateAgeDays(q?.timestamp,nowISO);
  if(!finite(q?.price)||q.price<=0||age===null||age>7)throw Error('Recent observed quote unavailable for '+ticker+'. Refresh quotes before comparing.');
  if(age>3)warnings.push(ticker+' quote is over three days old (possibly a weekend or market holiday).');
  const value=(units[ticker]||0)*q.price;
  if(!finite(value))throw Error('Holding valuation overflow for '+ticker+'.');
  if(value>0){values[ticker]=value;invested+=value;}
 }
 const total=cash+invested;
 if(!finite(total)||total<=0)throw Error('Positive total virtual portfolio value is required.');
 const purchaseQuote=quotes[symbol],unitsBought=budget/purchaseQuote.price;
 if(!finite(unitsBought)||unitsBought<=0)throw Error('Purchase units could not be computed.');
 const futureValues={...values,[symbol]:(values[symbol]||0)+budget};
 const afterCash=Math.max(0,cash-budget);
 const make=(valueMap,available)=>{
  const items=Object.keys(valueMap).sort().map(ticker=>({symbol:ticker,value:valueMap[ticker],weight:valueMap[ticker]/total}));
  items.sort((a,b)=>b.weight-a.weight||a.symbol.localeCompare(b.symbol));
  const cashWeight=available/total;
  // HHI includes cash as one allocation bucket; this is concentration, not predicted risk.
  const hhi=items.reduce((sum,p)=>sum+p.weight*p.weight,cashWeight*cashWeight);
  const invested=total-available;
  // Invested-only HHI excludes cash, whose zero price return dilutes modeled market volatility.
  // Undefined for an all-cash portfolio; it must never be reported as zero diversification risk.
  const investmentHhi=invested>0?items.reduce((sum,p)=>sum+(p.value/invested)**2,0):null;
  const largestInvestedWeight=invested>0?(items[0]?.value||0)/invested:null;
  return {cash:available,cashWeight,invested,positions:items,
   largest:items[0]||null,investedWeight:1-cashWeight,hhi,investmentHhi,largestInvestedWeight};
 };
 const before=make(values,cash),after=make(futureValues,afterCash);
 if(after.cashWeight>=0.5)warnings.push('More than half of total virtual portfolio value remains in cash. Cash-inclusive HHI does not measure investment risk, and historical volatility is diluted by an assumed zero-price-return cash weight.');
 if(before.investmentHhi===null)warnings.push('An all-cash starting portfolio has no defined invested-only HHI.');
 if(after.largest&&after.largest.weight>.4)warnings.push('Largest investment exceeds 40% of total virtual portfolio value.');
 else if(after.largest&&after.largest.weight>.25)warnings.push('Largest investment exceeds 25% of total virtual portfolio value.');
 warnings.push('This counterfactual assumes unchanged observed quotes for all positions, fractional virtual units, and zero fees, spreads, slippage or taxes. Quotes may have different observation times.');
 warnings.push('A concentration change is not a forecast of returns or investment suitability.');
 return {symbol,proposedBudget:budget,observedPrice:purchaseQuote.price,priceTime:purchaseQuote.timestamp,source:purchaseQuote.venue||'Unspecified',
  unitsBought,totalBefore:total,totalAfter:total,cashBefore:cash,cashAfter:afterCash,before,after,
  deltaHhi:after.hhi-before.hhi,deltaLargestWeight:(after.largest?.weight||0)-(before.largest?.weight||0),
  requiredSymbols:required,warnings};
}
function matchedRisk(plan,rows,annualization=252){
 if(!plan||!Array.isArray(rows)||!finite(annualization)||annualization<1||annualization>366)throw Error('Cannot evaluate historical risk.');
 const symbols=plan.requiredSymbols;
 // The 252-session model is calibrated to US equities, not crypto or mixed calendars.
 if(symbols.some(s=>s.includes('/')))return {available:false,reason:'Crypto or mixed holdings require a separately calibrated 365-session or mixed-calendar risk model; 252-session stock volatility is withheld.'};
 const lookup=new Map(rows.filter(r=>r&&typeof r.symbol==='string').map(r=>[r.symbol,r]));
 if(lookup.size<symbols.length||!symbols.every(s=>lookup.has(s)))return {available:false,reason:'Not every virtual holding and proposed investment has loaded historical data.'};
 const ref=lookup.get(symbols[0]);
 const d=ref.dates,n=d?.length;
 if(!Array.isArray(d)||n<126)return {available:false,reason:'At least 126 identical observed dates are required.'};
 if(!d.every((date,i)=>typeof date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(date)&&(i===0||date>d[i-1])))return {available:false,reason:'Historical date order is invalid.'};
 const matrix=[];
 for(const ticker of symbols){
  const row=lookup.get(ticker);
  if(!Array.isArray(row.prices)||row.prices.length!==n||!Array.isArray(row.dates)||row.dates.length!==n||
     row.dates.some((date,i)=>date!==d[i])||row.prices.some(x=>!finite(x)||x<=0))
    return {available:false,reason:'Historical prices cannot be aligned on identical dates for every holding.'};
  matrix.push(row.prices.slice(1).map((p,i)=>p/row.prices[i]-1));
 }
 const weights=side=>symbols.map(t=>side.positions.find(p=>p.symbol===t)?.weight||0);
 const vector=ws=>Array.from({length:n-1},(_,i)=>ws.reduce((sum,w,j)=>sum+w*matrix[j][i],0));
 const volatility=r=>{
  const m=r.reduce((sum,x)=>sum+x,0)/r.length;
  const v=r.reduce((sum,x)=>sum+(x-m)**2,0)/(r.length-1);
  return Math.sqrt(v*annualization);
 };
 const volBefore=volatility(vector(weights(plan.before))),volAfter=volatility(vector(weights(plan.after)));
 if(!finite(volBefore)||!finite(volAfter))return {available:false,reason:'Historical volatility calculation is not finite.'};
 return {available:true,annualizedVolBefore:volBefore,annualizedVolAfter:volAfter,deltaVol:volAfter-volBefore,
  sessions:n-1,firstDate:d[0],lastDate:d[n-1],annualization,
  note:'Static-weight, price-only US stock volatility with cash assumed to have zero price return. High cash weights reduce the reported volatility mechanically; this is not a forward forecast or an assessment of total financial risk.'};
}
function exportResearch(plan,risk,context){
 if(!plan)throw Error('Run a hypothetical allocation scenario first.');
 // Deliberately OMIT holdings, cash, units, position values, personal notes and raw prices.
 return {schema:'quantforge.allocation-research.v1',type:'virtual-what-if',hypothetical:true,
  candidate:plan.symbol,asOf:plan.priceTime,quoteVenue:plan.source,
  hypotheticalAllocationChange:{deltaConcentrationHhi:round(plan.deltaHhi),postCashWeight:round(plan.after.cashWeight),
   postLargestPositionWeight:round(plan.after.largest?.weight||0),
   preInvestedOnlyHhi:plan.before.investmentHhi===null?null:round(plan.before.investmentHhi),
   postInvestedOnlyHhi:plan.after.investmentHhi===null?null:round(plan.after.investmentHhi),
   preCashWeight:round(plan.before.cashWeight),
   concentrationInterpretation:'Cash-inclusive HHI is an allocation-bucket distribution, not equity risk. Invested-only HHI is defined solely over security positions; null means no investments.'},
  risk: risk?.available?{historicalSessions:risk.sessions,firstDate:risk.firstDate,lastDate:risk.lastDate,
   annualizedVolBefore:round(risk.annualizedVolBefore),annualizedVolAfter:round(risk.annualizedVolAfter),
   note:risk.note}:{available:false,reason:risk?.reason||'Historical risk not computed.'},
  historicalVolatilityInterpretation:risk?.available?(risk.annualizedVolAfter>risk.annualizedVolBefore+1e-12?'Modeled historical market volatility increased after the hypothetical purchase.':risk.annualizedVolAfter<risk.annualizedVolBefore-1e-12?'Modeled historical market volatility decreased after the hypothetical purchase.':'Modeled historical market volatility was unchanged.'):null,
  methodology:'Observed quotes, proposed cash-funded virtual purchase, static asset weights; no trades recorded.',
  notes:[...plan.warnings,'The export omits portfolio balances, holdings, units, investment budgets, raw licensed prices and personal account details.',
   'No tax, execution, earnings-event, sector or expected-return model; never a guaranteed return or buy recommendation.'],
  researchContext:{marketSource:typeof context?.source==='string'?context.source:'Private historical data',
   historyPeriod:typeof context?.period==='string'?context.period:'Not loaded'}};
}
root.QFPrivateAllocationV74=Object.freeze({dateAgeDays,scenario,matchedRisk,exportResearch});
if(typeof module==='object'&&module.exports)module.exports=root.QFPrivateAllocationV74;
})(typeof window!=='undefined'?window:globalThis);
