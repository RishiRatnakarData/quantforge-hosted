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
function decisionSummary({financial,observed=false,risk=null,prediction=null,held=false,preferences={}}={}){
 const m=financial?.metrics||{},favorable=[],concerns=[];
 const pct=x=>(100*x).toFixed(1)+'%';
 if(finite(m.revenue_growth))(m.revenue_growth>=0?favorable:concerns).push('Reported annual revenue '+(m.revenue_growth>=0?'grew ':'fell ')+pct(Math.abs(m.revenue_growth))+'.');
 if(finite(m.operating_margin))(m.operating_margin>0?favorable:concerns).push('Operating margin was '+pct(m.operating_margin)+' — operating income per dollar of sales.');
 if(finite(m.free_cash_flow_usd))(m.free_cash_flow_usd>0?favorable:concerns).push('The latest annual cash-flow proxy was '+(m.free_cash_flow_usd>0?'positive':'non-positive')+' after reported PP&E purchases.');
 const missing=['revenue_growth','operating_margin','free_cash_flow_usd'].filter(k=>!finite(m[k]));
 if(missing.length)concerns.push('Financial comparisons are incomplete ('+missing.length+' key measures unavailable); absent data is not zero.');
 if(!observed||!risk)concerns.push('Eligible observed market risk is unavailable. Public simulations do not describe this investment.');
 const boundary=Number(preferences.drawdown);
 const elevated=observed&&risk&&finite(risk.max_drawdown)&&[0.15,0.30,0.50].includes(boundary)&&Math.abs(risk.max_drawdown)>boundary;
 if(observed&&risk)concerns.push('Largest observed peak-to-trough decline: '+pct(Math.abs(risk.max_drawdown))+'. Future loss can be larger.');
 const model=observed&&prediction?.ready?'Five-session direction: held-out accuracy '+pct(prediction.evaluatedAccuracy)+' versus '+pct(prediction.baselineAccuracy)+' baseline; Brier error '+prediction.evaluatedBrier.toFixed(3)+' versus '+prediction.baselineBrier.toFixed(3)+' over '+prediction.testWindows+' later windows. '+(prediction.qualified?'Exploratory screen passed; profitability and future reliability remain unproven.':'Signal withheld: this evaluation does not support using it as a decision signal.'):'No validated company-specific predictive evidence is available here. Inspect Prediction Evaluation before using a model; probability, a scenario and expected return are different quantities.';
 return {disposition:elevated?'Historical loss exceeded your review boundary':missing.length||!observed?'Current evidence is incomplete':'Further investigation required',favorable,concerns,model,
 context:(held?'Already held in your virtual portfolio: adding could increase single-company concentration. ':'Not identified as an existing virtual holding; this does not establish diversification. ')+(elevated?'The sampled drawdown exceeded your chosen review boundary; test allocation scenarios before revising your thesis. ':'A review boundary is a reflection prompt, not a forecast or suitability assessment. ')+(preferences.horizon==='long'?'A multi-year horizon still requires updated filings, valuation assumptions and liquidity planning.':preferences.horizon==='short'?'Short-term objectives can be sensitive to drawdown and liquidity; annual statements alone do not resolve them.':'Choose an optional horizon to frame the next questions.'),
 next:'Read the latest official Business and risk-factor disclosures, check whether newer filings exist, compare compatible peers and stress-test valuation assumptions. No supported fair-share-price conclusion is inferred from the cash-flow proxy.',
 invalidation:'Revisit your thesis if revenue or margins deteriorate, cash generation weakens, portfolio concentration rises, or updated out-of-sample model error loses its baseline advantage. These are questions to investigate, not automatic trade rules.'};
}
root.QFResearchGuide30=Object.freeze({prompts,encode,decode,describe,health,concentration,decisionSummary});
if(typeof module==='object'&&module.exports)module.exports=root.QFResearchGuide30;
})(typeof window!=='undefined'?window:globalThis);
