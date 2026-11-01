import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
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

test('teaching metadata is tied to the unchanged result snapshot and preserves claim boundaries',()=>{
 const d=JSON.parse(readFileSync(new URL('../public/data/fdi/transparency.json',import.meta.url),'utf8'));
 const b=JSON.parse(readFileSync(new URL('../public/data/fdi/observatory.json',import.meta.url),'utf8'));
 assert.equal(d.parent,b.identity);assert.equal(d.papers.length,10);assert.equal(new Set(d.papers.map(p=>p.doi)).size,10);
 assert.ok(d.papers.every(p=>p.year>=2020&&p.application&&p.scope));
 assert.equal(d.books.length,3);assert.match(d.hypothesis_status,/not a claim of preregistration/);
 const r=d.gdp_response_to_fdi;assert.equal(r.estimate,b.national.irf[4][1][4]);
 assert.equal(r.lower,b.national.irf_intervals['0.025'][4][1][4]);assert.equal(r.upper,b.national.irf_intervals['0.975'][4][1][4]);
 assert.ok(r.lower<0&&r.upper>0);assert.match(d.supersession.active_municipal,/no empirical municipal ATT/);
 const nb=JSON.parse(readFileSync(new URL('../public/data/brazil_fdi_robustness.ipynb',import.meta.url),'utf8'));
 assert.equal(nb.metadata.research_status,'prepared_not_executed');
 assert.ok(nb.cells.filter(c=>c.cell_type==='code').every(c=>c.execution_count===null&&c.outputs.length===0));
 assert.ok(nb.cells.some(c=>c.source.join('').includes('RUN_NEW_CHECKS=False')));
});

test('completed sensitivity export preserves baseline points and separates synthetic evidence',()=>{
 const r=JSON.parse(readFileSync(new URL('../public/data/fdi/robustness.json',import.meta.url),'utf8'));
 const b=JSON.parse(readFileSync(new URL('../public/data/fdi/observatory.json',import.meta.url),'utf8'));
 assert.equal(r.parent,b.identity);assert.equal(r.state,'complete');assert.equal(r.baseline_bootstrap_rerun,false);
 assert.equal(r.saved_draws.new_draws,0);assert.equal(r.saved_draws.saved_draws,2000);assert.equal(r.validation.mc_checkpoints_reconciled,8000);
 assert.ok(r.validation.baseline_lp_max_abs_difference<1e-10);assert.equal(r.simulation.synthetic,true);
 assert.deepEqual(r.lp.specifications.map(s=>s.extra_lags),[0,1,2]);
 assert.ok(r.lp.specifications.every(s=>s.pointwise_95_hac[4][1][4][0]<0&&s.pointwise_95_hac[4][1][4][1]>0));
 assert.ok(r.lp.specifications[0].irf[4][1][4]<0&&r.lp.specifications[1].irf[4][1][4]>0);
 for(let h=0;h<13;h++)assert.ok(Math.abs(r.baseline.unit_gdp_growth[h]-b.national.irf[h][1][4]/r.baseline.impact_fdi_pp)<1e-12);
 for(const c of r.simulation.cells){assert.equal(c.valid+c.failures,c.requested);assert.equal(c.requested,1000);assert.ok(c.conditional_coverage<.95);assert.ok(c.mcse>0)}
 assert.ok(r.saved_draws.gdp_level_pointwise_95['0.025'][4]<0&&r.saved_draws.gdp_level_pointwise_95['0.975'][4]>0);
 assert.match(r.interpretation,/not new causal identification/);
});
test('sensitivity deep links validate selections and reject malformed controls',()=>{
 const bad=parseRoute('#/fdi/methods?lpExtra=5&responseView=nominal-causal-effect');assert.equal(bad.params.has('lpExtra'),false);assert.equal(bad.params.has('responseView'),false);
 const good=parseRoute('#/fdi/methods?lpExtra=2&responseView=unit-growth');assert.equal(good.params.get('lpExtra'),'2');assert.equal(good.params.get('responseView'),'unit-growth');
});

test('inference follow-up deep links validate methods and common-sample lag choices',()=>{
 const bad=parseRoute('#/fdi/methods?followLag=7&intervalMethod=causality-fixed&calibrationSample=brazil-truth');
 for(const key of ['followLag','intervalMethod','calibrationSample'])assert.equal(bad.params.has(key),false);
 const good=parseRoute('#/fdi/methods?followLag=4&intervalMethod=hc3_t&calibrationSample=holdout');
 assert.equal(good.params.get('followLag'),'4');assert.equal(good.params.get('intervalMethod'),'hc3_t');assert.equal(good.params.get('calibrationSample'),'holdout');
});

test('bootstrap deep links accept stated methods and reject invented causal fixes',()=>{
 for(const method of ['hc3_t','recursive_wild_t','block4_t','block8_t'])assert.equal(parseRoute('#/fdi/methods?bootMethod='+method).params.get('bootMethod'),method);
 assert.equal(parseRoute('#/fdi/methods?bootMethod=causal-certification').params.has('bootMethod'),false);
});

