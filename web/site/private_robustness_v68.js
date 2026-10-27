/* QuantForge V6.8: controlled OOS robustness comparisons using already-loaded private bars.
 * Pure calculations; no brokerage commands, provider requests, state writes, or randomness.
 */
(function (root, factory) {
  'use strict';
  const value = factory(
    root.QFPrivateWalkforward || (typeof require === 'function' ? require('./private_walkforward_v65.js') : null),
    root.QFPrivateIntegrity || (typeof require === 'function' ? require('./private_integrity_v67.js') : null)
  );
  if (typeof module === 'object' && module.exports) module.exports = value;
  else root.QFPrivateRobustness = value;
})(typeof window !== 'undefined' ? window : this, function (walk, integrity) {
  'use strict';
  const finite = n => typeof n === 'number' && Number.isFinite(n);
  const sum = a => a.reduce((s, x) => s + x, 0);
  function guard(history, baseline) {
    if (!walk || !integrity) throw Error('Research modules unavailable.');
    const data = integrity.canonicalMarket(history);
    if (!baseline || !Array.isArray(baseline.dates) || baseline.dates.length < 2 ||
        !Array.isArray(baseline.windows) || baseline.windows.length < 2 ||
        baseline.symbols?.join('|') !== data.symbols.join('|') ||
        ![baseline.optimized?.wealth, baseline.benchmark?.wealth].every(a =>
          Array.isArray(a) && a.length === baseline.dates.length && a.every(x => finite(x) && x > 0))) {
      throw Error('Run Walk-forward on this loaded dataset before reviewing robustness.');
    }
    const start = data.dates.indexOf(baseline.start);
    if (start < 0 || baseline.dates.length + start > data.dates.length ||
        baseline.dates.some((d, i) => d !== data.dates[start + i]) ||
        baseline.end !== baseline.dates.at(-1) ||
        !finite(baseline.feeBps) || !finite(baseline.capital) || baseline.capital <= 0) {
      throw Error('Evaluation dates do not match the loaded historical prices.');
    }
    for (let i = 0; i < baseline.windows.length; i++) {
      const w = baseline.windows[i], p = baseline.dates.indexOf(w.trainingEnd), q = baseline.dates.indexOf(w.testEnd);
      if (p < 0 || q <= p || baseline.dates[p + 1] !== w.testStart ||
          (i && w.trainingEnd !== baseline.windows[i-1].testEnd) ||
          (i === 0 && p !== 0) || (i === baseline.windows.length-1 && q !== baseline.dates.length-1)) {
        throw Error('Non-contiguous evaluation windows; cannot compare strategies.');
      }
    }
    return {data, start};
  }
  function passiveBenchmark(history, baseline) {
    const {data, start} = guard(history, baseline);
    const n = data.symbols.length, capital = baseline.capital;
    const entryFee = capital * baseline.feeBps / 10000;
    if (entryFee >= capital) throw Error('Initial transaction fees exceed capital.');
    const net = capital - entryFee;
    const wealth = [capital];
    for (let i = 1; i < baseline.dates.length; i++) {
      const t = start + i;
      const value = net * sum(data.prices.map(prices => prices[t] / prices[start])) / n;
      if (!finite(value) || value <= 0) throw Error('Invalid passive benchmark wealth.');
      wealth.push(value);
    }
    const results = walk.metrics(wealth, baseline.annual);
    return {name:'Equal-weight buy and hold', change:results.change, annualVol:results.annualVol,
      maxDrawdown:results.maxDrawdown, finalWealth:wealth.at(-1), fee:entryFee,
      wealth, allocation:'Equal investment dollars at the first evaluation close; no further rebalancing'};
  }
  function leaveOneWindowOut(baseline) {
    const changes = [];
    for (let omit = 0; omit < baseline.windows.length; omit++) {
      let o = 1, b = 1;
      baseline.windows.forEach((w, i) => {
        const p = baseline.dates.indexOf(w.trainingEnd), q = baseline.dates.indexOf(w.testEnd);
        if (p < 0 || q <= p) throw Error('Invalid test-window alignment.');
        if (omit !== i) {
          o *= baseline.optimized.wealth[q] / baseline.optimized.wealth[p];
          b *= baseline.benchmark.wealth[q] / baseline.benchmark.wealth[p];
        }
      });
      changes.push({excludedWindow:omit + 1,
        excludedDates:baseline.windows[omit].testStart + ' to ' + baseline.windows[omit].testEnd,
        strategyReturn:o - 1, benchmarkReturn:b - 1, differencePp:(o-b)*100});
    }
    return changes;
  }
  function analyze(history, baseline) {
    const {data} = guard(history, baseline);
    const passive = passiveBenchmark(history, baseline);
    const base = {train:baseline.train,step:baseline.step,objective:baseline.objective,
      cap:baseline.cap,feeBps:baseline.feeBps,capital:baseline.capital};
    // Confirm that the original analysis was actually generated from the currently loaded bars.
    // Matching symbols and dates alone does not detect in-memory price changes.
    const checked = walk.run(history, base);
    const equalValue = (a, b) => Math.abs(a-b) <= 1e-9 * Math.max(1,Math.abs(a),Math.abs(b));
    if (checked.dates.join('|') !== baseline.dates.join('|') ||
        !equalValue(checked.optimized.wealth.at(-1),baseline.optimized.wealth.at(-1)) ||
        !equalValue(checked.benchmark.wealth.at(-1),baseline.benchmark.wealth.at(-1)) ||
        !equalValue(checked.optimized.fees,baseline.optimized.fees)) {
      throw Error('Loaded market data changed since Walk-forward ran. Re-run Walk-forward first.');
    }
    const cases = [{label:'Selected allocation',options:base,run:baseline}];
    for (const objective of ['minimum','inverse','tilt']) {
      if (objective !== base.objective) cases.push({label:({minimum:'Minimum volatility',inverse:'Inverse volatility',tilt:'Return tilt'})[objective],
        options:{...base,objective}});
    }
    const smallerCap = Math.max(1 / data.symbols.length, Math.round((base.cap - .10) * 100) / 100);
    if (smallerCap < base.cap - 1e-8) cases.push({label:'Tighter position cap',options:{...base,cap:smallerCap}});
    if (base.feeBps < 100) cases.push({label:'Higher transaction fee',options:{...base,feeBps:Math.min(100,base.feeBps + 15)}});
    const strategyCases = cases.map(c => {
      const run = c.run || walk.run(history,c.options);
      if (run.dates.join('|') !== baseline.dates.join('|') || run.windows.length !== baseline.windows.length) {
        throw Error('A comparison used different evaluation dates; stopped to avoid misleading results.');
      }
      return {label:c.label,objective:c.options.objective,train:c.options.train,
        step:c.options.step,cap:c.options.cap,feeBps:c.options.feeBps,
        optimizedReturn:run.optimized.metrics.change,
        equalWeightReturn:run.benchmark.metrics.change,
        activeDifferencePp:(run.optimized.metrics.change - run.benchmark.metrics.change) * 100,
        volatility:run.optimized.metrics.annualVol,
        fees:run.optimized.fees,windows:run.windows.length};
    });
    const loo = leaveOneWindowOut(baseline);
    const fullActivePp = (baseline.optimized.metrics.change - baseline.benchmark.metrics.change) * 100;
    return {schema:'quantforge.robustness.v1',symbols:[...data.symbols],
      source:String(history.source || baseline.source || 'Historical observations'),
      dates:{start:baseline.start,end:baseline.end},
      evaluationSessions:baseline.dates.length - 1,windowCount:baseline.windows.length,
      selectedModel:{...base},passive,
      strategyCases,leaveOneOut:loo,
      summary:{fullActivePp,
        looMinActivePp:Math.min(...loo.map(x=>x.differencePp)),
        looMaxActivePp:Math.max(...loo.map(x=>x.differencePp)),
        windowDependentSign:loo.some(x=>x.differencePp*fullActivePp < 0)},
      warnings:[
        'All allocation-rule comparisons use exactly the same fitted-through and evaluation dates; training window length and rebalance frequency are held fixed.',
        'The passive benchmark invests once at the first evaluation close; it does not periodically rebalance. Initial one-way fee uses the same basis-point assumption.',
        'Leave-one-window-out excludes a realized test-window return without refitting the other windows; it is descriptive sensitivity, not a new independent backtest.',
        'These alternatives are preselected robustness diagnostics; comparing their returns does not establish statistical significance or future outperformance.',
        'Historical closes are price-only, not total returns; no dividend, spread, slippage, borrow, or tax modeling.'
      ]};
  }
  function report(result,manifest) {
    if (!result || result.schema !== 'quantforge.robustness.v1' || manifest?.researchType !== 'walkforward' ||
        manifest.data?.symbols?.join('|') !== result.symbols.join('|')) throw Error('Research manifest mismatch.');
    const {passive, ...other} = result;
    return {...other,passive:{...passive,wealth:undefined},
      type:'walkforward-robustness',historicalOnly:true,manifest,
      limitations:result.warnings};
  }
  return {passiveBenchmark,leaveOneWindowOut,analyze,report};
});
