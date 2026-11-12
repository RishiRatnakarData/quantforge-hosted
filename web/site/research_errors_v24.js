/* Safe API presentation. Provider responses and validation inputs are never echoed. */
(function(root){
'use strict';
const actionMessages=Object.freeze({'write_rejected':'The saved-account service rejected the update. Refresh before trying again; storage access may need checking.','provider_unavailable':'The data provider did not return a usable response. Check data access or connectivity, then try again.','account_changed': 'Your saved account changed. Refresh it, review activity and create a new preview.', 'quote_stale': 'The provider quote is too old for a virtual transaction. Wait for fresh market data and preview again.', 'quote_timestamp': 'The provider quote has an invalid observation time. No virtual transaction was recorded.', 'quote_missing': 'No usable positive provider quote is available. No virtual transaction was recorded.', 'quote_mismatch': 'The provider observation belongs to another investment. Select the intended investment and preview again.', 'quote_moved': 'The price moved more than 0.5% since preview. Review a fresh preview before confirming.', 'buy_budget': 'Use a virtual budget of at least $1, including fees, and no more than available cash.', 'sell_units': 'The sale exceeds the units you own. Check available units and preview again.', 'withdraw_cash': 'The withdrawal exceeds available virtual cash. Invested positions must be sold separately.', 'funding_amount': 'Enter between $1 and $1,000,000 in virtual funding.', 'funding_limit': 'This funding change exceeds the supported net-contribution range.', 'request_reused': 'This request identifier already belongs to another recorded action. Refresh and inspect activity.'});
function apiError(status,path='',code=''){
 if(![401,403,429].includes(status)&&!String(path).includes('auth/')&&Object.hasOwn(actionMessages,code))return actionMessages[code];
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
