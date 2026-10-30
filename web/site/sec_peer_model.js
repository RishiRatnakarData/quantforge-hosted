/* Public SEC issuer similarity. Descriptive, deterministic; no price signals or predictions. */
(function(root){
'use strict';
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const features=Object.freeze([
 {key:'growth',label:'Annual revenue growth',description:'(Latest revenue / prior fiscal-year revenue - 1) × 100'},
 {key:'operating',label:'Operating margin',description:'Operating income / annual revenue × 100'},
 {key:'net',label:'Net margin',description:'Net income / annual revenue × 100'},
 {key:'fcf',label:'Free cash flow proxy margin',description:'(Operating cash flow - capex) / annual revenue × 100'}
]);
function companyRow(c,cutoff){
 const [current,previous]=c?.annual||[];
 if(!current||!previous||!/^\d{4}-\d{2}-\d{2}$/.test(current.fiscal_end)||current.fiscal_end>cutoff)return null;
 const m=current.metrics||{},p=previous.metrics||{};
 const completeFields=['revenue_usd','operating_income_usd','net_income_usd','operating_cash_flow_usd','capex_usd'];
 const coverage=completeFields.filter(k=>finite(m[k])&&current.sources?.[k]?.accession&&current.sources[k].filed<=cutoff).length;
 const priorSource=previous.sources?.revenue_usd;
 if(coverage!==5||!priorSource?.accession||priorSource.filed>cutoff||!finite(p.revenue_usd)||p.revenue_usd<=0||!(m.revenue_usd>0))return null;
 const days=(Date.parse(cutoff+'T00:00:00Z')-Date.parse(current.fiscal_end+'T00:00:00Z'))/86400000;
 if(!(days>=0&&days<=550))return null; // do not compare very stale reporting periods
 const values=[100*(m.revenue_usd/p.revenue_usd-1),100*m.operating_income_usd/m.revenue_usd,
  100*m.net_income_usd/m.revenue_usd,100*m.free_cash_flow_usd/m.revenue_usd];
 if(values.some(v=>!finite(v)))return null;
 return {symbol:c.symbol,name:c.name,sector:c.sector||'Not classified',fiscalEnd:current.fiscal_end,
  latestFiled:completeFields.map(k=>current.sources[k].filed).sort().at(-1),values,companyfacts:c.source_url};
}
function median(a){const s=[...a].sort((x,y)=>x-y);return (s[(s.length-1)>>1]+s[s.length>>1])/2;}
function compare(snapshot,symbol,{sectorOnly=false}={}){
 if(!Array.isArray(snapshot?.companies)||!/^\d{4}-\d{2}-\d{2}$/.test(snapshot.expanded_as_of||snapshot.as_of||''))return {ready:false,reason:'No dated SEC companyfacts snapshot available.'};
 const cutoff=snapshot.expanded_as_of||snapshot.as_of;
 const all=snapshot.companies.map(c=>companyRow(c,cutoff)).filter(Boolean);
 const selected=all.find(c=>c.symbol===symbol);
 if(!selected)return {ready:false,reason:'Selected issuer lacks all four comparable reported features and accession-backed coverage.',universe:snapshot.companies.length,eligible:all.length,cutoff};
 const group=sectorOnly&&selected.sector!=='Not classified'?all.filter(c=>c.sector===selected.sector):all;
 if(group.length<3)return {ready:false,reason:'Insufficient eligible companies in the selected peer group.',universe:snapshot.companies.length,eligible:all.length,groupSize:group.length,cutoff};
 const center=features.map((_,i)=>median(group.map(c=>c.values[i])));
 const scales=features.map((_,i)=>{
  const values=group.map(c=>c.values[i]);const sd=Math.sqrt(values.reduce((sum,c)=>sum+(c-center[i])**2,0)/values.length);
  return sd>1e-9?sd:1;
 });
 const normalized=c=>c.values.map((v,i)=>Math.max(-3,Math.min(3,(v-center[i])/scales[i])));
 const base=normalized(selected);
 const peers=group.filter(c=>c.symbol!==symbol).map(c=>({...c,distance:Math.sqrt(normalized(c).reduce((sum,v,i)=>sum+(v-base[i])**2,0))})).sort((a,b)=>a.distance-b.distance||a.symbol.localeCompare(b.symbol));
 return {ready:true,symbol,selected,peers,eligible:all.length,universe:snapshot.companies.length,compared:group.length,
  excluded:snapshot.companies.length-all.length,cutoff,features,sectorOnly:sectorOnly&&selected.sector!=='Not classified',
  message:'Four equal-weight, snapshot-standardized SEC financial-ratio features. Median-centered z-scores clipped at ±3 to reduce outlier dominance. Distances indicate similarity, not investment quality. Fiscal year-ends may differ; sector tags are incomplete.'};
}
const api=Object.freeze({compare,companyRow,features});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPublicSECPeers=api;
})(typeof window!=='undefined'?window:globalThis);
