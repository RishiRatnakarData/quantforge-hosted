const {test}=require('node:test');
const assert=require('node:assert/strict');
const {build}=require('../site/private_value_v73.js');
const TODAY='2026-10-27T12:00:00Z';
const company={symbol:'MSFT',annual:[{fiscal_end:'2026-06-30',metrics:{revenue_usd:331839000000,free_cash_flow_usd:66987000000}}]};
const capital={symbol:'MSFT',shares:{value:7500000000,periodEnd:'2026-07-31',tag:'EntityCommonStockSharesOutstanding'},cash:{value:30000000000,periodEnd:'2026-06-30'},reportedDebtComponentsTotal:47000000000,debtCashSamePeriod:true,source:'SEC EDGAR',sourceUrl:'https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json'};
const quote={symbol:'MSFT',price:400,venue:'IEX',timestamp:'2026-10-26T19:59:00Z'};
test('price to cash flow and yield use SEC shares and observed quote',()=>{
 const m=build(company,capital,quote,TODAY);
 assert.equal(m.marketCap,3e12);assert.equal(m.pFcf,3e12/66987000000);
 assert.equal(m.fcfYield,66987000000/3e12);assert.equal(m.approximateEV,3e12+47e9-30e9);
 assert.equal(m.enterpriseComplete,false);assert.equal(m.symbol,'MSFT');
});
test('missing shares suppresses all market-cap-based measures',()=>{
 const m=build(company,{...capital,shares:null},quote,TODAY);
 assert.equal(m.marketCap,null);assert.equal(m.fcfYield,null);assert.equal(m.pFcf,null);
});
test('no quote date or stale date cannot silently pass',()=>{
 for(const q of [{...quote,timestamp:undefined},{...quote,timestamp:'2026-01-01T00:00:00Z'}]){
  const m=build(company,capital,q,TODAY); assert.equal(m.marketCap,null);
 }
});
test('negative FCF has a negative yield but no meaningless P/FCF',()=>{
 const c={...company,annual:[{...company.annual[0],metrics:{...company.annual[0].metrics,free_cash_flow_usd:-5e9}}]};
 const m=build(c,capital,quote,TODAY);
 assert(m.fcfYield<0);assert.equal(m.pFcf,null);
});
test('missing SEC debt, or different period, removes indicative EV without inventing zero',()=>{
 const m=build(company,{...capital,debtCashSamePeriod:false},quote,TODAY);
 assert.equal(m.marketCap,3e12);assert.equal(m.approximateEV,null);
});
test('issuer mismatches cannot create a comparison',()=>{
 assert.throws(()=>build(company,{...capital,symbol:'AAPL'},quote,TODAY),/symbols do not match/);
 assert.throws(()=>build(company,capital,{...quote,symbol:'AAPL'},TODAY),/symbols do not match/);
});
test('stale SEC shares or annual data are unavailable',()=>{
 const c={...capital,shares:{...capital.shares,periodEnd:'2024-01-01'}};
 assert.equal(build(company,c,quote,TODAY).marketCap,null);
 const old={...company,annual:[{...company.annual[0],fiscal_end:'2023-06-30'}]};
 const m=build(old,capital,quote,TODAY);
 assert.equal(m.marketCap,3e12);assert.equal(m.fcfYield,null);assert.equal(m.pSales,null);
});
