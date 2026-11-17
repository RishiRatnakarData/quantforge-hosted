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
function decisionSummary({financial,observed=false,risk=null,prediction=null,held=false,preferences={},healthRow=null,valuation=null,portfolioImpact=null,overlap=[],asOf=new Date().toISOString()}={}){
 const m=financial?.metrics||{},favorable=[],concerns=[],conflicts=[],coverage=[];
 const pct=x=>(100*x).toFixed(1)+'%';
 const age=date=>{const a=Date.parse(date),b=Date.parse(asOf);return finite(a)&&finite(b)&&b>=a?(b-a)/86400000:null;};
 const period=financial?.source?.period,financialAge=age(period),financialCurrent=financialAge!==null&&financialAge<=550;
 if(finite(m.revenue_growth))(m.revenue_growth>=0?favorable:concerns).push('Reported annual revenue '+(m.revenue_growth>=0?'grew ':'fell ')+pct(Math.abs(m.revenue_growth))+'.');
 if(finite(m.operating_margin))(m.operating_margin>0?favorable:concerns).push('Operating margin was '+pct(m.operating_margin)+' — operating income per dollar of sales.');
 if(finite(m.free_cash_flow_usd))(m.free_cash_flow_usd>0?favorable:concerns).push('The annual operating-cash-flow-minus-capex proxy was '+(m.free_cash_flow_usd>0?'positive':'non-positive')+'.');
 const missing=['revenue_growth','operating_margin','free_cash_flow_usd'].filter(k=>!finite(m[k]));
 if(missing.length)concerns.push('Financial comparisons are incomplete ('+missing.length+' key measures unavailable); absent data is not zero.');
 if(!financialCurrent)concerns.push(financialAge===null?'The financial period is unavailable or invalid; these figures cannot establish a current assessment.':'The financial period is '+Math.floor(financialAge)+' days old. The 550-day review policy withholds a current financial conclusion; inspect newer filings.');
 coverage.push({domain:'Company financials',status:!missing.length&&financialCurrent?'covered':'incomplete',detail:period?'Fiscal end '+period:'No valid financial period'});
 const compatibleHealth=healthRow?.fiscal_end===period&&financialCurrent;
 const balance=compatibleHealth?health(healthRow):health(null);
 const negativeEquity=compatibleHealth&&finite(healthRow?.metrics?.equity_usd)&&healthRow.metrics.equity_usd<0;
 if(negativeEquity)concerns.push('Reported stockholders’ equity is negative. Investigate accumulated losses, buybacks and financing; negative equity alone does not establish insolvency.');
 if(balance.current_ratio!==null)concerns.push('Same-filing current assets / current liabilities: '+balance.current_ratio.toFixed(2)+'×. '+(balance.current_ratio<1?'Current liabilities exceed current assets; inspect liquidity and maturities.':'This accounting coverage does not establish readily available cash.'));
 if(balance.liabilities_to_assets!==null)concerns.push('Reported liabilities / assets: '+pct(balance.liabilities_to_assets)+'. Liabilities include more than borrowing; this is not a debt-only ratio.');
 coverage.push({domain:'Financial health',status:compatibleHealth&&(balance.current_ratio!==null||balance.liabilities_to_assets!==null||negativeEquity)?'covered':'incomplete',detail:compatibleHealth?'Same fiscal end; compatible accessions required for ratios':'No matching covered balance-sheet period'});
 const marketRisk=observed&&risk&&finite(risk.max_drawdown)&&risk.max_drawdown<=0&&risk.max_drawdown>=-1;
 const marketAge=marketRisk?age(risk.last):null,marketCurrent=marketAge!==null&&marketAge<=7;
 if(!marketRisk)concerns.push('Eligible observed market risk is unavailable. Public simulations do not describe this investment.');
 if(marketRisk)concerns.push('Largest observed peak-to-trough decline: '+pct(Math.abs(risk.max_drawdown))+'. Future loss can be larger.');
 if(marketRisk&&!marketCurrent)concerns.push('The historical market sample is not verified within the seven-day research review policy. It remains historical evidence, not current trading data.');
 coverage.push({domain:'Observed market risk',status:marketRisk&&marketCurrent?'covered':'incomplete',detail:marketRisk?(risk.first||'Start unavailable')+' to '+(risk.last||'end unavailable'):'Observed history missing'});
 const boundary=Number(preferences.drawdown),elevated=marketRisk&&[.15,.30,.50].includes(boundary)&&Math.abs(risk.max_drawdown)>boundary;
 const validPrediction=observed&&prediction?.ready&&['evaluatedAccuracy','baselineAccuracy','evaluatedBrier','baselineBrier'].every(k=>finite(prediction[k])&&prediction[k]>=0&&prediction[k]<=1)&&Number.isInteger(prediction.testWindows)&&prediction.testWindows>0;
 const supported=validPrediction&&prediction.qualified===true&&prediction.testWindows>=12&&prediction.evaluatedAccuracy>=prediction.baselineAccuracy&&prediction.evaluatedBrier<prediction.baselineBrier-.005;
 const model=validPrediction?'Five-session direction: held-out accuracy '+pct(prediction.evaluatedAccuracy)+' versus '+pct(prediction.baselineAccuracy)+' baseline; Brier error '+prediction.evaluatedBrier.toFixed(3)+' versus '+prediction.baselineBrier.toFixed(3)+' over '+prediction.testWindows+' later windows. '+(supported?'Exploratory screen passed; profitability and future reliability remain unproven.':'Signal withheld: this evaluation does not support using it as a decision signal.'):'No validated company-specific predictive evidence is available here. Inspect Prediction Evaluation before using a model; probability, a scenario and expected return are different quantities.';
 if(validPrediction&&prediction.evaluatedAccuracy>=prediction.baselineAccuracy&&prediction.evaluatedBrier>=prediction.baselineBrier)conflicts.push('Directional accuracy matches or exceeds the baseline, but probability error does not improve. Accuracy alone does not justify a predictive signal.');
 const financialCaution=(finite(m.revenue_growth)&&m.revenue_growth<0)||(finite(m.operating_margin)&&m.operating_margin<=0)||(finite(m.free_cash_flow_usd)&&m.free_cash_flow_usd<=0)||negativeEquity;
 if(marketRisk&&finite(risk.change)&&risk.change>0&&financialCaution)conflicts.push('Prices rose over the loaded window while reported business evidence has cautions. Historical price strength does not resolve weak cash generation or financial health.');
 if(supported&&financialCaution)conflicts.push('The short-horizon model passed its exploratory screen while financial cautions remain. These methods address different horizons; the classifier does not establish business quality.');
 if(favorable.length&&elevated)conflicts.push('Favorable operating evidence coexists with losses beyond your review boundary. A profitable business can still expose a concentrated position to substantial downside.');
 const validValue=observed&&valuation?.valid===true&&valuation.symbol===financial?.symbol&&finite(valuation.marketCap)&&valuation.marketCap>0&&valuation.fiscalEnd===period&&age(valuation.priceTime)!==null&&age(valuation.priceTime)<=7&&age(valuation.sharesTime)!==null&&age(valuation.sharesTime)<=550&&financialCurrent;
 let valueText='Observed-price valuation is incomplete. A cash-flow-proxy DCF is an assumption-driven scenario, not an equity value or fair share price. Profitability alone cannot establish an attractive purchase price.';
 if(validValue){
  valueText='Approximate market capitalization uses a dated price and reported common shares. '+(finite(valuation.pFcf)&&valuation.pFcf>0?'Price / annual cash-flow proxy: '+valuation.pFcf.toFixed(1)+'×. ':'A positive price / cash-flow multiple is unavailable. ')+(finite(valuation.fcfYield)?'Annual cash-flow-proxy yield: '+pct(valuation.fcfYield)+'. ':'')+'This yield is not a dividend or expected return; inspect growth, reinvestment and comparable peers before judging price.';
  if(favorable.length)conflicts.push('Positive operating results do not establish attractive valuation. The observed-price ratios and forward assumptions require a separate price case.');
 }
 coverage.push({domain:'Observed-price valuation',status:validValue?'covered':'incomplete',detail:validValue?'Price '+valuation.priceTime+'; shares '+valuation.sharesTime:'No complete, matching price/shares/financial bridge'});
 const weight=portfolioImpact?.currentWeight,portfolioCovered=finite(weight)&&weight>=0&&weight<=1;
 const related=observed&&Array.isArray(overlap)?overlap.filter(x=>typeof x.symbol==='string'&&finite(x.correlation)&&x.correlation>=-1&&x.correlation<=1&&Number.isInteger(x.observations)&&x.observations>=60):[];
 let context=(held?'Already held in your virtual portfolio: adding could increase single-company concentration. ':'Not identified as an existing virtual holding; this does not establish diversification. ');
 context+=portfolioCovered?'Current marked single-name weight: '+pct(weight)+'. An assumed 20% isolated position loss would change account value by '+pct(-.2*weight)+' before correlated moves, fees or taxes. ':'A complete recent quote mark is missing; current portfolio weights and incremental risk are withheld. ';
 if(related.length)context+='Loaded held-position correlations: '+related.map(x=>x.symbol+' '+x.correlation.toFixed(2)+' over '+x.observations+' common-date returns').join('; ')+'. This is the covered subset, not complete fund look-through or future diversification. ';
 if(related.some(x=>x.correlation>=.8))conflicts.push('At least one loaded holding has historical correlation of 0.80 or more. The 0.80 review flag is a disclosed heuristic, not a validated suitability threshold; another ticker need not add diversification.');
 context+=(elevated?'The sampled drawdown exceeded your chosen review boundary. ':'A review boundary is a reflection prompt, not a forecast or suitability assessment. ')+(preferences.horizon==='long'?'A multi-year horizon still requires updated filings and liquidity planning.':preferences.horizon==='short'?'Short-term objectives need particular attention to liquidity and drawdown.':'Choose an optional horizon to frame the next questions.');
 coverage.push({domain:'Virtual portfolio exposure',status:portfolioCovered?'covered':'incomplete',detail:portfolioCovered?'Marked exposure; correlation covers loaded holdings only':'Incomplete or missing recent marks'});
 const complete=coverage.every(x=>x.status==='covered');
 const disposition=elevated?'Historical loss exceeded your review boundary':!complete?'Current evidence is incomplete':conflicts.length?'Resolve the conflicting evidence before forming a thesis':'Evidence supports a structured research review';
 return {disposition,favorable,concerns,conflicts,coverage,model,valuation:valueText,context,
  conclusion:complete?'The covered inputs support reviewing a thesis, not an automatic investment decision. '+(conflicts.length?'Resolve the stated conflicts and stress-test assumptions first.':'A price case, current disclosures and human judgment remain necessary.'):'A defensible overall investment assessment is withheld. Missing evidence: '+coverage.filter(x=>x.status!=='covered').map(x=>x.domain.toLowerCase()).join(', ')+'. Available historical facts remain inspectable.',
  next:'Read current official filings, compare compatible peers, review the observed-price ratios and stress-test valuation assumptions. For a fund, inspect holdings, fees and concentration disclosures; issuer-style ratios do not describe a diversified fund.',
  invalidation:'Revisit the thesis when filings change, cash generation weakens, model error loses its baseline advantage, or exposure/correlation changes. Review dates and these conditions are monitoring prompts, not scheduled alerts or automatic trade rules.'};
}

root.QFResearchGuide30=Object.freeze({prompts,encode,decode,describe,health,concentration,decisionSummary});
if(typeof module==='object'&&module.exports)module.exports=root.QFResearchGuide30;
})(typeof window!=='undefined'?window:globalThis);
