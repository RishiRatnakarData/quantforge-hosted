'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../site/private_french_factors_v87.js'),'utf8');
const {parseDailyCsv,assess}=require('../site/private_french_factors_v87.js');
const iso=i=>{const d=new Date(Date.UTC(2023,0,2+i));return d.toISOString().slice(0,10);};
const compact=d=>d.replaceAll('-','');
function fixture(n=440){
 const factors=[];const dates=[];const prices=[100];const peers=[100];
 for(let i=0;i<n;i++){
  const date=iso(i),mkt=.004*Math.sin(i*1.51)+.002*Math.cos(i*.17),smb=.003*Math.cos(i*.71),hml=.003*Math.sin(i*.43);
  const rf=.0001,epsilon=.0003*Math.cos(i*.27);
  const annualRet=.0002+1.24*mkt+.53*smb-.31*hml+rf+epsilon;
  factors.push({date,mkt,smb,hml,rf});dates.push(date);
  if(i>0){prices.push(prices.at(-1)*(1+annualRet));peers.push(peers.at(-1)*(1+.5*mkt));}
 }
 const text=['This file was created for tests, not an official downloaded file.',',Mkt-RF,SMB,HML,RF',
  ...factors.map(x=>[compact(x.date),x.mkt*100,x.smb*100,x.hml*100,x.rf*100].map((v,j)=>j===0?v:Number(v).toFixed(6)).join(','))].join('\n');
 const history={symbols:['TEST','SPY'],dates,closes:{TEST:prices,SPY:peers},sessions_per_year:252,calendar:'equity'};
 return {text,history,factors,selection:['TEST','SPY']};
}
test('parses daily French-style percent CSV, units converted into decimals with provenance caveat',()=>{
 const {text}=fixture();const d=parseDailyCsv(text);
 assert.equal(d.rows.length,440);assert.equal(d.from,iso(0));assert.equal(d.to,iso(439));
 assert.ok(Math.abs(d.rows[4].rf-.0001)<1e-12);assert.match(d.source,/not authenticated/);
});
test('estimates FF3 excess-return loadings and alpha against synthetic known coefficients',()=>{
 const f=fixture(),res=assess({history:f.history,selection:f.selection,symbol:'TEST',factors:parseDailyCsv(f.text)});
 assert.equal(res.ready,true, res.reason);
 assert.ok(Math.abs(res.model.factorBetas[0]-1.24)<.08);
 assert.ok(Math.abs(res.model.factorBetas[1]-.53)<.08);
 assert.ok(Math.abs(res.model.factorBetas[2]+.31)<.08);
 assert.ok(Math.abs(res.model.alphaDaily-.0002)<.0001);
 assert.ok(res.model.alphaAnnualCi95[0]<res.model.alphaAnnualCi95[1]);
 assert.ok(res.model.r2>.95);assert.ok(res.holdout.train>=126);assert.ok(res.holdout.test>=60);
 assert.equal(res.model.hacLag,5);
});
test('chronological holdout is separate from training and reports ex-post factor exposure, not trading forecast',()=>{
 const f=fixture(),res=assess({history:f.history,selection:f.selection,symbol:'TEST',factors:parseDailyCsv(f.text)});
 assert.ok(res.holdout.trainThrough<res.holdout.testFrom);
 assert.ok(res.holdout.testThrough<=res.to);
 assert.match(res.holdout.interpretation,/NOT an executable return forecast/);
 assert.ok(Number.isFinite(res.holdout.r2));
});
test('exact-date joins omit missing factor dates, do not forward-fill',()=>{
 const f=fixture();const lines=f.text.split('\n');const drop=iso(175).replaceAll('-','');
 const changed=lines.filter(l=>!l.startsWith(drop+',' )).join('\n');
 const res=assess({history:f.history,selection:f.selection,symbol:'TEST',factors:parseDailyCsv(changed)});
 assert.equal(res.ready,true);assert.equal(res.excludedPrices,1);
});
test('monthly data, duplicates, malformed units and invalid dates are rejected',()=>{
 const f=fixture(),rows=f.text.split('\n');
 assert.throws(()=>parseDailyCsv(',Mkt-RF,SMB,HML,RF\n202301,1,2,3,0.01'),/At least 200/);
 assert.throws(()=>parseDailyCsv(rows.concat(rows[8]).join('\n')),/Duplicate/);
 assert.throws(()=>parseDailyCsv(f.text.replace(/\d{8},/, '20231345,')),/Invalid/);
 assert.throws(()=>parseDailyCsv(f.text.replace(/,0\.01\d*\n/,',999\n')),/Expected|Factor/);
});
test('FF missing code is excluded, not silently zero-filled',()=>{
 const f=fixture(),lines=f.text.split('\n');
 const row=lines[17].split(',');assert.equal(row.length,5);row[4]='-99.99';lines[17]=row.join(',');
 const d=parseDailyCsv(lines.join('\n'));
 assert.equal(d.missing,1);
 assert.equal(d.rows.length,439);
 assert.ok(!d.rows.some(x=>x.date===iso(15)));
});
test('crypto and mixed calendars are withheld',()=>{
 const f=fixture(),factor=parseDailyCsv(f.text);
 for(const calendar of ['mixed','crypto'])assert.match(assess({history:{...f.history,calendar},selection:f.selection,symbol:'TEST',factors:factor}).reason,/crypto or mixed/);
 assert.match(assess({history:{...f.history,sessions_per_year:365},selection:f.selection,symbol:'TEST',factors:factor}).reason,/crypto or mixed/);
});
test('stale selection, missing imported data and insufficient matches are withheld',()=>{
 const f=fixture(),factor=parseDailyCsv(f.text),base={history:f.history,selection:f.selection,symbol:'TEST',factors:factor};
 assert.match(assess({...base,selection:['TEST','QQQ']}).reason,/matching/);
 assert.match(assess({...base,factors:null}).reason,/Import/);
 const shifted={...f.history,dates:f.history.dates.map((_,i)=>iso(1000+i))};
 assert.match(assess({...base,history:shifted}).reason,/matching daily/);
});
test('factor calculations are pure and do not reach network, browser storage or trading APIs',()=>{
 assert.doesNotMatch(source, /\b(fetch|XMLHttpRequest|localStorage|sessionStorage|WebSocket)\s*\(/);
 assert.doesNotMatch(source, /\b(?:broker|placeOrder|submitTrade|api)\s*\(/i);
 assert.match(source,/Newey/);
});
