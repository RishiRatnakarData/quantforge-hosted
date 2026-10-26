/* Pure, offline SEC analytics. All inputs are the reviewed public filing snapshot. */
(function(root){
'use strict';
const METRICS={
 revenue:{label:'Annual revenue',unit:'usd'},
 growth:{label:'Revenue growth (YoY)',unit:'percent'},
 margin:{label:'Operating margin',unit:'percent'},
 fcf:{label:'Free cash flow proxy',unit:'usd'}
};
const finite=n=>typeof n==='number'&&Number.isFinite(n);
function metricValue(annual,key){
 if(!annual?.length)return null;
 const current=annual[0].metrics||{},previous=annual[1]?.metrics||{};
 if(key==='revenue')return finite(current.revenue_usd)?current.revenue_usd:null;
 if(key==='fcf')return finite(current.free_cash_flow_usd)?current.free_cash_flow_usd:null;
 if(key==='margin')return finite(current.operating_income_usd)&&finite(current.revenue_usd)&&current.revenue_usd>0?100*current.operating_income_usd/current.revenue_usd:null;
 if(key==='growth')return finite(current.revenue_usd)&&finite(previous.revenue_usd)&&previous.revenue_usd>0?100*(current.revenue_usd/previous.revenue_usd-1):null;
 return null;
}
function ranking(snapshot,key){
 if(!Object.hasOwn(METRICS,key))throw Error('Unknown SEC ranking metric');
 if(!Array.isArray(snapshot?.companies))return [];
 return snapshot.companies.map(c=>({symbol:c.symbol,name:c.name,sector:c.sector||'Not classified',fiscal_end:c.annual?.[0]?.fiscal_end||'',value:metricValue(c.annual,key)}))
  .sort((a,b)=>{
   if(a.value===null)return b.value===null?a.symbol.localeCompare(b.symbol):1;
   if(b.value===null)return -1;
   return b.value-a.value || a.symbol.localeCompare(b.symbol);
  });
}
function revenueSeries(company){
 if(!Array.isArray(company?.annual))return [];
 return [...company.annual].filter(r=>finite(r.metrics?.revenue_usd)&&r.metrics.revenue_usd>=0)
  .sort((a,b)=>a.fiscal_end.localeCompare(b.fiscal_end))
  .map(r=>({fiscal_end:r.fiscal_end,revenue_usd:r.metrics.revenue_usd}));
}
function csvEscape(value){
 if(value===null||value===undefined)return '';
 if(finite(value))return String(value);
 let v=String(value);
 // Protect spreadsheet consumers against formula injection; preserve the original
 // string only for ordinary numeric, date, and issuer values.
 if(/^[\s\u0000-\u001f]*[=+@-]/.test(v))v="'"+v;
 return '"'+v.replaceAll('"','""')+'"';
}
const SOURCE_FIELDS=['revenue_usd','operating_income_usd','net_income_usd','operating_cash_flow_usd','capex_usd'];
const DATA_FIELDS=[...SOURCE_FIELDS,'free_cash_flow_usd'];
function snapshotCsv(snapshot){
 if(!Array.isArray(snapshot?.companies))throw Error('No SEC data to export');
 const header=['as_of','symbol','company','editorial_sector','cik','fiscal_end',...DATA_FIELDS,...SOURCE_FIELDS.flatMap(k=>[k+'_tag',k+'_filed',k+'_accession']),'companyfacts_url'];
 const rows=[header];
 for(const company of snapshot.companies){
  for(const annual of company.annual||[]){
   const cells=[snapshot.as_of,company.symbol,company.name,company.sector,company.cik,annual.fiscal_end,
    ...DATA_FIELDS.map(k=>annual.metrics?.[k]??null),
    ...SOURCE_FIELDS.flatMap(k=>[annual.sources?.[k]?.tag??null,annual.sources?.[k]?.filed??null,annual.sources?.[k]?.accession??null]),
    company.source_url];
   rows.push(cells);
  }
 }
 return rows.map(row=>row.map(csvEscape).join(',')).join('\r\n')+'\r\n';
}
root.QFSecAnalytics={METRICS,metricValue,ranking,revenueSeries,snapshotCsv};
})(typeof globalThis!=='undefined'?globalThis:this);
