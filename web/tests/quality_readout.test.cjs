const test=require('node:test'),assert=require('node:assert/strict');
const Q=require('../site/research_readout_v29.js'),C=require('../site/research_models_core_v22.js'),E=require('../site/research_errors_v24.js');
require('../site/research_evidence_v26.js');
const record=(date,revenue,operating,net=20)=>({fiscal_end:date,metrics:{revenue_usd:revenue,operating_income_usd:operating,net_income_usd:net,operating_cash_flow_usd:40,capex_usd:50,free_cash_flow_usd:-10}});
test('financial finding distinguishes percentage growth from percentage-point margin change',()=>{
 const financial={annual:[record('2025-12-31',200e9,60e9),record('2024-12-31',100e9,20e9)]};
 assert.match(Q.financialView(financial).summary,/up 100.0%/);
 assert.match(Q.financialView(financial,'margin').summary,/30.0%.*20.0%.*10.0 percentage-point/);
 assert.deepEqual(Q.financialView(financial,'margin').lines[1].values,[null,1]);
});
test('missing operating income retains genuine revenue periods and a gap, not zero',()=>{
 const r=Q.financialView({annual:[record('2024-12-31',100e9,10e9),record('2025-12-31',120e9,null),record('2026-12-31',144e9,30e9)]});
 assert.deepEqual(r.lines.find(x=>x.name==='Revenue').values,[100,120,144]);
 assert.deepEqual(r.lines.find(x=>x.name==='Operating income').values,[10,null,30]);
 const missing=Q.financialView({annual:[record('2024-12-31',100,null),record('2025-12-31',null,null)]});
 assert.match(missing.summary,/unavailable/);assert.equal(missing.metrics[0].value,null);
});
test('nonannual gaps withhold annual growth and margin-change comparisons',()=>{
 const r={annual:[record('2022-12-31',100,20),record('2025-12-31',200,60)]};
 assert.equal(Q.financialView(r,'margin').lines.find(x=>x.name==='Annual revenue growth'),undefined);
 assert.match(Q.financialView(r).summary,/growth is unavailable/);
 assert.doesNotMatch(Q.financialView(r,'margin').summary,/prior annual/);
 assert.match(Q.financialView(r,'cash').summary,/spending exceeded operating cash flow/);
});
test('short-window axis labels are distinct and tick count adapts to readable width',()=>{
 const dates=Array.from({length:30},(_,i)=>'2026-01-'+String(i+1).padStart(2,'0'));
 assert.deepEqual(Q.axisTicks(dates,260),[{index:0,label:'01-01'},{index:29,label:'01-30'}]);
 assert.equal(Q.axisTicks(dates,500).length,3);assert.equal(Q.axisTicks(dates,850).length,5);
});
test('opt-in chart gaps break paths and disclose missing values; strict callers stay strict',()=>{
 const args=['Reported',['2024','2025','2026'],[{name:'Revenue',values:[100,null,120]}]];
 assert.match(globalThis.QFCharts26.curve(...args),/unavailable/);
 const html=globalThis.QFCharts26.curve(...args,{allowGaps:true});
 assert.doesNotMatch(html,/NaN|undefined/);assert.match(html,/Missing values remain unavailable and create gaps/);assert.match(html,/qf29-chart-legend/);
 assert.match(html,/d="M[0-9.]+ [0-9.]+  M[0-9.]+ [0-9.]+"/);
 assert.match(globalThis.QFCharts26.curve('Empty',['a','b'],[{name:'None',values:[null,null]}],{allowGaps:true}),/unavailable/);
});
test('session, owner and request-limit errors take precedence over provider codes',()=>{
 assert.match(E.apiError(401,'private/history','quote_stale'),/session expired/);
 assert.match(E.apiError(403,'private/history','buy_budget'),/authorized owner/);
 assert.match(E.apiError(429,'private/history','provider_unavailable'),/Too many requests/);
});
test('independent alternating-price risk and constant-cash-flow present value checks',()=>{
 const prices=Array.from({length:91},(_,i)=>({date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),close:i%2?110:100}));
 const risk=C.risk(prices),expectedVol=Math.sqrt(252*90/89*(21/220)**2);
 assert.ok(Math.abs(risk.annual_volatility-expectedVol)<1e-12);
 for(const x of [risk.daily_var95_loss,risk.daily_es95_loss,-risk.max_drawdown])assert.ok(Math.abs(x-1/11)<1e-12);
 const dcf=C.dcfProxy({metrics:{free_cash_flow_usd:100}},{growth:0,discount:.1,terminal:0});
 assert.ok(Math.abs(dcf.proxy_pv-1000)<1e-9);
});

test('financial readout keeps small and negative reported amounts distinguishable from zero',()=>{assert.equal(Q.money(-10),'−$10.00');assert.equal(Q.money(2e6),'$2.00M');assert.equal(Q.money(null),'Unavailable');assert.equal(Q.money(0),'$0.00');});
