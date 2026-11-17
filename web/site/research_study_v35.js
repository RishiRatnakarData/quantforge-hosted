/* Isolated company studies. Reuse the retained engines and canonical assessment. */
(function(root){
'use strict';
function assessmentInput(input,packet,E=root){
 const prices=input.assessmentPrices||[],financial=E.QFResearchCore20.financialSummary(input.company,input.asOf);
 const observed=input.origin==='market'&&prices.length>0;
 const crypto=input.symbol.includes('/');
 const h={symbols:[input.symbol],dates:prices.map(r=>r.date),closes:{[input.symbol]:prices.map(r=>r.close)},asset_classes:{[input.symbol]:crypto?'crypto':'us_equity'},source:input.assessmentSource||input.history?.source};
 const prediction=observed?E.QFPrivatePredictiveMLV180.analyze(h,input.symbol):{ready:false,reason:'No eligible observed company history.'};
 let overlap=[];
 try{const c=E.QFResearchB21.compare(input.history),at=c.symbols.indexOf(input.symbol);overlap=c.symbols.filter(s=>s!==input.symbol&&Number(input.portfolio?.holdings?.[s])>0).map(symbol=>({symbol,correlation:c.correlation_matrix[at][c.symbols.indexOf(symbol)],observations:c.dates.length-1,first:c.dates[0],last:c.dates.at(-1)}));}catch(_){/* Missing common dates never establish diversification. */}
 return {financial,observed,risk:observed?E.QFResearchCore20.priceStatistics(prices,crypto?365:252):null,prediction,
  held:Number(input.portfolio?.holdings?.[input.symbol])>0,portfolio:input.portfolio,ownerVersion:input.portfolio?.version,
  healthRow:(E.QFHealthSnapshot30?.companies?.[input.symbol]?.annual||[]).find(r=>r.fiscal_end===financial.source.period)||null,
  readFailures:input.readFailures||[],valuation:packet.results.value,portfolioImpact:packet.results.candidate?.portfolioImpact,overlap,asOf:input.asOf};
}
async function load({symbol,snapshot,portfolio,read,signal,now=()=>new Date().toISOString()},E=root){
 if(!/^[A-Z][A-Z0-9.]{0,9}$/.test(symbol)||!snapshot?.companies?.some(c=>c.symbol===symbol)||!portfolio||typeof read!=='function')throw Error('A covered eligible issuer and verified owner snapshot are required.');
 const check=()=>{if(signal?.aborted)throw new DOMException('Research cancelled.','AbortError');};check();
 const held=Object.entries(portfolio.holdings||{}).filter(([s,u])=>!s.includes('/')&&Number.isFinite(u)&&u>0).map(([s])=>s).slice(0,3);
 const symbols=[...new Set([symbol,symbol==='SPY'?'VTI':'SPY',...held])].slice(0,5),quoteNames=[...new Set([symbol,...Object.keys(portfolio.holdings||{})])].slice(0,8);
 const paths=[['prices','private/history-single?'+new URLSearchParams({symbol,days:'365'})],['batch','private/history?'+new URLSearchParams({symbols:symbols.join(','),days:'730'})],['quotes','private/quotes?'+new URLSearchParams({symbols:quoteNames.join(',')})],['capital','private/valuation-capital?'+new URLSearchParams({symbol})],['company','private/sec/company?'+new URLSearchParams({symbol})]];
 const outcomes=await Promise.allSettled(paths.map(([,path])=>read(path,signal)));check();
 if(outcomes.every(r=>r.status==='rejected'))throw Error('No requested evidence could be loaded.');
 const values={},failures=[];outcomes.forEach((r,i)=>{if(r.status==='fulfilled')values[paths[i][0]]=r.value;else failures.push(paths[i][0]);});
 const raw=values.prices;
 let assessmentPrices=[];
 if(raw?.licensed_private===true&&raw.symbol===symbol&&raw.ohlcv_available===false){try{assessmentPrices=E.QFResearchCore20.priceSeries(raw.observations);}catch(_){failures.push('prices');}}
 else if(raw)failures.push('prices');
 let history={symbols:[symbol],dates:assessmentPrices.map(p=>p.date),closes:{[symbol]:assessmentPrices.map(p=>p.close)},sessions_per_year:252,source:'Incomplete observed study; no synthetic replacement',calendar:'equity_sessions'};
 if(values.batch){try{history={...E.QFResearchB21.fromBatch(values.batch,symbols),sessions_per_year:252,source:values.batch.source||'Authenticated observations',calendar:'equity_sessions'};}catch(_){failures.push('batch');}}
 const company=values.company?.symbol===symbol&&Array.isArray(values.company.annual)?values.company:snapshot.companies.find(c=>c.symbol===symbol);
 if(values.company&&!(values.company.symbol===symbol&&Array.isArray(values.company.annual)))failures.push('company');
 if(values.capital&&values.capital.symbol!==symbol)failures.push('capital');
 if(values.quotes&&!Array.isArray(values.quotes.quotes))failures.push('quotes');
 const quotes=Array.isArray(values.quotes?.quotes)?Object.fromEntries(values.quotes.quotes.map(q=>[q.symbol,q])):{};
 return {scope:'company',symbol,company,snapshot,history,origin:'market',asOf:now(),assessmentPrices,assessmentSource:raw?.source||'Unavailable observed history',quote:quotes[symbol]||null,quotes,capital:values.capital?.symbol===symbol?values.capital:null,portfolio,readFailures:[...new Set(failures)]};
}
function study(input,{rules={},revision=0,preferences={horizon:'long'}}={},E=root){
 const packet=E.QFDeepResearch25.run(input),base=assessmentInput(input,packet,E);
 const report=E.QFDecision34.assess({...base,rules,revision,preferences},E.QFResearchGuide30);
 return {input,packet,assessmentInput:base,report};
}
function createBatch({run,valid=()=>true,onChange=()=>{},timeoutMs=60000}={}){
 let generation=0,controller=null,rows=[],pending=null;
 const snapshot=()=>rows.map(r=>({...r}));
 function cancel(){generation++;controller?.abort();controller=null;pending=null;rows=[];onChange(snapshot());}
 function start(candidates,context){
  if(pending)return pending;
  if(!Array.isArray(candidates)||candidates.length<1||candidates.length>5||new Set(candidates.map(c=>c.symbol)).size!==candidates.length)throw Error('Select one to five distinct shortlist companies.');
  cancel();const token=generation;controller=new AbortController();const signal=controller.signal;
  rows=candidates.map(c=>({symbol:c.symbol,name:c.name,state:'Waiting',result:null}));onChange(snapshot());
  const current=()=>token===generation&&!signal.aborted&&valid(context);
  const task=(async()=>{
   for(let i=0;i<rows.length;i++){
    if(!current())break;const item=rows[i];item.state='Loading evidence';onChange(snapshot());
    const timed=new AbortController(),abort=()=>timed.abort();signal.addEventListener('abort',abort,{once:true});let timer;
    try{
     const timeout=new Promise((_,reject)=>{timer=setTimeout(()=>{timed.abort();reject(Error('Evidence request timed out.'));},timeoutMs);});
     const result=await Promise.race([run(item.symbol,context,timed.signal,()=>{if(current()){item.state='Analyzing';onChange(snapshot());}}),timeout]);
     if(!current())break;
     item.result=result;item.state=result.report.coverage.every(r=>r.status==='covered')?'Completed':'Incomplete';
     if(result.input.readFailures?.length)item.state='Incomplete';
    }catch(error){if(!current())break;item.state='Failed';item.reason=error.name==='AbortError'?'Evidence request cancelled or timed out.':'Evidence could not be loaded. Other completed results are preserved.';}
    finally{clearTimeout(timer);signal.removeEventListener('abort',abort);}
    if(current())onChange(snapshot());
   }
   if(token===generation&&!valid(context)){rows=[];onChange(snapshot());}
   return token===generation?snapshot():[];
  })();
  const tracked=task.finally(()=>{if(pending===tracked){pending=null;onChange(snapshot());}});pending=tracked;onChange(snapshot());return tracked;
 }
 return Object.freeze({start,cancel,snapshot,busy:()=>Boolean(pending)});
}
const api=Object.freeze({load,study,assessmentInput,createBatch});root.QFCompanyStudy35=api;if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
