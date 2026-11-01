"""Audit every new raw bootstrap draw and export only aggregate evidence."""
from pathlib import Path
import argparse,hashlib,io,json,math
import numpy as np
from scipy.stats import t as student_t
from build_fdi_robustness_export import read_archive,PARENT,PACKAGES
from fdi_bootstrap_checks import CONFIG,BASELINE,PRIOR,canonical
REPO=Path(__file__).resolve().parents[1]
def digest(b):return hashlib.sha256(b).hexdigest()
def near(a,b):
 if b is None:assert a is None;return
 assert isinstance(a,(int,float)) and math.isfinite(a) and math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-10),(a,b)
def expected_interval(point,se,raw,center):
 valid=np.isfinite(raw).all(axis=1)&(raw[:,1]>1e-12);n=int(valid.sum())
 result={'available':n>=math.ceil(.95*len(raw)),'valid':n,'failures':len(raw)-n}
 if result['available']:
  q=np.quantile((raw[valid,0]-center)/raw[valid,1],[.025,.975],method='linear')
  result.update(center=float(center),q025=float(q[0]),q975=float(q[1]),lower=float(point-se*q[1]),upper=float(point-se*q[0]))
 return result
def check_result(cp,npz_bytes,B,sd=False):
 r=cp['result'];assert cp['result_sha256']==digest(canonical(r)) and cp['npz_sha256']==digest(npz_bytes)
 if 'failure' in r:return r,0
 assert r['B']==B and r['n']-r['k']==r['df'] and 0<r['maximum_leverage']<1
 A=np.asarray(r['generator_A']);assert np.isfinite(A).all();p,k,_=A.shape;comp=np.zeros((p*k,p*k));comp[:k,:]=np.hstack(A)
 if p>1:comp[k:,:-k]=np.eye((p-1)*k)
 radius=float(np.max(np.abs(np.linalg.eigvals(comp))));near(r['training_radius'],radius);assert r['training_unstable']==(radius>=1)
 phi=[np.eye(k)]
 for h in range(1,5):phi.append(sum((A[l-1]@phi[h-l] for l in range(1,min(p,h)+1)),np.zeros((k,k))))
 unit=float(phi[4][1,-1]);cov=np.asarray(r['generator_HC2_covariance']);assert np.isfinite(cov).all() and np.allclose(cov,cov.T,atol=1e-12);impact=float(np.linalg.cholesky(cov)[-1,-1])
 with np.load(io.BytesIO(npz_bytes),allow_pickle=False) as f:
  names={'wild_unit','block4_unit','block8_unit'}|({'wild_sd'} if sd else set());assert set(f.files)==names
  draws={key:f[key] for key in names}
 for raw in draws.values():assert raw.shape==(B,2) and raw.dtype==np.dtype('float64')
 for target in (['unit','sd'] if sd else ['unit']):
  values=r['targets'][target];estimate,se=values['estimate'],values['se'];assert math.isfinite(estimate) and math.isfinite(se) and se>0
  crit=float(student_t.ppf(.975,r['df']));ref=values['hc3_t'];assert ref['available'];near(ref['lower'],estimate-crit*se);near(ref['upper'],estimate+crit*se)
  for method,array,center in [('recursive_wild_t','wild_'+target,unit*(impact if target=='sd' else 1)),*([('block4_t','block4_unit',estimate),('block8_t','block8_unit',estimate)] if target=='unit' else [])]:
   actual=values[method];expected=expected_interval(estimate,se,draws[array],center)
   assert set(actual)==set(expected)
   for key,v in expected.items():
    if isinstance(v,bool):assert actual[key]==v
    else:near(actual[key],v)
 if sd:
  near(r['targets']['sd']['estimate'],r['targets']['unit']['estimate']*r['original_SD_impact']);near(r['targets']['sd']['se'],r['targets']['unit']['se']*r['original_SD_impact'])
  u,s=draws['wild_unit'],draws['wild_sd'];ok=np.isfinite(u).all(axis=1)&np.isfinite(s).all(axis=1)&(u[:,1]>1e-12)
  scaling=s[ok,1]/u[ok,1];assert (scaling>0).all();assert np.allclose(s[ok,0],u[ok,0]*scaling,rtol=1e-8,atol=1e-10)
  assert np.ptp(scaling)>1e-8,'Synthetic first-stage SD unexpectedly held fixed'
 return r,sum(len(a) for a in draws.values())

