'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const ML=require('../site/private_predictive_ml_v180.js');
function samples(n=30){return Array.from({length:n},(_,i)=>({t:i*5,date:new Date(Date.UTC(2025,0,1+i*7)).toISOString().slice(0,10),y:i%2,prediction:i<n/2?i%2:1-i%2,baseline:.5}));}
test('frozen descriptive review catches a held-out Brier advantage that reverses recently',()=>{const r=ML.diagnostics(samples());assert.equal(r.state,'deteriorating');assert.equal(r.early.modelBrier,0);assert.equal(r.recent.modelBrier,1);assert.equal(r.early.baselineBrier,.25);assert.equal(r.recent.baselineBrier,.25);assert.equal(r.early.windows,15);assert.match(r.limitation,/Not a significance test/);});
test('small, overlapping and malformed held-out samples do not create deterioration evidence',()=>{assert.equal(ML.diagnostics(samples(20)).state,'insufficient');const x=samples();x[1].t=1;assert.equal(ML.diagnostics(x).state,'insufficient');x[1].t=5;x[1].prediction=NaN;assert.equal(ML.diagnostics(x).state,'insufficient');});
test('stable descriptive loss does not become a future accuracy claim',()=>{const x=samples().map(r=>({...r,prediction:r.y})),r=ML.diagnostics(x);assert.equal(r.state,'no-clear-deterioration');assert.match(r.interpretation,/does not establish future stability/);});
