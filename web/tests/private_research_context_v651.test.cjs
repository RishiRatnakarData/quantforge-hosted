'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function setup() {
  const nodes = new Map();
  const el = id => {
    if (!nodes.has(id)) nodes.set(id, {
      id, value:'', textContent:'', innerHTML:'', hidden:false, disabled:false, listeners:{},
      classList:{toggle() {},add() {},remove() {}},
      addEventListener(event, fn){this.listeners[event]=fn;},
      removeAttribute() {}, setAttribute() {}, focus() {},
      dataset:{},
    });
    return nodes.get(id);
  };
  el('private-history-days').value='365';
  el('private-history-selection').textContent='Choose investments';
  const doc = {
    getElementById:el,
    querySelectorAll(){return [];},
    querySelector(){return {id:'page-private'};},
    addEventListener(){},
  };
  const urlCalls=[];
  let defer = null;
  const data={symbols:['AAPL','NVDA','META'], dates:['2026-01-02','2026-01-05','2026-01-06','2026-01-07'],
    closes:{AAPL:[100,102,103,104],NVDA:[200,201,200,205],META:[90,91,91.3,92]},source:'Alpaca test fixture',as_of:'2026-01-07',calendar:'stocks',annualization:252};
  async function fetchMock(url){
    urlCalls.push(url);
    if (url.startsWith('/api/private/history?')) {
      if (defer) return await defer();
      return {ok:true,json: async ()=>data};
    }
    throw Error('No mocked response for '+url);
  }
  const window={QFModel:{bySymbol:{}},QFPrivateOptimizer:{},QFPrivateWalkforward:{},QFPrivateMultiMarket:{analyze(d){return {assets:d.symbols.map(symbol=>({symbol,kind:'us_equity',observedChange:0.04,annualVolatility:0.2,maxDrawdown:-0.1,worstDay:-0.02})),stress:[{name:'Equity shock',change:-0.2}],calendar:'U.S. sessions',annual:252};}},confirm(){return true;}};
  const sourcePath=path.resolve(__dirname,'../../web/site/private.js');
  const source=fs.readFileSync(sourcePath,'utf8');
  const marker='\n})();';
  assert.equal(source.includes(marker),true);
  const injected=source.replace(marker, '\nwindow.__qfTest={chooseAsset,privateTab,loadHistory,refreshResearchContext,wfChart,setUser(v){privateState=v},setResearchMode(){browserState.mode="research"},getHistory(){return historySeries}};\n})();');
  const context={document:doc,window,fetch:fetchMock,URL,console,setTimeout,clearTimeout,queueMicrotask,Blob,Number,String,Math,Array,Object,Date};
  vm.runInNewContext(injected,context,{filename:'private.js'});
  return {el,window,data,urlCalls,setDeferred(fn){defer=fn}};
}

test('research panel exposes selection separately from loaded investments across all research tabs',async()=>{
 const m=setup(),{el}=m;
 m.window.__qfTest.setUser({holdings:{},cash:10000,notes:[]});m.window.__qfTest.setResearchMode();
 m.window.__qfTest.privateTab('research');
 assert.equal(el('private-research-dataset').hidden,false);
 for (const [symbol,name] of [['AAPL','Apple'],['NVDA','NVIDIA'],['META','Meta']]) {
   m.window.__qfTest.chooseAsset(symbol,name,'us_equity');
 }
 assert.match(el('private-research-selected').textContent,/3 selected:/);
 assert.match(el('private-research-loaded').textContent,/No historical data loaded/);
 await m.window.__qfTest.loadHistory();
 assert.match(el('private-research-loaded').textContent,/3 loaded:/);
 assert.match(el('private-research-loaded').textContent,/AAPL/);
 assert.match(el('private-research-loaded').textContent,/2026-01-02 to 2026-01-07/);
 for (const tab of ['optimization','backtest','walkforward']){
   m.window.__qfTest.privateTab(tab);
   assert.equal(el('private-research-dataset').hidden,false);
 }
 m.window.__qfTest.privateTab('valuation');
 assert.equal(el('private-research-dataset').hidden,true);
});

test('changing date range clears previously loaded data and disables stale exports',async()=>{
 const m=setup(),{el}=m;
 m.window.__qfTest.setUser({holdings:{},cash:10000,notes:[]});m.window.__qfTest.setResearchMode();
 for (const [s,n] of [['AAPL','Apple'],['NVDA','NVIDIA'],['META','Meta']])m.window.__qfTest.chooseAsset(s,n,'us_equity');
 await m.window.__qfTest.loadHistory();
 assert.ok(m.window.__qfTest.getHistory());
 el('private-history-days').value='730';
 el('private-history-days').listeners.change();
 assert.equal(m.window.__qfTest.getHistory(),null);
 assert.equal(el('private-wf-export').disabled,true);
 assert.equal(el('private-opt-export').disabled,true);
 assert.match(el('private-research-loaded').textContent,/No historical data loaded/);
 assert.match(el('private-research-state').textContent,/Not loaded yet/);
});


test('a delayed price response cannot reload an obsolete selection',async()=>{
 const m=setup(),{el}=m;
 m.window.__qfTest.setUser({holdings:{},cash:10000,notes:[]});m.window.__qfTest.setResearchMode();
 for (const [s,n] of [['AAPL','Apple'],['NVDA','NVIDIA'],['META','Meta']])m.window.__qfTest.chooseAsset(s,n,'us_equity');
 let release;
 m.setDeferred(()=>new Promise(resolve=>{release=()=>resolve({ok:true,json:async()=>m.data});}));
 const pending=m.window.__qfTest.loadHistory();
 assert.equal(typeof release,'function');
 m.window.__qfTest.chooseAsset('TSLA','Tesla','us_equity');
 release();
 await pending;
 assert.equal(m.window.__qfTest.getHistory(),null);
 assert.match(el('private-research-loaded').textContent,/No historical data loaded/);
});

test('walk-forward graph explicitly attributes two lines to all three investments',()=>{
 const m=setup();
 const chart=m.window.__qfTest.wfChart({
  symbols:['AAPL','NVDA','META'],start:'2026-01-02',end:'2026-01-07',
  optimized:{wealth:[10000,10100,10500]},benchmark:{wealth:[10000,10030,10200]},
 });
 assert.match(chart,/3 investments are combined into two portfolio lines/);
 assert.match(chart,/optimized portfolio \(all selected investments\)/);
 assert.match(chart,/equal-weight benchmark \(the same investments\)/);
 for (const sym of ['AAPL','NVDA','META'])assert.ok(chart.includes(sym));
});
