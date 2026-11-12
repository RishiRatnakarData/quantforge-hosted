const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const Q=require('../site/research_completion_v28.js'),P=require('../site/investment_picker_v27.js');
const root=path.resolve(__dirname,'../..');
test('SEC quality counts retain zero and negative values and separate source coverage',()=>{
 const snap={companies:[{symbol:'A',as_of:'2026-10-01',annual:[{fiscal_end:'2025-12-31',metrics:{revenue_usd:0,free_cash_flow_usd:-4},sources:{revenue_usd:{accession:'a'},operating_cash_flow_usd:{accession:'a'},capex_usd:{accession:'a'}}}]},{symbol:'B',annual:[]}]};
 const q=Q.quality(snap);assert.equal(q.issuers,2);assert.equal(q.negativeFCF,1);assert.equal(q.withoutAnnual,1);assert.equal(q.missingCutoff,1);assert.equal(q.fields.find(f=>f.key==='revenue_usd').available,1);assert.equal(q.fields.find(f=>f.key==='free_cash_flow_usd').sourced,1);
 assert.equal(Q.quality(JSON.parse(fs.readFileSync(path.join(root,'web/site/sec_snapshot.json'),'utf8'))).issuers,94);
});
test('leveraged name disclosure does not outrank the intended issuer',()=>{
 const fund={symbol:'MSFU',name:'Direxion Daily Microsoft Bull ETF',asset_class:'us_equity'},issuer={symbol:'MSFT',name:'Microsoft Corporation',asset_class:'us_equity'};
 assert.match(P.instrument(fund),/Leveraged/);assert.equal(P.rank([fund,issuer],'Microsoft')[0].symbol,'MSFT');assert.equal(P.rank([fund,issuer],'MSFU')[0].symbol,'MSFU');
});
