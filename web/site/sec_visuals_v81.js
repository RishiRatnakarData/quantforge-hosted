/* QuantForge V8.1: pure SEC chart builders; historical XBRL data and explicit scenarios only.
   No fetch, account calls, provider prices, browser storage, or state mutation. */
(function(root){
'use strict';
const esc=v=>String(v??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const valid=v=>typeof v==='number'&&Number.isFinite(v);
const usd=v=>valid(v)?(v<0?'-$':'$')+(Math.abs(v)/1e9).toFixed(2)+'B':'Not reported';
const percent=v=>valid(v)?(100*v).toFixed(1)+'%':'Not reported';
const definitions={
 margin:{label:'Operating margin',key:'operating_income_usd',denominator:'revenue_usd',type:'percent'},
 fcf:{label:'Free cash flow proxy',key:'free_cash_flow_usd',type:'usd'},
 income:{label:'Net income',key:'net_income_usd',type:'usd'}
};
function history(company,metric){
 const def=definitions[metric];if(!def||!Array.isArray(company?.annual))return [];
 return company.annual.map(row=>{
  const m=row?.metrics||{};let v=m[def.key];
  if(def.denominator)v=valid(v)&&valid(m[def.denominator])&&m[def.denominator]>0?v/m[def.denominator]:null;
  return {period:String(row.fiscal_end||''),value:valid(v)?v:null};
 }).filter(r=>/^\d{4}-\d{2}-\d{2}$/.test(r.period)).sort((a,b)=>a.period.localeCompare(b.period));
}
function lineSvg(points,label,fmt){
 const usable=points.filter(p=>valid(p.value));
 if(usable.length<2)return '<p class="qf-chart-empty">Not enough comparable annual observations to draw this chart. Missing values are not filled in.</p>';
 let lo=Math.min(0,...usable.map(p=>p.value)),hi=Math.max(0,...usable.map(p=>p.value));
 if(lo===hi){lo-=1;hi+=1;}
 const x=i=>55+(i*545/Math.max(1,points.length-1));
 const y=v=>204-(v-lo)/(hi-lo)*160;
 const path=points.map((p,i)=>valid(p.value)?`${i===0||!valid(points[i-1].value)?'M':'L'}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`:'').filter(Boolean).join(' ');
 const dots=points.map((p,i)=>valid(p.value)?`<circle cx="${x(i).toFixed(1)}" cy="${y(p.value).toFixed(1)}" r="4.5" fill="#126652"><title>${esc(p.period)}: ${esc(fmt(p.value))}</title></circle>`:'').join('');
 const labels=points.map((p,i)=>`<text x="${x(i).toFixed(1)}" y="230" text-anchor="middle" font-size="11" fill="#56766a">${esc(p.period.slice(0,4))}</text>`).join('');
 return `<svg viewBox="0 0 650 250" role="img" aria-label="${esc(label)} annual SEC data, chronological fiscal periods" xmlns="http://www.w3.org/2000/svg"><title>${esc(label)} by fiscal year</title><line x1="55" y1="${y(0).toFixed(1)}" x2="600" y2="${y(0).toFixed(1)}" stroke="#bdd1c7"/><path d="${path}" fill="none" stroke="#126652" stroke-width="3" stroke-linejoin="round"/>${dots}${labels}</svg>`;
}
function historicalHtml(company,metric){
 const def=definitions[metric];if(!def)return '<p>Choose a valid metric.</p>';
 const points=history(company,metric);
 const fmt=def.type==='percent'?percent:usd;
 const cells=points.map(p=>`<tr><td>${esc(p.period)}</td><td>${fmt(p.value)}</td></tr>`).join('');
 return `<h4>${esc(def.label)} · reported fiscal years</h4>${lineSvg(points,def.label,fmt)}<div class="qf-chart-table"><table><thead><tr><th>Fiscal year ended</th><th>${esc(def.label)}</th></tr></thead><tbody>${cells}</tbody></table></div><p class="tiny">Historical SEC issuer filings. FCF proxy is operating cash flow minus cash purchases of property and equipment; not a valuation or market-price series.</p>`;
}
function projection(company,growth,years){
 if(!valid(growth)||growth< -30||growth>40||!Number.isInteger(years)||years<1||years>5)return null;
 const rows=Array.isArray(company?.annual)?company.annual:[];
 const current=rows.find(row=>valid(row?.metrics?.revenue_usd)&&row.metrics.revenue_usd>0&&/^\d{4}-\d{2}-\d{2}$/.test(String(row.fiscal_end)));
 if(!current)return null;
 const year=Number(current.fiscal_end.slice(0,4));
 const list=[{year,value:current.metrics.revenue_usd,observed:true}];
 for(let i=1;i<=years;i++)list.push({year:year+i,value:current.metrics.revenue_usd*((1+growth/100)**i),observed:false});
 return list;
}
function projectionHtml(company,growth,years){
 const list=projection(company,growth,years);
 if(!list)return '<p class="qf-chart-empty">Scenario unavailable: choose a growth rate from −30% to +40% and valid SEC-reported revenue.</p>';
 const max=Math.max(...list.map(p=>p.value)),height=145;
 const bars=list.map((p,i)=>{
  const x=48+i*(550/list.length),w=Math.min(72,500/list.length),h=p.value/max*height;
  return `<rect x="${x}" y="${199-h}" width="${w}" height="${h}" rx="3" fill="${p.observed?'#176450':'#b7d9cb'}" ${p.observed?'':'stroke="#3a806c" stroke-dasharray="4 3"'}><title>${p.year}: ${usd(p.value)} · ${p.observed?'SEC reported':'assumed scenario'}</title></rect><text x="${x+w/2}" y="222" text-anchor="middle" fill="#4c6c60" font-size="11">${p.year}</text>`;
 }).join('');
 return `<p class="qf-chart-subline">Assuming ${growth.toFixed(1)}% annual revenue growth for ${years} year${years===1?'':'s'} from the latest eligible reported annual revenue. <strong>Not an earnings prediction, stock forecast, or valuation.</strong></p><svg viewBox="0 0 650 245" role="img" aria-label="Reported annual revenue baseline and hypothetical forward revenue scenario"><title>Revenue scenario: observed baseline and user assumption</title><line x1="36" y1="200" x2="620" y2="200" stroke="#c9d7d1"/>${bars}</svg><div class="qf-chart-key"><span>■ Dark: SEC reported baseline</span><span>□ Light dashed: hypothetical future years</span></div><div class="qf-chart-table"><table><thead><tr><th>Year</th><th>Revenue</th><th>Type</th></tr></thead><tbody>${list.map(p=>`<tr><td>${p.year}</td><td>${usd(p.value)}</td><td>${p.observed?'SEC reported':'Assumed scenario'}</td></tr>`).join('')}</tbody></table></div>`;
}
function rankingHtml(rows,label,unit){
 const validRows=Array.isArray(rows)?rows.filter(x=>valid(x?.value)&&x.value>0).slice(0,8):[];
 if(!validRows.length)return '<p class="qf-chart-empty">No positive comparable metric values available for these bars. See the complete table below.</p>';
 const max=Math.max(...validRows.map(r=>r.value));
 return `<h4>${esc(label)} · selected companies</h4><div class="qf-peer-bars">${validRows.map(r=>`<div class="qf-peer-row"><span title="${esc(r.name)}">${esc(r.symbol)}</span><div class="qf-peer-track"><span style="width:${Math.max(1,100*r.value/max).toFixed(1)}%"></span></div><strong>${esc(unit==='usd'?usd(r.value):r.value.toFixed(1)+'%')}</strong></div>`).join('')}</div><p class="tiny">Top positive reported values under the selected metric (up to eight companies). Fiscal years differ between issuers; the table below has the full units, years, and rankings. A longer bar does not mean a better investment.</p>`;
}
root.QFPublicVisualsV81=Object.freeze({history,historicalHtml,projection,projectionHtml,rankingHtml});
})(typeof window!=='undefined'?window:globalThis);
