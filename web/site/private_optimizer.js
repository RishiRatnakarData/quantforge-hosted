/* QuantForge private research: pure in-sample portfolio analytics.
 * No external requests, synthetic data, brokerage orders, or portfolio mutations.
 * The public demo model is deliberately not imported here.
 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.QFPrivateOptimizer = api;
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';
  const finite = x => typeof x === 'number' && Number.isFinite(x);
  const sum = x => x.reduce((a, b) => a + b, 0);
  const dot = (a, b) => sum(a.map((x, i) => x * b[i]));
  const average = a => sum(a) / a.length;
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));

  function prepare(data) {
    if (!data || !Array.isArray(data.symbols) || !Array.isArray(data.dates) ||
        !data.closes || data.symbols.length < 2 || data.symbols.length > 5 ||
        new Set(data.symbols).size !== data.symbols.length || data.dates.length < 31 ||
        data.dates.length > 900 || data.dates.some((d, i) =>
          typeof d !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(d) ||
          (i > 0 && d <= data.dates[i - 1]))) {
      throw Error('Load at least 31 aligned daily prices for 2–5 distinct investments.');
    }
    const annual = data.sessions_per_year === 365 ? 365 : 252;
    const prices = data.symbols.map(s => {
      const arr = data.closes[s];
      if (!Array.isArray(arr) || arr.length !== data.dates.length ||
          arr.some(p => !finite(p) || p <= 0)) throw Error('Incomplete or invalid price history.');
      return arr;
    });
    const assetReturns = prices.map(p => p.slice(1).map((x, i) => x / p[i] - 1));
    if (assetReturns.some(a => a.some(r => !finite(r) || r <= -1 || r > 10))) {
      throw Error('Unsupported or discontinuous daily price history.');
    }
    const count = assetReturns[0].length;
    const means = assetReturns.map(average);
    const raw = assetReturns.map((a, i) => assetReturns.map((b, j) => {
      let v = 0;
      for (let t = 0; t < count; t++) v += (a[t] - means[i]) * (b[t] - means[j]);
      return v / (count - 1);
    }));
    const covariance = raw.map((row, i) => row.map((c, j) =>
      c * (i === j ? 1 : 0.80))); // fixed 20% diagonal shrinkage, off-diagonal only
    return {symbols: [...data.symbols], dates: [...data.dates], count, assetReturns,
      means: means.map(x => x * annual), rawCovariance: raw, covariance, prices, annual};
  }

  function project(values, maxWeight) {
    const n = values.length;
    if (!finite(maxWeight) || maxWeight <= 0 || maxWeight > 1 ||
        n * maxWeight < 1 - 1e-10) throw Error('Maximum position weight is too low for the selected investments.');
    if (values.some(x => !finite(x))) throw Error('Invalid allocation calculation.');
    let low = Math.min(...values) - maxWeight;
    let high = Math.max(...values);
    for (let k = 0; k < 100; k++) {
      const mid = (low + high) / 2;
      const s = sum(values.map(x => clamp(x - mid, 0, maxWeight)));
      if (s > 1) low = mid; else high = mid;
    }
    const out = values.map(x => clamp(x - (low + high) / 2, 0, maxWeight));
    let residual = 1 - sum(out);
    for (let k = 0; k < out.length && Math.abs(residual) > 1e-11; k++) {
      const change = residual > 0 ? Math.min(residual, maxWeight - out[k]) :
        Math.max(residual, -out[k]);
      out[k] += change;
      residual -= change;
    }
    if (Math.abs(sum(out) - 1) > 1e-8) throw Error('Cannot satisfy allocation constraints.');
    return out;
  }

  function variance(weights, covariance) {
    return dot(weights, covariance.map(row => dot(row, weights)));
  }

  function solve(data, maxWeight, mode, tiltStrength = 0.02) {
    const n = data.symbols.length;
    const c = data.covariance.map(row => row.map(x => x * data.annual));
    const initial = project(Array(n).fill(1 / n), maxWeight);
    if (mode === 'inverse') {
      const sigmas = data.covariance.map((row, i) => Math.sqrt(Math.max(row[i], 1e-12)));
      return project(sigmas.map(x => 1 / x / sum(sigmas.map(y => 1 / y))), maxWeight);
    }
    if (mode !== 'minimum' && mode !== 'tilt') throw Error('Unknown optimization objective.');
    // Center and shrink highly unstable historical annualized return estimates.
    // This score is descriptive, not an expected-return forecast.
    const common = average(data.means);
    const scores = data.means.map(x => clamp((x - common) * 0.25, -0.20, 0.20));
    const maxRow = Math.max(...c.map(row => sum(row.map(Math.abs))), 1e-7);
    const learningRate = 0.75 / (2 * maxRow);
    let weights = initial;
    for (let k = 0; k < 1800; k++) {
      const gradient = weights.map((_, i) =>
        2 * dot(c[i], weights) - (mode === 'tilt' ? tiltStrength * scores[i] : 0));
      const next = project(weights.map((w, i) => w - learningRate * gradient[i]), maxWeight);
      const delta = Math.max(...weights.map((w, i) => Math.abs(w - next[i])));
      weights = next;
      if (delta < 1e-11) break;
    }
    return weights;
  }

  function weightsStats(data, weights) {
    if (weights.length !== data.symbols.length || weights.some(x => !finite(x) || x < -1e-9) ||
        Math.abs(sum(weights) - 1) > 1e-6) throw Error('Invalid portfolio weights.');
    const daily = data.assetReturns[0].map((_, t) =>
      dot(weights, data.assetReturns.map(row => row[t])));
    const avg = average(daily);
    const sampleVar = sum(daily.map(x => (x - avg) ** 2)) / (daily.length - 1);
    const vol = Math.sqrt(Math.max(0, variance(weights, data.covariance) * data.annual));
    const wealth = [1];
    for (const r of daily) wealth.push(wealth.at(-1) * (1 + r));
    let high = 1, drawdown = 0;
    for (const v of wealth) {high = Math.max(high, v); drawdown = Math.min(drawdown, v / high - 1);}
    const ordered = [...daily].sort((a, b) => a - b);
    const tail = Math.max(1, Math.ceil(ordered.length * 0.05));
    const dailyVaR = Math.max(0, -ordered[tail - 1]);
    const dailyES = Math.max(0, -average(ordered.slice(0, tail)));
    const sigma = Math.sqrt(Math.max(0, variance(weights, data.covariance)));
    const contributions = weights.map((w, i) =>
      sigma <= 1e-12 ? 0 : w * dot(data.covariance[i], weights) / (sigma * sigma));
    function worstWindow(days) {
      if (daily.length < days) return null;
      let worst = Infinity;
      for (let k = 0; k + days <= daily.length; k++) {
        let p = 1;
        for (let t = k; t < k + days; t++) p *= 1 + daily[t];
        worst = Math.min(worst, p - 1);
      }
      return worst;
    }
    return {annualHistoricalMean: avg * data.annual, annualVolatility: vol,
      realizedVolatility: Math.sqrt(sampleVar * data.annual), compoundChange: wealth.at(-1) - 1,
      maxDrawdown: drawdown, dailyVaR, dailyES, effectiveHoldings: 1 / sum(weights.map(w => w * w)),
      riskContributions: contributions, worst5: worstWindow(5), worst20: worstWindow(20)};
  }

  function correlation(data) {
    return data.rawCovariance.map((row, i) => row.map((v, j) => {
      const a = data.rawCovariance[i][i], b = data.rawCovariance[j][j];
      return a > 1e-15 && b > 1e-15 ? clamp(v / Math.sqrt(a * b), -1, 1) : null;
    }));
  }

  function run(history, opts = {}) {
    const data = prepare(history);
    const cap = Number(opts.maxWeight ?? 0.6);
    const objective = opts.objective || 'minimum';
    const baseline = project(Array(data.symbols.length).fill(1 / data.symbols.length), cap);
    const chosen = solve(data, cap, objective);
    const frontier = [0, 0.005, 0.01, 0.02, 0.035, 0.05, 0.08].map(s => {
      const w = solve(data, cap, s === 0 ? 'minimum' : 'tilt', s);
      const stats = weightsStats(data, w);
      return {risk: stats.annualVolatility, historicalMean: stats.annualHistoricalMean};
    });
    return {symbols: data.symbols, periodStart: data.dates[0], periodEnd: data.dates.at(-1),
      observations: data.count, annualSessions: data.annual, objective, maxWeight: cap, chosen,
      optimized: weightsStats(data, chosen), equalWeights: baseline,
      equal: weightsStats(data, baseline), correlation: correlation(data), frontier,
      source: history.source || 'Alpaca historical close observations'};
  }

  return {prepare, project, solve, weightsStats, correlation, run};
});
