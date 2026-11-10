const {test}=require('node:test');
const assert=require('node:assert/strict');
const {apiError}=require('../site/research_errors_v24.js');
test('structured FastAPI and provider payloads cannot become visible objects or leaked inputs',()=>{
 for(const status of [400,401,403,409,422,429,500,503]){
  for(const payload of [{detail:{message:'secret'}},{detail:[{input:'secret',msg:'bad'}]},{error:{token:'secret'}}]){
   const text=apiError(status,'auth/login',payload);
   assert.equal(typeof text,'string');assert.ok(text.length>20);
   assert.doesNotMatch(text,/object Object|secret|token|HTTP/);
  }
 }
});
test('session, conflict and rate-limit errors have actionable distinct messages',()=>{
 assert.match(apiError(401,'private/state'),/session expired/);
 assert.match(apiError(409),/Refresh/);assert.match(apiError(429),/Wait/);
 assert.match(apiError(422,'auth/mfa/verify'),/six-digit/);
});
