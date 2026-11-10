/* Account marks are observations, not a replay of current holdings or a return forecast. */
(function(root){
'use strict';
function summarize(records){
 if(!Array.isArray(records)||records.length>365)throw Error('Invalid valuation history.');
 let last='';
 const points=records.map(p=>{
  if(!p||typeof p.at!=='string'||!Number.isFinite(Date.parse(p.at))||p.at<=last||!['value','cash','net_contributions','pnl'].every(k=>typeof p[k]==='number'&&Number.isFinite(p[k]))||p.value<0||p.cash<0||p.net_contributions<0||Math.abs(p.pnl-(p.value-p.net_contributions))>.011)throw Error('Valuation marks are incomplete or inconsistent.');
  last=p.at;return {at:p.at,value:p.value,cash:p.cash,net_contributions:p.net_contributions,pnl:p.pnl};
 });
 const first=points[0],end=points.at(-1);
 return {points,count:points.length,value_change:first?end.value-first.value:null,capital_change:first?end.net_contributions-first.net_contributions:null,pnl_change:first?(end.value-first.value)-(end.net_contributions-first.net_contributions):null};
}
const api=Object.freeze({summarize});if(typeof module==='object'&&module.exports)module.exports=api;root.QFAccountHistory25=api;
})(typeof window!=='undefined'?window:globalThis);
