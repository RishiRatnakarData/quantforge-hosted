"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
require('../site/research_evidence_v26.js');
test('every showcased discipline references existing implementation and reproducible checks', () => {
  assert.equal(globalThis.QFEvidence26.catalog.length, 7);
  for (const discipline of globalThis.QFEvidence26.catalog) {
    for (const file of [...discipline.files, ...discipline.tests]) {
      assert.ok(fs.statSync(path.resolve(__dirname, '../..', file)).isFile(), file);
    }
  }
});
test('scaled accessible plots reject nonfinite or disjoint inputs and escape source text', () => {
  const chart = globalThis.QFCharts26.curve;
  assert.match(chart('test', ['a','b'], [{name:'x',values:[1]}]), /unavailable/);
  assert.match(chart('test', ['a','b'], [{name:'x',values:[1,NaN]}]), /unavailable/);
  const html = chart('<img>', ['2026-01-01','2026-01-02'], [{name:'<script>',values:[.1,.2]}], {format:'percent'});
  assert.ok(!html.includes('<img>') && !html.includes('<script>'));
  assert.match(html, /20\.0%/);
  assert.match(html, /tabindex="0"/);
  assert.match(html, /role="status"/);
});
