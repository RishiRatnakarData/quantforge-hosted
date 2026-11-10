'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const core=require('../site/research_core_v20.js');
const snapshot=JSON.parse(fs.readFileSync(path.join(__dirname,'../site/sec_snapshot.json'),'utf8'));
const company=snapshot.companies.find(c=>c.symbol==='MSFT');
const f=core.financialSummary(company,snapshot.as_of);

test('company summaries have scoped versioned evidence IDs and SEC metadata',()=>{
 assert.equal(f.schema_version,1);
 assert.equal(f.symbol,'MSFT');
 assert.equal(f.scope,'single_company');
 assert.equal(f.source.type,'sec');
 assert.ok(f.annual.length>1);
 assert.ok(f.evidence.some(e=>e.accession&&e.filed&&e.fiscal_end));
 for(const finding of f.findings)for(const id of finding.evidence_ids)assert.ok(f.evidence.some(e=>e.id===id),id);
});

test('reported negative FCF is retained, not clamped or zero-filled',()=>{
 const c={symbol:'TEST',annual:[{fiscal_end:'2025-12-31',metrics:{revenue_usd:100,operating_income_usd:-2,free_cash_flow_usd:-50}},{fiscal_end:'2024-12-31',metrics:{revenue_usd:200}}]};
 const r=core.financialSummary(c,'2026-05-01');
 assert.equal(r.metrics.free_cash_flow_usd,-50);
 assert.equal(r.metrics.revenue_growth,-.5);
 assert.ok(r.findings.some(x=>x.kind==='caution'&&x.evidence_ids.includes('sec:free_cash_flow_usd')));
 assert.equal(r.metrics.net_income_usd,null);
});

test('public simulation is deterministic and remains separate from genuine market risk',()=>{
 const a=core.syntheticPrice('MSFT'),b=core.syntheticPrice('MSFT'),c=core.syntheticPrice('AAPL');
 assert.equal(a.length,520);
 assert.deepEqual(a,b);
 assert.notDeepEqual(a,c);
 const result=core.researchResult(f,a,{type:'synthetic'});
 assert.equal(result.price_source,'synthetic');
 assert.ok(!('observed_price_risk' in result.metrics));
 assert.ok(result.limitations.some(x=>x.includes('Synthetic chart')));
 assert.ok(!result.evidence.some(e=>e.id==='market:drawdown'));
});

test('observed market risk includes exact dated evidence but no forecast',()=>{
 const prices=core.syntheticPrice('MSFT');
 const r=core.researchResult(f,prices,{type:'market',source:'Unit fixture'});
 assert.equal(r.metrics.observed_price_risk.sessions,520);
 assert.ok(r.evidence.some(e=>e.id==='market:volatility'&&e.period.first===prices[0].date));
 assert.ok(!r.findings.some(x=>/price target|buy|sell/.test(x.text.toLowerCase())));
});

test('price series validates dates, duplicates, ordering and price values',()=>{
 const price=core.syntheticPrice('MSFT');
 assert.throws(()=>core.priceSeries([price[1],price[0]]),/ascending/);
 assert.throws(()=>core.priceSeries([price[0],price[0]]),/distinct/);
 assert.throws(()=>core.priceSeries([{date:'2026-05-06',close:NaN}]),/finite/);
 assert.throws(()=>core.priceSeries([{date:'2026-05-06',close:0}]),/positive/);
 assert.throws(()=>core.priceSeries([{date:'not a date',close:100}]),/dates/);
});

test('history windows are anchored to last observation and do not interpolate missing dates',()=>{
 const p=core.syntheticPrice('NVDA');
 assert.deepEqual(core.chartWindow(p,'ALL'),p);
 const month=core.chartWindow(p,30);
 assert.equal(month.at(-1).date,p.at(-1).date);
 assert.ok(month.length<=25&&month.length>10);
 assert.throws(()=>core.chartWindow(p,-1),/Unsupported/);
});

test('drawdown uses running peak and historical volatility has finite units',()=>{
 const data=Array.from({length:20},(_,i)=>({date:new Date(Date.UTC(2026,0,1+i)).toISOString().slice(0,10),close:i===5?150:i>=6?75:100}));
 const metrics=core.priceStatistics(data);
 assert.equal(metrics.max_drawdown,-0.5);
 assert.ok(metrics.annual_volatility>0);
 assert.equal(core.priceStatistics(data.slice(0,5)),null);
});

test('missing SEC issuer metrics remain unavailable and do not produce positive findings',()=>{
 const result=core.financialSummary({symbol:'NONE',annual:[{fiscal_end:'2025-12-31',metrics:{}},{fiscal_end:'2024-12-31',metrics:{}}]},'2026-03-01');
 assert.equal(result.metrics.revenue_growth,null);
 assert.equal(result.metrics.operating_margin,null);
 assert.ok(result.findings.length===0);
 assert.equal(result.status,'partial');
});

test('generated public HTML includes five visible destinations, source distinctions and one-company flow',()=>{
 const html=fs.readFileSync(path.join(__dirname,'../site/site.template.html'),'utf8');
 const nav=html.split('id="qf-v20-navigation"')[1].split('</nav>')[0];
 assert.deepEqual([...nav.matchAll(/data-page="(\w+)"/g)].map(x=>x[1]),['explore','compare','models','portfolio','methods']);
 assert.match(html,/id="qf-v20-chart"/);
 assert.match(html,/id="qf-v20-analyze"/);
 assert.match(html,/id="qf-v20-news"/);
 assert.match(html,/id="qf-v20-financial-table"/);
 assert.match(html,/Illustrative public chart/);
});