test('bootstrap reproduction template is gated, unexecuted and tied to the exact source ZIP',()=>{
 const n=JSON.parse(readFileSync(new URL('../public/data/brazil_fdi_bootstrap.ipynb',import.meta.url),'utf8'));
 assert.equal(n.metadata.research_status,'prepared_not_executed');
 assert.ok(n.cells.filter(c=>c.cell_type==='code').every(c=>c.execution_count===null&&c.outputs.length===0));
 const text=n.cells.map(c=>c.source.join('')).join('\n');
 assert.match(text,/RUN_NEW_BOOTSTRAP=False/);assert.match(text,/EMPIRICAL_BACKUP_VERIFIED=False/);
 assert.doesNotMatch(text,/fernando\.liaison|base64\.b64decode|1M1WuRl8/);
 const source=readFileSync(new URL('../public/data/fdi_bootstrap_source.zip',import.meta.url));
 assert.equal(createHash('sha256').update(source).digest('hex'),n.metadata.frozen_source_zip_sha256);
});

test('completed bootstrap evidence preserves points, proper centers and causal limits',()=>{
 const d=JSON.parse(readFileSync(new URL('../public/data/fdi/bootstrap.json',import.meta.url),'utf8'));
 const prior=JSON.parse(readFileSync(new URL('../public/data/fdi/inference-followup.json',import.meta.url),'utf8'));
 assert.equal(d.state,'complete');assert.equal(d.parent,prior.parent);assert.equal(d.prior_inference_export,prior.identity);
 assert.equal(d.causal_identification_validated,false);assert.equal(d.preservation.original_2000_bootstrap_rerun,false);assert.equal(d.preservation.Financial_Intelligence_rerun,false);
 assert.equal(d.validation.outer_checkpoints,4000);assert.equal(d.validation.percentile_t_bounds_recomputed,true);assert.equal(d.validation.packet_count,10);
 assert.equal(d.configuration.empirical_B,1999);assert.equal(d.configuration.MC_B,499);assert.deepEqual(d.randomization.fresh_outer_ids,[2000,2499]);
 assert.deepEqual(d.empirical.rows.map(r=>r.p),[1,2,3,4]);
 for(const r of d.empirical.rows){
  assert.equal(r.n,111);const u=r.targets.unit;const old=prior.empirical.rows.find(v=>v.p===r.p&&v.h===4);
  assert.ok(Math.abs(u.estimate-old.intervals.hc3_t.estimate)<1e-10);
  assert.ok(Math.abs(u.se-old.intervals.hc3_t.se)<1e-10);
  for(const method of ['recursive_wild_t','block4_t','block8_t']){const ci=u[method];assert.equal(ci.available,true);assert.equal(ci.valid+ci.failures,1999);assert.ok(ci.lower<0&&ci.upper>0);assert.ok(ci.q025<ci.q975)}
  assert.ok(Math.abs(u.recursive_wild_t.center-u.estimate)>1e-8);assert.equal(u.block4_t.center,u.estimate);assert.equal(u.block8_t.center,u.estimate);
 }
 assert.equal(d.calibration.cells.length,8);
 for(const c of d.calibration.cells){assert.equal(c.replications,500);assert.deepEqual(Object.keys(c.targets.sd).sort(),['hc3_t','recursive_wild_t']);for(const target of Object.values(c.targets))for(const s of Object.values(target)){assert.equal(s.valid+s.unavailable,500);if(s.coverage!==null){assert.ok(s.coverage>=0&&s.coverage<=1);assert.ok(s.mcse>=0);assert.ok(s.mean_width>0)}}}
});

test('completed follow-up preserves evidence and reports unresolved calibration',()=>{
 const d=JSON.parse(readFileSync(new URL('../public/data/fdi/inference-followup.json',import.meta.url),'utf8'));
 const b=JSON.parse(readFileSync(new URL('../public/data/fdi/observatory.json',import.meta.url),'utf8'));
 assert.equal(d.parent,b.identity);assert.equal(d.state,'complete');assert.equal(d.validation.checkpoints_reconciled,12000);
 assert.equal(d.preservation.baseline_rerun,false);assert.equal(d.preservation.original_bootstrap_rerun,false);
 assert.equal(d.empirical.rows.length,52);assert.ok(d.empirical.normalization_equivalence_max_abs_difference<1e-9);
 const h4=d.empirical.rows.filter(r=>r.h===4);assert.deepEqual(h4.map(r=>r.n),[111,111,111,111]);assert.deepEqual(h4.map(r=>r.k),[16,21,26,31]);
 for(const r of h4)assert.ok(r.intervals.hac_corrected_t.lower<0&&r.intervals.hac_corrected_t.upper>0);
 assert.ok(h4.some(r=>r.intervals.hac_corrected_t.estimate<0)&&h4.some(r=>r.intervals.hac_corrected_t.estimate>0));
 assert.equal(d.calibration.cells.length,12);
 for(const c of d.calibration.cells){for(const score of Object.values(c.methods)){assert.equal(score.valid,1000);assert.equal(score.failures,0);assert.ok(score.mcse>0);assert.ok(score.mean_width>0)}}
 const holdout=d.calibration.cells.filter(c=>c.sample==='holdout');assert.equal(holdout.length,4);
 for(const c of holdout){assert.ok(c.methods.hac_corrected_t.coverage<.95);assert.ok(c.methods.hc3_t.coverage>c.methods.legacy_hac_normal.coverage);assert.ok(c.methods.hc3_t.mean_width>c.methods.legacy_hac_normal.mean_width);assert.ok(c.methods.oracle_hac_corrected_t.coverage<.95)}
});
