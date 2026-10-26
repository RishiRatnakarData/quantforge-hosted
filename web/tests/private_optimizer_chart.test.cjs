"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const src = fs.readFileSync(require('node:path').join(__dirname,'../site/private.js'),'utf8');
const first = src.indexOf('function optSvgFrontier(points, equal, optimized){');
const last = src.indexOf('\nfunction optimizationTable(',first);
assert.ok(first >= 0 && last > first, 'chart function must be defined');
const ctx = {};
vm.runInNewContext(src.slice(first,last) + '\nthis.drawChart = optSvgFrontier;',ctx);
const draw=ctx.drawChart;
const s=(risk,mean)=>({risk,historicalMean:mean});
test('constant-volatility scenario is centered, labeled, and never collapses to left axis',()=>{
  const html=draw([s(.26,.14),s(.26,.18)],{annualVolatility:.26,annualHistoricalMean:.15},{annualVolatility:.26,annualHistoricalMean:.18});
  assert.match(html,/almost identical volatility/);
  assert.match(html,/26\.00%/);
  assert.doesNotMatch(html,/NaN|Infinity/);
  const scenario=html.match(/<circle cx="([\d.]+)" cy="[\d.]+" r="4"/);
  assert.ok(scenario);
  const x=Number(scenario[1]);
  assert.ok(x>220&&x<410,`expected centered scenario x, got ${x}`);
});
test('overlapping candidates are collapsed into distinct markers',()=>{
 const html=draw([s(.27,.12),s(.27,.12),s(.28,.16)],null,null);
 assert.equal((html.match(/r="4"/g)||[]).length,2);
 assert.match(html,/Annualized historical volatility/);
});
test('selected and equal portfolios have distinct markers and non-finite inputs fail closed',()=>{
 const html=draw([s(.22,.11),s(.28,.17)],{annualVolatility:.25,annualHistoricalMean:.14},{annualVolatility:.22,annualHistoricalMean:.11});
 assert.match(html,/Equal-weight/);
 assert.match(html,/Selected optimized/);
 assert.match(html,/0\.00%|22\.00%/);
 assert.match(draw([s(Infinity,.2)],null,null),/unavailable/);
});
