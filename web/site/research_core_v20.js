/* QuantForge 2.0 Release A: deterministic, pure, evidence-linked single-company research.
   No network, DOM, private state, browser storage, or investment advice. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const iso=x=>/^\d{4}-\d{2}-\d{2}$/.test(x)&&!Number.isNaN(Date.parse(x+'T00:00:00Z'));
function priceSeries(observations){
 if(!Array.isArray(observations))return [];
 let previous='';
 return observations.map(r=>{
  if(!r||!iso(r.date)||r.date<=previous||!finite(r.close)||r.close<=0)throw Error('Price observations require distinct ascending dates and positive finite closes.');
  previous=r.date;return {date:r.date,close:r.close};
 });
}
function chartWindow(points,days){
 if(!points.length)return [];
 if(days==='ALL')return points.slice();
 if(!Number.isInteger(days)||days<1||days>1200)throw Error('Unsupported chart window.');
 const end=Date.parse(points[points.length-1].date+'T00:00:00Z');
 const cutoff=new Date(end-days*86400000).toISOString().slice(0,10);
 return points.filter(x=>x.date>=cutoff);
}
function priceStatistics(points){
 const p=priceSeries(points);
 if(p.length<15)return null;
 let peak=p[0].close, drawdown=0;
 const returns=[];
 for(let i=1;i<p.length;i++){
  peak=Math.max(peak,p[i].close);
  drawdown=Math.min(drawdown,p[i].close/peak-1);
  returns.push(Math.log(p[i].close/p[i-1].close));
 }
 const mean=returns.reduce((a,b)=>a+b,0)/returns.length;
 const variance=returns.reduce((a,b)=>a+(b-mean)**2,0)/(returns.length-1);
 return {sessions:p.length,first:p[0].date,last:p[p.length-1].date,
  change:p[p.length-1].close/p[0].close-1,annual_volatility:Math.sqrt(variance*252),max_drawdown:drawdown,
  convention:'Consecutive close-to-close log returns; 252-session annualization. Price-only, excluding dividends and fees.'};
}
// Product interaction fixture: stable across refreshes; NEVER an actual company price.
function syntheticPrice(symbol){
 if(!/^[A-Z0-9.]{1,10}$/.test(symbol))throw Error('Unsupported demonstration symbol.');
 let seed=2166136261;
 for(const char of symbol){seed=Math.imul(seed^char.charCodeAt(0),16777619)>>>0;}
 let close=100,rows=[];
 const date=new Date('2024-10-14T00:00:00Z');
 for(let i=0;rows.length<520;i++){
  const d=new Date(date.getTime()+i*86400000);
  if(d.getUTCDay()===0||d.getUTCDay()===6)continue;
  seed=(Math.imul(seed,1664525)+1013904223)>>>0;
  const noise=(seed/4294967296-0.5)*0.032;
  close*=Math.exp(0.00018+0.003*Math.sin(rows.length/17)+noise);
  rows.push({date:d.toISOString().slice(0,10),close:Number(close.toFixed(4))});
 }
 return rows;
}
function financialSummary(company,cutoff){
 if(!company||!Array.isArray(company.annual))return {status:'unavailable',symbol:company?.symbol||null,source:{type:'sec',period:null},metrics:{},evidence:[],findings:[],annual:[],limitations:['No annual SEC filings in the published snapshot.']};
 const rows=[...company.annual].filter(r=>iso(r?.fiscal_end)&&r.metrics).sort((a,b)=>b.fiscal_end.localeCompare(a.fiscal_end));
 const a=rows[0],b=rows[1];
 const am=a?.metrics||{},bm=b?.metrics||{};
 const growth=finite(am.revenue_usd)&&finite(bm.revenue_usd)&&bm.revenue_usd>0?am.revenue_usd/bm.revenue_usd-1:null;
 const margin=finite(am.operating_income_usd)&&finite(am.revenue_usd)&&am.revenue_usd>0?am.operating_income_usd/am.revenue_usd:null;
 const netMargin=finite(am.net_income_usd)&&finite(am.revenue_usd)&&am.revenue_usd>0?am.net_income_usd/am.revenue_usd:null;
 const keys=['revenue_usd','net_income_usd','free_cash_flow_usd','operating_income_usd'];
 const metrics={revenue_usd:finite(am.revenue_usd)?am.revenue_usd:null,
  net_income_usd:finite(am.net_income_usd)?am.net_income_usd:null,
  free_cash_flow_usd:finite(am.free_cash_flow_usd)?am.free_cash_flow_usd:null,
  revenue_growth:growth,operating_margin:margin,net_margin:netMargin};
 const evidence=keys.filter(k=>finite(am[k])).map(k=>({id:'sec:'+k,kind:'reported_or_derived',metric:k,value:am[k],unit:'USD',fiscal_end:a.fiscal_end,
  accession:a.sources?.[k]?.accession||null,filed:a.sources?.[k]?.filed||null,
  ...(k==='free_cash_flow_usd'?{kind:'derived',method:'operating cash flow - cash purchases of property and equipment',components:[a.sources?.operating_cash_flow_usd||null,a.sources?.capex_usd||null]}:{})}));
 if(growth!==null)evidence.push({id:'sec:revenue_growth',kind:'derived',metric:'revenue_growth',value:growth,unit:'fraction',fiscal_end:a.fiscal_end,method:'latest / prior fiscal annual revenue - 1'});
 if(margin!==null)evidence.push({id:'sec:operating_margin',kind:'derived',metric:'operating_margin',value:margin,unit:'fraction',fiscal_end:a.fiscal_end,method:'operating income / annual revenue'});
 const findings=[];
 if(growth!==null)findings.push({kind:growth>=0?'strength':'caution',text:`Annual reported revenue ${growth>=0?'increased':'decreased'} ${Math.abs(growth*100).toFixed(1)}% between fiscal years ended ${b.fiscal_end} and ${a.fiscal_end}.`,evidence_ids:['sec:revenue_growth']});
 if(margin!==null)findings.push({kind:margin>=0?'context':'caution',text:`Operating margin was ${(margin*100).toFixed(1)}% for the latest covered fiscal year. It is an accounting ratio, not a share-price return.`,evidence_ids:['sec:operating_margin']});
 if(finite(am.free_cash_flow_usd))findings.push({kind:am.free_cash_flow_usd<0?'caution':'context',text:`Reported cash-flow proxy was ${am.free_cash_flow_usd<0?'negative':'positive'} for fiscal year ended ${a.fiscal_end}. This proxy subtracts cash property-and-equipment purchases from operating cash flow.`,evidence_ids:['sec:free_cash_flow_usd']});
 const limitations=[];
 if(growth===null)limitations.push('Prior-period revenue comparison is unavailable; no growth rate was inferred.');
 if(margin===null)limitations.push('An operating margin could not be calculated without compatible reported inputs.');
 if(!finite(am.free_cash_flow_usd))limitations.push('Annual free-cash-flow proxy is not reported for this issuer.');
 limitations.push('SEC fiscal periods and filing availability differ; snapshot figures are not live market data.');
 return {schema_version:1,symbol:company.symbol,scope:'single_company',as_of:cutoff||null,status:keys.every(k=>finite(am[k]))?'available':'partial',
  source:{type:'sec',label:'SEC EDGAR Company Facts (annual 10-K snapshot)',period:a?.fiscal_end||null},metrics,evidence,findings,limitations,
  annual:rows.map(r=>({fiscal_end:r.fiscal_end,metrics:r.metrics,sources:r.sources||{}})),
  validation:{sample_count:rows.length,window:rows.length?{first:rows[rows.length-1].fiscal_end,last:a.fiscal_end}:null,baseline:null}};
}
function researchResult(financial,prices,priceSource){
 const findings=financial.findings.slice();const evidence=financial.evidence.slice();const limitations=financial.limitations.slice();
 let price=null;
 if(priceSource?.type==='market'&&Array.isArray(prices)){
  price=priceStatistics(prices);
  if(price){evidence.push({id:'market:drawdown',kind:'derived',metric:'max_drawdown',value:price.max_drawdown,unit:'fraction',period:{first:price.first,last:price.last}});
   evidence.push({id:'market:volatility',kind:'derived',metric:'annual_volatility',value:price.annual_volatility,unit:'fraction',period:{first:price.first,last:price.last}});
   findings.push({kind:'caution',text:`On ${price.sessions} observed sessions, maximum price drawdown was ${(100*price.max_drawdown).toFixed(1)}% and annualized close-return volatility ${(100*price.annual_volatility).toFixed(1)}%. Neither predicts future loss.`,evidence_ids:['market:drawdown','market:volatility']});
  }
 }
 if(!price)limitations.push('Company-specific market-price risk could not be evaluated from entitled observed history. Synthetic chart behavior is not company risk.');
 if(!findings.some(f=>f.kind==='caution'))findings.push({kind:'uncertainty',text:'Historical financial statements do not establish future returns, valuation or investment suitability.',evidence_ids:evidence.length?[evidence[0].id]:[]});
 return {schema_version:1,symbol:financial.symbol,scope:'single_company',as_of:financial.as_of,
  source:financial.source,status:financial.status,metrics:{...financial.metrics,...(price?{observed_price_risk:price}:{})},visuals:[],findings,evidence,limitations,
  validation:financial.validation,price_source:priceSource?.type||'unavailable'};
}
root.QFResearchCore20=Object.freeze({priceSeries,chartWindow,priceStatistics,syntheticPrice,financialSummary,researchResult});
if(typeof module==='object'&&module.exports)module.exports=root.QFResearchCore20;
})(typeof window!=='undefined'?window:globalThis);
