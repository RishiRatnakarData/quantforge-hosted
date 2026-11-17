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
 const sources=fiscal?.sources||{};
 const sourced=key=>{const s=sources[key];return Boolean(s?.accession&&s?.filed&&dateAge(s.filed,asOf)!==null&&(!s.end||s.end===fiscal.fiscal_end));};
 const cashCompatible=sourced('operating_cash_flow_usd')&&sourced('capex_usd')&&sources.operating_cash_flow_usd.accession===sources.capex_usd.accession&&(!sources.operating_cash_flow_usd.start||!sources.capex_usd.start||sources.operating_cash_flow_usd.start===sources.capex_usd.start);
 const usableFcf=usableAnnual&&finite(fcf)&&cashCompatible;
 const usableRevenue=usableAnnual&&finite(revenue)&&revenue>0&&sourced('revenue_usd');
 const usableEarnings=usableAnnual&&finite(money.net_income_usd)&&money.net_income_usd>0&&sourced('net_income_usd')&&usableRevenue&&sources.net_income_usd.accession===sources.revenue_usd.accession;
 const pEarnings=marketCap&&usableEarnings?marketCap/money.net_income_usd:null;
 const yieldFcf=marketCap&&usableFcf?fcf/marketCap:null;
 const pFcf=marketCap&&usableFcf&&fcf>0?marketCap/fcf:null;
 const pSales=marketCap&&usableRevenue?marketCap/revenue:null;
 const balanceAge=dateAge(capital.cash?.periodEnd,asOf);
 const components=capital.debtCashSamePeriod===true && capital.debtCashSameFiling===true && finite(capital.reportedDebtComponentsTotal)
  &&finite(capital.cash?.value)&&balanceAge!==null&&balanceAge<=550;
 const approximateEV=marketCap&&components?marketCap+capital.reportedDebtComponentsTotal-capital.cash.value:null;
 if(!usableAnnual)problems.push('Latest reported annual financials are unavailable or stale.');
 if(!usableFcf)problems.push('Compatible, same-filing annual operating-cash-flow and capex facts are missing or stale.');
 if(!components)problems.push('Compatible same-filing SEC cash and long-term debt components are incomplete; enterprise approximation is omitted.');
 return {symbol,valid,price:valid?price:null,priceTime:quote.timestamp,venue:quote.venue||'Unspecified',
  shares:valid?shares:null,sharesTime:shareObj?.periodEnd||null,sharesTag:shareObj?.tag||null,
  fiscalEnd:fiscal?.fiscal_end||null,reportedFcf:usableFcf?fcf:null,
  marketCap,pFcf,fcfYield:yieldFcf,pSales,pEarnings,earningsBasis:'Approximate market capitalization / compatible annual net income. Not diluted-EPS P/E or a price target.',earningsAccession:usableEarnings?sources.net_income_usd.accession:null,
  annualDilutedShares:capital.annualDilutedShares||null,shareBasisDisclosure:capital.shareBasisDisclosure||'Diluted-share evidence is unavailable; instant common shares are not a fully diluted equity bridge.',
  approximateEV,enterpriseComplete:false, // Approximation omits many enterprise claims.
  source:capital.source,secUrl:capital.sourceUrl,fullValuationMissing:['Complete unlevered cash-flow forecast','Other borrowing and lease claims','Preferred stock and noncontrolling claims','Noncash investments and other enterprise adjustments','Point-in-time fully diluted equity share count'],ttmStatus:'Unavailable: no verified four-quarter roll-forward is loaded in the annual research contract.',
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
