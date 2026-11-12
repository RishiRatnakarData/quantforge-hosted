/* Guided research primitives. No network, storage, recommendations or DOM. */
(function(root){
'use strict';
const finite=Number.isFinite;
const prompts=[['interest','Why am I interested?'],['evidence','What evidence supports the idea?'],['concerns','What are my main concerns?'],['assumptions','Which assumptions matter most?'],['change','What would change my view?'],['unknowns','What information do I still need?']];
const prefix='QFTHESIS1|';
function encode(fields,meta={}){
 const data={v:1,id:String(meta.id||'').slice(0,70),revision:Number.isInteger(meta.revision)&&meta.revision>0?meta.revision:1,parent:String(meta.parent||'').slice(0,40),period:String(meta.period||'').slice(0,10),snapshot:String(meta.snapshot||'').slice(0,10),review:String(fields.review||'').slice(0,10)};
 data.observed=Object.fromEntries(['revenue_usd','operating_margin','free_cash_flow_usd'].map(k=>[k,finite(meta.observed?.[k])?meta.observed[k]:null]));
 for(const [key] of prompts){data[key]=String(fields[key]||'').trim();if(data[key].length>220)throw Error('Keep each thesis response within 220 characters.');}
 if(!prompts.some(([key])=>data[key]))throw Error('Write at least one research observation or question.');
 if(data.review&&(!/^\d{4}-\d{2}-\d{2}$/.test(data.review)||Number.isNaN(Date.parse(data.review+'T00:00:00Z'))||new Date(data.review+'T00:00:00Z').toISOString().slice(0,10)!==data.review))throw Error('Use a calendar date for review.');
 const text=prefix+JSON.stringify(data);if(text.length>2000)throw Error('Keep this thesis within the 2,000-character saved-record limit.');return text;
}
function decode(text){if(typeof text!=='string'||!text.startsWith(prefix))return null;try{const d=JSON.parse(text.slice(prefix.length));if(d.v!==1||!Number.isInteger(d.revision)||d.revision<1||typeof d.id!=='string'||prompts.some(([key])=>typeof d[key]!=='string'))return null;return d;}catch(_){return null;}}
function describe(d){return 'Your investment thesis · revision '+d.revision+'\n'+prompts.filter(([k])=>d[k]).map(([k,label])=>label+' '+d[k]).join('\n')+(d.review?'\nReview on '+d.review:'')+'\nEvidence period '+(d.period||'unavailable')+' · snapshot '+(d.snapshot||'unavailable')+'. User-written beliefs; not calculated findings.';}
function health(row){
 const m=row?.metrics||{},sources=row?.sources||{};
 const ratio=(a,b)=>finite(m[a])&&finite(m[b])&&m[b]>0&&sources[a]?.accession&&sources[a].accession===sources[b]?.accession?m[a]/m[b]:null;
 const current=ratio('current_assets_usd','current_liabilities_usd'),leverage=ratio('liabilities_usd','assets_usd');
 const debt=finite(m.long_term_debt_current_usd)&&finite(m.long_term_debt_noncurrent_usd)&&sources.long_term_debt_current_usd?.accession===sources.long_term_debt_noncurrent_usd?.accession&&sources.long_term_debt_current_usd?.accession?m.long_term_debt_current_usd+m.long_term_debt_noncurrent_usd:null;
 return {current_ratio:current,liabilities_to_assets:leverage,long_term_debt_components:debt};
}
function concentration(holdings,cash,quotes){
 if(!finite(cash)||cash<0)return null;
 const positions=Object.entries(holdings||{}).filter(([,u])=>finite(u)&&u>0);
 if(positions.some(([s])=>!finite(quotes?.[s])||quotes[s]<=0))return null;
 const values=positions.map(([symbol,u])=>({symbol,value:u*quotes[symbol]})),total=cash+values.reduce((a,b)=>a+b.value,0);if(total<=0)return null;
 return {total,cash_weight:cash/total,largest:values.sort((a,b)=>b.value-a.value)[0]||null,hhi:values.reduce((a,b)=>a+(b.value/total)**2,0)+(cash/total)**2,positions:values.length};
}
root.QFResearchGuide30=Object.freeze({prompts,encode,decode,describe,health,concentration});
if(typeof module==='object'&&module.exports)module.exports=root.QFResearchGuide30;
})(typeof window!=='undefined'?window:globalThis);
