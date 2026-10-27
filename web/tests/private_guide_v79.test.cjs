'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../site/private_guide_v79.js'),'utf8');
const {analyze}=require('../site/private_guide_v79.js');
test('pure report has no fetch, networking, storage, account mutations or AI provider calls',()=>{
 for(const pattern of [/\bfetch\s*\(/,/\blocalStorage\b/,/\bsessionStorage\b/,/\bXMLHttpRequest\b/,/\bWebSocket\b/,/\/api\/private\//,/\btrade\s*\(/])assert.doesNotMatch(source,pattern);
});
test('zero holdings creates next-step actions without an investment recommendation',()=>{
 const r=analyze({cash:0,holdings:{},quotes:{}});
 assert.match(r.facts.join(' '),/no funded positions/);
 assert.ok(r.actions.some(x=>x.id==='ideas'));
 assert.doesNotMatch(JSON.stringify(r),/buy now|sell now|guaranteed/ig);
});
test('missing quotes suppress total and concentration',()=>{
 const r=analyze({cash:300,holdings:{MSFT:3},quotes:{}});
 assert.ok(r.warnings.some(x=>/withheld/.test(x)));
 assert.ok(!r.facts.some(x=>/total, including/.test(x)));
});
test('concentration and cash are calculated only from complete priced positions',()=>{
 const r=analyze({cash:100,holdings:{MSFT:9,GOOGL:1},quotes:{MSFT:{price:100},GOOGL:{price:100}}});
 assert.ok(r.warnings.some(x=>/Concentration check/.test(x)));
 assert.ok(r.facts.some(x=>/\$1,100 total/.test(x)));
});
test('historical optimization must match the loaded universe',()=>{
 const base={cash:0,holdings:{},quotes:{},history:{symbols:['AAA','BBB'],dates:['2026-01-01','2026-09-30']},optimizer:{symbols:['X','Y'],equal:{annualVolatility:.2},optimized:{annualVolatility:.11}}};
 const r=analyze(base);
 assert.ok(!r.facts.some(x=>/Portfolio allocation model/.test(x)));
 assert.ok(r.actions.some(x=>x.id==='optimization'));
});
test('walk-forward remains a retrospective comparison, not a recommendation',()=>{
 const r=analyze({cash:1000,holdings:{},quotes:{},history:{symbols:['A','B'],dates:['2026-01-01','2026-05-01']},walkforward:{symbols:['A','B'],optimized:{metrics:{change:.06,maxDrawdown:-.17}},benchmark:{metrics:{change:.09}}}});
 assert.ok(r.facts.some(x=>/strategy 6.0% vs equal-weight benchmark 9.0%/.test(x)));
 assert.ok(r.warnings.some(x=>/selection bias/.test(x)));
});
test('no fabricated financial values when company record has missing metrics',()=>{
 const r=analyze({company:{name:'Demo',annual:[{fiscal_end:'2024-12-31',metrics:{revenue_usd:null,free_cash_flow_usd:null}}]}});
 assert.ok(!r.facts.some(x=>/reported revenue/.test(x)));
 assert.ok(r.warnings.some(x=>/cash-flow proxy is unavailable/.test(x)));
});
test('personal risk caveats are conditional and do not pretend to know suitability',()=>{
 const r=analyze({horizon:'short',comfort:'low'});
 assert.ok(r.warnings.length>=2);
 assert.match(r.notes.join(' '),/does not know your debts/);
});

test('screening, what-if and robustness are integrated without treating scores as profit chances',()=>{
 const r=analyze({cash:1000,holdings:{AAPL:2},quotes:{AAPL:{price:100,timestamp:'2026-10-01T15:30:00Z'}},
 screening:{comparisons:[{symbol:'AAPL'}],warnings:['missing data']},
 purchaseImpact:{proposedBudget:250,before:{largest:{weight:.2}},after:{largest:{weight:.4}}},
 robustness:{matchedWindows:4},forecast:{scenarios:[]},now:'2026-10-27T18:00:00Z'});
 assert.ok(r.facts.some(x=>/1 candidates compared/.test(x)));
 assert.ok(r.facts.some(x=>/20.0% before versus 40.0% after/.test(x)));
 assert.ok(r.facts.some(x=>/robustness/.test(x)));
 assert.ok(r.warnings.some(x=>/seven calendar days old/.test(x)));
 assert.ok(r.facts.some(x=>/hypothetical multi-year/.test(x)));
});

test('cross-model synthesis identifies mixed evidence without a buy or sell decision',()=>{
 const report=analyze({history:{symbols:['A','B'],dates:['2026-01-01','2026-07-01']},
  optimizer:{symbols:['A','B'],equal:{annualVolatility:.20},optimized:{annualVolatility:.16}},
  walkforward:{symbols:['A','B'],optimized:{metrics:{change:-.08}},benchmark:{metrics:{change:.03}}}});
 assert.ok(report.warnings.some(x=>/different measures/.test(x)));
 assert.doesNotMatch(JSON.stringify(report),/you should buy|you should sell/);
});
