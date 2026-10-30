/* Public SEC reported issuer peer comparisons: deterministic, comparable features, no price predictions. */
(function(root){
'use strict';
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const features=Object.freeze([
 {key:'growth',label:'Annual revenue growth',description:'Current / previous annual revenue minus one'},
 {key:'operating',label:'Operating margin',description:'Reported operating income divided by annual revenue'},
 {key:'net',label:'Net margin',description:'Reported net income divided by annual revenue'},
 {key:'fcf',label:'Free-cash-flow proxy margin',description:'(Reported operating cash flow − cash PP&E purchases) divided by annual revenue'}
]);
// Editorial, broad industry groups for comparison, not an SEC-reported sector attribute.
const groups=Object.freeze({
 Technology:'MSFT AAPL NVDA AMD ADBE AMAT ANET CDNS CRM CSCO FIS FISV IBM INTC INTU KLAC MA MU NOW ORCL PANW PYPL QCOM',
 Communication:'GOOGL META CHTR CMCSA DIS',
 'Consumer discretionary':'AMZN F GM HD LOW MAR MCD NKE',
 'Consumer staples':'COST WMT KO CL EL KHC MDLZ MO PEP PG PM',
 Healthcare:'JNJ AMGN BMY BSX CVS DHR GILD ISRG LLY MRK PFE REGN',
 Energy:'XOM COP CVX EOG OXY',
 Industrials:'CAT BA CSX DE EMR ETN FDX GD GE HON LHX LIN LMT MMM NSC',
 Utilities:'DUK EXC NEE',
 Financials:'AXP BAC CB CBOE CME JPM MCO MET MS PNC',
 'Real estate':'AMT PLD'
});
const sectorOf=(c)=>Object.entries(groups).find(([,syms])=>(' '+syms+' ').includes(' '+c.symbol+' '))?.[0]||
 (c.sector&&c.sector!=='Not classified'?c.sector:'Not classified');
function observed(value,source,cutoff){return finite(value)&&source?.accession&&source?.filed<=cutoff&&source?.filed>= '1990-01-01';}
function companyRow(c,cutoff){
 const [a,b]=c?.annual||[];
 if(!a||!/^\d{4}-\d{2}-\d{2}$/.test(a.fiscal_end)||a.fiscal_end>cutoff)return null;
 const days=(Date.parse(cutoff+'T00:00:00Z')-Date.parse(a.fiscal_end+'T00:00:00Z'))/86400000;
 if(!Number.isFinite(days)||days<0||days>550)return null;
 const m=a.metrics||{},s=a.sources||{},p=b?.metrics||{},ps=b?.sources||{};
 if(!observed(m.revenue_usd,s.revenue_usd,cutoff)||!(m.revenue_usd>0))return null;
 const values=[null,null,null,null];
 if(b&&b.fiscal_end<a.fiscal_end&&observed(p.revenue_usd,ps.revenue_usd,cutoff)&&p.revenue_usd>0)
  values[0]=100*(m.revenue_usd/p.revenue_usd-1);
 if(observed(m.operating_income_usd,s.operating_income_usd,cutoff))values[1]=100*m.operating_income_usd/m.revenue_usd;
 if(observed(m.net_income_usd,s.net_income_usd,cutoff))values[2]=100*m.net_income_usd/m.revenue_usd;
 if(observed(m.operating_cash_flow_usd,s.operating_cash_flow_usd,cutoff)&&observed(m.capex_usd,s.capex_usd,cutoff))
  values[3]=100*(m.operating_cash_flow_usd-m.capex_usd)/m.revenue_usd;
 const available=values.map((v,i)=>finite(v)?i:null).filter(v=>v!==null);
 if(!available.length)return null;
 return {symbol:c.symbol,name:c.name,sector:sectorOf(c),fiscalEnd:a.fiscal_end,
  latestFiled:Object.values(s).filter(x=>x?.filed).map(x=>x.filed).sort().at(-1)||null,
  values,available,companyfacts:c.source_url};
}
function median(a){const s=[...a].sort((x,y)=>x-y);return (s[(s.length-1)>>1]+s[s.length>>1])/2;}
function compare(snapshot,symbol,{sectorOnly=false}={}){
 if(!Array.isArray(snapshot?.companies)||!/^\d{4}-\d{2}-\d{2}$/.test(snapshot.expanded_as_of||snapshot.as_of||''))
  return {ready:false,reason:'A dated SEC Company Facts snapshot is unavailable.'};
 const cutoff=snapshot.expanded_as_of||snapshot.as_of;
 const rows=snapshot.companies.map(c=>companyRow(c,cutoff)).filter(Boolean);
 const selected=rows.find(c=>c.symbol===symbol);
 if(!selected)return {ready:false,reason:'This issuer has no current, accession-backed annual revenue. Open Company Financials to examine the available filings.',universe:snapshot.companies.length,cutoff};
 const base=sectorOnly&&selected.sector!=='Not classified'?rows.filter(r=>r.sector===selected.sector):rows;
 // Same features for EVERY compared peer; never compare unequal-dimensional distances.
 // Prefer four complete ratios, otherwise the strongest shared three; only last resort a labeled two-ratio preview.
 let indices=null,group=[];
 for(let count=4;count>=2&&!indices;count--){
  const combos=[];
  function walk(start,picked){if(picked.length===count){combos.push([...picked]);return;}
   for(let i=start;i<features.length;i++)walk(i+1,[...picked,i]);}
  walk(0,[]);
  const options=combos.filter(combo=>combo.every(i=>finite(selected.values[i]))).map(combo=>({combo,
   available:base.filter(r=>combo.every(i=>finite(r.values[i])))})).filter(o=>o.available.length>=3);
  options.sort((a,b)=>b.available.length-a.available.length||a.combo.join('').localeCompare(b.combo.join('')));
  if(options.length){indices=options[0].combo;group=options[0].available;}
 }
 if(!indices&&sectorOnly&&selected.sector!=='Not classified'){
  const broad=compare(snapshot,symbol,{sectorOnly:false});
  if(broad.ready)return {...broad,groupFallback:true,caution:'The selected business group has too few comparable peers; showing a broader cross-industry comparison. '+broad.caution};
 }
 if(!indices)return {ready:false,reason:'Too few comparable annual financial ratios are available for a defensible peer comparison. Open Company Financials for the available reported figures.',selected,universe:snapshot.companies.length,eligible:0,cutoff,available:selected.available.length};
 const center=indices.map(i=>median(group.map(c=>c.values[i])));
 const scale=indices.map((i,j)=>{const v=group.map(c=>c.values[i]);const sd=Math.sqrt(v.reduce((sum,x)=>sum+(x-center[j])**2,0)/v.length);return sd>1e-9?sd:1;});
 const z=c=>indices.map((i,j)=>Math.max(-3,Math.min(3,(c.values[i]-center[j])/scale[j])));
 const a=z(selected);
 const peers=group.filter(c=>c.symbol!==symbol).map(c=>({...c,distance:Math.sqrt(z(c).reduce((sum,v,i)=>sum+(v-a[i])**2,0))})).sort((u,v)=>u.distance-v.distance||u.symbol.localeCompare(v.symbol));
 return {ready:true,symbol,selected,peers,universe:snapshot.companies.length,eligible:group.length,
  compared:group.length,excluded:snapshot.companies.length-group.length,cutoff,
  indices,features:indices.map(i=>features[i]),featureCount:indices.length,
  partial:indices.length<4,sectorOnly:sectorOnly&&selected.sector!=='Not classified',
  caution:indices.length===2?'Limited two-ratio comparison. Do not interpret this as a comprehensive financial match.':indices.length===3?'Three shared financial ratios are available; the fourth is missing for this peer group.':'All four reporting ratios available.',
  message:'Equal-weight standardized distances are calculated on the SAME reported ratios for every peer, with median centering and z-scores clipped at ±3. Financial profiles are not predictions of returns, valuation, or investment quality. Different fiscal-year ends can limit comparability. Broad industry groups are editorial, not SEC sector classifications.'};
}
const api=Object.freeze({compare,companyRow,features,sectorOf});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPublicSECPeers=api;
})(typeof window!=='undefined'?window:globalThis);
