/* QuantForge Release B: pure, deterministic comparison and historical portfolio research.
   No browser, API, user state, trading, or credentials. Price-only, not a return forecast. */
(function(root){
'use strict';
const isFiniteNumber=x=>typeof x==='number'&&Number.isFinite(x);
const validSymbol=s=>typeof s==='string'&&/^[A-Z0-9.]{1,12}$/.test(s);
const validDate=s=>{if(typeof s!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;const t=Date.parse(s+'T00:00:00Z');return Number.isFinite(t)&&new Date(t).toISOString().slice(0,10)===s;};
function requireUniverse(symbols){
 if(!Array.isArray(symbols)||symbols.length<2||symbols.length>5||new Set(symbols).size!==symbols.length||!symbols.every(validSymbol))throw Error('Choose 2–5 distinct valid companies.');
 return symbols;
}
function align(observations,symbols,minimum=31){
 requireUniverse(symbols);
 const maps={};let common=null;
 for(const s of symbols){
  const rows=observations?.[s];if(!Array.isArray(rows))throw Error('Missing company price history: '+s);
  let prior='';const dict=new Map();
  for(const r of rows){
   if(!r||!validDate(r.date)||r.date<=prior||!isFiniteNumber(r.close)||r.close<=0)throw Error('Malformed or nonchronological history for '+s+'.');
   dict.set(r.date,r.close);prior=r.date;
  }
  maps[s]=dict;const available=new Set(dict.keys());common=common===null?available:new Set([...common].filter(d=>available.has(d)));
 }
 const dates=[...common].sort();if(dates.length<minimum)throw Error('Not enough common observed close dates for this analysis (need '+minimum+').');
 const closes=Object.fromEntries(symbols.map(s=>[s,dates.map(d=>maps[s].get(d))]));
 return Object.freeze({symbols:symbols.slice(),dates,closes});
}
function fromBatch(raw,symbols){
 requireUniverse(symbols);
 if(raw?.licensed_private!==true||!Array.isArray(raw.symbols)||raw.symbols.length!==symbols.length||symbols.some((s,i)=>raw.symbols[i]!==s))throw Error('Authenticated history returned a mismatched company universe.');
 const dates=raw.dates;
 if(!Array.isArray(dates)||dates.length>1000||dates.length<31)throw Error('Insufficient or oversized common-date history.');
 const observations={};
 for(const s of symbols){
  const values=raw.closes?.[s];if(!Array.isArray(values)||values.length!==dates.length)throw Error('Unaligned private price data.');
  observations[s]=dates.map((d,i)=>({date:d,close:values[i]}));
 }
 if(raw.sessions_per_year!==252)throw Error('Only common US-equity session annualization is supported by this release.');
 return align(observations,symbols);
}
const average=x=>x.reduce((sum,v)=>sum+v,0)/x.length;
function covariance(x,y){if(x.length!==y.length||x.length<2)throw Error('Covariance requires matching observations.');const a=average(x),b=average(y);return x.reduce((sum,v,i)=>sum+(v-a)*(y[i]-b),0)/(x.length-1);}
function quantile(sorted,p){const at=(sorted.length-1)*p,lo=Math.floor(at),hi=Math.ceil(at);return sorted[lo]+(sorted[hi]-sorted[lo])*(at-lo);}
function measures(returns,levels){
 if(returns.length<30||levels.length!==returns.length+1||!returns.every(isFiniteNumber))throw Error('Insufficient aligned market-return observations.');
 const sorted=[...returns].sort((a,b)=>a-b),tailCutoff=quantile(sorted,0.05);
 const tail=sorted.filter(x=>x<=tailCutoff+1e-12);
 const variance=covariance(returns,returns);
 let peak=levels[0],drawdown=0;
 for(const p of levels){peak=Math.max(peak,p);drawdown=Math.min(drawdown,p/peak-1);}
 return {total_return:levels.at(-1)/levels[0]-1,annual_volatility:Math.sqrt(Math.max(0,variance)*252),max_drawdown:drawdown,
  daily_var95_loss:Math.max(0,-tailCutoff),daily_es95_loss:Math.max(0,-average(tail)),worst_day:Math.min(...returns),
  session_count:returns.length,average_daily_return:average(returns)};
}
function correlation(x,y){const a=covariance(x,x),b=covariance(y,y);return a>1e-18&&b>1e-18?Math.max(-1,Math.min(1,covariance(x,y)/Math.sqrt(a*b))):null;}
function compare(aligned){
 const {symbols,dates,closes}=aligned;requireUniverse(symbols);
 if(dates.length<31||dates.length>1000)throw Error('Need at least 31 shared closes and at most 1,000.');
 const returns={},indexed={},metrics={};
 for(const s of symbols){
  const series=closes[s];if(!Array.isArray(series)||series.length!==dates.length||series.some(x=>!isFiniteNumber(x)||x<=0))throw Error('Invalid aligned closes.');
  returns[s]=series.slice(1).map((p,i)=>p/series[i]-1);
  indexed[s]=series.map((p,i)=>i===0?100:100*p/series[0]);
  metrics[s]=measures(returns[s],indexed[s]);
 }
 const covariance_matrix=symbols.map(s=>symbols.map(t=>covariance(returns[s],returns[t])));
 const correlation_matrix=symbols.map(s=>symbols.map(t=>correlation(returns[s],returns[t])));
 return {schema_version:1,scope:'comparison',symbols:symbols.slice(),dates:dates.slice(),indexed,returns,metrics,covariance_matrix,correlation_matrix,
  coverage:{first:dates[0],last:dates.at(-1),common_closes:dates.length,sessions_per_year:252},
  convention:'Exact common dates; daily close-to-close simple returns, split-adjusted for entitled private equities; price-only, no dividends or fees. Annualized using 252 sessions.'};
}
function histogram(result,bins=9){
 if(!Number.isInteger(bins)||bins<4||bins>25)throw Error('Invalid histogram resolution.');
 const all=result.symbols.flatMap(s=>result.returns[s]);let lo=Math.min(...all),hi=Math.max(...all);if(Math.abs(hi-lo)<1e-9){lo-=0.01;hi+=0.01;}
 const width=(hi-lo)/bins;
 return {edges:Array.from({length:bins+1},(_,i)=>lo+width*i),counts:Object.fromEntries(result.symbols.map(s=>{
  const counts=Array(bins).fill(0);for(const r of result.returns[s])counts[Math.min(bins-1,Math.max(0,Math.floor((r-lo)/width)))]+=1;
  return [s,counts];
 }))};
}
function validWeights(symbols,weights){
 requireUniverse(symbols);
 if(!weights||!isFiniteNumber(weights.cash)||weights.cash<0||weights.cash>1)throw Error('Cash weight must be between 0 and 1.');
 let sum=weights.cash;
 for(const s of symbols){const v=weights[s];if(!isFiniteNumber(v)||v<0||v>1)throw Error('Each allocation weight must be between 0 and 100%.');sum+=v;}
 if(Math.abs(sum-1)>1e-7)throw Error('Cash and investment allocations must sum to exactly 100%.');
 return weights;
}
function suggestedWeights(symbols){
 requireUniverse(symbols);
 const result={cash:0.2};for(const s of symbols)result[s]=0.8/symbols.length;return result;
}
function concentration(symbols,weights){
 validWeights(symbols,weights);
 const invested=1-weights.cash;return {cash_share:weights.cash,invested_share:invested,
  invested_hhi:invested>1e-12?symbols.reduce((v,s)=>v+(weights[s]/invested)**2,0):null,
  largest_position:Math.max(...symbols.map(s=>weights[s])),effective_positions:invested>1e-12?1/symbols.reduce((v,s)=>v+(weights[s]/invested)**2,0):null};
}
function scenario(result,weights,initial=10000){
 validWeights(result.symbols,weights);
 if(!isFiniteNumber(initial)||initial<100||initial>1e8)throw Error('Choose a hypothetical budget between $100 and $100 million.');
 const returns=[];let balance=100;const indexed=[100];
 for(let i=0;i<result.dates.length-1;i++){
  const daily=result.symbols.reduce((v,s)=>v+weights[s]*result.returns[s][i],0);
  if(daily<=-1)throw Error('A scenario return exceeded the supported range.');
  returns.push(daily);balance*=1+daily;indexed.push(balance);
 }
 const summary=measures(returns,indexed);
 const half=Math.floor(returns.length/2);
 const earlier=returns.slice(0,half),later=returns.slice(half);
 const split_vol=earlier.length>=30&&later.length>=30?
  {first_half:Math.sqrt(covariance(earlier,earlier)*252),second_half:Math.sqrt(covariance(later,later)*252)}:null;
 return {schema_version:1,scope:'portfolio',weights:{...weights},indexed,dates:result.dates.slice(),summary,
  concentration:concentration(result.symbols,weights),initial,ending_value:initial*balance/100,split_vol,
  assumption:'Hypothetical constant-weight daily rebalancing using historical aligned close-to-close simple price returns. No cash interest, fees, spreads, taxes, dividends or future forecasts. Not a recorded virtual-account return.'};
}
function projectCapped(vector,total,cap){
 if(!Array.isArray(vector)||vector.length<2||vector.some(x=>!isFiniteNumber(x))||!isFiniteNumber(total)||total<0||total>1||!isFiniteNumber(cap)||cap<=0||cap>1||vector.length*cap+1e-10<total)throw Error('Infeasible allocation cap or investable amount.');
 if(total===0)return vector.map(()=>0);
 let lo=Math.min(...vector)-cap,hi=Math.max(...vector);
 for(let k=0;k<110;k++){
  const mid=(lo+hi)/2,sum=vector.reduce((a,b)=>a+Math.max(0,Math.min(cap,b-mid)),0);
  if(sum>total)lo=mid;else hi=mid;
 }
 const weights=vector.map(v=>Math.max(0,Math.min(cap,v-(lo+hi)/2)));
 let residual=total-weights.reduce((a,b)=>a+b,0);
 if(Math.abs(residual)>1e-10){
  for(let i=0;i<weights.length&&Math.abs(residual)>1e-10;i++){
   const space=residual>0?cap-weights[i]:weights[i];const d=Math.sign(residual)*Math.min(Math.abs(residual),space);weights[i]+=d;residual-=d;
  }
 }
 if(Math.abs(residual)>1e-8)throw Error('Cannot satisfy target weights with allocation constraints.');
 return weights;
}
function minimumVariance(result,current,cap=0.7){
 validWeights(result.symbols,current);
 const total=1-current.cash, n=result.symbols.length,C=result.covariance_matrix;
 if(total===0)throw Error('All cash: no invested covariance allocation to optimize.');
 if(cap*n+1e-9<total)throw Error('Increase maximum single-company weight to make the allocation feasible.');
 // Convex quadratic on PSD sample covariance, projected gradient with conservative Lipschitz bound.
 const limit=Math.max(1e-10,...C.map(row=>row.reduce((sum,v)=>sum+Math.abs(v),0)));
 const step=0.4/limit;
 let w=projectCapped(result.symbols.map(s=>current[s]),total,cap);
 let prev=Infinity;
 for(let t=0;t<1800;t++){
  const grad=C.map(row=>2*row.reduce((sum,v,i)=>sum+v*w[i],0));
  const next=projectCapped(w.map((v,i)=>v-step*grad[i]),total,cap);
  const drift=Math.max(...next.map((v,i)=>Math.abs(v-w[i])));
  w=next;if(drift<1e-11)break;
  const varNow=w.reduce((sum,v,i)=>sum+v*C[i].reduce((a,c,j)=>a+c*w[j],0),0);
  if(Math.abs(prev-varNow)<1e-17)break;prev=varNow;
 }
 const weights={cash:current.cash};result.symbols.forEach((s,i)=>{weights[s]=w[i];});
 validWeights(result.symbols,weights);
 const before=scenario(result,current),after=scenario(result,weights);
 return {weights,cap,base:before,optimized:after,
  improved_in_sample:after.summary.annual_volatility<=before.summary.annual_volatility+1e-7,
  limitation:'Sample minimum-variance fit, using the very same history displayed. No untouched future holdout and no guarantee of lower future risk. Cost of rebalancing not included.'};
}
function ownerSnapshot(portfolio,quotes,nowIso){
 // The existing private ledger maintains initial_cash as net deposited capital, including resets.
 // Never confuse capital transfers with market P&L; prices must cover all holdings.
 const cash=portfolio?.cash,capital=portfolio?.initial_cash,holdings=portfolio?.holdings;
 if(!isFiniteNumber(cash)||cash<0||!isFiniteNumber(capital)||capital<0||!holdings||typeof holdings!=='object'||Array.isArray(holdings))throw Error('Incomplete virtual ledger accounting.');
 const positions=Object.entries(holdings).filter(([,q])=>q!==0);
 if(positions.length>8||positions.some(([s,q])=>typeof s!=='string'||!/^[A-Z0-9./-]{1,15}$/.test(s)||!isFiniteNumber(q)||q<=0))throw Error('Owner positions exceed quote coverage or contain invalid quantities.');
 if(!Array.isArray(quotes)||quotes.length!==positions.length)throw Error('Cannot value the virtual portfolio without every authenticated quote.');
 const now=new Date(nowIso);if(!Number.isFinite(now.getTime()))throw Error('Snapshot time invalid.');
 const bySymbol=new Map();
 for(const q of quotes){
  if(!q||q.synthetic!==false||!isFiniteNumber(q.price)||q.price<=0||typeof q.symbol!=='string'||bySymbol.has(q.symbol)||typeof q.timestamp!=='string'||!/(?:[zZ]|[+-]\d{2}:\d{2})$/.test(q.timestamp))throw Error('Unverified owner quote or duplicate asset.');
  const when=new Date(q.timestamp),age=(now-when)/1000;
  if(!Number.isFinite(age)||age< -90||age>5*86400)throw Error('Owner quote is stale, future-dated or missing timestamp.');
  bySymbol.set(q.symbol,{price:q.price,timestamp:q.timestamp,age});
 }
 const valued=positions.map(([s,q])=>{
  const quote=bySymbol.get(s);if(!quote)throw Error('Missing entitled owner quote for '+s+'.');
  return {symbol:s,units:q,price:quote.price,market_value:q*quote.price,timestamp:quote.timestamp};
 });
 const holdingsValue=valued.reduce((v,r)=>v+r.market_value,0),totalValue=cash+holdingsValue;
 return {cash,net_contributions:capital,total_value:totalValue,holdings_value:holdingsValue,
  cumulative_paper_pnl:totalValue-capital,quotes:valued,
  note:'Indicative mark-to-last-available authorized trade. Net contributions include recorded deposits/withdrawals; cumulative paper P&L is NOT time-weighted or money-weighted return. Asynchronous/after-hours prices, fees, trade history limits and tax treatment may affect interpretation.'};
}
root.QFResearchB21=Object.freeze({requireUniverse,align,fromBatch,compare,histogram,validWeights,suggestedWeights,concentration,scenario,minimumVariance,projectCapped,ownerSnapshot});
if(typeof module==='object'&&module.exports)module.exports=root.QFResearchB21;
})(typeof window!=='undefined'?window:globalThis);
