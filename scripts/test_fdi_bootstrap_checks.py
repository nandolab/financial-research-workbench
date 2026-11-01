from pathlib import Path
import sys
import numpy as np
import statsmodels.api as sm
import io,json,hashlib,pytest,zipfile
sys.path.insert(0,str(Path(__file__).parent))
from fdi_bootstrap_checks import solve_batch,lp_batch,last_impact_batch,block_indices,invert_t,synthetic,experiment,checkpoint
from fdi.models import fit_system,responses,local_projections
from build_fdi_bootstrap_export import check_result

def test_batched_HC3_matches_statsmodels_without_normal_equations():
 rng=np.random.default_rng(18);x=np.concatenate([np.ones((3,80,1)),rng.normal(size=(3,80,6))],axis=2);y=rng.normal(size=(3,80))
 beta,se,good,_=solve_batch(x,y);assert good.all()
 for i in range(3):
  ref=sm.OLS(y[i],x[i]).fit(cov_type='HC3');assert np.allclose(beta[i],ref.params,atol=1e-12);assert np.isclose(se[i],ref.bse[-1],atol=1e-12)

def test_synthetic_refit_and_scale_match_frozen_estimator():
 y,_=synthetic(119,.5,2,7);z=np.zeros((119,0));model=fit_system(y,z,2);_,B=responses(model,0)
 impact,good=last_impact_batch(y,z,2);assert good.all();assert np.isclose(impact[0],B[-1,-1],atol=1e-12)
 lp=lp_batch(y,z,2,2);ref,_=local_projections(y,z,model,4)
 assert np.isclose(lp['estimate'][0]*impact[0],ref[4,1,2],atol=1e-12)

def test_percentile_t_inversion_uses_the_declared_DGP_center():
 draws=np.array([[1.,1.],[2.,1.],[3.,1.],[4.,1.]])
 a=invert_t(10.,2.,draws,2.);b=invert_t(10.,2.,draws,10.)
 assert a['lower']<a['upper'];assert np.isclose(b['lower']-a['lower'],16.)
 bad=draws.copy();bad[0]=np.nan;assert not invert_t(10,2,bad,2)['available']

def test_blocks_are_consecutive_inside_each_fixed_length():
 rows=block_indices(np.random.default_rng(9),4,80,8).reshape(4,10,8)
 assert np.all((np.diff(rows,axis=2)%80)==1)

def test_bootstrap_replay_is_deterministic_and_checked_before_reuse(tmp_path):
 y,_=synthetic(119,0.,1,2000);z=np.zeros((119,0));model=fit_system(y,z,1)
 fn=lambda:experiment(y,z,model,1,1,19,[88],True)
 a,raw=fn();b,other=fn();assert a==b
 for key in raw:assert np.array_equal(raw[key],other[key])
 first=checkpoint(tmp_path,'sample',fn)
 assert checkpoint(tmp_path,'sample',lambda:(_ for _ in ()).throw(Exception('must skip')))==first

@pytest.fixture
def raw_audit_case():
 y,_=synthetic(119,.5,1,2011);z=np.zeros((119,0));model=fit_system(y,z,1)
 r,raw=experiment(y,z,model,1,1,19,[44],True);stream=io.BytesIO();np.savez_compressed(stream,**raw);b=stream.getvalue()
 canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
 cp={'result':r,'result_sha256':hashlib.sha256(canonical(r)).hexdigest(),'npz_sha256':hashlib.sha256(b).hexdigest()}
 return cp,b,canonical

def test_raw_draw_import_recomputes_the_generator_center(raw_audit_case):
 cp,b,canonical=raw_audit_case;check_result(cp,b,19,True)
 changed=json.loads(json.dumps(cp));changed['result']['targets']['unit']['recursive_wild_t']['center']+=.1
 changed['result_sha256']=hashlib.sha256(canonical(changed['result'])).hexdigest()
 with pytest.raises(AssertionError):check_result(changed,b,19,True)

def test_raw_draw_import_rejects_a_rehashed_wrong_quantile(raw_audit_case):
 cp,b,canonical=raw_audit_case;changed=json.loads(json.dumps(cp));changed['result']['targets']['unit']['block8_t']['q025']+=.05
 changed['result_sha256']=hashlib.sha256(canonical(changed['result'])).hexdigest()
 with pytest.raises(AssertionError):check_result(changed,b,19,True)

def test_public_source_package_contains_only_exact_code_and_no_private_inputs():
 repo=Path(__file__).resolve().parents[1]
 with zipfile.ZipFile(repo/'web/public/data/fdi_bootstrap_source.zip') as z:
  assert z.testzip() is None
  assert set(z.namelist())=={'scripts/fdi_bootstrap_checks.py','scripts/fdi/models.py','scripts/fdi/storage.py','scripts/fdi/__init__.py'}
  for n in z.namelist():assert z.read(n)==(repo/n).read_bytes()
