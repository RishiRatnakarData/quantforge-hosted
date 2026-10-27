/* V6.7 research provenance & model-risk checks. Offline, deterministic, no network or storage. */
(function (root, factory) {
  'use strict';
  const value = factory();
  if (typeof module === 'object' && module.exports) module.exports = value;
  else root.QFPrivateIntegrity = value;
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';
  const finite = x => typeof x === 'number' && Number.isFinite(x);
  const isoDate = /^\d{4}-\d{2}-\d{2}$/;
  const VERSION = 'quantforge.research.manifest.v1';
  const MARKET_MODEL = 'quantforge.walkforward.v6.5';
  const FORECAST_MODEL = 'quantforge.sec.forecast.v6.5';
  const K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
  ];
  const ROT = (x, n) => (x >>> n) | (x << (32 - n));
  function sha256(text) {
    if (typeof text !== 'string') throw Error('Hash input must be text.');
    const bytes = Array.from(new TextEncoder().encode(text));
    const bitHi = Math.floor(bytes.length / 0x20000000), bitLo = (bytes.length * 8) >>> 0;
    bytes.push(0x80);
    while (bytes.length % 64 !== 56) bytes.push(0);
    for (const num of [bitHi, bitLo]) for (let shift = 24; shift >= 0; shift -= 8) bytes.push((num >>> shift) & 255);
    const h = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    for (let offset = 0; offset < bytes.length; offset += 64) {
      const w = Array(64).fill(0);
      for (let i = 0; i < 16; i++) {
        const at = offset + i * 4;
        w[i] = ((bytes[at] << 24) | (bytes[at + 1] << 16) | (bytes[at + 2] << 8) | bytes[at + 3]) >>> 0;
      }
      for (let i = 16; i < 64; i++) {
        const x = w[i - 15], y = w[i - 2];
        w[i] = (w[i - 16] + (ROT(x, 7) ^ ROT(x, 18) ^ (x >>> 3)) + w[i - 7] +
          (ROT(y, 17) ^ ROT(y, 19) ^ (y >>> 10))) >>> 0;
      }
      let [a,b,c,d,e,f,g,z] = h;
      for (let i = 0; i < 64; i++) {
        const temp1 = (z + (ROT(e,6)^ROT(e,11)^ROT(e,25)) + ((e&f)^(~e&g)) + K[i] + w[i]) >>> 0;
        const temp2 = ((ROT(a,2)^ROT(a,13)^ROT(a,22)) + ((a&b)^(a&c)^(b&c))) >>> 0;
        z=g;g=f;f=e;e=(d+temp1)>>>0;d=c;c=b;b=a;a=(temp1+temp2)>>>0;
      }
      [a,b,c,d,e,f,g,z].forEach((v,i) => { h[i] = (h[i] + v) >>> 0; });
    }
    return h.map(x => x.toString(16).padStart(8, '0')).join('');
  }
  function canonicalMarket(history) {
    const symbols = history?.symbols, dates = history?.dates, closes = history?.closes;
    if (!Array.isArray(symbols) || symbols.length < 2 || symbols.length > 5 ||
        new Set(symbols).size !== symbols.length || symbols.some(s => typeof s !== 'string' || !/^[A-Z0-9./-]{1,18}$/.test(s)) ||
        !Array.isArray(dates) || dates.length < 3 || dates.length > 10000 ||
        dates.some((date, i) => typeof date !== 'string' || !isoDate.test(date) ||
          !Number.isFinite(Date.parse(date)) || (i > 0 && date <= dates[i-1])) ||
        !closes || typeof closes !== 'object') throw Error('Aligned historical market data are required.');
    const rows = symbols.map(symbol => {
      const values = closes[symbol];
      if (!Array.isArray(values) || values.length !== dates.length ||
          values.some(v => !finite(v) || v <= 0)) throw Error('Incomplete or invalid observed prices.');
      return [...values];
    });
    // Numeric representation is the actual in-memory price values used by the model.
    // Property order cannot change the digest: arrays follow the explicit symbols order.
    return {symbols:[...symbols],dates:[...dates],prices:rows};
  }
  function marketManifest(history, run, requestedPeriod) {
    const series = canonicalMarket(history);
    if (!run || !Array.isArray(run.symbols) || run.symbols.join('|') !== series.symbols.join('|') ||
        run.start < series.dates[0] || run.end > series.dates.at(-1) || run.end <= run.start ||
        !Number.isInteger(run.train) || !Number.isInteger(run.step) || run.train < 2 || run.step < 1 ||
        !finite(run.cap) || !finite(run.feeBps) || !finite(run.capital) ||
        (requestedPeriod != null && !/^(?:\d+|\d+\s*(?:days|months|years))$/.test(String(requestedPeriod)))) {
      throw Error('Research inputs do not match the loaded data.');
    }
    return {
      schema:VERSION, researchType:'walkforward', engine:MARKET_MODEL,
      data:{provider:'Alpaca market observations', source:String(history.source || run.source || 'Unspecified'),
        asOf:String(history.as_of || ''), calendar:String(history.calendar || ''),
        annualization:Number(history.sessions_per_year || run.annual),
        symbols:series.symbols, observationCount:series.dates.length,
        observedStart:series.dates[0], observedEnd:series.dates.at(-1),
        requestedPeriod:requestedPeriod == null ? null : String(requestedPeriod),
        adjustment:'Provider-reported historical closes; feed and split-adjustment policy per source',
        excludes:'Dividends, cash distributions, spread, slippage and taxes',
        fingerprintAlgorithm:'SHA-256', fingerprint:sha256(JSON.stringify(series))},
      model:{trainingObservations:run.train, evaluationObservations:run.step,
        objective:run.objective, maxWeight:run.cap, feeBps:run.feeBps,
        startingVirtualCapital:run.capital, evaluationStart:run.start, evaluationEnd:run.end,
        evaluationWindows:run.windows.length},
      integrityNote:'Fingerprint identifies the aligned in-memory observations used for this run. It is not a proof of provider authenticity or independent replay without the original licensed data.'
    };
  }
  function verifyMarketFingerprint(history, manifest) {
    return !!manifest && manifest.schema === VERSION &&
      manifest.data?.fingerprintAlgorithm === 'SHA-256' &&
      manifest.data.fingerprint === sha256(JSON.stringify(canonicalMarket(history)));
  }
  function canonicalSEC(result) {
    if (!result || typeof result.symbol !== 'string' || !Array.isArray(result.historic) ||
        result.historic.length < 2) throw Error('Reported SEC history required.');
    const rows = result.historic.map(x => {
      if (typeof x.date !== 'string' || !isoDate.test(x.date) || !finite(x.revenue) || x.revenue <= 0 ||
          (x.fcf !== null && !finite(x.fcf))) throw Error('Invalid reported SEC baseline.');
      return {date:x.date,revenue:x.revenue,fcf:x.fcf};
    });
    if (rows.some((x,i) => i && x.date <= rows[i-1].date)) throw Error('SEC annual periods must be ordered.');
    return {symbol:result.symbol,rows};
  }
  function forecastRisk(result) {
    const baseline = canonicalSEC(result);
    const scenarios = result.scenarios;
    if (!Array.isArray(scenarios) || scenarios.length !== 3) throw Error('Forecast scenarios unavailable.');
    const reports = scenarios.map(s => {
      const terminalShare = finite(s.proxy) && s.proxy > 0 && finite(s.terminalPV) ?
        s.terminalPV / s.proxy : null;
      return {scenario:s.name, annualGrowth:s.growth, assumedFcfMargin:s.margin,
        discountedExplicitFcf:s.presentPV, discountedTerminal:s.terminalPV,
        totalCashFlowProxy:s.proxy, terminalShare,
        materialTerminalDependence:terminalShare !== null && terminalShare >= 0.60};
    });
    const latest = baseline.rows.at(-1), observedMargin = latest.fcf == null ? null : latest.fcf/latest.revenue;
    const base = reports.find(r => r.scenario === 'Base case');
    return {reportedFiscalYears:baseline.rows.length, observedFcfMargin:observedMargin,
      modelFcfMargin:base?.assumedFcfMargin ?? null,
      marginAssumptionDifferencePp:observedMargin === null || !base ? null :
        (base.assumedFcfMargin - observedMargin) * 100,
      scenarios:reports,
      warnings:[
        ...(reports.some(r => r.materialTerminalDependence) ?
          ['At least one scenario derives 60% or more of its modeled proxy from terminal assumptions.'] : []),
        ...(observedMargin === null ? ['Latest reported free-cash-flow proxy is unavailable.'] : []),
        'The discounted proxy is not enterprise value, equity value, or a per-share price target.'
      ]};
  }
  function secManifest(result) {
    const baseline = canonicalSEC(result);
    return {schema:VERSION, researchType:'forecast', engine:FORECAST_MODEL,
      data:{source:String(result.source || 'SEC EDGAR'), asOf:String(result.asOf || ''),
        symbol:result.symbol, fiscalEnd:result.fiscalEnd,
        reportedFiscalYears:baseline.rows.length, currency:'USD',
        fingerprintAlgorithm:'SHA-256', fingerprint:sha256(JSON.stringify(baseline)),
        excludes:'No capital structure or share count adjustments'},
      model:{projectionYears:result.years,discountRate:result.discount,terminalGrowth:result.terminal,
        scenarios:result.scenarios.map(s=>({name:s.name,annualGrowth:s.growth,fcfMargin:s.margin}))},
      integrityNote:'Fingerprint identifies the reported SEC annual baseline used; it does not authenticate SEC filings or prove forecast accuracy.'};
  }
  function attachWalkforward(exported, history, result, requestedPeriod) {
    if (exported?.type !== 'walkforward') throw Error('Expected a walk-forward report.');
    return {...exported,manifest:marketManifest(history,result,requestedPeriod),
      modelRisk:{evaluationWindows:result.windows.length,
        evaluationObservations:result.dates.length-1,
        flags:[...(result.windows.length < 6 ? ['Fewer than six evaluation windows; small sample.'] : []),
          ...(result.dates.length-1 < 126 ? ['Fewer than 126 out-of-sample observed sessions.'] : []),
          'Selection of assets and parameter tuning on known history may produce selection bias.']}};
  }
  function attachForecast(exported, result) {
    if (exported?.type !== 'forecast') throw Error('Expected a forecast report.');
    return {...exported,manifest:secManifest(result),modelRisk:forecastRisk(result)};
  }
  return {sha256,canonicalMarket,marketManifest,verifyMarketFingerprint,canonicalSEC,
    secManifest,forecastRisk,attachWalkforward,attachForecast};
});
