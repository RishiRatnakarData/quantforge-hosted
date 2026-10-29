const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const v92=require('../site/private_decision_review_v92.js');
function input(){
 const dates=Array.from({length:90},(_,i)=>new Date(Date.UTC(2026,0,i+1)).toISOString().slice(0,10));
 const history={symbols:['MSFT','SPY'],dates,source:'Dated observed prices',closes:{
  MSFT:dates.map((_,i)=>100+i),SPY:dates.map((_,i)=>200-i*.25)}};
 const assessment={decision:'Consider a small position (conditional)',readiness:'required-inputs-valid',
  policy:'explicit-screens.v1',asOf:'2026-04-01T12:00:00Z',symbol:'MSFT',reason:'Screening checks passed.',
  constraints:{risk:'balanced',horizon:'long',maxWeight:.2,maxDrawdown:.25},summary:'Research completed.',
  evidence:[{key:'history',state:'available',detail:'90 observations',source:'prices'},
   {key:'fundamentals',state:'supports',detail:'positive',source:'SEC'},
   {key:'valuation',state:'supports',detail:'multiple',source:'quote'},
   {key:'downside',state:'mixed',detail:'historical',source:'prices'},
   {key:'portfolio',state:'supports',detail:'below limit',source:'virtual'},
   {key:'walkforward',state:'unavailable',detail:'not run',source:'portfolio'},
   {key:'factors',state:'unavailable',detail:'not imported',source:'FF3'}],
  pro:['Reported margin is positive.'],con:[],gaps:[],steps:[],limitations:['No guarantee.'],
  orchestration:{completed:5,failed:0,unavailable:3,total:8,models:[{required:true,status:'completed'}]}};
 return {history,selection:['MSFT','SPY'],assessment};
}
test('identical dated market histories compare price-only change and drawdown without ranked buy claims',()=>{
 const x=input();const c=v92.historicalComparison(x.history,x.selection);
 assert.equal(c.ready,true);assert.equal(c.rows.length,2);assert.equal(c.rows[0].maxDrawdown,0);
 assert(c.rows[1].maxDrawdown<0);assert(c.rows[0].totalChange>0);
 assert(!JSON.stringify(c).includes('probability'));assert(!JSON.stringify(c).includes('best stock'));
 assert.equal(c.period.observations,90);
});
test('invalid, mismatched, missing, duplicate and unordered histories fail closed',()=>{
 const x=input();x.history.closes.SPY[2]=NaN;assert.equal(v92.historicalComparison(x.history,x.selection).ready,false);
 const y=input();y.history.dates[4]=y.history.dates[3];assert.equal(v92.historicalComparison(y.history,y.selection).ready,false);
 const z=input();z.selection=['MSFT','NVDA'];assert.equal(v92.historicalComparison(z.history,z.selection).ready,false);
 const d=input();d.history.closes.MSFT[3]=0;assert.equal(v92.historicalComparison(d.history,d.selection).ready,false);
 const e=input();e.selection=['MSFT','MSFT'];assert.equal(v92.historicalComparison(e.history,e.selection).ready,false);
});
test('incomplete required model blocks an otherwise positive assessment',()=>{
 const x=input();x.assessment.orchestration.models=[{required:true,status:'failed'}];
 const r=v92.review(x.assessment,x.history,x.selection);
 assert.equal(r.action,'Insufficient evidence');assert.equal(r.blocked,true);
 assert(r.flags.some(v=>/Required model/.test(v)));
});
test('missing key evidence blocks positive assessment, optional factor absence does not',()=>{
 const x=input();let r=v92.review(x.assessment,x.history,x.selection);
 assert.equal(r.blocked,false);assert.equal(r.action,x.assessment.decision);
 x.assessment.evidence.find(e=>e.key==='downside').state='unavailable';
 r=v92.review(x.assessment,x.history,x.selection);
 assert.equal(r.blocked,true);assert.equal(r.action,'Insufficient evidence');
});
test('support and caution evidence appear as conflicts without invented confidence probabilities',()=>{
 const x=input();x.assessment.con=['Valuation may be extended.'];
 x.assessment.evidence.find(e=>e.key==='valuation').state='cautions';
 const r=v92.review(x.assessment,x.history,x.selection);
 assert(r.flags.some(f=>/coexist/.test(f)));
 assert.equal(r.dimensionConcerns,1);
 assert(!('confidenceScore' in r));
 assert(!('probability' in r));
});
test('missing optional research does not create mandatory blocker',()=>{
 const x=input();x.assessment.orchestration.failed=1;
 x.assessment.orchestration.models.push({required:false,status:'failed'});
 const r=v92.review(x.assessment,x.history,x.selection);
 assert.equal(r.blocked,false);assert(r.flags.some(f=>/failed/.test(f)));
});
test('does not serialize price vectors or cash/holdings into review',()=>{
 const x=input();x.assessment.cash=123456789;x.assessment.holdings={MSFT:5000};
 const result=v92.review(x.assessment,x.history,x.selection);
 assert(!JSON.stringify(result).includes('123456789'));
 assert(!JSON.stringify(result).includes('closes'));
 assert(!JSON.stringify(result).includes('holdings'));
 assert.deepEqual(x.selection,['MSFT','SPY']);
});
test('review cannot issue orders, touch storage, or make network calls',()=>{
 const s=fs.readFileSync(path.join(__dirname,'../site/private_decision_review_v92.js'),'utf8');
 for(const banned of ['fetch(', 'XMLHttpRequest', 'localStorage', 'sessionStorage','placeOrder(',"api('private/trade'",'alpaca.markets'])
  assert(!s.includes(banned),banned);
 const x=input();assert.deepEqual(v92.review(x.assessment,x.history,x.selection),v92.review(x.assessment,x.history,x.selection));
 assert.throws(()=>v92.review({},null,[]),/complete/);
});
