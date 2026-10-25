/* QuantForge PUBLIC DEMO ONLY. Every price, return and financial statement is invented.
   Pure calculation library; no network calls or credentials. */
(function(root) {
'use strict';
const ASSETS = [
  {symbol:'MSFT', name:'Microsoft', kind:'stock', price:400},
  {symbol:'AAPL', name:'Apple', kind:'stock', price:220},
  {symbol:'NVDA', name:'NVIDIA', kind:'stock', price:160},
  {symbol:'AMZN', name:'Amazon', kind:'stock', price:180},
  {symbol:'VOO', name:'Vanguard S&P 500 ETF', kind:'etf', price:530},
  {symbol:'QQQ', name:'Invesco QQQ ETF', kind:'etf', price:590},
  {symbol:'BND', name:'Vanguard Total Bond Market ETF', kind:'etf', price:80},
  {symbol:'BTC/USD', name:'Bitcoin', kind:'crypto', price:60000},
  {symbol:'ETH/USD', name:'Ethereum', kind:'crypto', price:3200},
];
const bySymbol = Object.fromEntries(ASSETS.map(a=>[a.symbol,a]));
const ETF_HOLDINGS={
 VOO:{MSFT:0.06,AAPL:0.07,NVDA:0.06,AMZN:0.04,OTHER:0.77},
 QQQ:{MSFT:0.10,AAPL:0.08,NVDA:0.09,AMZN:0.05,OTHER:0.68},
 BND:{BONDS:1},
};
const COMPANY_FACTS={
 MSFT:{revenue:300,margin:0.40,growth:0.12,tax:0.21,da:0.06,capex:0.12,nwc:0.02,netDebt:-30,shares:7.4,features:[0.12,0.40,0.32,0.15,0.05]},
 AAPL:{revenue:390,margin:0.31,growth:0.06,tax:0.21,da:0.04,capex:0.05,nwc:0.01,netDebt:35,shares:15.0,features:[0.06,0.31,0.26,0.24,0.10]},
 NVDA:{revenue:145,margin:0.56,growth:0.25,tax:0.21,da:0.03,capex:0.04,nwc:0.03,netDebt:-25,shares:24.5,features:[0.25,0.56,0.41,0.42,0.01]},
 AMZN:{revenue:650,margin:0.12,growth:0.11,tax:0.21,da:0.10,capex:0.12,nwc:0.02,netDebt:45,shares:10.7,features:[0.11,0.12,0.07,0.03,0.13]},
 IBM:{revenue:64,margin:0.17,growth:0.04,tax:0.21,da:0.05,capex:0.04,nwc:0.01,netDebt:42,shares:0.92,features:[0.04,0.17,0.12,0.11,0.33]},
 ADBE:{revenue:21,margin:0.34,growth:0.11,tax:0.21,da:0.04,capex:0.05,nwc:0.02,netDebt:3,shares:0.42,features:[0.11,0.34,0.30,0.35,0.07]},
 QCOM:{revenue:39,margin:0.23,growth:0.09,tax:0.21,da:0.04,capex:0.05,nwc:0.02,netDebt:9,shares:1.11,features:[0.09,0.23,0.19,0.18,0.16]},
};
const COMPANY_NAMES={MSFT:'Microsoft',AAPL:'Apple',NVDA:'NVIDIA',AMZN:'Amazon',IBM:'IBM',ADBE:'Adobe',QCOM:'Qualcomm'};
function rnd(seed){let s=seed>>>0; return ()=>{s=(1664525*s+1013904223)>>>0;return s/4294967296;};}
function normal(r){return Math.sqrt(-2*Math.log(Math.max(1e-10,r())))*Math.cos(2*Math.PI*r());}
function history(symbols, n=276){
 const r=rnd(873491), out=Object.fromEntries(symbols.map(s=>[s,[]]));
 const coeff={MSFT:[0.88,0.010],AAPL:[0.86,0.012],NVDA:[1.38,0.018],AMZN:[1.05,0.014],VOO:[0.8,0.004],QQQ:[1.05,0.006],BND:[-0.06,0.0025],'BTC/USD':[1.45,0.033],'ETH/USD':[1.70,0.038]};
 for(let day=0;day<n;day++){
   const m=normal(r)*0.010;
   for(const s of symbols){const [beta,idio]=coeff[s];out[s].push(beta*m+idio*normal(r));}
 }
 return out;
}
function mean(x){return x.reduce((a,b)=>a+b,0)/x.length;}
function dot(a,b){return a.reduce((x,v,i)=>x+v*b[i],0);}
function cov(x,y){let mx=mean(x),my=mean(y),z=0;for(let i=0;i<x.length;i++)z+=(x[i]-mx)*(y[i]-my);return z/(x.length-1);}
function covariance(symbols){const h=history(symbols), c=symbols.map(a=>symbols.map(b=>cov(h[a],h[b])));return c;}
function variance(w,C){return dot(w,C.map(row=>dot(row,w)));}
function annualVol(w,C){return Math.sqrt(Math.max(0,variance(w,C)*252));}
function project(v,total,cap){
 if(total<1e-12) return v.map(()=>0);
 if(v.length*cap+1e-10<total) throw Error('Allocation limits are infeasible; raise max weight or select more assets.');
 let lo=Math.min(...v)-cap,hi=Math.max(...v);
 for(let k=0;k<90;k++){
  const mid=(lo+hi)/2, s=v.reduce((a,z)=>a+Math.max(0,Math.min(cap,z-mid)),0);
  if(s>total)lo=mid;else hi=mid;
 }
 let w=v.map(z=>Math.max(0,Math.min(cap,z-(lo+hi)/2)));
 const d=total-w.reduce((a,b)=>a+b,0);
 if(Math.abs(d)>1e-8){const i=w.findIndex(a=>a>1e-6&&a<cap-1e-6);if(i>=0)w[i]+=d;}
 return w;
}
function feasible(v,symbols,maxWeight,cryptoCap){
 const crypto=symbols.map((s,i)=>bySymbol[s].kind==='crypto'?i:-1).filter(i=>i>=0);
 if(crypto.length===0)return project(v,1,maxWeight);
 const none=symbols.map((s,i)=>bySymbol[s].kind!=='crypto'?i:-1).filter(i=>i>=0);
 if(none.length*maxWeight+crypto.length*maxWeight<1-1e-8) throw Error('Allocation limits are infeasible.');
 if(none.length*maxWeight+cryptoCap<1-1e-8) throw Error('Non-crypto investments cannot meet your maximum-weight rules.');
 let all=project(v,1,maxWeight), cr=crypto.reduce((z,i)=>z+all[i],0);
 if(cr<=cryptoCap+1e-8)return all;
 const a=project(crypto.map(i=>v[i]),cryptoCap,maxWeight);
 const b=project(none.map(i=>v[i]),1-cryptoCap,maxWeight);
 const out=new Array(v.length).fill(0);crypto.forEach((i,j)=>out[i]=a[j]);none.forEach((i,j)=>out[i]=b[j]);return out;
}
function optimize(symbols,maxWeight=0.6,cryptoCap=0.15){
 const C=covariance(symbols),n=symbols.length,base=new Array(n).fill(1/n);
 if(maxWeight<1/n-1e-9) throw Error('Max weight is too low for the number of investments.');
 let w=feasible(base,symbols,maxWeight,cryptoCap),lambda=0.002;
 for(let step=0;step<1200;step++){
  const grad=w.map((x,i)=>2*dot(C[i],w)+2*lambda*(x-base[i]));
  w=feasible(w.map((x,i)=>x-0.4*grad[i]),symbols,maxWeight,cryptoCap);
 }
 const b=feasible(base,symbols,maxWeight,cryptoCap);
 return {symbols,base:b,weights:w,cov:C,baselineVol:annualVol(b,C),optimalVol:annualVol(w,C)};
}
function cholesky(C){let n=C.length,L=Array.from({length:n},()=>Array(n).fill(0));for(let i=0;i<n;i++)for(let j=0;j<=i;j++){let z=C[i][j];for(let k=0;k<j;k++)z-=L[i][k]*L[j][k];L[i][j]=i===j?Math.sqrt(Math.max(z,1e-12)):z/L[j][j];}return L;}
function monteCarlo(weights,C,initial=10000,seed=9821,n=1800,days=21){
 const r=rnd(seed),L=cholesky(C),vals=[];
 for(let k=0;k<n;k++){
  let equity=initial;
  for(let d=0;d<days;d++){
   let z=weights.map(()=>normal(r));
   let moves=L.map(row=>row.reduce((a,b,i)=>a+b*z[i],0));
   const p=dot(weights,moves);equity*=Math.max(0.01,1+p);
  }
  vals.push(equity);
 }
 vals.sort((a,b)=>a-b);
 const at=p=>vals[Math.floor((n-1)*p)];const cutoff=at(0.05),tail=vals.filter(x=>x<=cutoff);
 return {low:cutoff,median:at(.5),high:at(.95),var95:Math.max(0,initial-cutoff),es95:Math.max(0,initial-mean(tail))};
}
function dcf(symbol,{growth=0.05,margin=null,wacc=0.10,terminal=0.025,tax=0.21}={}){
 const a=COMPANY_FACTS[symbol];if(!a)throw Error('DCF demonstration requires a company in the fictional financial dataset.');
 if(wacc<=terminal||wacc<=0||terminal<0||growth < -0.5||growth>0.8||wacc>1)throw Error('Check assumptions: WACC must exceed terminal growth.');
 let rev=a.revenue,pv=0,forecast=[];
 for(let y=1;y<=5;y++){
  let old=rev;rev*=1+growth;
  const op=rev*(margin??a.margin);const fcf=op*(1-tax)+rev*a.da-rev*a.capex-(rev-old)*a.nwc;
  pv+=fcf/Math.pow(1+wacc,y);forecast.push({year:y,revenue:rev,fcf});
 }
 const tv=forecast[4].fcf*(1+terminal)/(wacc-terminal),pvtv=tv/Math.pow(1+wacc,5);
 const enterprise=pv+pvtv,equity=enterprise-a.netDebt;
 return {value:equity/a.shares,enterprise,pvtv,pv,terminalFraction:pvtv/enterprise,forecast};
}
function peers(target){
 if(!COMPANY_FACTS[target])throw Error('Company not in fictional peer dataset.');
 const ss=Object.keys(COMPANY_FACTS), rows=ss.map(s=>COMPANY_FACTS[s].features);
 const means=Array.from({length:5},(_,i)=>mean(rows.map(r=>r[i])));
 const devs=means.map((a,i)=>Math.sqrt(mean(rows.map(r=>(r[i]-a)**2)))||1);
 const z=Object.fromEntries(ss.map(s=>[s,COMPANY_FACTS[s].features.map((v,i)=>(v-means[i])/devs[i])]));
 const dist=(a,b)=>Math.sqrt(a.reduce((v,n,i)=>v+(n-b[i])**2,0));
 const ranking=ss.filter(s=>s!==target).map(s=>({symbol:s,name:COMPANY_NAMES[s],distance:dist(z[target],z[s])})).sort((a,b)=>a.distance-b.distance);
 const unusual=ss.map(s=>({s,score:Math.sqrt(z[s].reduce((a,b)=>a+b*b,0))})).sort((a,b)=>b.score-a.score);
 return {ranking,unusualRank:unusual.findIndex(x=>x.s===target)+1,total:ss.length,target:COMPANY_FACTS[target].features};
}
function exposure(holdings){
 const values=Object.entries(holdings).map(([s,q])=>({s,value:q*bySymbol[s].price})),total=values.reduce((a,b)=>a+b.value,0);
 const byCompany={};for(const {s,value} of values){const f=ETF_HOLDINGS[s];if(f){for(const [name,w] of Object.entries(f))byCompany[name]=(byCompany[name]||0)+value*w;} else byCompany[s]=(byCompany[s]||0)+value;}
 return {total,holdings:values,lookthrough:Object.entries(byCompany).sort((a,b)=>b[1]-a[1]).map(([symbol,value])=>({symbol,value,pct:total?value/total:0}))};
}
root.QFModel={ASSETS,bySymbol,COMPANY_FACTS,COMPANY_NAMES,ETF_HOLDINGS,history,covariance,annualVol,optimize,monteCarlo,dcf,peers,exposure,variance};
})(typeof window!=='undefined'?window:globalThis);
