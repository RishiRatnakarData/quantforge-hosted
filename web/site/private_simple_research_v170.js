/* Beginner-readable presentation of completed private research. No fetching, pricing, trading, or generated predictions. */
(function(root){
'use strict';
const safe=v=>String(v??'').slice(0,400).replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const isSymbol=v=>typeof v==='string'&&/^[A-Z0-9.\-]{1,15}$/.test(v);
function tone(item){
 if(item.failed)return 'gray';
 const d=String(item.decision||'').toLowerCase();
 if(d.includes('insufficient'))return 'gray';
 if(d.includes('avoid')||d.includes('reducing')||d.includes('hold / avoid'))return 'red';
 if(d.includes('consider a small position'))return 'green';
 return 'amber';
}
const title=Object.freeze({green:'Passes configured research screens',amber:'Mixed findings — research further',red:'Current risk limits caution against adding',gray:'Not enough reliable evidence'});
function prepare({rows,selected,comparison,asOf}={}){
 if(!Array.isArray(selected)||selected.length<2||selected.length>5||!selected.every(isSymbol)||new Set(selected).size!==selected.length||
  !Array.isArray(rows)||rows.length!==selected.length||!selected.every(s=>rows.some(r=>r.symbol===s))||rows.some(r=>!isSymbol(r.symbol)||!r.decision||!r.reason))
  return {ready:false,reason:'Choose two to five different companies and run complete research before viewing the comparison.'};
 const result=rows.map(r=>{
  const signal=tone(r),risk=(comparison?.rows||[]).find(a=>a.symbol===r.symbol);
  return {symbol:r.symbol,name:String(r.name||r.symbol).slice(0,90),signal,status:title[signal],
   decision:String(r.decision).slice(0,160),reason:String(r.reason).slice(0,320),
   support:(r.pro||[]).filter(x=>typeof x==='string').slice(0,2),
   concerns:(r.con||[]).filter(x=>typeof x==='string').slice(0,2),
   next:(r.steps||[]).filter(x=>typeof x==='string'&&!/import|archive|file/i.test(x)).slice(0,1),
   modelCompleted:finite(r.modelCompleted)?r.modelCompleted:null,
   modelTotal:finite(r.modelTotal)?r.modelTotal:null,
   priceChange:risk&&finite(risk.totalChange)?100*risk.totalChange:null,
   maxDrawdown:risk&&finite(risk.maxDrawdown)?100*risk.maxDrawdown:null};
 });
 // Only screen-compatible companies can be leading candidates; never rank blocked/incomplete as investment picks.
 const favorable=result.filter(r=>r.signal==='green');
 const priority=favorable.length===1?favorable[0].symbol:null;
 return {ready:true,rows:result,priority,selected:selected.slice(),asOf:String(asOf||'').slice(0,32),
  period:comparison?.ready?comparison.period:null};
}
function render(input){
 const data=prepare(input);
 if(!data.ready)return '<p class="qf-v170-empty">'+safe(data.reason)+'</p>';
 const badges={green:'Positive screen',amber:'Mixed evidence',red:'Risk limit',gray:'Limited evidence'};
 const count=data.rows.filter(r=>r.signal==='green').length;
 const head='<div class="qf-v170-head"><span class="eyebrow">ONE RESEARCH SESSION · '+safe(data.asOf||'DATE UNAVAILABLE')+'</span><h3>Here is what the research found</h3><p>We compared '+data.rows.length+' selected investments using available SEC facts, historical market prices, portfolio exposure and strategy tests. No purchases or orders were made.</p></div>'+
 '<div class="qf-v170-overview"><strong>'+(
  data.priority?safe(data.rows.find(r=>r.symbol===data.priority).name)+' has the clearest screen-compatible case in this selection.':
  count>1?count+' companies pass the configured screens; no single clear leader is established.':
  'No company has a clear green light under all current research constraints.')+'</strong><p>These are research checks, not a trained stock-return prediction or a recommendation to buy. Red means a selected risk rule was breached; grey means key information was unavailable.</p></div>';
 const cards=data.rows.map(r=>'<article class="qf-v170-company qf-v170-'+r.signal+'" data-symbol="'+safe(r.symbol)+'">'+
  '<div class="qf-v170-company-title"><h4>'+safe(r.name)+' <small>('+safe(r.symbol)+')</small></h4><span class="qf-v170-pill qf-v170-'+r.signal+'">'+badges[r.signal]+'</span></div>'+
  '<strong class="qf-v170-verdict">'+safe(r.status)+'</strong><p>'+safe(r.reason)+'</p>'+
  (r.support.length?'<p class="qf-v170-plain"><b>What helps:</b> '+safe(r.support[0])+'</p>':'')+
  (r.concerns.length?'<p class="qf-v170-plain"><b>What concerns us:</b> '+safe(r.concerns[0])+'</p>':'')+
  (r.next.length?'<p class="qf-v170-plain"><b>What to check next:</b> '+safe(r.next[0])+'</p>':'')+
  (r.modelTotal!==null?'<p class="tiny">Research models completed: '+r.modelCompleted+' / '+r.modelTotal+' (this measures coverage, not success odds)</p>':'')+
  '</article>').join('');
 const priced=data.rows.filter(r=>finite(r.maxDrawdown));
 const chart=priced.length?'<section class="qf-v170-chart"><h4>How much have these investments fallen in the past?</h4><p>Each bar shows the worst peak-to-trough fall in the shared observed period. A larger bar means a larger historical decline, not a predicted loss.</p>'+priced.map(r=>'<div class="qf-v170-bar-row"><span>'+safe(r.name)+'</span><div class="qf-v170-bar"><span style="width:'+Math.min(100,Math.abs(r.maxDrawdown)/60*100).toFixed(1)+'%"></span></div><strong>'+Math.abs(r.maxDrawdown).toFixed(1)+'%</strong></div>').join('')+'<p class="tiny">'+safe(data.period?.start)+' to '+safe(data.period?.end)+' · '+safe(data.period?.observations)+' matched sessions · price-only data, excluding dividends. Bars capped visually at 60%; labels show actual values.</p></section>':
 '<p class="qf-v170-empty">The companies do not yet have a complete shared price history for a valid comparison. No chart was invented.</p>';
 return '<div class="qf-v170-results">'+head+'<div class="qf-v170-cards">'+cards+'</div>'+chart+'<p class="qf-v170-footer">Need the underlying statistics, exact model settings or historical data limitations? Open <b>Advanced Research</b> from the navigation. The main comparison remains unchanged until new research is run.</p></div>';
}
const api=Object.freeze({prepare,tone,render});
if(typeof module==='object'&&module.exports)module.exports=api;
root.QFPrivateSimpleResearchV170=api;
})(typeof window!=='undefined'?window:globalThis);
