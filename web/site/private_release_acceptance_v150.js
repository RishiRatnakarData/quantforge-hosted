/* V15.0: user-attested release acceptance, with no account or market data. */
(function(root){
'use strict';
const KEYS=Object.freeze(['mfa','provider','research','sec','briefing','archive']);
const LABELS=Object.freeze({
 mfa:'Fresh sign-in and authenticator challenge',
 provider:'Authorized virtual holdings and live provider quotes',
 research:'Selected company prices and current full assessment',
 sec:'Local SEC archive import and withheld-date review',
 briefing:'Research Hub, Lab and Briefing evidence consistency',
 archive:'Saved research persistence, deletion and signed-out privacy'
});
const ALLOWED=Object.freeze(['not-tested','passed','failed']);
function normalize(value){
 const src=value&&typeof value==='object'&&!Array.isArray(value)?value:{};
 const checks={};for(const key of KEYS){
  const state=src[key];checks[key]=ALLOWED.includes(state)?state:'not-tested';
 }
 return Object.freeze(checks);
}
function assess(value){
 const checks=normalize(value);const counts={passed:0,failed:0,notTested:0};
 for(const key of KEYS){if(checks[key]==='passed')counts.passed++;
  else if(checks[key]==='failed')counts.failed++;else counts.notTested++;}
 const status=counts.failed?'attention-required':counts.notTested?'not-fully-tested':'self-attested-complete';
 return Object.freeze({schema:'quantforge.manual-acceptance.v15.0',status,counts,checks,
  independentlyVerified:false,
  limitation:'Owner-reported browser checks, not independent MFA or provider verification. No investment-performance claims.'});
}
function update(value,key,state){
 if(!KEYS.includes(key)||!ALLOWED.includes(state))throw Error('Unknown acceptance check or status.');
 return normalize({...normalize(value),[key]:state});
}
function exportSafe(value){
 const result=assess(value);
 return {schema:result.schema,status:result.status,counts:{...result.counts},checks:{...result.checks},
  independentlyVerified:false,limitation:result.limitation};
}
const api=Object.freeze({keys:KEYS,labels:LABELS,assess,update,exportSafe});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateReleaseAcceptanceV150=api;
})(typeof window!=='undefined'?window:globalThis);
