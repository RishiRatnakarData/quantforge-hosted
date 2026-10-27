/* QuantForge V6.6: research-quality diagnostics over previously loaded private results.
   Pure computations; no external requests, credentials, trades, or storage side effects. */
(function(root, factory) {
  'use strict';
  const value = factory(
    root.QFPrivateForecast || (typeof require === 'function' ? require('./private_forecast_v65.js') : null),
    root.QFPrivateWalkforward || (typeof require === 'function' ? require('./private_walkforward_v65.js') : null)
  );
  if (typeof module === 'object' && module.exports) module.exports = value;
  else root.QFPrivateDiagnostics = value;
})(typeof window !== 'undefined' ? window : this, function(forecast, walkforward) {
  'use strict';
  const finite = x => typeof x === 'number' && Number.isFinite(x);
  const sum = values => values.reduce((acc, v) => acc + v, 0);
  const datePattern = /^\d{4}-\d{2}-\d{2}$/;
  const round = n => Math.round(n * 1e10) / 1e10;

  function summarizeWalkforward(result) {
    if (!result || !Array.isArray(result.windows) || !result.windows.length ||
        !Array.isArray(result.symbols) || result.symbols.length < 2 ||
        !Array.isArray(result.dates) || !result.dates.length ||
        !Array.isArray(result.optimized?.wealth) || !Array.isArray(result.benchmark?.wealth) ||
        result.optimized.wealth.length !== result.dates.length ||
        result.benchmark.wealth.length !== result.dates.length) {
      throw Error('Valid walk-forward results are required for diagnostics.');
    }
    const dateIndices = new Map(result.dates.map((d, i) => [d, i]));
    if (dateIndices.size !== result.dates.length || result.dates.some(d => !datePattern.test(d))) {
      throw Error('Evaluation dates must be distinct, chronological ISO dates.');
    }
    let endBefore = 0;
    const rows = result.windows.map((window, index) => {
      const start = dateIndices.get(window.testStart);
      const end = dateIndices.get(window.testEnd);
      if (!Number.isInteger(start) || !Number.isInteger(end) || start !== endBefore + 1 || end < start ||
          !datePattern.test(window.trainingEnd) || window.trainingEnd >= window.testStart ||
          !Array.isArray(window.weights) || window.weights.length !== result.symbols.length ||
          window.weights.some(w => !finite(w) || w < -1e-8 || w > 1 + 1e-8) ||
          Math.abs(sum(window.weights) - 1) > 1e-6) {
        throw Error('Walk-forward evaluation boundaries or weights are inconsistent.');
      }
      const a = result.optimized.wealth, b = result.benchmark.wealth;
      const values = [a[start - 1], a[end], b[start - 1], b[end]];
      if (values.some(x => !finite(x) || x <= 0)) throw Error('Invalid portfolio wealth observations.');
      const opt = a[end] / a[start - 1] - 1;
      const bench = b[end] / b[start - 1] - 1;
      const fees = window.rebalanceFees;
      const turnover = window.rebalanceTurnover;
      if (!Array.isArray(fees) || fees.length !== 2 || fees.some(x => !finite(x) || x < 0) ||
          !Array.isArray(turnover) || turnover.length !== 2 || turnover.some(x => !finite(x) || x < 0)) {
        throw Error('Per-window fee and turnover bookkeeping is missing. Re-run the test.');
      }
      endBefore = end;
      return {index: index + 1, trainingEnd: window.trainingEnd,
        testStart: window.testStart, testEnd: window.testEnd, sessions: end - start + 1,
        optimizedReturn: opt, benchmarkReturn: bench, activeReturn: opt - bench,
        optimizedFees: fees[0], benchmarkFees: fees[1],
        optimizedTurnover: turnover[0], benchmarkTurnover: turnover[1],
        weights: [...window.weights]};
    });
    if (endBefore !== result.dates.length - 1) throw Error('Some evaluation dates are not covered by windows.');
    const reportedFees = [result.optimized.fees, result.benchmark.fees];
    const totals = [sum(rows.map(x => x.optimizedFees)), sum(rows.map(x => x.benchmarkFees))];
    if (reportedFees.some((v, i) => !finite(v) || Math.abs(v - totals[i]) > Math.max(1e-5, Math.abs(v) * 1e-7))) {
      throw Error('Per-window fees do not reconcile with total costs.');
    }
    const changes = rows.slice(1).map((w, i) =>
      sum(w.weights.map((weight, j) => Math.abs(weight - rows[i].weights[j]))) / 2);
    const allReturns = rows.map(r => r.activeReturn);
    const capBinding = rows.filter(w => w.weights.some(weight => Math.abs(weight - result.cap) < 1e-4)).length;
    return {symbols: [...result.symbols], source: result.source, train: result.train,
      step: result.step, feeBps: result.feeBps, capital: result.capital,
      annualization: result.annual, start: result.start, end: result.end,
      rows, windowsCount: rows.length, positiveActiveWindows: allReturns.filter(x => x > 0).length,
      negativeActiveWindows: allReturns.filter(x => x < 0).length,
      meanWeightChange: changes.length ? sum(changes) / changes.length : 0,
      maxWeightChange: changes.length ? Math.max(...changes) : 0,
      capBindingWindows: capBinding,
      totalFees: totals,
      optimizedReturn: result.optimized.metrics.change,
      benchmarkReturn: result.benchmark.metrics.change,
      activeCompoundedReturn: result.optimized.metrics.change - result.benchmark.metrics.change};
  }

  function costSensitivity(history, baseline) {
    if (!walkforward || !baseline) throw Error('Loaded walk-forward results required.');
    const baselineParams = {train: baseline.train, step: baseline.step,
      objective: baseline.objective, cap: baseline.cap, capital: baseline.capital};
    const scenarios = [0, baseline.feeBps, Math.min(100, baseline.feeBps + 15)];
    const distinct = [...new Set(scenarios)];
    return distinct.map(feeBps => {
      // Every fee scenario re-fits using exactly the same past-only training schedule.
      const run = walkforward.run(history, {...baselineParams, feeBps});
      if (run.start !== baseline.start || run.end !== baseline.end ||
          run.windows.length !== baseline.windows.length ||
          run.symbols.join('|') !== baseline.symbols.join('|')) {
        throw Error('Transaction-cost scenarios do not share the same observation window.');
      }
      return {feeBps, optimizedChange: run.optimized.metrics.change,
        benchmarkChange: run.benchmark.metrics.change,
        activeChange: run.optimized.metrics.change - run.benchmark.metrics.change,
        optimizedFees: run.optimized.fees, benchmarkFees: run.benchmark.fees};
    });
  }

  function forecastSensitivity(company, opts) {
    if (!forecast) throw Error('Forecast engine unavailable.');
    const base = forecast.run(company, opts);
    const growth = Number(opts.growth), discount = Number(opts.discount);
    const offsets = [-0.04, -0.02, 0, 0.02, 0.04];
    const growthRates = offsets.map(x => round(growth + x));
    const discountRates = offsets.map(x => round(discount + x));
    const cells = discountRates.map(rate => growthRates.map(g => {
      if (g < -0.30 || g > 0.40 || rate < 0.02 || rate > 0.30 || rate <= Number(opts.terminal)) return null;
      try {
        // Hold forecast horizon, cash-flow margin and terminal growth fixed.
        const calc = forecast.run(company, {...opts, growth: g, discount: rate});
        return calc.scenarios.find(s => s.name === 'Base case')?.proxy ?? null;
      } catch (_) { return null; }
    }));
    const historicalGrowth = base.historic.map(x => x.revenueGrowth).filter(finite);
    return {symbol: base.symbol, company: base.name, source: base.source, asOf: base.asOf,
      fiscalEnd: base.fiscalEnd, growthRates, discountRates, cells,
      fcfAvailable: base.fcfAvailable,
      historicalPeriods: base.historic.length,
      observedGrowthMin: historicalGrowth.length ? Math.min(...historicalGrowth) : null,
      observedGrowthMax: historicalGrowth.length ? Math.max(...historicalGrowth) : null,
      observedGrowthAverage: historicalGrowth.length ? sum(historicalGrowth) / historicalGrowth.length : null,
      baseCaseProxy: base.scenarios.find(s => s.name === 'Base case')?.proxy ?? null,
      assumptions: {years: base.years, growth, fcfMargin: Number(opts.fcfMargin), discount,
        terminal: Number(opts.terminal)}};
  }

  function report(type, result, diagnostics) {
    if (!['walkforward', 'forecast'].includes(type) || !diagnostics) throw Error('Research report unavailable.');
    // Deliberately exclude provider tokens, raw Alpaca price feeds, private holdings, and note contents.
    if (type === 'walkforward') return {
      schema: 'quantforge.research.v1', type, historicalOnly: true,
      attribution: 'Alpaca historical market observations', createdFor: 'Local research export',
      investments: [...result.symbols], priceSource: result.source,
      methodology: 'Rolling past-only fitting and subsequent non-overlapping evaluation; same fee rule for both strategies.',
      limitations: ['Retrospective simulation, not live trading', 'Selection and optimization bias are possible',
        'No dividends, spread, slippage, taxes or borrow costs', 'IEX is not consolidated SIP coverage when fallback occurs'],
      parameters: {train: result.train, step: result.step, objective: result.objective,
        cap: result.cap, feeBps: result.feeBps, capital: result.capital, annualization: result.annual},
      period: {start: result.start, end: result.end},
      optimized: {metrics: result.optimized.metrics, totalFees: result.optimized.fees},
      benchmark: {metrics: result.benchmark.metrics, totalFees: result.benchmark.fees},
      diagnosticSummary: diagnostics};
    return {schema: 'quantforge.research.v1', type, hypothetical: true,
      company: diagnostics.company, symbol: diagnostics.symbol, source: diagnostics.source,
      asOf: diagnostics.asOf, fiscalEnd: diagnostics.fiscalEnd,
      methodology: 'Annual revenue compounding, assumed FCF/revenue margin, discounted FCF-plus-terminal proxy.',
      limitations: ['Not company enterprise value, equity value or per-share price target',
        'Not a predictive model or audited forecast', 'No capital-structure adjustments',
        'Few observed SEC years; scenarios depend heavily on assumptions'],
      observedSECAnnual: result.historic,
      modeledScenarios: result.scenarios,
      sensitivity: diagnostics};
  }
  return {summarizeWalkforward, costSensitivity, forecastSensitivity, report};
});
