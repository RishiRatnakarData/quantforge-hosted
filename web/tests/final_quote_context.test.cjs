'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {apiError}=require('../site/research_errors_v24.js');
test('stale observations explain dates, age, source and unchanged limits without raw errors',()=>{
 const observation={observed_at:'2026-11-13T20:00:00Z',age_seconds:36000,max_age_seconds:900,source:'Controlled fixture',owner_token:'never display'};
 const text=apiError(422,'private/trade-preview','quote_stale',observation);
 assert.match(text,/2026-11-13 20:00:00 UTC/);assert.match(text,/10.0 hours/);
 assert.match(text,/Controlled fixture/);assert.match(text,/15-minute/);
 assert.doesNotMatch(text,/never display|object Object/);
 assert.match(apiError(422,'private/trade-preview','quote_stale',{...observation,max_age_seconds:300}),/5-minute/);
 assert.doesNotMatch(apiError(403,'private/trade-preview','quote_stale',observation),/Controlled fixture/);
 assert.doesNotMatch(apiError(422,'private/trade-preview','quote_stale',{...observation,age_seconds:NaN}),/NaN/);
});
