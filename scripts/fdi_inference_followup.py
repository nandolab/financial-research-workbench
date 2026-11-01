"""Versioned follow-up: common-sample LP lags and paired interval calibration.

No call to national_models; no original estimate/checkpoint is overwritten.
This is an exploratory follow-up designed AFTER observing the first study.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile, platform
from pathlib import Path
import numpy as np
import pandas as pd
import scipy, statsmodels
from scipy.stats import t as student_t
import statsmodels.api as sm
from fdi.models import design, fit_system, responses

SEED=20261031
BASELINE={'prepared/quarterly.csv':'10426ad1fef8fcec3a53ff94c1753d289de4faf908437b1ffc787ac3b0d56b8a',
          'models/national.json':'eee06465aa0c4ee366e2476d1083902a4f3a3d1a7713d843e2ad239666a0cc82'}
OLD_SHA='febed2908f6230fd091818f8e4f8ca58e3cd14d549d7f3cf2f2f729e5b0ad134'
COMPACT_SHA='58111b26f48fe8b6c17decda64518c668b8cabe06f6b86a5702d0f60c273001d'
CONFIG={'version':1,'seed':SEED,'horizons':list(range(13)),'empirical_lags':[1,2,3,4],
 'empirical_start':4,'empirical_target':'GDP growth pp per +1 pp FDI/GDP impact; FDI last recursive ordering',
 'paired_replications':1000,'holdout_replications':1000,'holdout_ids':[1000,1999],
 'simulation_horizon':4,'simulation_n':[119,240],'simulation_ma':[0.,.5],'simulation_p':[1,2],
 'methods':['legacy_hac_normal','hac_corrected_normal','hac_corrected_t','hc3_t','oracle_hac_corrected_t'],
 'decision':'Report every cell, failures, width, bias, paired differences and MC uncertainty; select no winner from these results.',
 'limits':'Pointwise only. HC3-t is a finite-sample sensitivity, not an exact test. MA misspecification/identification remain. No empirical causal certification.',
 'references':['https://doi.org/10.3982/ECTA18756','https://doi.org/10.1016/j.jeconom.2024.105722',
 'https://www.statsmodels.org/v0.14.5/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html']}

def canon(x):return json.dumps(x,sort_keys=True,allow_nan=False,separators=(',',':')).encode()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_bytes(canon(x));q.replace(p)
def read(p):return json.loads(Path(p).read_bytes())
def checked_zip(path,expected=None):
 if expected:assert sha(path)==expected,'Archive hash mismatch'
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
  manifest=json.loads(z.read('file-manifest.json'))
  assert set(z.namelist())==set(manifest)|{'file-manifest.json'}
  for n,h in manifest.items():
   assert not Path(n).is_absolute() and '..' not in Path(n).parts
   assert hashlib.sha256(z.read(n)).hexdigest()==h,'Member hash mismatch'
  return {n:z.read(n) for n in manifest}
def preserved(run):
 result={n:sha(run/n) for n in BASELINE};assert result==BASELINE,'Baseline hash mismatch';return result
def legacy_members(old):
 if sha(old)==OLD_SHA:return checked_zip(old,OLD_SHA)
 compact=checked_zip(old,COMPACT_SHA);data=json.loads(compact['legacy-paired.json'])
 assert data['parent_archive_sha256']==OLD_SHA and len(data['records'])==8000
 return {n:canon({'result':v}) for n,v in data['records'].items()}
def make_plan(run,old,dest):
 assert not Path(dest).resolve().is_relative_to(Path(run).resolve())
 preserved(run);legacy_members(old)
 spec={'config':CONFIG,'baseline':BASELINE,'previous_archive':OLD_SHA,'paired_input_sha256':sha(old),'source':sha(__file__),
       'models_source':sha(Path(__file__).parent/'fdi/models.py'),
       'versions':{'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'statsmodels':statsmodels.__version__}}
 identity=hashlib.sha256(canon(spec)).hexdigest();root=Path(dest)/identity[:16];root.mkdir(parents=True,exist_ok=True)
 doc={'identity':identity,'specification':spec,'designed_after_previous_findings':True}
 if (root/'plan.json').exists():assert read(root/'plan.json')==doc
 else:save(root/'plan.json',doc);(root/'source.py').write_bytes(Path(__file__).read_bytes())
 return root
def ols_intervals(target,x,index,h,p):
 assert np.linalg.matrix_rank(x)==x.shape[1], 'Rank-deficient LP'
 f=sm.OLS(target,x).fit();estimate=float(f.params[index]);df=int(f.df_resid);critical=float(student_t.ppf(.975,df))
 out={}
 for name,cov,correction,crit in [('legacy_hac_normal','HAC',False,1.96),('hac_corrected_normal','HAC',True,1.96),('hac_corrected_t','HAC',True,critical),('hc3_t','HC3',False,critical)]:
  kw={'maxlags':h+p,'use_correction':correction} if cov=='HAC' else {}
  r=f.get_robustcov_results(cov_type=cov,**kw);se=float(r.bse[index]);assert np.isfinite(se) and se>0
  out[name]={'estimate':estimate,'se':se,'lower':estimate-crit*se,'upper':estimate+crit*se}
 return out,{'n':len(target),'k':x.shape[1],'df':df,'max_leverage':float(f.get_influence().hat_matrix_diag.max()),'condition':float(np.linalg.cond(x))}
def empirical(run):
 preserved(run);m=read(run/'models/national.json');frame=pd.read_csv(run/'prepared/quarterly.csv',index_col=0)
 y=frame[m['variables']].to_numpy(float);z=np.column_stack([frame[['us_gdp_growth','fedfunds_change']],pd.get_dummies(frame.quarter,drop_first=True).astype(float)])
 B=np.asarray(m['impact_matrix']);beta=np.asarray(m['coefficients']);p0=m['lag'];u=y[p0:]-design(y,z,p0)@beta;eps=np.linalg.solve(B,u.T).T
 out=[];equivalence=0.
 for p in CONFIG['empirical_lags']:
  for h in CONFIG['horizons']:
   start=CONFIG['empirical_start'];n=len(y)-start-h
   x=np.column_stack([design(y,z,p,start),y[start:]])[:n]
   values,diagnostic=ols_intervals(y[start+h:start+h+n,1],x,-1,h,p)
   # Exact algebraic comparison: all current variables versus all baseline innovations.
   xs=np.column_stack([design(y,z,p,start),eps[start-p0:]])[:n]
   coef=np.linalg.lstsq(xs,y[start+h:start+h+n,1],rcond=None)[0][-1]/B[-1,-1]
   equivalence=max(equivalence,abs(coef-values['hc3_t']['estimate']))
   if h==0:
    values={key:{'estimate':0.,'se':0.,'lower':0.,'upper':0.} for key in values}
   out.append({'p':p,'h':h,'first_predictor_quarter':frame.index[start],'last_predictor_quarter':frame.index[start+n-1],
               'last_outcome_quarter':frame.index[start+h+n-1],'impact_zero_imposed':h==0,'intervals':values,**diagnostic})
 assert equivalence<1e-9;preserved(run)
 return {'state':'complete','rows':out,'normalization_equivalence_max_abs_difference':equivalence,
 'baseline_impact_fdi_pp':float(B[-1,-1]),'target':CONFIG['empirical_target'],
 'formula':'g[t+h] = a[h] + b[h] FDI[t] + c[h] other_current_y[t] + sum(Phi[h,l] y[t-l]) + Gamma[h] z[t] + e[t+h]',
 'boundary':'Current GDP, GFCF, NFCI and REER are identification controls under the FDI-last ordering, not empirically certified confounders. Same sample within each horizon. No lag selected for its sign. Unit-impact normalization eliminates estimated SD scaling for this last-ordered shock; causal identification remains an assumption.'}
def synthetic_data(n,theta,p,rep):
 rng=np.random.default_rng(np.random.SeedSequence([SEED,n,int(theta*100),p,rep]))
 A=np.array([[.65,0,0],[.10,.45,.05],[.05,.12,.35]]);B=np.array([[1.,0,0],[.2,.8,0],[.1,.15,.6]])
 e=rng.normal(size=(n+501,3));y=np.zeros_like(e)
 for s in range(1,len(y)):y[s]=A@y[s-1]+B@e[s]+theta*B@e[s-1]
 truth=float((np.linalg.matrix_power(A,4)@B+theta*np.linalg.matrix_power(A,3)@B)[1,2])
 return y[501:],e[501:],truth
def replication(n,theta,p,rep,legacy=None):
 y,e,truth=synthetic_data(n,theta,p,rep);z=np.zeros((n,0));model=fit_system(y,z,p)
 if model['radius']>=1:return {'failure':'unstable fitted synthetic VAR'}
 _,B=responses(model,0);eps=np.linalg.solve(B,model['residuals'].T).T
 h=4;length=n-p-h;lag=design(y,z,p)
 xx=np.column_stack([lag,eps])[:length];values,diag=ols_intervals(y[p+h:,1],xx,-1,h,p)
 if legacy is not None:
  assert abs(legacy['estimate']-values['legacy_hac_normal']['estimate'])<1e-10,'Paired estimate differs'
  assert abs(legacy['se']-values['legacy_hac_normal']['se'])<1e-10,'Paired SE differs'
  assert abs(truth-legacy['truth'])<1e-14
 oracle,_=ols_intervals(y[p+h:,1],np.column_stack([lag,e[p:]])[:length],-1,h,p)
 values['oracle_hac_corrected_t']=oracle['hac_corrected_t']
 for v in values.values():v['covered']=bool(v['lower']<=truth<=v['upper'])
 return {'truth':truth,'methods':values,'diagnostic':diag,'legacy_paired':legacy is not None}
def summarize(rows):
 valid=[r for r in rows if 'failure' not in r];result={}
 for method in CONFIG['methods']:
  flags=np.array([r['methods'][method]['covered'] for r in valid],float)
  baseline=np.array([r['methods']['legacy_hac_normal']['covered'] for r in valid],float)
  delta=flags-baseline;coverage=float(flags.mean()) if len(flags) else None
  result[method]={'valid':len(valid),'failures':len(rows)-len(valid),'coverage':coverage,
   'mcse':float(np.sqrt(coverage*(1-coverage)/len(flags))) if len(flags) else None,
   'coverage_difference':float(delta.mean()) if len(flags) else None,
   'paired_difference_mcse':float(delta.std(ddof=1)/np.sqrt(len(flags))) if len(flags)>1 else None,
   'mean_width':float(np.mean([r['methods'][method]['upper']-r['methods'][method]['lower'] for r in valid])) if valid else None,
   'bias':float(np.mean([r['methods'][method]['estimate']-r['truth'] for r in valid])) if valid else None}
 return result
def calibration(root,old):
 members=legacy_members(old);cells=[]
 for sample in ['paired','holdout']:
  for n in ([119,240] if sample=='paired' else [119]):
   for theta in [0.,.5]:
    for p in [1,2]:
     rows=[];count=1000
     for rep in range(0 if sample=='paired' else 1000,1000 if sample=='paired' else 2000):
      name=f'n{n}-ma{theta}-p{p}/{rep:05}.json';path=root/'mc'/sample/name
      if path.exists():
       cp=read(path);assert cp['sha256']==hashlib.sha256(canon(cp['result'])).hexdigest();row=cp['result']
      else:
       previous=json.loads(members['mc/'+name])['result'] if sample=='paired' else None
       try:row=replication(n,theta,p,rep,previous)
       except (ValueError,np.linalg.LinAlgError) as ex:row={'failure':str(ex)}
       save(path,{'result':row,'sha256':hashlib.sha256(canon(row)).hexdigest()})
      rows.append(row)
      if len(rows)%250==0:print(sample,n,theta,p,len(rows),flush=True)
     cells.append({'sample':sample,'n':n,'ma':theta,'p':p,'requested':count,'methods':summarize(rows)})
     save(root/'calibration-progress.json',cells)
 return {'state':'complete','synthetic':True,'cells':cells,'checkpoints':12000,
 'boundary':'Follow-up methods fixed after prior undercoverage was known; independent seed holdout uses the same narrow DGP family. Oracle shocks are observed only in simulations. Feasible intervals remain conditional on generated shocks. MA cases deliberately misspecify finite VAR dynamics. Student-t/HC3 adjustments have no exact finite-sample guarantee. No causal identification or Brazil-wide coverage certificate.'}
def archive(root):
 members={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file() and p.suffix in ['.json','.py']}
 output=root.parent/(root.name+'-verified.zip')
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
  for n,b in members.items():z.writestr(n,b)
  z.writestr('file-manifest.json',canon({n:hashlib.sha256(b).hexdigest() for n,b in members.items()}))
 checked_zip(output);return output
def main():
 a=argparse.ArgumentParser();a.add_argument('--run',type=Path,required=True);a.add_argument('--old',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--stage',choices=['inspect','empirical','calibration'],default='inspect');args=a.parse_args()
 root=make_plan(args.run,args.old,args.output);print('FOLLOWUP',root.name,args.stage,flush=True)
 if args.stage!='inspect':
  path=root/(args.stage+'.json')
  if path.exists():assert read(root/(args.stage+'-status.json'))['sha256']==sha(path) and read(path)['state']=='complete'
  else:
   result=empirical(args.run) if args.stage=='empirical' else calibration(root,args.old)
   save(path,result);save(root/(args.stage+'-status.json'),{'state':'complete','sha256':sha(path)})
 preserved(args.run);print('VERIFIED',archive(root),flush=True)
if __name__=='__main__':main()
