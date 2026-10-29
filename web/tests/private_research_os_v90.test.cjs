const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {assess}=require('../site/private_research_os_v90.js');
function fixture(){
 const symbol='MSFT';
 return {asOf:'2026-10-29T12:00:00Z',symbol,selection:[symbol,'SPY'],
  history:{symbols:[symbol,'SPY'],dates:['2026-01-02','2026-10-28']},
  quote:{symbol,price:400,timestamp:'2026-10-28T19:50:00Z'},
  portfolio:{cash:100000,holdings:{}},
  dossier:{ready:true,symbol,history:{observations:190,end:'2026-10-28'},
   fundamentals:{available:true,fiscalEnd:'2026-06-30',revenueGrowth:.12,operatingMargin:.34,freeCashFlowMargin:.22},
   valuation:{marketCapAvailable:true,pSales:8,fcfYield:.04},
   metrics:{maxDrawdown:-.16,dailyES95:.021},portfolioImpact:{currentWeight:0}},
  risk:'balanced',horizon:'long',maxWeight:.2,maxDrawdown:.25};
}
test('automatic assessment can conditionally consider rather than fabricate certainty',()=>{
 const x=assess(fixture());
 assert.equal(x.decision,'Consider a small position (conditional)');
 assert.equal(x.readiness,'required-inputs-valid');
 assert.equal(x.evidence.length,7);
 assert(!JSON.stringify(x).includes('100000'));
 assert(x.limitations.some(s=>/No virtual or live trade/.test(s)));
});
test('never recommends from missing candidate dossier',()=>{
 const x=fixture();x.dossier=null;
 assert.equal(assess(x).decision,'Insufficient evidence');
});
test('stale quote withholds recommendation regardless of other attractive metrics',()=>{
 const x=fixture();x.quote.timestamp='2026-10-10T12:00:00Z';
 assert.equal(assess(x).decision,'Insufficient evidence');
});
test('stale price history and changed selection invalidate previous results',()=>{
 const x=fixture();x.dossier.history.end='2026-10-01';
 assert.equal(assess(x).decision,'Insufficient evidence');
 const y=fixture();y.selection=['MSFT','NVDA'];
 assert.equal(assess(y).decision,'Insufficient evidence');
});
test('fresh but high drawdown triggers constraint-driven wait decision',()=>{
 const x=fixture();x.dossier.metrics.maxDrawdown=-.32;
 assert.equal(assess(x).decision,'Avoid adding for now');
 assert(assess(x).con.some(s=>/drawdown exceeded/.test(s)));
});
test('oversized existing position triggers review/reduce, not an order',()=>{
 const x=fixture();x.dossier.portfolioImpact.currentWeight=.36;x.portfolio.holdings.MSFT=70;
 assert.equal(assess(x).decision,'Review / consider reducing exposure');
});
test('negative cash generation can defeat the permissive case',()=>{
 const x=fixture();x.dossier.valuation.fcfYield=-.02;
 assert.equal(assess(x).decision,'Research further before adding');
});
test('change in policy materially changes decision',()=>{
 const x=fixture();x.maxDrawdown=.15;
 assert.equal(assess(x).decision,'Avoid adding for now');
});
test('missing valuation withholds an add signal',()=>{
 const x=fixture();x.dossier.valuation.marketCapAvailable=false;
 assert.equal(assess(x).decision,'Research further before adding');
});
test('portfolio walk-forward result described as multi-asset rather than single-name',()=>{
 const x=fixture();x.walkforward={symbols:['MSFT','SPY'],windows:[{},{}],start:'2026-01-02',end:'2026-10-28',optimized:{metrics:{change:.02}},benchmark:{metrics:{change:.1}}};
 const z=assess(x);
 assert(z.con.some(s=>/multi-asset allocation/.test(s)));
 assert(z.evidence.find(e=>e.key==='walkforward').detail.includes('not a single-company forecast'));
});
test('pure policy module has no API, storage, private trade, or hosted AI calls',()=>{
 const s=fs.readFileSync(path.join(__dirname,'../site/private_research_os_v90.js'),'utf8');
 for(const banned of ['fetch(', 'XMLHttpRequest', 'localStorage', 'sessionStorage', "api('private/trade'", 'placeOrder(', 'openai.com', 'alpaca.markets'])
  assert(!s.includes(banned),`unexpected ${banned}`);
 assert.deepEqual(assess(fixture()),assess(fixture()));
});
