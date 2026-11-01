import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parseRoute,finite,format,axisTick} from '../src/fdi/types.ts';
test('small positive and negative response ticks retain distinct numeric labels',()=>{
 const values=[-.3,-.25,-.2,-.15,-.1,-.05,0,.05,.1];
 assert.equal(new Set(values.map(axisTick)).size,values.length);
 assert.notEqual(axisTick(.00005),axisTick(.0001));assert.equal(axisTick(0),'0');
});
test('FDI deep links reject invalid model indices and geography before rendering',()=>{
 const {section,params}=parseRoute('#/fdi/effects?year=NaN&shock=99&response=-1&state=../../private&city=x&country=xx');
 assert.equal(section,'effects');for(const key of ['year','shock','response','state','city','country'])assert.equal(params.has(key),false);
 const good=parseRoute('#/fdi/brazil?year=2020&localYear=2021&state=35&city=3550308&shock=0&response=4');assert.equal(good.params.get('state'),'35');assert.equal(good.params.get('shock'),'0');
});
test('numeric presentation preserves actual zero and negative flows and labels unavailable data',()=>{
 assert.equal(finite(null),false);assert.equal(finite(NaN),false);assert.equal(finite(0),true);assert.equal(format(null),'Not available');assert.match(format(-1e9,'USD'),/-/);
});
test('actual source bundle separates observations from unestimated causal effects',()=>{
 const d=JSON.parse(readFileSync(new URL('../public/data/fdi/observatory.json',import.meta.url),'utf8'));
 assert.equal(d.annual.length,new Set(d.annual.map(r=>r.country+':'+r.year)).size);
 assert.ok(d.annual.some(r=>r.flow_usd<0));assert.ok(d.annual.some(r=>r.flow_usd===null));
 if(d.national.state!=='complete')assert.equal(d.national.causal_release_eligible,false);
 if(d.municipal.state!=='complete')assert.equal(d.research_status.complete_causal_study,false);
 assert.ok(d.joint.length>0);assert.ok(d.source_manifest.bcb_positions||Object.keys(d.source_manifest).some(k=>k.includes('position')));
});

import {windowStats,temporalWindow} from '../src/fdi/temporal.ts';
test('time comparisons reject CAGR across missing, nonpositive or incomplete windows',()=>{
 const rows=[{year:2000,x:100},{year:2001,x:121}];
 assert.ok(Math.abs(windowStats(rows,'x',2000,2001).cagr-21)<1e-10);
 assert.equal(windowStats([{year:2000,x:-100},{year:2001,x:121}],'x',2000,2001).cagr,null);
 assert.equal(windowStats([{year:2000,x:0},{year:2001,x:121}],'x',2000,2001).cagr,null);
 assert.equal(windowStats([{year:2000,x:100},{year:2001,x:null},{year:2002,x:121}],'x',2000,2002).cagr,null);
 assert.equal(windowStats(rows,'x',1999,2001).cagr,null);
 assert.equal(windowStats([{year:2000,x:-10},{year:2001,x:5}],'x',2000,2001).change,15);
 assert.deepEqual(temporalWindow(new URLSearchParams('from=2025&to=1996')),{start:1996,end:2025});
});
test('Colab monetary export preserves the nominal snapshot, signs, base year and missing data',()=>{
 const d=JSON.parse(readFileSync(new URL('../public/data/fdi/temporal.json',import.meta.url),'utf8'));
 const b=JSON.parse(readFileSync(new URL('../public/data/fdi/observatory.json',import.meta.url),'utf8'));
 assert.equal(d.parent,b.identity);assert.equal(d.base_year,2025);assert.equal(d.rows.length,b.annual.length);
 for(const row of d.rows){
  const original=b.annual.find(r=>r.country===row.country&&r.year===row.year);
  assert.equal(row.current_usd,original.flow_usd);
  if(row.year===2025&&row.current_usd!==null)assert.ok(Math.abs(row.constant_usd-row.current_usd)<=Math.max(1,Math.abs(row.current_usd))*1e-12);
  if(row.current_usd===null)assert.equal(row.constant_usd,null);
  if(row.current_usd<0)assert.ok(row.constant_usd<0);
  if(row.country!=='BRA')assert.equal(row.constant_brl,null);
 }
 assert.equal(d.rows.filter(r=>r.country==='BRA'&&Number.isFinite(r.constant_brl)).length,30);
});
