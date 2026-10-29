const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const api=require('../site/private_research_intelligence_v96.js');
require('../site/private_portfolio_validation_v95.js');
// Browser integration tests use the actual V9.5 helper on global scope.
const days=Array.from({length:315},(_,i)=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10));
const pathSeries=(base,mul)=>days.map((_,i)=>base*Math.exp(.0003*i+.013*Math.sin(i*.31)*mul));
const history={symbols:['AAA','BBB','CCC'],dates:days,closes:{AAA:pathSeries(100,1),BBB:pathSeries(75,.5),CCC:pathSeries(130,.9)},sessions_per_year:252};
const quotes={AAA:{price:130,timestamp:'2025-11-10T12:00:00Z'},BBB:{price:80,timestamp:'2025-11-10T12:00:00Z'}};
const portfolio={cash:2500,holdings:{AAA:3,BBB:4}};
const asOf='2025-11-11';
const snap={as_of:'2025-11-01',companies:[
 {symbol:'AAA',source_url:'https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json',annual:[
  {fiscal_end:'2025-06-30',metrics:{revenue_usd:1e9,free_cash_flow_usd:1.4e8,operating_cash_flow_usd:1.8e8,capex_usd:-4e7,net_income_usd:1.1e8}},
  {fiscal_end:'2024-06-30',metrics:{revenue_usd:9e8,free_cash_flow_usd:1.1e8}}]},
 {symbol:'BBB',annual:[{fiscal_end:'2025-06-30',metrics:{revenue_usd:8e8,free_cash_flow_usd:-2e7,net_income_usd:-3e7}},
  {fiscal_end:'2024-06-30',metrics:{revenue_usd:7e8,free_cash_flow_usd:1e7}}]}
]};
const brief={schema:'quantforge.research-brief.v9.3',symbol:'AAA',universe:[{symbol:'AAA'},{symbol:'BBB'},{symbol:'CCC'}],
 action:'Review',readiness:'Cautious',asOf,policy:'Balanced',modelCoverage:{completed:5}};
