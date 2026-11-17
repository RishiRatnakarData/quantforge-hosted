/* Safe API presentation. Provider responses and validation inputs are never echoed. */
(function(root){
'use strict';
const actionMessages=Object.freeze({'write_rejected':'The saved-account service rejected the update. Refresh before trying again; storage access may need checking.','provider_unavailable':'The data provider did not return a usable response. Check data access or connectivity, then try again.','account_changed': 'Your saved account changed. Refresh it, review activity and create a new preview.', 'quote_stale': 'The provider quote is too old for a virtual transaction. Wait for fresh market data and preview again.', 'quote_timestamp': 'The provider quote has an invalid observation time. No virtual transaction was recorded.', 'quote_missing': 'No usable positive provider quote is available. No virtual transaction was recorded.', 'quote_mismatch': 'The provider observation belongs to another investment. Select the intended investment and preview again.', 'quote_moved': 'The price moved more than 0.5% since preview. Review a fresh preview before confirming.', 'buy_budget': 'Use a virtual budget of at least $1, including fees, and no more than available cash.', 'sell_units': 'The sale exceeds the units you own. Check available units and preview again.', 'withdraw_cash': 'The withdrawal exceeds available virtual cash. Invested positions must be sold separately.', 'funding_amount': 'Enter between $1 and $1,000,000 in virtual funding.', 'funding_limit': 'This funding change exceeds the supported net-contribution range.', 'request_reused': 'This request identifier already belongs to another recorded action. Refresh and inspect activity.'});
function quoteContext(info){
 if(!info||typeof info!=='object')return '';
 const at=typeof info.observed_at==='string'?Date.parse(info.observed_at):NaN;
 const age=info.age_seconds,limit=info.max_age_seconds;
 if(!Number.isFinite(at)||!Number.isFinite(age)||age<0||![300,900].includes(limit))return '';
 const elapsed=age<3600?Math.floor(age/60)+' min':(age/3600).toFixed(1)+' hours';
 const source=typeof info.source==='string'?info.source.replace(/[<>\x00-\x1f]/g,'').slice(0,100):'Provider not specified';
 return ' Observation: '+new Date(at).toISOString().replace('T',' ').replace('.000Z',' UTC')+'; age '+elapsed+'; source '+source+'. The '+(limit/60)+'-minute freshness limit remains enforced. Closed markets can leave an older last trade; market hours alone do not guarantee a fresh observation.';
}
function apiError(status,path='',code='',observation=null){
 if(![401,403,429].includes(status)&&!String(path).includes('auth/')&&Object.hasOwn(actionMessages,code))return actionMessages[code]+(code==='quote_stale'?quoteContext(observation):'');
 const auth=String(path).includes('auth/');
 if(status===401)return auth?'Sign-in could not be verified. Check your details or authenticator code and try again.':'Your session expired. Sign in and verify your authenticator again.';
 if(status===403)return 'This action requires the authorized owner and authenticator verification.';
 if(status===422||status===400)return auth?'Check the email, password and six-digit authenticator code, then try again.':'Check the selected investment and input values, then try again.';
 if(status===409)return 'Your saved workspace changed. Refresh it before saving again.';
 if(status===429)return 'Too many requests. Wait a moment, then try again.';
 return 'The service is unavailable. Try again shortly; other research remains available.';
}
const api=Object.freeze({apiError});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFErrors24=api;
})(typeof window!=='undefined'?window:globalThis);
