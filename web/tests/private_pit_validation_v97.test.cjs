const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const api=require('../site/private_pit_validation_v97.js');
const dateAt=i=>new Date(Date.UTC(2024,0,1+i)).toISOString().slice(0,10);
const dates=Array.from({length:850},(_,i)=>dateAt(i));
const prices=(k,m)=>dates.map((_,i)=>k*Math.exp(.00025*i+.006*Math.sin(i*.11)*m));
const history={dates,symbols:['AAA','BBB'],closes:{AAA:prices(90,1),BBB:prices(80,.7)}};
const src=(field,filed,accn)=>({filed,accession:accn,tag:field});
const report=(end,filed,rev,ocf,capex,accn)=>({fiscal_end:end,metrics:{revenue_usd:rev,operating_cash_flow_usd:ocf,capex_usd:capex,free_cash_flow_usd:ocf-capex},sources:{revenue_usd:src('Revenues',filed,accn),operating_cash_flow_usd:src('NetCashProvidedByUsedInOperatingActivities',filed,accn),capex_usd:src('PaymentsToAcquirePropertyPlantAndEquipment',filed,accn)}});
const issuer={symbol:'AAA',annual:[
 report('2025-12-31','2026-03-04',1400,180,50,'0000000001-26-000001'),
 report('2024-12-31','2025-03-04',1250,160,45,'0000000001-25-000001'),
 report('2023-12-31','2024-03-04',1100,140,40,'0000000001-24-000001'),
]};
const snap={as_of:'2026-04-29',companies:[issuer]};
const input={snapshot:snap,history,candidate:'AAA',selection:['AAA','BBB'],train:126,step:21,maxDrawdown:.5};
test('SEC annual data is inaccessible before actual filing date, not fiscal period end',()=>{
 const a=api.auditOne(issuer,'2025-02-28');
 const b=api.auditOne(issuer,'2025-03-05');
 assert.equal(a.ready,false);assert.equal(b.ready,true);
 assert.equal(b.period,'2024-12-31');
 assert.equal(b.revenueGrowth,Number((1250/1100-1).toFixed(5)));
});
test('future restatement is excluded rather than reinterpreted as old information',()=>{
 const restated=structuredClone(issuer);
 restated.annual[1].sources.revenue_usd.filed='2026-01-01';
 assert.equal(api.auditOne(restated,'2025-06-01').ready,false);
 assert.equal(api.auditOne(restated,'2026-02-01').ready,true);
});
test('all contributing metrics have dated accessions and cashflow arithmetic',()=>{
 for(const modified of [
  c=>{delete c.annual[1].sources.capex_usd;},
  c=>{c.annual[1].sources.capex_usd.accession='bad';},
  c=>{c.annual[1].metrics.free_cash_flow_usd+=999;},
  c=>{c.annual[1].sources.revenue_usd.filed='2027-10-01';},
 ]){
  const c=structuredClone(issuer);modified(c);
  assert.equal(api.auditOne(c,'2025-04-01').ready,false);
 }
});
test('two full eligible fiscal periods are needed for comparison',()=>{
 const c=structuredClone(issuer);c.annual=c.annual.slice(0,1);
 assert.equal(api.auditOne(c,'2026-04-01').ready,false);
});
test('coverage reports withheld windows and does NOT publish partial performance',()=>{
 const x=api.replay(input);
 assert.equal(x.ready,false);assert.ok(x.counts.planned>x.counts.eligible);
 assert.equal(x.summary,null);assert.ok(x.windows.every(w=>w.latestFiled<=w.decisionDate));
});
test('complete disclosure-covered period produces comparable net rule and passive results',()=>{
 const d=dates.filter(s=>s>='2025-04-01'&&s<='2026-03-31');
 const first=dates.indexOf(d[0]);
 const h={dates:d,symbols:['AAA','BBB'],closes:{AAA:history.closes.AAA.slice(first,first+d.length),BBB:history.closes.BBB.slice(first,first+d.length)}};
 const x=api.replay({...input,history:h});
 assert.equal(x.ready,true,x.reason);assert.equal(x.counts.withheld,0);
 assert.equal(x.counts.eligible,x.counts.planned);assert.ok(x.summary.netRuleReturn!==null);
 assert.ok(x.windows.every(w=>w.decisionDate<w.executionDate&&w.executionDate<=w.testThrough&&w.latestFiled<=w.decisionDate));
});
test('future price mutation never changes earlier model gate decision',()=>{
 const d=dates.filter(s=>s>='2025-04-01'&&s<='2026-03-31');const first=dates.indexOf(d[0]);
 const h={dates:d,symbols:['AAA','BBB'],closes:{AAA:history.closes.AAA.slice(first,first+d.length),BBB:history.closes.BBB.slice(first,first+d.length)}};
 const a=api.replay({...input,history:h});const changed=structuredClone(h);changed.closes.AAA[146]*=.71;
 const b=api.replay({...input,history:changed});
 assert.equal(a.ready,true);assert.equal(b.ready,true);
 assert.equal(a.windows[0].exposure,b.windows[0].exposure);
 assert.notEqual(a.windows[0].observedTestReturn,b.windows[0].observedTestReturn);
});
test('fees cannot improve an always-invested model',()=>{
 const d=dates.filter(s=>s>='2025-04-01'&&s<='2026-03-31');const first=dates.indexOf(d[0]);
 const h={dates:d,symbols:['AAA','BBB'],closes:{AAA:history.closes.AAA.slice(first,first+d.length),BBB:history.closes.BBB.slice(first,first+d.length)}};
 const a=api.replay({...input,history:h,feeBps:0});const b=api.replay({...input,history:h,feeBps:80});
 assert.ok(a.ready&&b.ready);assert.ok(a.summary.netRuleReturn>=b.summary.netRuleReturn-1e-7);
});
test('price data must be current, aligned, unique, positive and match selection',()=>{
 for(const bad of [
  {...history,dates:[...history.dates.slice(0,15),history.dates[14],...history.dates.slice(16)]},
  {...history,closes:{AAA:history.closes.AAA.slice(1),BBB:history.closes.BBB}},
  {...history,symbols:['AAA','AAA']},
 ])assert.equal(api.replay({...input,history:bad}).ready,false);
 assert.equal(api.replay({...input,selection:['AAA','CCC']}).ready,false);
 assert.equal(api.replay({...input,maxDrawdown:-.1}).ready,false);
});
test('SEC snapshot cutoff must cover the evaluated period',()=>{
 assert.equal(api.replay({...input,snapshot:{...snap,as_of:'2025-01-01'}}).ready,false);
});
test('summary exports do not carry price histories, MFA, holdings, trade requests, or source accessions',()=>{
 const output=JSON.stringify(api.safeSummary(api.replay(input)));
 for(const secret of ['closes','holdings','account','accession','sourceAccessions','portfolio','quotes','password','apiKey','observedTestReturn'])assert.ok(!output.includes(secret),secret);
});
test('engine is pure and cannot fetch, trade, save notes, or mutate login state',()=>{
 const source=fs.readFileSync(path.resolve(__dirname,'../site/private_pit_validation_v97.js'),'utf8');
 for(const verb of ['fetch(', 'localStorage','sessionStorage','private/notes','private/trade','XMLHttpRequest','navigator.sendBeacon','WebSocket('])assert.ok(!source.includes(verb),verb);
});