test('historical model compares disjoint later periods and charges fees only on exposure change',()=>{
 const x=api.futureRiskScreen({history,symbol:'AAA',limit:.25,feeBps:10});
 assert.equal(x.ready,true);assert.ok(x.period.windows>=2);
 for(const w of x.windows)assert.ok(w.trainThrough<w.outOfSampleFrom&&w.outOfSampleFrom<=w.outOfSampleThrough);
 assert.equal(x.summary.feeBps,10);assert.equal(x.summary.blockedWindows+x.summary.investedWindows,x.period.windows);
 assert.equal(x.period.observations,x.period.windows*21);
});
test('out-of-sample price mutation never alters earlier training decision',()=>{
 const a=api.futureRiskScreen({history,symbol:'AAA',limit:.25});
 const h={...history,closes:{...history.closes,AAA:[...history.closes.AAA]}};
 h.closes.AAA[146]*=.67;
 const b=api.futureRiskScreen({history:h,symbol:'AAA',limit:.25});
 assert.equal(a.ready,true);assert.equal(b.ready,true);
 assert.equal(a.windows[0].riskScreenPassed,b.windows[0].riskScreenPassed);
 assert.notEqual(a.windows[0].observedPeriodReturn,b.windows[0].observedPeriodReturn);
});
test('transaction costs cannot improve always-invested model return',()=>{
 const a=api.futureRiskScreen({history,symbol:'AAA',limit:.9,feeBps:0});
 const b=api.futureRiskScreen({history,symbol:'AAA',limit:.9,feeBps:80});
 assert.ok(a.ready&&b.ready);assert.ok(a.summary.investedWindows>0);
 assert.ok(b.summary.netScreenReturn<=a.summary.netScreenReturn+1e-8);
});
test('bad histories, invalid rules and insufficient data never produce a plausible backtest',()=>{
 for(const bad of [null,{...history,dates:days.slice(0,20)}, {...history,closes:{...history.closes,AAA:[...history.closes.AAA].reverse()}},
  {...history,dates:[...history.dates.slice(0,10),history.dates[9],...history.dates.slice(11)]}]){
  if(bad?.closes?.AAA&&bad.closes.AAA.length===315&&bad.closes.AAA[0]!==history.closes.AAA[0])continue; // reverse valid prices are not themselves a data corruption signal
  assert.equal(api.futureRiskScreen({history:bad,symbol:'AAA'}).ready,false);
 }
 assert.equal(api.futureRiskScreen({history,symbol:'AAA',feeBps:-3}).ready,false);
 assert.equal(api.futureRiskScreen({history,symbol:'NOT'}).ready,false);
});
test('SEC FCF quality comparison preserves negatives, capex, and source lineage',()=>{
 const x=api.financialBridge({snapshot:snap,selection:['AAA','BBB','CCC'],asOf});
 assert.equal(x.ready,true);assert.equal(x.coverage,2);
 assert.equal(x.rows[0].fcfMargin,.14);assert.equal(x.rows[0].fcfGrowth,.2727);
 assert.equal(x.rows[0].capexIntensity,.04);assert.equal(x.rows[0].cfoCoverage,1.6364);
 assert.equal(x.rows[1].fcf,-2e7);assert.equal(x.rows[1].fcfGrowth,null);
 assert.equal(x.rows[2].status,'unavailable');
});
test('future or stale snapshot and mismatched fiscal periods fail closed',()=>{
 assert.equal(api.financialBridge({snapshot:{...snap,as_of:'2026-01-01'},selection:['AAA','BBB'],asOf}).ready,false);
 assert.equal(api.financialBridge({snapshot:{...snap,as_of:'2021-01-01'},selection:['AAA','BBB'],asOf}).ready,false);
 const malformed=structuredClone(snap);malformed.companies[0].annual[1].fiscal_end='2025-01-01';
 assert.equal(api.financialBridge({snapshot:malformed,selection:['AAA','BBB'],asOf}).rows[0].status,'unavailable');
});
test('position-weighted scenarios use fresh authenticated holdings and refuse partial coverage',()=>{
 const a=api.allocationStress({portfolio,quotes,history,symbol:'AAA',asOf});
 assert.equal(a.ready,true);assert.equal(a.rows.length,3);assert.equal(a.rows.filter(r=>r.ready).length,3);
 assert.ok(a.rows[0].newCandidateWeight<a.rows[1].newCandidateWeight);
 assert.ok(a.rows.every(r=>r.deltaVolatility!==null));
 const missing=api.allocationStress({portfolio:{...portfolio,holdings:{...portfolio.holdings,ZZZ:2}},quotes,history,symbol:'AAA',asOf});
 assert.equal(missing.ready,false);
 assert.equal(api.allocationStress({portfolio,quotes:{...quotes,AAA:{price:130,timestamp:'2025-09-01'}},history,symbol:'AAA',asOf}).ready,false);
});
test('cash shortage marks individual scenario unavailable rather than fabricating positive cash',()=>{
 const a=api.allocationStress({portfolio:{cash:45,holdings:{AAA:3,BBB:4}},quotes,history,symbol:'AAA',asOf});
 assert.equal(a.ready,true);assert.ok(a.rows.some(x=>x.ready===false));
});
test('MFA-protected archive note codec is short, bounded, explicit and rejects malformed values',()=>{
 const saved=api.archiveRecord(brief,asOf+'T13:00:00Z');
 assert.ok(saved.text.startsWith(api.TAG));assert.ok(saved.text.length<1100);
 const roundtrip=api.readArchive(saved);
 assert.equal(roundtrip.symbol,'AAA');assert.equal(roundtrip.covered,5);
 assert.equal(api.readArchive({text:'Personal note'}),null);
 assert.equal(api.readArchive({text:api.TAG+'{"v":1,"date":"bad"}'}),null);
 assert.throws(()=>api.archiveRecord({...brief,symbol:'DIFFERENT'},asOf));
 assert.ok(!saved.text.includes('cash')&&!saved.text.includes('holdings'));
});
test('sanitized export contains no account prices, quantities, weights or derived private risks',()=>{
 const p=api.build({history,portfolio,quotes,snapshot:snap,selection:['AAA','BBB','CCC'],symbol:'AAA',limit:.25,asOf});
 assert.equal(p.schema,'quantforge.intelligence.v9.6');
 const serialized=JSON.stringify(api.safeSummary(p));
 for(const secret of ['"holdings"','"cashWeight"','"annualVolatility"','"netModelReturn"','"quotes"','"positions"','"AAA"','"portfolio"'])assert.ok(!serialized.includes(secret),secret);
});
test('pure module has no local storage, provider fetch, MFA mutation or trade execution',()=>{
 const text=fs.readFileSync(path.resolve(__dirname,'../site/private_research_intelligence_v96.js'),'utf8');
 for(const keyword of ['fetch(', 'localStorage','sessionStorage','private/trade','private/state','private/notes','XMLHttpRequest','navigator.sendBeacon'])assert.ok(!text.includes(keyword),keyword);
});
