/* QuantForge public SEC company-facts comparison. No network access, storage or brokerage operations. */
(function(root){
'use strict';
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function rows(snapshot){
 if(!Array.isArray(snapshot?.companies))return [];
 return snapshot.companies.map(company=>{
  const latest=company.annual?.[0], prior=company.annual?.[1];
  const m=latest?.metrics||{},p=prior?.metrics||{};
  if(!finite(m.revenue_usd)||m.revenue_usd<=0||!finite(p.revenue_usd)||p.revenue_usd<=0||!finite(m.operating_income_usd))return null;
  const growth=100*(m.revenue_usd/p.revenue_usd-1),margin=100*m.operating_income_usd/m.revenue_usd;
  if(!finite(growth)||!finite(margin))return null;
  return {symbol:String(company.symbol||''),name:String(company.name||''),fiscalEnd:String(latest.fiscal_end||''),growth,margin};
 }).filter(Boolean).sort((a,b)=>a.symbol.localeCompare(b.symbol));
}
function quantile(values,fraction){
 const a=[...values].sort((x,y)=>x-y);if(!a.length)return NaN;
 const p=(a.length-1)*fraction,lo=Math.floor(p),hi=Math.ceil(p);
 return a[lo]+(a[hi]-a[lo])*(p-lo);
}
function extent(numbers){
 const low=Math.min(...numbers),high=Math.max(...numbers),spread=Math.max(high-low,0.1);
 return [low-spread*.12,high+spread*.12];
}
function viewport(data,mode='focus'){
 if(data.length<12||mode==='all')return {x:extent(data.map(r=>r.growth)),y:extent(data.map(r=>r.margin)),mode:'all'};
 return {x:extent([quantile(data.map(r=>r.growth),.1),quantile(data.map(r=>r.growth),.9)]),
         y:extent([quantile(data.map(r=>r.margin),.1),quantile(data.map(r=>r.margin),.9)]),mode:'focus'};
}
function inside(r,v){return r.growth>=v.x[0]&&r.growth<=v.x[1]&&r.margin>=v.y[0]&&r.margin<=v.y[1];}
function view(snapshot,options={}){
 const data=rows(snapshot);
 if(data.length<2)return '<p class="notice">Comparable SEC revenue and operating-income observations are unavailable for this exhibit. No illustrative values were substituted.</p>';
 const mode=options.mode==='all'?'all':'focus';
 const selected=typeof options.selected==='string'?data.find(r=>r.symbol===options.selected):null;
 const v=viewport(data,mode),visible=data.filter(r=>inside(r,v)),outside=data.filter(r=>!inside(r,v));
 const plotX=x=>75+(x-v.x[0])/(v.x[1]-v.x[0])*490;
 const plotY=y=>269-(y-v.y[0])/(v.y[1]-v.y[0])*210;
 const axes=[0,.25,.5,.75,1].map(t=>{
  const x=75+490*t,y=269-210*t;
  return `<line x1="${x}" y1="59" x2="${x}" y2="269" stroke="#e0ece6"/><line x1="75" y1="${y}" x2="565" y2="${y}" stroke="#e0ece6"/>`+
   `<text x="${x}" y="291" text-anchor="middle" font-size="11" fill="#4e6b5d">${(v.x[0]+(v.x[1]-v.x[0])*t).toFixed(1)}%</text>`+
   `<text x="66" y="${y+4}" text-anchor="end" font-size="11" fill="#4e6b5d">${(v.y[0]+(v.y[1]-v.y[0])*t).toFixed(1)}%</text>`;
 }).join('');
 // Labels are reserved for the selected company. Putting labels on every
 // marker was unreadable at full coverage and caused collisions.
 const circles=visible.map(r=>{
  const x=plotX(r.growth),y=plotY(r.margin),active=selected?.symbol===r.symbol;
  return `<circle data-evidence-symbol="${esc(r.symbol)}" tabindex="0" role="button" aria-label="Select ${esc(r.name)} (${esc(r.symbol)}), growth ${r.growth.toFixed(2)}%, operating margin ${r.margin.toFixed(2)}%" cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="${active?8:4.8}" fill="${active?'#a25a24':'#197c66'}" opacity="${active?1:.65}" stroke="${active?'#fff':'none'}" stroke-width="2"><title>${esc(r.name)} (${esc(r.symbol)}) · Growth ${r.growth.toFixed(2)}% · Margin ${r.margin.toFixed(2)}% · FY ${esc(r.fiscalEnd)}</title></circle>`;
 }).join('');
 const label=selected&&inside(selected,v)?`<text x="${Math.min(530,plotX(selected.growth)+12).toFixed(2)}" y="${Math.max(37,plotY(selected.margin)-13).toFixed(2)}" font-size="13" font-weight="800" fill="#8a4a23">${esc(selected.symbol)}</text>`:'';
 const optionsHTML=data.map(r=>`<option value="${esc(r.symbol)}" ${selected?.symbol===r.symbol?'selected':''}>${esc(r.name)} (${esc(r.symbol)})</option>`).join('');
 const table=data.map(r=>`<tr ${selected?.symbol===r.symbol?'class="qf-evidence-active"':''}><td><button type="button" data-evidence-symbol="${esc(r.symbol)}">${esc(r.symbol)}</button></td><td>${esc(r.fiscalEnd)}</td><td>${r.growth.toFixed(2)}%</td><td>${r.margin.toFixed(2)}%</td></tr>`).join('');
 const detail=selected?`<strong>${esc(selected.name)} (${esc(selected.symbol)})</strong> · FY ${esc(selected.fiscalEnd)} · Revenue growth ${selected.growth.toFixed(2)}% · Operating margin ${selected.margin.toFixed(2)}%${!inside(selected,v)?' · Outside the focused plot. Select “All observations” to display its marker.':''}`:'Select a company from the dropdown, table, or plot to inspect exact values.';
 const context=v.mode==='focus'?`Focused axis range: 10th–90th percentiles of each metric, with padding. ${visible.length} of ${data.length} markers shown; ${outside.length} outside the plotted range. All companies remain in the table.`:`Full axis range: ${visible.length} of ${data.length} companies plotted, including extreme values.`;
 const asOf=esc(snapshot?.as_of||'Cutoff not recorded');
 return `<div class="qf-evidence-explorer"><div class="qf-evidence-toolbar" aria-label="SEC chart display settings"><div class="qf-evidence-switch"><button type="button" data-evidence-mode="focus" aria-pressed="${v.mode==='focus'}">Focused range</button><button type="button" data-evidence-mode="all" aria-pressed="${v.mode==='all'}">All observations</button></div><label for="qf-evidence-company">Inspect company</label><select id="qf-evidence-company" data-evidence-select><option value="">Choose a company…</option>${optionsHTML}</select></div><p class="qf-evidence-context" role="status">${context}</p><div class="evidence-quant-grid qf-evidence-layout"><div class="evidence-graph"><svg viewBox="0 0 630 348" role="img" aria-label="SEC annual revenue growth and operating margin for ${visible.length} visible companies; use the adjacent table for all ${data.length} observations"><title>Annual revenue growth and operating margin from SEC filings</title>${axes}${circles}${label}<text x="320" y="328" text-anchor="middle" font-size="13" fill="#36584d">Annual revenue growth (%)</text><text x="17" y="164" transform="rotate(-90 17 164)" text-anchor="middle" font-size="13" fill="#36584d">Operating margin (%)</text></svg><p class="tiny">${data.length} comparable issuers · SEC source cutoff ${asOf}. Company fiscal years differ; these are financial-statement ratios, not stock returns.</p></div><div class="evidence-data table-wrap"><table><thead><tr><th>Issuer</th><th>FY ending</th><th>Revenue growth</th><th>Operating margin</th></tr></thead><tbody>${table}</tbody></table></div></div><p class="qf-evidence-selection" aria-live="polite">${detail}</p><p class="qf-evidence-footnote">The focused range changes only the visualization, not the data or calculations. Outlying company metrics should be investigated in their original filings before cross-company interpretation.</p></div>`;
}
function render(snapshot,element){
 if(!element)return;
 const state={mode:'focus',selected:''};
 function paint(){element.innerHTML=view(snapshot,state);}
 paint();
 element.addEventListener('click',event=>{
  const mode=event.target.closest?.('[data-evidence-mode]');
  if(mode){state.mode=mode.getAttribute('data-evidence-mode');paint();return;}
  const point=event.target.closest?.('[data-evidence-symbol]');
  if(point){state.selected=point.getAttribute('data-evidence-symbol');paint();}
 });
 element.addEventListener('change',event=>{
  if(event.target.matches?.('[data-evidence-select]')){state.selected=event.target.value;paint();}
 });
 element.addEventListener('keydown',event=>{
  if(event.key!=='Enter'&&event.key!==' ')return;
  const marker=event.target.closest?.('circle[data-evidence-symbol]');
  if(marker){event.preventDefault();state.selected=marker.getAttribute('data-evidence-symbol');paint();}
 });
}
const api={rows,quantile,viewport,view,render};
root.QFPublicEvidence=api;
if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
