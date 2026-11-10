/* Safe API presentation. Provider responses and validation inputs are never echoed. */
(function(root){
'use strict';
function apiError(status,path=''){
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
