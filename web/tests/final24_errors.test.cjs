const test=require('node:test'),assert=require('node:assert/strict');
const E=require('../site/research_errors_v24.js');
test('actionable error codes are allowlisted; provider detail objects are never rendered',()=>{
 assert.match(E.apiError(422,'private/trade-preview','quote_stale'),/too old/);
 assert.match(E.apiError(422,'private/capital-preview','withdraw_cash'),/exceeds available/);
 assert.match(E.apiError(409,'private/trade','account_changed'),/new preview/);
 assert.doesNotMatch(E.apiError(422,'private/trade',{detail:'secret-input'}),/secret-input|object Object/);
 assert.doesNotMatch(E.apiError(422,'auth/login','quote_stale'),/too old/);
 assert.doesNotMatch(E.apiError(422,'private/trade','<script>private-data</script>'),/private-data/);
});
