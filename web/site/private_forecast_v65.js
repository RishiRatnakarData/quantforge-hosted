/* SEC annual revenue/FCF projection scenarios; pure calculations, no provider calls. */
(function(root,factory){
 'use strict';
 const value=factory();
 if(typeof module==='object'&&module.exports)module.exports=value;
 else root.QFPrivateForecast=value;
})(typeof window!=='undefined'?window:this,function(){
 'use strict';
 const num=x=>typeof x==='number'&&Number.isFinite(x);
 const within=(x,a,b)=>num(x)&&x>=a&&x<=b;
 function run(company,opts={}){
  const years=Number(opts.years??5),growth=Number(opts.growth??0.06),margin=Number(opts.fcfMargin??0.12),
   discount=Number(opts.discount??0.10),terminal=Number(opts.terminal??0.02);
  if(!Number.isInteger(years)||years<3||years>7||!within(growth,-.30,.40)||
     !within(margin,-.25,.60)||!within(discount,.02,.30)||!within(terminal,-.05,.08)||
     discount<=terminal)throw Error('Check forecast assumptions and ensure the discount rate exceeds terminal growth.');
  const annual=company?.annual;
  if(!Array.isArray(annual)||annual.length<2)throw Error('At least two SEC annual periods are required for a historical baseline.');
  const hist=annual.filter(x=>/^\d{4}-\d{2}-\d{2}$/.test(x?.fiscal_end||'')&&
      num(x?.metrics?.revenue_usd)&&x.metrics.revenue_usd>0).sort((a,b)=>a.fiscal_end.localeCompare(b.fiscal_end));
  if(hist.length<2)throw Error('At least two comparable annual SEC revenue figures are required.');
  for(let i=1;i<hist.length;i++)if(hist[i].fiscal_end===hist[i-1].fiscal_end)throw Error('Repeated SEC fiscal periods.');
  const latest=hist.at(-1),baseRev=latest.metrics.revenue_usd,latestFCF=latest.metrics.free_cash_flow_usd;
  const fcfAvailable=num(latestFCF);
  const baseMargin=fcfAvailable?latestFCF/baseRev:null;
  const scenarios=[{name:'Conservative',growth:Math.max(-.30,growth-.04),margin:Math.max(-.25,margin-.03)},
   {name:'Base case',growth,margin},{name:'Optimistic',growth:Math.min(.40,growth+.04),margin:Math.min(.60,margin+.03)}];
  const output=scenarios.map(s=>{
   let revenue=baseRev,present=0;const projection=[];
   for(let year=1;year<=years;year++){
    // A specified constant growth assumption; not learned from future data.
    revenue*=(1+s.growth);
    const fcf=fcfAvailable?revenue*s.margin:null;
    if(fcfAvailable)present+=fcf/(1+discount)**year;
    projection.push({year,revenue,fcf});
   }
   const endFCF=projection.at(-1).fcf;
   const terminalPV=fcfAvailable&&endFCF>0?
    endFCF*(1+terminal)/(discount-terminal)/(1+discount)**years:null;
   const proxy=terminalPV===null?null:present+terminalPV;
   return {...s,projection,presentPV:fcfAvailable?present:null,terminalPV,proxy};
  });
  const historic=hist.map((row,i)=>({date:row.fiscal_end,revenue:row.metrics.revenue_usd,
   fcf:num(row.metrics.free_cash_flow_usd)?row.metrics.free_cash_flow_usd:null,
   revenueGrowth:i?(row.metrics.revenue_usd/hist[i-1].metrics.revenue_usd-1):null}));
  return {symbol:company.symbol,name:company.name,asOf:company.as_of||'',fiscalEnd:latest.fiscal_end,
   source:company.source||'SEC EDGAR company facts',historic,baseRev,baseMargin,
   fcfAvailable,years,discount,terminal,scenarios:output};
 }
 return {run};
});