def recalc(rows,target,method):
 good=[r for r in rows if 'failure' not in r and r['targets'][target][method]['available']]
 flags=np.array([r['targets'][target][method]['lower']<=r['truth'][target]<=r['targets'][target][method]['upper'] for r in good],float)
 ref=np.array([r['targets'][target]['hc3_t']['lower']<=r['truth'][target]<=r['targets'][target]['hc3_t']['upper'] for r in good],float);delta=flags-ref
 coverage=float(flags.mean()) if len(flags) else None
 return {'requested':len(rows),'valid':len(good),'unavailable':len(rows)-len(good),'coverage':coverage,
  'mcse':float(np.sqrt(coverage*(1-coverage)/len(good))) if good else None,
  'mean_width':float(np.mean([r['targets'][target][method]['upper']-r['targets'][target][method]['lower'] for r in good])) if good else None,
  'bias':float(np.mean([r['targets'][target]['estimate']-r['truth'][target] for r in good])) if good else None,
  'paired_coverage_difference_vs_HC3':float(delta.mean()) if good else None,
  'paired_difference_mcse':float(delta.std(ddof=1)/np.sqrt(len(delta))) if len(delta)>1 else None,
  'invalid_inner_draws':sum(r['targets'][target][method].get('failures',0) for r in rows if 'failure' not in r)}

