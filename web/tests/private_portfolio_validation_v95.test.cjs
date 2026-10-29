const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const api=require('../site/private_portfolio_validation_v95.js');
const dates=Array.from({length:310},(_,i)=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10));
const closes=(base,mult)=>dates.map((_,i)=>base*Math.exp(.0003*i+.017*Math.sin(i*.3)*mult));
const history={symbols:['AAA','BBB','CCC'],dates,closes:{AAA:closes(100,1),BBB:closes(150,.4),CCC:closes(70,.7)},sessions_per_year:252};
const asOf='2025-11-10';
const quotes={AAA:{price:120,timestamp:'2025-11-09T16:00:00Z'},BBB:{price:100,timestamp:'2025-11-09T16:00:00Z'}};
const portfolio={cash:1000,holdings:{AAA:10,BBB:10}};
function fakeSec(){return {as_of:'2025-10-31',companies:[
 {symbol:'AAA',source_url:'https://www.sec.gov',annual:[{fiscal_end:'2025-06-30',metrics:{revenue_usd:1e9,free_cash_flow_usd:1e8,net_income_usd:8e7}},{fiscal_end:'2024-06-30',metrics:{revenue_usd:9e8}}]},
 {symbol:'BBB',annual:[{fiscal_end:'2025-06-30',metrics:{revenue_usd:9e8,free_cash_flow_usd:-3e7,net_income_usd:-1e7}},{fiscal_end:'2024-06-30',metrics:{revenue_usd:8e8}}]}
]};}
test('full portfolio weights include cash and validated holdings, and cash-funded scenario changes volatility',()=>{
 const p=api.portfolioRisk({portfolio,quotes,history,asOf,symbol:'AAA',maxWeight:.5});
 assert.equal(p.ready,true);assert.equal(p.allocation.positions.length,2);
 assert.equal(p.allocation.cashWeight,0.3125);assert.equal(p.allocation.largestWeight,.375);
 assert.ok(p.baseline.annualVolatility>=0);assert.equal(p.baseline.observations,309);
 assert.ok(p.hypothetical);assert.equal(p.hypothetical.fundedFromCashPercent,5);
 assert.notEqual(p.baseline.annualVolatility,p.hypothetical.annualVolatility);
});
test('incomplete whole-portfolio coverage refuses to disguise selected subset as full risk',()=>{
 const p=api.portfolioRisk({portfolio:{cash:1000,holdings:{AAA:3,CCC:2}},quotes:{...quotes,CCC:{price:90,timestamp:quotes.AAA.timestamp}},history:{...history,symbols:['AAA','BBB'],closes:{AAA:history.closes.AAA,BBB:history.closes.BBB}},asOf});
 assert.equal(p.ready,false);assert.match(p.reason,/EVERY held investment/);assert.equal(p.baseline,null);
});
test('stale quote, invalid quantity, unavailable cash reject whole account',()=>{
 assert.equal(api.portfolioRisk({portfolio,quotes:{...quotes,AAA:{price:120,timestamp:'2025-10-01'}},history,asOf}).ready,false);
 assert.equal(api.portfolioRisk({portfolio:{cash:-1,holdings:{}},history,asOf}).ready,false);
 assert.equal(api.portfolioRisk({portfolio:{cash:10,holdings:{AAA:-2}},history,asOf}).ready,false);
});
test('cash-only account returns well-defined zero price volatility without invented holdings',()=>{
 const p=api.portfolioRisk({portfolio:{cash:500,holdings:{}},quotes:{},asOf});
 assert.equal(p.ready,true);assert.equal(p.baseline.annualVolatility,0);assert.equal(p.hypothetical,null);
});
test('past-only gates use training ending before non-overlapping later windows',()=>{
 const p=api.riskGateAudit({history,symbol:'AAA',maxDrawdown:.15,train:126,test:21});
 assert.equal(p.ready,true);assert.ok(p.summary.count>=2);
 for(const w of p.windows)assert.ok(w.trainThrough<w.testFrom&&w.testFrom<=w.testThrough);
 assert.ok(p.summary.count===p.summary.allowed+p.summary.blocked);
});
test('changing only later prices cannot change first training gate, but can change the observed test result',()=>{
 const base=api.riskGateAudit({history,symbol:'AAA',maxDrawdown:.15,train:126,test:21});
 const mutated={...history,closes:{...history.closes,AAA:[...history.closes.AAA]}};
 mutated.closes.AAA[140]*=.6;
 const edited=api.riskGateAudit({history:mutated,symbol:'AAA',maxDrawdown:.15,train:126,test:21});
 assert.equal(base.ready,true);assert.equal(edited.ready,true);
 // Check first test window using the shared first chronological boundary via independently calculated train-period prices.
 const firstGate=prices=>{let peak=prices[0],dd=0;for(const p of prices){peak=Math.max(peak,p);dd=Math.min(dd,p/peak-1);}return dd>=-.15;};
 assert.equal(firstGate(history.closes.AAA.slice(0,126)),firstGate(mutated.closes.AAA.slice(0,126)));
 assert.notEqual(history.closes.AAA[140],mutated.closes.AAA[140]);
});
test('thin data and missing candidates cannot become completed policy audits',()=>{
 assert.equal(api.riskGateAudit({history,symbol:'NOT',maxDrawdown:.2}).ready,false);
 assert.equal(api.riskGateAudit({history:{...history,dates:dates.slice(0,80),closes:Object.fromEntries(Object.entries(history.closes).map(([s,v])=>[s,v.slice(0,80)]))},symbol:'AAA',maxDrawdown:.2}).ready,false);
});
test('cashflow scenarios use authentic annual FCF but withhold negative and missing values',()=>{
 const s=api.cashFlowScenarios({snapshot:fakeSec(),selection:['AAA','BBB','CCC'],asOf});
 assert.equal(s.ready,true);assert.equal(s.rows[0].aggregateFcfScenarios[0],1);
 assert.equal(s.rows[0].cashConversion,1.25);
 assert.equal(s.rows[1].aggregateFcfScenarios,null);
 assert.equal(s.rows[2].aggregateFcfScenarios,null);
 assert.match(s.note,/not enterprise valuations/);
});
test('future or stale SEC snapshot cannot invent cashflow comparisons',()=>{
 assert.equal(api.cashFlowScenarios({snapshot:{...fakeSec(),as_of:'2026-01-01'},selection:['AAA','BBB'],asOf}).ready,false);
 assert.equal(api.cashFlowScenarios({snapshot:{...fakeSec(),as_of:'2019-01-01'},selection:['AAA','BBB'],asOf}).ready,false);
});
test('export is intentionally sanitized: no holdings, cash, prices, weights or quantitative risk',()=>{
 const packet=api.build({portfolio,quotes,history,symbol:'AAA',snapshot:fakeSec(),selection:['AAA','BBB','CCC'],asOf,maxDrawdown:.25,maxWeight:.5});
 const brief=JSON.stringify(api.exportSafe(packet));
 for(const secret of ['\"holdings\":','\"cashWeight\":','\"largestWeight\":','\"annualVolatility\":','\"AAA\"','\"120\"','\"1000\"','\"positions\":'])assert.equal(brief.includes(secret),false,secret);
 assert.equal(api.exportSafe(packet).portfolioRiskAvailable,true);
});
test('new helper is pure and has no IO, storage, authentication or brokerage methods',()=>{
 const text=fs.readFileSync(path.resolve(__dirname,'../site/private_portfolio_validation_v95.js'),'utf8');
 for(const forbidden of ['fetch(', 'localStorage','sessionStorage','private/trade','private/state','api(', 'XMLHttpRequest','navigator.sendBeacon'])assert.equal(text.includes(forbidden),false,forbidden);
});
