"""Separate Python bootstrap-t study; original research outputs are read-only.

Recursive wild t is centered on the bootstrap DGP's VAR response, NOT the
sample LP estimate. Circular pairs t is centered on the sample LP estimate.
This is an adapted finite-design experiment, not a theorem or paper replication.
"""
from __future__ import annotations
import argparse,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import scipy,statsmodels
from scipy.stats import t as student_t
from fdi.models import design,fit_system,responses

BASELINE={'prepared/quarterly.csv':'10426ad1fef8fcec3a53ff94c1753d289de4faf908437b1ffc787ac3b0d56b8a','models/national.json':'eee06465aa0c4ee366e2476d1083902a4f3a3d1a7713d843e2ad239666a0cc82'}
PRIOR='7a0dc4441ed0b4ba41821acde7f5f6bae8469d094d53c13df1265081fb500941'
CONFIG={'version':1,'seed':20261101,'horizon':4,'empirical_lags':[1,2,3,4],'common_start':4,
 'empirical_B':1999,'MC_B':499,'outer_reps':500,'outer_ids':[2000,2499],
 'n':[119,240],'ma':[0.,.5],'p':[1,2],'block_lengths':[4,8],'draw_batch':64,
 'methods':['hc3_t','recursive_wild_t','block4_t','block8_t'],
 'wild_weights':'one independent N(0,1) scalar per date, shared across equations',
 'wild_residuals':'equationwise HC2 adjustment, then column centering',
 'initial_conditions':'fixed observed first p values; fixed exogenous path',
 'studentizer':'HC3; equal-tailed percentile-t, linear empirical quantiles',
 'VAR_coefficients':'unadjusted restricted OLS; no Pope correction; HC2 and fixed initials are declared adaptations, not a full paper replication',
 'wild_center':'response implied by generating VAR; SD target uses HC2-adjusted generating covariance',
 'blocks':'circular moving blocks of complete LP rows; unit target only',
 'failures':'no replacement draws; require >=95% finite valid inner draws; record all failures and unstable fits, never truncate merely for instability',
 'design_status':'Specified after previous undercoverage; fresh outer seed IDs. Limited pilot, not general calibration.',
 'scope':'Q4 only, pointwise, no lag reselection, no causal identification certificate',
 'references':['https://doi.org/10.3982/ECTA18756','https://doi.org/10.1016/j.jeconom.2024.105722']}

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_bytes(canonical(x));q.replace(p)
def read(p):return json.loads(Path(p).read_bytes())
def preserve(run):assert {n:sha(run/n) for n in BASELINE}==BASELINE,'Original baseline changed'
def plan(run,output):
 preserve(run);assert not output.resolve().is_relative_to(run.resolve())
 spec={'config':CONFIG,'baseline':BASELINE,'prior_export':PRIOR,'source_sha256':sha(__file__),'frozen_models_sha256':sha(Path(__file__).parent/'fdi/models.py'),'versions':{'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'statsmodels':statsmodels.__version__}}
 identity=hashlib.sha256(canonical(spec)).hexdigest();root=output/identity[:16];root.mkdir(parents=True,exist_ok=True)
 record={'identity':identity,'specification':spec}
 if (root/'plan.json').exists():assert read(root/'plan.json')==record
 else:save(root/'plan.json',record);(root/'source.py').write_bytes(Path(__file__).read_bytes())
 return root

def solve_batch(x,y):
 """SVD OLS with HC3 scalar studentizer; exactly matches full-rank OLS."""
 u,s,v=np.linalg.svd(x,full_matrices=False);tol=np.finfo(float).eps*max(x.shape[-2:])*s[:,:1]
 valid=(s>tol).all(axis=1);inv=np.divide(1.,s,out=np.zeros_like(s),where=s>tol)
 pinv=np.einsum('bji,bj,bkj->bik',v,inv,u)
 beta=np.einsum('bki,bi->bk',pinv,y);resid=y-np.einsum('bij,bj->bi',x,beta)
 leverage=(u*u).sum(axis=2);denom=1-leverage
 valid&=(denom>1e-10).all(axis=1)
 ratio=np.divide(resid,denom,out=np.zeros_like(resid),where=denom>1e-10)
 se=np.sqrt(np.sum((pinv[:,-1,:]*ratio)**2,axis=1));valid&=np.isfinite(se)&(se>1e-12)&np.isfinite(beta[:,-1])
 return beta,se,valid,leverage

def lp_batch(y,z,p,start=4,h=4):
 if y.ndim==2:y=y[None,:,:]
 n=y.shape[1]-start-h
 if z.ndim==2:z=np.broadcast_to(z,(len(y),*z.shape))
 x=np.concatenate([np.ones((len(y),n,1)),z[:,start:start+n],*[y[:,start-l:start-l+n] for l in range(1,p+1)],y[:,start:start+n]],axis=2)
 target=y[:,start+h:start+h+n,1];beta,se,valid,lev=solve_batch(x,target)
 return {'estimate':beta[:,-1],'se':se,'valid':valid,'leverage':lev,'x':x,'target':target,'df':n-x.shape[2]}

def last_impact_batch(y,z,p):
 """Refit/reidentify only synthetic bootstrap draws for the one-SD target."""
 if y.ndim==2:y=y[None,:,:]
 b,n,k=y.shape;d=1+z.shape[1]
 x=np.concatenate([np.ones((b,n-p,1)),np.broadcast_to(z[p:],(b,n-p,z.shape[1])),*[y[:,p-l:n-l] for l in range(1,p+1)]],axis=2)
 # Full-system OLS, with the frozen first-equation own-lag restriction.
 pinv=np.linalg.pinv(x);beta=np.einsum('bqn,bnk->bqk',pinv,y[:,p:])
 use=[*range(d),*[d+l*k for l in range(p)]]
 own=x[:,:,use];b0=np.einsum('bqn,bn->bq',np.linalg.pinv(own),y[:,p:,0]);beta[:,:,0]=0;beta[:,use,0]=b0
 resid=y[:,p:]-np.einsum('bnq,bqk->bnk',x,beta);cov=np.einsum('bni,bnj->bij',resid,resid)/(n-p)
 good=np.linalg.matrix_rank(x)==x.shape[-1];eigen=np.linalg.eigvalsh(cov);good&=(eigen[:,0]>np.finfo(float).eps*np.maximum(eigen[:,-1],1))
 safe=cov.copy();safe[~good]=np.eye(k)
 impact=np.linalg.cholesky(safe)[:,-1,-1];impact[~good]=np.nan
 return impact,good

def hc2_generator(y,z,model):
 p=model['p'];k=y.shape[1];x=design(y,z,p);raw=y[p:]-x@model['beta'];d=1+z.shape[1]
 leverage=np.empty_like(raw)
 for j in range(k):
  use=[*range(d),*[d+l*k for l in range(p)]] if j==0 else list(range(x.shape[1]))
  u,s,_=np.linalg.svd(x[:,use],full_matrices=False);assert np.linalg.matrix_rank(x[:,use])==len(use)
  leverage[:,j]=(u*u).sum(axis=1)
 assert (leverage<1-1e-10).all()
 adjusted=raw/np.sqrt(1-leverage);adjusted-=adjusted.mean(axis=0)
 return adjusted

def wild_paths(y,z,model,weights):
 p=model['p'];batch=len(weights);out=np.broadcast_to(y,(batch,*y.shape)).copy();d=model['d']
 for t in range(p,len(y)):
  v=np.broadcast_to(np.r_[1.,z[t]]@model['beta'][:d],(batch,y.shape[1])).copy()
  for l,A in enumerate(model['A'],1):v+=out[:,t-l]@A.T
  out[:,t]=v+weights[:,t-p,None]*model['adjusted_residuals'][t-p]
 return out

def block_indices(rng,batch,n,length):
 starts=rng.integers(0,n,(batch,int(np.ceil(n/length))))
 return ((starts[:,:,None]+np.arange(length))%n).reshape(batch,-1)[:,:n]

def invert_t(point,se,draws,center):
 ok=np.isfinite(draws[:,0])&np.isfinite(draws[:,1])&(draws[:,1]>1e-12)
 if ok.sum()<np.ceil(.95*len(draws)):return {'available':False,'valid':int(ok.sum()),'failures':int((~ok).sum())}
 t=(draws[ok,0]-center)/draws[ok,1];q=np.quantile(t,[.025,.975],method='linear')
 return {'available':True,'valid':int(ok.sum()),'failures':int((~ok).sum()),'center':float(center),'q025':float(q[0]),'q975':float(q[1]),'lower':float(point-se*q[1]),'upper':float(point-se*q[0])}

def experiment(y,z,model,p,start,B,seed,sd=False):
 lp=lp_batch(y,z,p,start);assert lp['valid'][0]
 point=float(lp['estimate'][0]);se=float(lp['se'][0]);df=lp['df'];critical=float(student_t.ppf(.975,df))
 adjusted=hc2_generator(y,z,model);model={**model,'adjusted_residuals':adjusted}
 gen_cov=adjusted.T@adjusted/len(adjusted);_,genB=responses({**model,'cov':gen_cov},4)
 irf,_=responses({**model,'cov':gen_cov},4);unit_center=float(irf[4,1,-1]/genB[-1,-1])
 originals={'unit':{'estimate':point,'se':se,'hc3_t':{'available':True,'lower':point-critical*se,'upper':point+critical*se}}}
 original_impact=None
 if sd:
  _,impact=responses(model,0);original_impact=float(impact[-1,-1]);originals['sd']={'estimate':point*original_impact,'se':se*original_impact,'hc3_t':{'available':True,'lower':(point-critical*se)*original_impact,'upper':(point+critical*se)*original_impact}}
 raw={name:np.full((B,2),np.nan) for name in ['wild_unit','block4_unit','block8_unit']+(['wild_sd'] if sd else [])}
 for offset in range(0,B,CONFIG['draw_batch']):
  count=min(CONFIG['draw_batch'],B-offset)
  # Seed each draw, so changing batch boundaries does not change its identity.
  weights=np.stack([np.random.default_rng(np.random.SeedSequence([CONFIG['seed'],*seed,0,j])).normal(size=len(y)-p) for j in range(offset,offset+count)])
  paths=wild_paths(y,z,model,weights);f=lp_batch(paths,z,p,start)
  est=f['estimate'].copy();std=f['se'].copy();est[~f['valid']]=np.nan;std[~f['valid']]=np.nan
  raw['wild_unit'][offset:offset+count]=np.column_stack([est,std])
  if sd:
   impact,good=last_impact_batch(paths,z,p);a=est*impact;b=std*impact;a[~good]=np.nan;b[~good]=np.nan
   raw['wild_sd'][offset:offset+count]=np.column_stack([a,b])
  for length in CONFIG['block_lengths']:
   n=lp['x'].shape[1]
   indices=np.concatenate([block_indices(np.random.default_rng(np.random.SeedSequence([CONFIG['seed'],*seed,length,j])),1,n,length) for j in range(offset,offset+count)])
   x=lp['x'][0][indices];target=lp['target'][0][indices];beta,bse,good,_=solve_batch(x,target)
   a=beta[:,-1].copy();b=bse.copy();a[~good]=np.nan;b[~good]=np.nan
   raw[f'block{length}_unit'][offset:offset+count]=np.column_stack([a,b])
 originals['unit']['recursive_wild_t']=invert_t(point,se,raw['wild_unit'],unit_center)
 for length in CONFIG['block_lengths']:originals['unit'][f'block{length}_t']=invert_t(point,se,raw[f'block{length}_unit'],point)
 if sd:originals['sd']['recursive_wild_t']=invert_t(point*original_impact,se*original_impact,raw['wild_sd'],float(irf[4,1,-1]))
 return {'targets':originals,'n':int(lp['x'].shape[1]),'k':int(lp['x'].shape[2]),'df':int(df),'maximum_leverage':float(lp['leverage'].max()),'training_radius':model['radius'],'training_unstable':bool(model['radius']>=1),'B':B,
  'generator_A':model['A'].tolist(),'generator_HC2_covariance':gen_cov.tolist(),'original_SD_impact':original_impact},raw

def checkpoint(root,name,fn):
 jp=root/(name+'.json');npz=root/(name+'.npz')
 if jp.exists():
  d=read(jp);assert d['npz_sha256']==sha(npz) and d['result_sha256']==hashlib.sha256(canonical(d['result'])).hexdigest();return d['result']
 result,raw=fn();npz.parent.mkdir(parents=True,exist_ok=True)
 temp=npz.with_suffix('.tmp.npz');np.savez_compressed(temp,**raw);temp.replace(npz)
 save(jp,{'result':result,'result_sha256':hashlib.sha256(canonical(result)).hexdigest(),'npz_sha256':sha(npz)});return result

def empirical(run,root):
 preserve(run);m=read(run/'models/national.json');f=pd.read_csv(run/'prepared/quarterly.csv',index_col=0);y=f[m['variables']].to_numpy(float)
 z=np.column_stack([f[['us_gdp_growth','fedfunds_change']],pd.get_dummies(f.quarter,drop_first=True).astype(float)]);rows=[]
 for p in CONFIG['empirical_lags']:
  if p==m['lag']:
   beta=np.asarray(m['coefficients']);d=1+z.shape[1];model={'p':p,'d':d,'beta':beta,'A':np.stack([beta[d+l*5:d+(l+1)*5].T for l in range(p)]),'cov':np.asarray(m['residual_covariance']),'radius':m['diagnostics']['spectral_radius']}
  else:model=fit_system(y,z,p) # New bootstrap nuisance fit only; no baseline file writes.
  r=checkpoint(root,f'empirical/p{p}',lambda:experiment(y,z,model,p,4,CONFIG['empirical_B'],[1,p]));rows.append({'p':p,'baseline_coefficients_reused':p==m['lag'],**r})
 preserve(run);return {'state':'complete','horizon':4,'rows':rows,'target':'GDP-growth pp per +1pp FDI/GDP impact, FDI last; common 111 rows','bootstrap_new':True,'original_2000_draws_rerun':False}

def synthetic(n,ma,p,rep):
 rng=np.random.default_rng(np.random.SeedSequence([20261031,n,int(ma*100),p,rep]));A=np.array([[.65,0,0],[.1,.45,.05],[.05,.12,.35]]);B=np.array([[1.,0,0],[.2,.8,0],[.1,.15,.6]])
 e=rng.normal(size=(n+501,3));y=np.zeros_like(e)
 for t in range(1,len(y)):y[t]=A@y[t-1]+B@e[t]+ma*B@e[t-1]
 truth=float((np.linalg.matrix_power(A,4)@B+ma*np.linalg.matrix_power(A,3)@B)[1,2]);return y[501:],{'unit':truth/B[-1,-1],'sd':truth}

def summarize(rows):
 result={}
 for target,methods in [('unit',CONFIG['methods']),('sd',['hc3_t','recursive_wild_t'])]:
  result[target]={}
  for method in methods:
   valid=[r for r in rows if 'failure' not in r and r['targets'][target][method]['available']];flags=[r['targets'][target][method]['lower']<=r['truth'][target]<=r['targets'][target][method]['upper'] for r in valid]
   baseline=[r['targets'][target]['hc3_t']['lower']<=r['truth'][target]<=r['targets'][target]['hc3_t']['upper'] for r in valid];delta=np.array(flags,dtype=float)-np.array(baseline,dtype=float)
   c=float(np.mean(flags)) if flags else None
   result[target][method]={'requested':len(rows),'valid':len(valid),'unavailable':len(rows)-len(valid),'coverage':c,'mcse':float(np.sqrt(c*(1-c)/len(flags))) if flags else None,'mean_width':float(np.mean([r['targets'][target][method]['upper']-r['targets'][target][method]['lower'] for r in valid])) if valid else None,'bias':float(np.mean([r['targets'][target]['estimate']-r['truth'][target] for r in valid])) if valid else None,'paired_coverage_difference_vs_HC3':float(delta.mean()) if flags else None,'paired_difference_mcse':float(delta.std(ddof=1)/np.sqrt(len(delta))) if len(delta)>1 else None,'invalid_inner_draws':sum(r['targets'][target][method].get('failures',0) for r in rows if 'failure' not in r)}
 return result

def pack(root,packet,prefixes):
 paths=[]
 for prefix in prefixes:
  target=root/prefix;paths.extend([target] if target.is_file() else list(target.rglob('*')))
 members={p.relative_to(root).as_posix():p.read_bytes() for p in paths if p.is_file() and p.suffix in ['.json','.npz','.py']}
 for n in ['plan.json','source.py','empirical.json','empirical-status.json','calibration.json','calibration-status.json']:
  if (root/n).exists():members[n]=(root/n).read_bytes()
 dest=root.parent/(root.name+'-'+packet+'.zip')
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
  for n,b in members.items():z.writestr(n,b)
  z.writestr('file-manifest.json',canonical({n:hashlib.sha256(b).hexdigest() for n,b in members.items()}))
 verify_zip(dest)
 receipt={'packet':packet,'file':dest.name,'sha256':sha(dest),'bytes':dest.stat().st_size,'members':len(members),'CRC_all_members':True};save(root/('receipt-'+packet+'.json'),receipt);return receipt
def verify_zip(path):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
  manifest=json.loads(z.read('file-manifest.json'));assert set(manifest)|{'file-manifest.json'}==set(z.namelist())
  for n,h in manifest.items():assert '..' not in Path(n).parts and not Path(n).is_absolute() and hashlib.sha256(z.read(n)).hexdigest()==h

def calibration(root):
 cells=[]
 for n in CONFIG['n']:
  for ma in CONFIG['ma']:
   for p in CONFIG['p']:
    name=f'n{n}-ma{ma}-p{p}';rows=[]
    for rep in range(2000,2500):
     def compute():
      try:
       y,truth=synthetic(n,ma,p,rep);z=np.zeros((n,0));model=fit_system(y,z,p)
       r,raw=experiment(y,z,model,p,p,CONFIG['MC_B'],[2,n,int(ma*100),p,rep],True);return {**r,'truth':truth,'replication':rep},raw
      except (ValueError,np.linalg.LinAlgError) as ex:return {'failure':str(ex),'replication':rep},{}
     rows.append(checkpoint(root,'mc/'+name+f'/{rep:05}',compute))
     if len(rows)%50==0:print(name,len(rows),flush=True)
    cell={'name':name,'n':n,'ma':ma,'p':p,'replications':500,'training_unstable':sum(r.get('training_unstable',False) for r in rows),'targets':summarize(rows)};save(root/'cells'/(name+'.json'),cell)
    cells.append(cell);pack(root,name,['mc/'+name,'cells/'+name+'.json']);save(root/'progress.json',{'completed_cells':[c['name'] for c in cells]})
 return {'state':'complete','cells':cells,'outer_replications':4000,'inner_B':499,'fresh_ids':[2000,2499],'synthetic':True,'causal_identification_validated':False}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--stage',choices=['inspect','empirical','calibration'],default='inspect');a=ap.parse_args();root=plan(a.run,a.output);print('BOOTSTRAP STUDY',root.name,a.stage,flush=True)
 if a.stage!='inspect':
  p=root/(a.stage+'.json')
  if p.exists():assert read(root/(a.stage+'-status.json'))['sha256']==sha(p) and read(p)['state']=='complete'
  else:
   result=empirical(a.run,root) if a.stage=='empirical' else calibration(root);save(p,result);save(root/(a.stage+'-status.json'),{'state':'complete','sha256':sha(p)})
  if a.stage=='empirical':print(json.dumps(pack(root,'empirical',['empirical'])),flush=True)
  if a.stage=='calibration':
   prefixes=['cells','progress.json','launch.json',*[p.name for p in root.glob('receipt-*.json')]]
   print(json.dumps(pack(root,'summary',prefixes)),flush=True)
 preserve(a.run);print('STAGE COMPLETE',a.stage,flush=True)
if __name__=='__main__':main()
