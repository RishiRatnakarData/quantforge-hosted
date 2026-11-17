"use strict";
const test=require('node:test'),assert=require('node:assert/strict');
const B=require('../site/research_compare_portfolio_v21.js');
test('marked P&L separates realized, unrealized and contributions; legacy basis stays unknown',()=>{
 const now='2026-11-16T15:00:00Z',quotes=[{symbol:'CASE',price:120,timestamp:now,synthetic:false}];
 const p={cash:900,initial_cash:1000,holdings:{CASE:1},basis_accounting:{version:1,positions:{CASE:{units:1,total_basis:101}},realized_pnl:1,realized_complete:true}};
 const r=B.ownerSnapshot(p,quotes,now);assert.equal(r.cumulative_paper_pnl,20);assert.equal(r.unrealized_pnl,19);assert.equal(r.realized_pnl,1);
 delete p.basis_accounting;const legacy=B.ownerSnapshot(p,quotes,now);assert.equal(legacy.unrealized_pnl,null);assert.equal(legacy.realized_pnl,null);assert.equal(legacy.cumulative_paper_pnl,20);
});
