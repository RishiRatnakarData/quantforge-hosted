'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const integrity = require('../site/private_integrity_v67.js');
const wf = require('../site/private_walkforward_v65.js');
const forecast = require('../site/private_forecast_v65.js');
const diagnostics = require('../site/private_diagnostics_v66.js');
function history(n=190) {
  const dates=Array.from({length:n},(_,i)=>new Date(Date.UTC(2025,0,i+1)).toISOString().slice(0,10));
  return {symbols:['AAA','BBB','CCC'], dates, source:'Alpaca stocks IEX split-adjusted daily bars',
    as_of:'2025-07-10',calendar:'shared US stock sessions',sessions_per_year:252,
    closes:{AAA:dates.map((_,i)=>+(100*Math.exp(i*.0003+.03*Math.sin(i/8))).toFixed(5)),
      BBB:dates.map((_,i)=>+(80*Math.exp(i*.0001+.05*Math.sin(i/11+1))).toFixed(5)),
      CCC:dates.map((_,i)=>+(160*Math.exp(-i*.0002+.04*Math.cos(i/9))).toFixed(5))}};
}
const options={train:63,step:21,objective:'inverse',cap:.65,feeBps:5,capital:10000};
const company={symbol:'ACME',name:'Test Co',source:'synthetic fixture',as_of:'2025-10-01',
  annual:[{fiscal_end:'2023-12-31',metrics:{revenue_usd:1000000,free_cash_flow_usd:150000}},
    {fiscal_end:'2024-12-31',metrics:{revenue_usd:1100000,free_cash_flow_usd:180000}},
    {fiscal_end:'2025-12-31',metrics:{revenue_usd:1200000,free_cash_flow_usd:200000}}]};
const forecastOpts={years:5,growth:.06,fcfMargin:.12,discount:.1,terminal:.02};
test('SHA-256 implements standard UTF-8 vectors, not an insecure shortened hash',()=>{
  for(const v of ['', 'abc', 'QuantForge Δ emerging research','🤖🦊']) {
    assert.equal(integrity.sha256(v),createHash('sha256').update(v,'utf8').digest('hex'));
  }
});
test('market data fingerprint deterministic across object property order and use of the same data',()=>{
  const h=history(),r=wf.run(h,options),m=integrity.marketManifest(h,r,'2 years');
  assert.equal(m.schema,'quantforge.research.manifest.v1');
  assert.equal(m.data.fingerprint.length,64);
  assert.equal(m.data.observationCount,190);
  assert.equal(m.data.requestedPeriod,'2 years');
  assert.ok(integrity.verifyMarketFingerprint(h,m));
  const changedOrder={...h,closes:{CCC:h.closes.CCC,AAA:h.closes.AAA,BBB:h.closes.BBB}};
  assert.ok(integrity.verifyMarketFingerprint(changedOrder,m));
  assert.equal(m.data.fingerprint,integrity.marketManifest(h,r,'2 years').data.fingerprint);
});
test('single historical close mutation invalidates original fingerprint',()=>{
  const h=history(),r=wf.run(h,options),m=integrity.marketManifest(h,r,'365');
  const tampered=history();tampered.closes.BBB[84]+=0.01;
  assert.equal(integrity.verifyMarketFingerprint(tampered,m),false);
});
test('invalid, stale or incomplete histories cannot produce plausible research fingerprints',()=>{
  const h=history(),r=wf.run(h,options);
  assert.throws(()=>integrity.marketManifest({...h,dates:[...h.dates].reverse()},r),/Aligned/);
  assert.throws(()=>integrity.marketManifest({...h,closes:{...h.closes,AAA:h.closes.AAA.slice(1)}},r),/Incomplete/);
  assert.throws(()=>integrity.marketManifest({...h,closes:{...h.closes,AAA:h.closes.AAA.map((x,i)=>i===5?NaN:x)}},r),/Incomplete/);
  assert.throws(()=>integrity.marketManifest(h,{...r,symbols:['BBB','AAA','CCC']}),/do not match/);
});
test('market research manifest records IEX provenance and reproducible settings without raw prices',()=>{
  const h=history(),r=wf.run(h,options),d=diagnostics.summarizeWalkforward(r);
  const report=integrity.attachWalkforward(diagnostics.report('walkforward',r,d),h,r,'2 years');
  assert.equal(report.manifest.data.source,h.source);
  assert.equal(report.manifest.model.trainingObservations,63);
  assert.equal(report.manifest.model.feeBps,5);
  assert.equal(report.modelRisk.evaluationWindows,r.windows.length);
  assert.ok(report.modelRisk.flags.some(s=>s.includes('Selection')));
  const text=JSON.stringify(report);
  for(const privateField of ['closes','access_token','refresh_token','api_key','private_notes','holdings']) {
    assert.equal(text.includes('"'+privateField+'"'),false);
  }
  assert.equal(text.includes(h.closes.AAA[10].toString()),false);
});
test('forecast baseline digest stable and detects a revised reported revenue',()=>{
  const r=forecast.run(company,forecastOpts),manifest=integrity.secManifest(r);
  assert.equal(manifest.data.reportedFiscalYears,3);
  assert.equal(manifest.data.fingerprint.length,64);
  assert.equal(manifest.data.fingerprint,integrity.secManifest(r).data.fingerprint);
  const changed=JSON.parse(JSON.stringify(r));changed.historic[0].revenue+=1;
  assert.notEqual(manifest.data.fingerprint,integrity.secManifest(changed).data.fingerprint);
});
test('forecasts make terminal-value exposure prominent and compare assumed against reported margin',()=>{
  const r=forecast.run(company,forecastOpts),risk=integrity.forecastRisk(r),base=risk.scenarios[1];
  assert.ok(base.terminalShare>0 && base.terminalShare<1);
  assert.equal(base.terminalShare,r.scenarios[1].terminalPV/r.scenarios[1].proxy);
  assert.ok(Math.abs(risk.observedFcfMargin-1/6)<1e-8);
  assert.ok(Math.abs(risk.marginAssumptionDifferencePp-(.12-1/6)*100)<1e-8);
  assert.ok(risk.warnings.some(x=>x.includes('per-share')));
});
test('missing SEC cash flows cannot produce fabricated terminal share or valuation',()=>{
  const blank={...company,annual:company.annual.map(x=>({...x,metrics:{...x.metrics,free_cash_flow_usd:null}}))};
  const r=forecast.run(blank,forecastOpts),risk=integrity.forecastRisk(r);
  assert.equal(risk.observedFcfMargin,null);
  assert.equal(risk.scenarios[1].terminalShare,null);
  assert.equal(risk.scenarios[1].totalCashFlowProxy,null);
});
test('tampered and unordered SEC annual periods are rejected',()=>{
  const r=forecast.run(company,forecastOpts);
  assert.throws(()=>integrity.secManifest({...r,historic:[...r.historic].reverse()}),/ordered/);
  assert.throws(()=>integrity.secManifest({...r,historic:r.historic.map((x,i)=>i===0?{...x,revenue:-3}:x)}),/Invalid/);
});
test('forecast export retains provenance but omits provider credentials',()=>{
  const r=forecast.run(company,forecastOpts),grid=diagnostics.forecastSensitivity(company,forecastOpts);
  const report=integrity.attachForecast(diagnostics.report('forecast',r,grid),r);
  assert.equal(report.manifest.researchType,'forecast');
  assert.equal(report.modelRisk.reportedFiscalYears,3);
  assert.ok(!JSON.stringify(report).includes('api_key'));
  assert.equal(report.hypothetical,true);
});