def validate(summary_path):
 summary_path=Path(summary_path);members=read_archive(summary_path.read_bytes());plan=json.loads(members['plan.json']);spec=plan['specification']
 assert plan['identity']==digest(canonical(spec)) and spec['config']==CONFIG and spec['baseline']==BASELINE and spec['prior_export']==PRIOR and spec['versions']==PACKAGES
 assert spec['source_sha256']==digest(members['source.py'])==digest((REPO/'scripts/fdi_bootstrap_checks.py').read_bytes())
 assert spec['frozen_models_sha256']==digest((REPO/'scripts/fdi/models.py').read_bytes())
 for stage in ['empirical','calibration']:
  status=json.loads(members[stage+'-status.json']);assert status['state']=='complete' and status['sha256']==digest(members[stage+'.json'])
 emp=json.loads(members['empirical.json']);cal=json.loads(members['calibration.json']);assert emp['state']==cal['state']=='complete' and cal['outer_replications']==4000 and len(cal['cells'])==8
 assert emp['original_2000_draws_rerun'] is False and cal['causal_identification_validated'] is False
 receipts={json.loads(b)['packet']:json.loads(b) for n,b in members.items() if n.startswith('receipt-')}
 expected={'empirical'}|{f'n{n}-ma{ma}-p{p}' for n in [119,240] for ma in [0.,.5] for p in [1,2]};assert set(receipts)==expected
 packages={};draw_count=0;outer_count=0
 prior=json.loads((REPO/'web/public/data/fdi/inference-followup.json').read_bytes());assert prior['identity']==PRIOR
 for name,receipt in receipts.items():
  assert receipt['file']==plan['identity'][:16]+'-'+name+'.zip','Unexpected packet path'
  path=summary_path.parent/receipt['file'];raw=path.read_bytes();assert digest(raw)==receipt['sha256'] and len(raw)==receipt['bytes']
  packet=read_archive(raw);assert len(packet)==receipt['members'] and packet['plan.json']==members['plan.json'] and packet['source.py']==members['source.py'];packages[name]=packet
 empirical=packages['empirical'];assert len(emp['rows'])==4 and [r['p'] for r in emp['rows']]==[1,2,3,4]
 for row in emp['rows']:
  p=row['p'];cp=json.loads(empirical[f'empirical/p{p}.json']);r,draws=check_result(cp,empirical[f'empirical/p{p}.npz'],1999);draw_count+=draws
  assert r=={k:v for k,v in row.items() if k not in ['p','baseline_coefficients_reused']}
  assert r['n']==111 and r['k']==11+5*p and row['baseline_coefficients_reused']==(p==1)
  original=next(v for v in prior['empirical']['rows'] if v['p']==p and v['h']==4)
  near(r['targets']['unit']['estimate'],original['intervals']['hc3_t']['estimate']);near(r['targets']['unit']['se'],original['intervals']['hc3_t']['se'])
 for cell in cal['cells']:
  name=cell['name'];n,ma,p=cell['n'],cell['ma'],cell['p'];assert name==f'n{n}-ma{ma}-p{p}' and name in expected
  packet=packages[name];json_names={x for x in packet if x.startswith('mc/') and x.endswith('.json')};npz_names={x for x in packet if x.startswith('mc/') and x.endswith('.npz')}
  assert json_names=={f'mc/{name}/{r:05}.json' for r in range(2000,2500)} and npz_names=={x[:-5]+'.npz' for x in json_names}
  rows=[]
  A=np.array([[.65,0,0],[.1,.45,.05],[.05,.12,.35]]);B=np.array([[1.,0,0],[.2,.8,0],[.1,.15,.6]])
  truth=float((np.linalg.matrix_power(A,4)@B+ma*np.linalg.matrix_power(A,3)@B)[1,2])
  for rep in range(2000,2500):
   base=f'mc/{name}/{rep:05}';cp=json.loads(packet[base+'.json']);r,count=check_result(cp,packet[base+'.npz'],499,True);draw_count+=count;outer_count+=1
   assert r['replication']==rep
   if 'failure' not in r:
    near(r['truth']['sd'],truth);near(r['truth']['unit'],truth/.6);assert r['n']==n-p-4 and r['k']==4+3*p
   rows.append(r)
  assert cell['training_unstable']==sum(r.get('training_unstable',False) for r in rows)
  for target,methods in [('unit',CONFIG['methods']),('sd',['hc3_t','recursive_wild_t'])]:
   assert set(cell['targets'][target])==set(methods)
   for method in methods:
    actual=cell['targets'][target][method];want=recalc(rows,target,method);assert set(actual)==set(want)
    for key,v in want.items():near(actual[key],v)
 assert outer_count==4000
 public={'state':'complete','parent':PARENT,'prior_inference_export':PRIOR,'run_identity':plan['identity'],'configuration':CONFIG,'randomization':{'outer_DGP_base_seed':20261031,'inner_bootstrap_base_seed':20261101,'fresh_outer_ids':[2000,2499],'identity':'method/design/draw indices enter SeedSequence; batch boundaries do not change draws'},'empirical':emp,'calibration':cal,'backup_packets':[{k:v for k,v in r.items() if k!='file'} for r in receipts.values()],
 'validation':{'outer_checkpoints':outer_count,'raw_estimate_SE_pairs_audited':draw_count,'percentile_t_bounds_recomputed':True,'packet_count':len(receipts)+1,'summary_sha256':digest(summary_path.read_bytes()),'all_CRC_and_member_hashes':True},'preservation':{'baseline_VAR_rerun':False,'original_2000_bootstrap_rerun':False,'Financial_Intelligence_rerun':False},'causal_identification_validated':False}
 public['identity']=digest(canonical(public));return public
def main():
 ap=argparse.ArgumentParser();ap.add_argument('summary',type=Path);ap.add_argument('--output',type=Path,default=REPO/'web/public/data/fdi/bootstrap.json');a=ap.parse_args();d=validate(a.summary);a.output.write_bytes(canonical(d));print(json.dumps({'identity':d['identity'],'validation':d['validation']}))
if __name__=='__main__':main()
