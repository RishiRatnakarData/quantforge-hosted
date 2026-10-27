'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const diagnostics = require('../site/private_diagnostics_v66.js');
const walkforward = require('../site/private_walkforward_v65.js');
const forecast = require('../site/private_forecast_v65.js');

const company = {
  symbol:'ACME',name:'ACME (synthetic test fixture)',source:'synthetic SEC-style fixture',as_of:'2026-10-01',
  annual:[
    {fiscal_end:'2025-12-31',metrics:{revenue_usd:1400000,free_cash_flow_usd:250000}},
    {fiscal_end:'2024-12-31',metrics:{revenue_usd:1300000,free_cash_flow_usd:230000}},
    {fiscal_end:'2023-12-31',metrics:{revenue_usd:1200000,free_cash_flow_usd:200000}}
  ]
};
function history(n=190){
  const dates=Array.from({length:n},(_,i)=>new Date(Date.UTC(2025,0,i+1)).toISOString().slice(0,10));
  return {symbols:['AAA','BBB','CCC'],dates,source:'synthetic fixture — not real market data',sessions_per_year:252,
    closes:{
      AAA:dates.map((_,i)=>+(100*Math.exp(i*.0003+.03*Math.sin(i/8))).toFixed(5)),
      BBB:dates.map((_,i)=>+(80*Math.exp(i*.0001+.05*Math.sin(i/11+1))).toFixed(5)),
      CCC:dates.map((_,i)=>+(160*Math.exp(-i*.0002+.04*Math.cos(i/9))).toFixed(5))
    }};
}
const options={train:63,step:21,objective:'inverse',cap:.65,feeBps:5,capital:10000};

test('walk-forward diagnostics reconcile per-window fees and nonoverlapping windows',()=>{
  const run=walkforward.run(history(),options);
  const audit=diagnostics.summarizeWalkforward(run);
  assert.ok(audit.rows.length>=3);
  assert.equal(audit.rows.length,run.windows.length);
  assert.ok(Math.abs(audit.totalFees[0]-run.optimized.fees)<1e-6);
  assert.ok(Math.abs(audit.totalFees[1]-run.benchmark.fees)<1e-6);
  assert.equal(audit.rows[0].testStart,run.windows[0].testStart);
  assert.ok(audit.rows.every(x=>Number.isFinite(x.optimizedReturn)&&Number.isFinite(x.activeReturn)));
  assert.ok(audit.meanWeightChange>=0&&audit.maxWeightChange<=1);
});

test('diagnostics reject missing or tampered fee attribution',()=>{
  const run=walkforward.run(history(),options);
  run.windows[0].rebalanceFees=[0,0];
  assert.throws(()=>diagnostics.summarizeWalkforward(run),/reconcile/i);
});

test('diagnostics reject overlapping or missing future date boundaries',()=>{
  const run=walkforward.run(history(),options);
  run.windows[1].testStart=run.windows[0].testStart;
  assert.throws(()=>diagnostics.summarizeWalkforward(run),/boundaries/i);
});

test('transaction-cost counterfactuals reuse the same evaluation dates',()=>{
  const h=history(),run=walkforward.run(h,options);
  const check=diagnostics.costSensitivity(h,run);
  assert.deepEqual(check.map(x=>x.feeBps),[0,5,20]);
  assert.ok(check.every(x=>Number.isFinite(x.optimizedChange)&&x.optimizedFees>=0));
  assert.ok(check[0].optimizedChange >= check.at(-1).optimizedChange-1e-8);
});

test('SEC growth/discount sensitivity central cell equals base-case forecast',()=>{
  const opts={years:5,growth:.06,fcfMargin:.12,discount:.10,terminal:.02};
  const grid=diagnostics.forecastSensitivity(company,opts);
  const base=forecast.run(company,opts).scenarios[1].proxy;
  assert.equal(grid.cells.length,5);
  assert.equal(grid.cells[0].length,5);
  assert.ok(Math.abs(grid.cells[2][2]-base)<1e-5);
  assert.ok(grid.cells[2][4]>grid.cells[2][0]);
  assert.ok(grid.cells[0][2]>grid.cells[4][2]);
  assert.equal(grid.historicalPeriods,3);
});

test('forecast sensitivity suppresses values when reported FCF is unavailable',()=>{
  const blank={...company,annual:company.annual.map((x,i)=>({...x,metrics:{...x.metrics,free_cash_flow_usd:null}}))};
  const grid=diagnostics.forecastSensitivity(blank,{years:5,growth:.06,fcfMargin:.12,discount:.10,terminal:.02});
  assert.equal(grid.fcfAvailable,false);
  assert.ok(grid.cells.flat().every(v=>v===null));
});

test('forecasts reject invalid assumptions and do not invent SEC data',()=>{
  assert.throws(()=>diagnostics.forecastSensitivity(company,{years:5,growth:.06,fcfMargin:.12,discount:.01,terminal:.02}),/discount rate/);
  assert.throws(()=>diagnostics.forecastSensitivity({...company,annual:[]},{years:5,growth:.06,fcfMargin:.12,discount:.10,terminal:.02}),/SEC annual/);
});

test('research JSON reports exclude credentials, holdings and raw provider prices',()=>{
  const h=history(),r=walkforward.run(h,options),a=diagnostics.summarizeWalkforward(r);
  const exported=JSON.stringify(diagnostics.report('walkforward',r,a));
  assert.equal(JSON.parse(exported).schema,'quantforge.research.v1');
  for(const banned of ['access_token','api_key','refresh_token','password','closes'])assert.equal(exported.includes(banned),false);
  assert.equal(JSON.parse(exported).investments.length,3);
  const fc=forecast.run(company,{years:5,growth:.06,fcfMargin:.12,discount:.1,terminal:.02});
  const grid=diagnostics.forecastSensitivity(company,{years:5,growth:.06,fcfMargin:.12,discount:.1,terminal:.02});
  assert.equal(diagnostics.report('forecast',fc,grid).hypothetical,true);
});
