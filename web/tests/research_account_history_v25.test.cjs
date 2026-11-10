const {test}=require('node:test');
const assert=require('node:assert/strict');
const {summarize}=require('../site/research_account_history_v25.js');
const p=(at,value,capital)=>({at,value,cash:100,net_contributions:capital,pnl:value-capital});
test('deposits and withdrawals cannot masquerade as account profit',()=>{
 const r=summarize([p('2026-10-01',1000,1000),p('2026-10-02',1600,1500),p('2026-10-03',1300,1200)]);
 assert.equal(r.value_change,300);assert.equal(r.capital_change,200);assert.equal(r.pnl_change,100);
 assert.equal('return' in r,false);
});
test('marks must be chronological, finite and reconcile value less contributions',()=>{
 for(const rows of [[p('2026-10-02',100,100),p('2026-10-01',100,100)],[p('bad',100,100)],[{...p('2026-10-01',100,100),pnl:50}],[p('2026-10-01',Infinity,100)]])assert.throws(()=>summarize(rows));
 assert.equal(summarize([]).count,0);
});
