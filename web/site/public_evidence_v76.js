/* Public source-backed research evidence, separate from authenticated investment data. */
(function(root){
'use strict';
const finite = value => typeof value === 'number' && Number.isFinite(value);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
function rows(snapshot){
 if(!Array.isArray(snapshot?.companies))return [];
 return snapshot.companies.map(company=>{
  const latest=company.annual?.[0], earlier=company.annual?.[1];
  const current=latest?.metrics||{},prior=earlier?.metrics||{};
  if(!finite(current.revenue_usd)||current.revenue_usd<=0||
     !finite(prior.revenue_usd)||prior.revenue_usd<=0||
     !finite(current.operating_income_usd))return null;
  const growth=100*(current.revenue_usd/prior.revenue_usd-1);
  const margin=100*current.operating_income_usd/current.revenue_usd;
  if(!finite(growth)||!finite(margin))return null;
  return {symbol:String(company.symbol||''),name:String(company.name||''),
          fiscalEnd:String(latest.fiscal_end||''),growth,margin};
 }).filter(Boolean).sort((a,b)=>a.symbol.localeCompare(b.symbol));
}
function bounds(numbers){
 const low=Math.min(...numbers),high=Math.max(...numbers),span=high-low||Math.max(Math.abs(high),1);
 return [low-span*0.17,high+span*0.17];
}
function view(snapshot){
 const data=rows(snapshot);
 if(data.length<2)return '<p class="notice">Comparable SEC revenue and operating-income observations are unavailable for this exhibit. No illustrative values were substituted.</p>';
 const [minX,maxX]=bounds(data.map(x=>x.growth)),[minY,maxY]=bounds(data.map(x=>x.margin));
 const plotX=v=>64+(v-minX)/(maxX-minX)*480;
 const plotY=v=>253-(v-minY)/(maxY-minY)*200;
 const grids=[0,.25,.5,.75,1].map(t=>{
  const x=64+480*t,y=253-200*t;
  const xval=minX+(maxX-minX)*t,yval=minY+(maxY-minY)*t;
  return `<line x1="${x}" x2="${x}" y1="53" y2="253" stroke="#e2eee7"/>`+
         `<line x1="64" x2="544" y1="${y}" y2="${y}" stroke="#e2eee7"/>`+
         `<text x="${x}" y="275" text-anchor="middle" fill="#526b5e" font-size="10">${xval.toFixed(1)}%</text>`+
         `<text x="54" y="${y+4}" text-anchor="end" fill="#526b5e" font-size="10">${yval.toFixed(1)}%</text>`;
 }).join('');
 const circles=data.map((r,i)=>{
  const x=plotX(r.growth),y=plotY(r.margin);
  return `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="6.5" fill="#18745c" opacity=".86"><title>${escapeHTML(r.name)} (${escapeHTML(r.symbol)}): revenue growth ${r.growth.toFixed(2)}%, operating margin ${r.margin.toFixed(2)}%, FY ${escapeHTML(r.fiscalEnd)}</title></circle>`+
         `<text x="${Math.min(547,x+9).toFixed(2)}" y="${Math.max(35,y-9).toFixed(2)}" font-size="10" fill="#274d40">${escapeHTML(r.symbol)}</text>`;
 }).join('');
 const table=data.map(r=>`<tr><td>${escapeHTML(r.symbol)}</td><td>${escapeHTML(r.fiscalEnd)}</td><td>${r.growth.toFixed(2)}%</td><td>${r.margin.toFixed(2)}%</td></tr>`).join('');
 const asOf=escapeHTML(snapshot?.as_of||'Cutoff not recorded');
 return `<div class="evidence-quant-grid"><div class="evidence-graph"><svg viewBox="0 0 600 320" role="img" aria-label="SEC annual revenue growth compared with operating margins for ${data.length} companies; corresponding values are in the adjacent table"><title>Revenue growth and operating margin from published SEC annual facts</title>${grids}${circles}<text x="304" y="305" text-anchor="middle" fill="#36584d" font-size="12">Annual revenue growth (%)</text><text x="15" y="155" transform="rotate(-90 15 155)" text-anchor="middle" fill="#36584d" font-size="12">Operating margin (%)</text></svg><p class="tiny">${data.length} comparable companies · SEC source cutoff ${asOf}. Company fiscal years differ. Each marker reflects historical disclosures, not market returns.</p></div>`+
 `<div class="evidence-data table-wrap"><table><thead><tr><th>Issuer</th><th>FY ending</th><th>Revenue growth</th><th>Operating margin</th></tr></thead><tbody>${table}</tbody></table></div></div>`;
}
function render(snapshot, element){if(element)element.innerHTML=view(snapshot);}
const api={rows,view,render};
root.QFPublicEvidence=api;
if(typeof module!=='undefined' && module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
