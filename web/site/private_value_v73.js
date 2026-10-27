/* QuantForge V7.3 — pure, independently testable owner-only price/SEC bridge. */
(function(root){
'use strict';
const finite=n=>typeof n==='number'&&Number.isFinite(n);
function dateAge(earlier,later){
 if(typeof earlier!=='string'||typeof later!=='string')return null;
 const a=Date.parse(earlier),b=Date.parse(later);
 if(!Number.isFinite(a)||!Number.isFinite(b))return null;
 const days=(b-a)/86400000;
 return days>=0?days:null;
}
function build(company,capital,quote,nowISO){
 const symbol=company?.symbol;
 if(!symbol||capital?.symbol!==symbol||quote?.symbol!==symbol)throw Error('Issuer symbols do not match.');
 const fiscal=company?.annual?.[0];
 const money=fiscal?.metrics||{};
 const asOf=typeof nowISO==='string'?nowISO:new Date().toISOString();
 const price=quote.price;
 const shareObj=capital.shares;
 const shares=shareObj?.value;
 const fcf=money.free_cash_flow_usd;
 const revenue=money.revenue_usd;
 const priceAge=dateAge(quote.timestamp,asOf);
 const shareAge=dateAge(shareObj?.periodEnd,asOf);
 const annualAge=dateAge(fiscal?.fiscal_end,asOf);
 const problems=[];
 if(!finite(price)||price<=0||priceAge===null||priceAge>7)problems.push('A recent positive stock price with a valid observation time is unavailable.');
 if(!finite(shares)||shares<=0||shareAge===null||shareAge>550)problems.push('Recent SEC point-in-time common shares outstanding are unavailable.');
 const valid=problems.length===0;
 const marketCap=valid?price*shares:null;
 const usableAnnual=annualAge!==null&&annualAge<=550;
 const usableFcf=usableAnnual&&finite(fcf);
 const usableRevenue=usableAnnual&&finite(revenue)&&revenue>0;
 const yieldFcf=marketCap&&usableFcf?fcf/marketCap:null;
 const pFcf=marketCap&&usableFcf&&fcf>0?marketCap/fcf:null;
 const pSales=marketCap&&usableRevenue?marketCap/revenue:null;
 const balanceAge=dateAge(capital.cash?.periodEnd,asOf);
 const components=capital.debtCashSamePeriod===true && finite(capital.reportedDebtComponentsTotal)
  &&finite(capital.cash?.value)&&balanceAge!==null&&balanceAge<=550;
 const approximateEV=marketCap&&components?marketCap+capital.reportedDebtComponentsTotal-capital.cash.value:null;
 if(!usableAnnual)problems.push('Latest reported annual financials are unavailable or stale.');
 if(!usableFcf)problems.push('Annual SEC operating-cash-flow-minus-capex data are missing.');
 if(!components)problems.push('Comparable SEC cash and both long-term debt components are incomplete; enterprise value is omitted.');
 return {symbol,valid,price:valid?price:null,priceTime:quote.timestamp,venue:quote.venue||'Unspecified',
  shares:valid?shares:null,sharesTime:shareObj?.periodEnd||null,sharesTag:shareObj?.tag||null,
  fiscalEnd:fiscal?.fiscal_end||null,reportedFcf:usableFcf?fcf:null,
  marketCap,pFcf,fcfYield:yieldFcf,pSales,
  approximateEV,enterpriseComplete:false, // Approximation omits many enterprise claims.
  source:capital.source,secUrl:capital.sourceUrl,
  warnings:problems,
  limitations:[
   'Market cap approximates point-in-time price times reported common shares, not a fully reconciled diluted equity value.',
   'Annual FCF proxy is operating cash flow minus cash capital expenditure, not unlevered FCFF or a complete equity cash-flow forecast.',
   'The equity-price multiples do not predict future investment returns; FCF yield is not a dividend yield.',
   'Indicative enterprise value excludes leases, short-term debt, preferred stock, noncontrolling interests and noncash investments.',
   'Quotes may be IEX-only and stale outside trading hours. Price and financial-statement dates can differ.'
  ]};
}
root.QFPrivateValueV73={build,dateAge};
if(typeof module==='object'&&module.exports)module.exports=root.QFPrivateValueV73;
})(typeof window!=='undefined'?window:globalThis);
