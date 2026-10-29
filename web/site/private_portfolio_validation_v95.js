/* V9.5: pure, owner-only portfolio diagnostics, past-only risk-screen audit,
 * and hypothetical cash-flow scenarios. No I/O, storage, execution, or trading. */
(function(root){
'use strict';
const num=x=>typeof x==='number'&&Number.isFinite(x);
const date=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;
const round=(x,d=4)=>num(x)?Number(x.toFixed(d)):null;
function validHistory(history){
 return !!history&&Array.isArray(history.symbols)&&history.symbols.length>=2&&history.symbols.length<=5&&
  new Set(history.symbols).size===history.symbols.length&&Array.isArray(history.dates)&&
  history.dates.length>=64&&history.dates.length<=2500&&history.dates.every((x,i)=>date(x)&&(!i||x>history.dates[i-1]))&&
  history.symbols.every(s=>Array.isArray(history.closes?.[s])&&history.closes[s].length===history.dates.length&&
   history.closes[s].every(p=>num(p)&&p>0));
}
function risk(returns,annual){
 if(!Array.isArray(returns)||returns.length<63||returns.some(r=>!num(r)||r<=-1))return null;
 const mean=returns.reduce((s,r)=>s+r,0)/returns.length;
 const sd=Math.sqrt(returns.reduce((s,r)=>s+(r-mean)**2,0)/(returns.length-1));
 const sorted=[...returns].sort((a,b)=>a-b),q=sorted[Math.floor(.05*(sorted.length-1))];
 const tail=sorted.filter(x=>x<=q);
 let wealth=1,peak=1,drawdown=0;
 for(const x of returns){wealth*=1+x;if(!num(wealth)||wealth<=0)return null;peak=Math.max(peak,wealth);drawdown=Math.min(drawdown,wealth/peak-1);}
 return {annualVolatility:round(sd*Math.sqrt(annual)),dailyVaR95:round(Math.max(0,-q)),
  dailyES95:round(Math.max(0,-tail.reduce((s,x)=>s+x,0)/tail.length)),
  maxDrawdown:round(drawdown),observations:returns.length};
}
function portfolioRisk({portfolio,quotes,history,asOf,symbol,maxWeight}={}){
 const fail=(reason,allocation=null)=>({ready:false,reason,allocation,baseline:null,hypothetical:null});
 if(!portfolio||!num(portfolio.cash)||portfolio.cash<0||!portfolio.holdings||
  typeof portfolio.holdings!=='object'||Array.isArray(portfolio.holdings))return fail('An authenticated portfolio with valid cash and holdings is required.');
 const holdings=Object.entries(portfolio.holdings).filter(([,q])=>q!==0);
 if(holdings.length>100||holdings.some(([s,q])=>!s||!num(q)||q<=0))return fail('Portfolio holdings contain unsupported quantities.');
 const now=String(asOf||'').slice(0,10);
 if(!date(now))return fail('The research date is invalid.');
 let total=portfolio.cash;
 const values={};
 for(const [s,q] of holdings){
  const quote=quotes?.[s],stamp=String(quote?.timestamp||'').slice(0,10);
  if(!num(quote?.price)||quote.price<=0||!date(stamp)||stamp>now||
   (Date.parse(now)-Date.parse(stamp))/86400000>7)return fail('A holding has no valid, recent quote; all weighted portfolio calculations are withheld.');
  values[s]=q*quote.price;
  if(!num(values[s])||values[s]<0)return fail('An invalid priced position prevents a reliable allocation.');
  total+=values[s];
 }
 if(!num(total)||total<=0)return fail('Portfolio total value is unavailable.');
 const allocation={cashWeight:round(portfolio.cash/total),positions:holdings.map(([s])=>({symbol:String(s).slice(0,20),weight:round(values[s]/total)}))};
 const weights=Object.fromEntries(holdings.map(([s])=>[s,values[s]/total]));
 const positions=Object.keys(weights);
 const maxObserved=positions.length?Math.max(...Object.values(weights)):0;
 allocation.largestWeight=round(maxObserved);
 allocation.concentrationFlag=num(maxWeight)&&maxWeight>0&&maxObserved>maxWeight+1e-9;
 if(!positions.length)return {ready:true,reason:'All-cash portfolio; historical invested risk is zero.',allocation,
  baseline:{annualVolatility:0,dailyVaR95:0,dailyES95:0,maxDrawdown:0,observations:0},hypothetical:null,
  note:'All cash has no equity price-risk exposure. Cash purchasing-power and counterparty risks are not modeled.'};
 if(!validHistory(history)||positions.some(s=>!history.symbols.includes(s)))return fail(
  'Full portfolio risk withheld: load matching aligned history for EVERY held investment; a selected subset is insufficient.',allocation);
 const end=history.dates.at(-1);
 if(end>now||(Date.parse(now)-Date.parse(end))/86400000>7)return fail('Loaded market history is stale or dated after this assessment.',allocation);
 const annual=history.sessions_per_year===365?365:252;
 const n=history.dates.length,series={};
 for(const s of positions)series[s]=history.closes[s].slice(1).map((p,i)=>p/history.closes[s][i]-1);
 const combine=w=>Array.from({length:n-1},(_,i)=>Object.keys(w).reduce((sum,s)=>sum+w[s]*series[s][i],0));
 const baseline=risk(combine(weights),annual);
 if(!baseline)return fail('Current-weight daily returns could not be validated.',allocation);
 let hypothetical=null;
 if(symbol&&history.symbols.includes(symbol)&&portfolio.cash/total>=.05&&positions.length<6){
  const scenario={...weights};
  scenario[symbol]=(scenario[symbol]||0)+.05;
  if(!series[symbol])series[symbol]=history.closes[symbol].slice(1).map((p,i)=>p/history.closes[symbol][i]-1);
  const after=risk(combine(scenario),annual);
  if(after)hypothetical={fundedFromCashPercent:5,annualVolatility:after.annualVolatility,dailyES95:after.dailyES95,
   maxDrawdown:after.maxDrawdown,concentrationFlag:num(maxWeight)&&scenario[symbol]>maxWeight};
 }
 return {ready:true,reason:null,allocation,baseline,hypothetical,period:{start:history.dates[0],end,sessions:n,annualization:annual},
  note:'Historical daily-risk approximation holds TODAY\'S weights constant over the earlier price window. It is not actual realized account performance, does not include dividends, fees, financing, or cash interest, and cannot predict future risk.'};
}
function riskGateAudit({history,symbol,maxDrawdown,train=126,test=21}={}){
 const unavailable=reason=>({ready:false,reason,windows:[],summary:null});
 if(!validHistory(history)||!history.symbols.includes(symbol))return unavailable('Past-only policy audit requires a fully aligned candidate price series.');
 if(!num(maxDrawdown)||maxDrawdown<=0||maxDrawdown>=1)return unavailable('Choose a valid historical drawdown screen.');
 if(!Number.isInteger(train)||train<63||train>504||!Number.isInteger(test)||test<5||test>126)return unavailable('Invalid chronological evaluation windows.');
 const ps=history.closes[symbol];if(ps.length<train+test*2)return unavailable('Insufficient samples for two disjoint test windows.');
 const windows=[];
 for(let end=train-1;end+test<ps.length&&windows.length<80;end+=test){
  let peak=ps[end-train+1],mdd=0;
  for(let k=end-train+1;k<=end;k++){peak=Math.max(peak,ps[k]);mdd=Math.min(mdd,ps[k]/peak-1);}
  const observed=ps[end+test]/ps[end]-1;
  windows.push({trainThrough:history.dates[end],testFrom:history.dates[end+1],testThrough:history.dates[end+test],
   trailingDrawdown:round(mdd),gatePassed:mdd>=-maxDrawdown,observedForwardReturn:round(observed)});
 }
 if(windows.length<2)return unavailable('Fewer than two complete disjoint later observation windows.');
 const allowed=windows.filter(w=>w.gatePassed),blocked=windows.filter(w=>!w.gatePassed);
 const average=xs=>xs.length?round(xs.reduce((sum,w)=>sum+w.observedForwardReturn,0)/xs.length):null;
 return {ready:true,reason:null,windows:windows.slice(-8),summary:{count:windows.length,allowed:allowed.length,blocked:blocked.length,
  allowedObservedAverage:average(allowed),blockedObservedAverage:average(blocked)},
  methodology:{train,test,screen:maxDrawdown,firstTrainThrough:windows[0].trainThrough,lastTestThrough:windows.at(-1).testThrough},
  note:'A chronological retrospective test of the price-drawdown gate ONLY. Every decision uses its preceding training history, then observes later non-overlapping prices. It does not reconstruct SEC filings, quotes, portfolio actions, transaction costs, or the full investment decision policy and cannot validate predictive accuracy.'};
}
function cashFlowScenarios({snapshot,selection,asOf}={}){
 const stale=reason=>({ready:false,reason,rows:[]});
 if(!Array.isArray(selection)||selection.length<2||selection.length>5||new Set(selection).size!==selection.length)
  return stale('Select two to five different companies.');
 const cutoff=String(asOf||'').slice(0,10),stamp=snapshot?.as_of;
 if(!date(cutoff)||!date(stamp)||stamp>cutoff||(Date.parse(cutoff)-Date.parse(stamp))/86400000>730||!Array.isArray(snapshot?.companies))
  return stale('SEC snapshot is missing, outdated, or inconsistent with this research date.');
 const index=new Map(snapshot.companies.map(c=>[c.symbol,c]));
 const rows=selection.map(symbol=>{
  const item=index.get(symbol),cur=item?.annual?.[0],prev=item?.annual?.[1];
  const fiscal=cur?.fiscal_end,prior=prev?.fiscal_end;
  const valid=date(fiscal)&&date(prior)&&prior<fiscal&&fiscal<=cutoff&&
   (Date.parse(cutoff)-Date.parse(fiscal))/86400000<=800&&
   (Date.parse(fiscal)-Date.parse(prior))/86400000>=300&&
   (Date.parse(fiscal)-Date.parse(prior))/86400000<=430;
  const revenue=valid?cur.metrics?.revenue_usd:null,fcf=valid?cur.metrics?.free_cash_flow_usd:null;
  const ni=valid?cur.metrics?.net_income_usd:null;
  const comparable=num(fcf)&&fcf>0&&num(revenue)&&revenue>0;
  return {symbol:String(symbol).slice(0,20),fiscalEnd:valid?fiscal:null,
   fcfToRevenue:comparable?round(fcf/revenue):null,
   cashConversion:num(fcf)&&num(ni)&&ni>0?round(fcf/ni):null,
   aggregateFcfScenarios:comparable?[10,15,20].map(m=>round(fcf*m/1e9,2)):null,
   source:valid?String(item?.source_url||'').slice(0,180):null};
 });
 return {ready:true,reason:null,asOf:stamp,rows,
  note:'Illustrative 10x/15x/20x annual free-cash-flow capitalization in USD billions, BEFORE debt, cash and share-count adjustments. These are not enterprise valuations, equity values, market multiples, fair prices or stock-price targets. Negative/missing FCF is withheld; fiscal years can differ.'};
}
function build(input={}){
 const portfolio=portfolioRisk(input);
 const gate=riskGateAudit(input);
 const valuation=cashFlowScenarios(input);
 return {schema:'quantforge.portfolio-validation.v9.5',symbol:String(input.symbol||'').slice(0,20),
  portfolio,gate,valuation,asOf:String(input.asOf||'').slice(0,10)};
}
function exportSafe(packet){
 if(packet?.schema!=='quantforge.portfolio-validation.v9.5')throw Error('Invalid diagnostics.');
 return {schema:'quantforge.portfolio-validation-summary.v9.5',asOf:packet.asOf,
  portfolioRiskAvailable:packet.portfolio.ready,policyAuditAvailable:packet.gate.ready,
  valuationScenarioCoverage:packet.valuation.rows.filter(r=>r.aggregateFcfScenarios).length,
  note:'Actual holdings, allocation weights, account values, raw prices and portfolio risk metrics are intentionally excluded. The on-screen private assessment can contain account-sensitive information.'};
}
const api=Object.freeze({build,portfolioRisk,riskGateAudit,cashFlowScenarios,exportSafe});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivatePortfolioValidationV95=api;
})(typeof window!=='undefined'?window:globalThis);
