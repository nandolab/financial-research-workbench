"""Additional CPU-only robustness stages. Baseline files are read-only.
No acquisition, inference models, LangSmith calls or baseline bootstrap execution.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, zipfile, importlib.metadata
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from fdi.models import design, fit_system, responses, local_projections, plain

VARIABLES=['nfci','gdp_growth','gfcf_growth','reer_change','fdi_gdp']
SEED=20261031
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(plain(value),sort_keys=True,indent=2,allow_nan=False).encode()
    temp=p.with_suffix('.tmp');temp.write_bytes(raw);temp.replace(p)
    assert json.loads(p.read_bytes())==plain(value)
def inputs(run):
    run=Path(run)
    f=pd.read_csv(run/'prepared/quarterly.csv',index_col=0)
    m=json.loads((run/'models/national.json').read_text(encoding='utf8'))
    assert m['state']=='complete' and m['bootstrap']['valid']==2000
    assert list(f.index)==list(pd.period_range(f.index[0],f.index[-1],freq='Q').astype(str))
    assert len(f)==119 and f.index[0]=='1996Q2' and f.index[-1]=='2025Q4'
    assert np.array_equal(f.quarter.to_numpy(),pd.PeriodIndex(f.index,freq='Q').quarter)
    y=f[VARIABLES].to_numpy(float)
    z=np.column_stack([f[['us_gdp_growth','fedfunds_change']].to_numpy(float),pd.get_dummies(f.quarter,drop_first=True).to_numpy(float)])
    assert np.isfinite(y).all() and np.isfinite(z).all()
    # Reconstruct residuals from SAVED coefficients, not a new baseline fit.
    x=design(y,z,m['lag']);u=y[m['lag']:]-x@np.asarray(m['coefficients'])
    shocks=np.linalg.solve(np.asarray(m['impact_matrix']),u.T).T
    return f,m,y,z,u,shocks
def plan(run,dest,replications=1000):
    run=Path(run);dest=Path(dest)
    if not isinstance(replications,int) or replications<1:raise ValueError('Positive replication count required')
    assert dest.resolve()!=run.resolve() and not dest.resolve().is_relative_to(run.resolve())
    f,m,*_=inputs(run)
    hashes={s:sha(run/s) for s in ['prepared/quarterly.csv','models/national.json']}
    config={'version':1,'seed':SEED,'baseline':hashes,'code_sha256':sha(__file__),'dependency_code':{p.name:sha(p) for p in [Path(__file__).parent/'fdi/models.py',Path(__file__).parent/'fdi/storage.py']},'packages':{p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','statsmodels']},'horizons':list(range(13)),
            'lp_extra_lags':[0,1,2],'hac_bandwidth':'h + baseline p + extra lags',
            'residual_checks':'HAC squared-residual quarter-indicator and auxiliary residual-vector lag Wald diagnostics; Holm within each five-equation family',
            'simulation':{'replications_per_cell':replications,'n':[119,240],'ma':[0.,.5],'fit_lags':[1,2]},
            'status':'prepared; new stages require explicit execution','claims':'Sensitivity checks, not new identification. No new baseline bootstrap.'}
    identity=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    root=dest/identity[:16];root.mkdir(parents=True,exist_ok=True)
    save(root/'plan.json',dict(config,identity=identity,observed_rows=len(f)))
    (root/'fdi_robustness.py').write_bytes(Path(__file__).read_bytes())
    return root
def residual_checks(run):
    f,m,y,z,u,shocks=inputs(run);p=m['lag'];q=f.quarter.iloc[p:].to_numpy()
    quarter=pd.get_dummies(q,drop_first=True).to_numpy(float)
    # Quarter means are already fitted: re-testing those means would be tautological.
    x=np.column_stack([np.ones(len(q)),quarter]);season=[];serial=[]
    original=design(y,z,p);d=1+z.shape[1];k=y.shape[1]
    for j,name in enumerate(VARIABLES):
        fit=sm.OLS(u[:,j]**2,x).fit(cov_type='HAC',cov_kwds={'maxlags':4,'use_correction':True})
        w=fit.wald_test(np.eye(4)[1:],scalar=True,use_f=False)
        season.append({'variable':name,'statistic':float(w.statistic),'df':3,'p':float(w.pvalue)})
        use=list(range(d))+([d+lag*k for lag in range(p)] if j==0 else list(range(d,d+p*k)))
        for L in [4,8]:
            lagged=np.column_stack([u[L-lag:len(u)-lag] for lag in range(1,L+1)])
            reg=np.column_stack([original[L:,use],lagged])
            if np.linalg.matrix_rank(reg)!=reg.shape[1]:raise ValueError('Rank-deficient residual diagnostic')
            aux=sm.OLS(u[L:,j],reg).fit(cov_type='HAC',cov_kwds={'maxlags':L,'use_correction':True})
            restriction=np.zeros((k*L,reg.shape[1]));restriction[:,-k*L:]=np.eye(k*L)
            w=aux.wald_test(restriction,scalar=True,use_f=False)
            serial.append({'variable':name,'lag':L,'statistic':float(w.statistic),'df':k*L,'p':float(w.pvalue),'rows':len(u)-L})
    for row,pv in zip(season,multipletests([r['p'] for r in season],method='holm')[1]):row['holm_p']=float(pv)
    for L in [4,8]:
        family=[r for r in serial if r['lag']==L]
        for row,pv in zip(family,multipletests([r['p'] for r in family],method='holm')[1]):row['holm_p']=float(pv)
    return {'state':'complete','seasonal_null':'equal quarter-specific mean squared residuals (seasonal volatility screen), not a repeat test of fitted quarter means',
            'serial_null':'all lagged residual-vector coefficients zero in each auxiliary equation, retaining its original regressors',
            'seasonal':season,'serial':serial,'caution':'HAC asymptotic auxiliary Wald diagnostics with generated residuals; small sample/model selection can distort size. Not an exact small-sample system test or causal validation.'}
def lp_sensitivity(run):
    f,m,y,z,u,shocks=inputs(run);p=m['lag'];out=[]
    for extra in [0,1,2]:
        lag=p+extra;start=lag
        x=design(y,z,lag,start);eps=shocks[start-p:]
        xx=np.column_stack([x,eps]);est=[];interval=[]
        for h in range(13):
            n=len(eps)-h
            if n<=xx.shape[1]+5:raise ValueError('Insufficient residual degrees of freedom')
            row=[];ci=[]
            for j in range(5):
                fit=sm.OLS(y[start+h:start+h+n,j],xx[:n]).fit(cov_type='HAC',cov_kwds={'maxlags':h+lag,'use_correction':True})
                row.append(fit.params[-5:]);ci.append(fit.conf_int(alpha=.05)[-5:])
            est.append(row);interval.append(ci)
        out.append({'extra_lags':extra,'irf':est,'pointwise_95_hac':interval})
    return {'state':'complete','specifications':out,
            'boundary':'Same baseline generated shocks; conditional HAC omits shock-estimation uncertainty. Lag augmentation alone does not certify the cited uniform-inference theorem. Not independent identification.'}
def saved_draw_summaries(run):
    f,m,*_=inputs(run);curves=[];cumulative=[]
    for i in range(2000):
        with np.load(Path(run)/f'checkpoints/national-bootstrap/{i:05}.npz',allow_pickle=False) as c:
            irf=c['irf'];impact=irf[0,4,4]
            if not np.isfinite(impact) or impact<=1e-10:raise ValueError('Invalid normalization')
            curves.append(irf[:,:,4]/impact) # response to a +1 pp FDI/GDP impact
            cumulative.append(np.expm1(np.cumsum(irf[:,1,4])/100)*100)
    point=np.asarray(m['irf'])
    return {'state':'complete','saved_draws':len(curves),'new_draws':0,
        'unit_shock':'responses per +1 percentage point FDI/GDP innovation; normalize each draw by its own impact',
        'unit_quantiles':{str(q):np.quantile(curves,q,axis=0) for q in [.025,.16,.84,.975]},
        'gdp_level_percent':np.expm1(np.cumsum(point[:,1,4])/100)*100,
        'gdp_level_pointwise_95':{str(q):np.quantile(cumulative,q,axis=0) for q in [.025,.975]},
        'boundary':'Cumulative response starts at impact (h=0). Draw-wise nonlinear conversion; inherits baseline identification/VAR bootstrap. Not simultaneous bands.'}
def simulation_replication(n,theta,p,rep):
    # Three-variable triangular structural DGP; true shock is epsilon, not fitted VAR residual.
    rng=np.random.default_rng(np.random.SeedSequence([SEED,n,int(theta*100),p,rep]))
    A=np.array([[.65,0,0],[.10,.45,.05],[.05,.12,.35]])
    B=np.array([[1.,0,0],[.2,.8,0],[.1,.15,.6]])
    e=rng.normal(size=(n+501,3));y=np.zeros_like(e)
    for t in range(1,len(y)):y[t]=A@y[t-1]+B@e[t]+theta*B@e[t-1]
    y=y[501:];z=np.zeros((n,0));model=fit_system(y,z,p)
    if model['radius']>=1:return {'failure':'unstable fitted VAR'}
    irf,_=responses(model,12);lp,se=local_projections(y,z,model,12,True)
    # True response of variable 1 to structural shock 2 at h=4.
    h=4;truth=(np.linalg.matrix_power(A,h)@B+theta*np.linalg.matrix_power(A,h-1)@B)[1,2]
    est=lp[h,1,2];sd=se[h,1,2]
    return {'truth':truth,'estimate':est,'se':sd,'covered':bool(est-1.96*sd<=truth<=est+1.96*sd),
            'var_estimate':float(irf[h,1,2]),'boundary':'Pointwise normal-HAC LP interval conditional on estimated shocks; generated-shock/selection uncertainty not fully propagated.'}
def monte_carlo(root,replications=1000):
    # Each replication is cached independently. Failures stay in the denominator report.
    results=[]
    for n in [119,240]:
        for theta in [0.,.5]:
            for p in [1,2]:
                rows=[]
                for rep in range(replications):
                    target=root/'mc'/f'n{n}-ma{theta}-p{p}'/f'{rep:05}.json'
                    if target.exists():
                        checkpoint=json.loads(target.read_bytes());row=checkpoint['result']
                        assert checkpoint['sha256']==hashlib.sha256(json.dumps(plain(row),sort_keys=True).encode()).hexdigest(),'Replication checksum mismatch'
                    else:
                        try:row=simulation_replication(n,theta,p,rep)
                        except (ValueError,np.linalg.LinAlgError) as ex:row={'failure':str(ex)}
                        save(target,{'result':row,'sha256':hashlib.sha256(json.dumps(plain(row),sort_keys=True).encode()).hexdigest()})
                    rows.append(row)
                valid=[r for r in rows if 'failure' not in r];coverage=np.mean([r['covered'] for r in valid]) if valid else None
                results.append({'n':n,'ma':theta,'p':p,'requested':replications,'valid':len(valid),'failures':len(rows)-len(valid),
                    'conditional_coverage':coverage,'mcse':float(np.sqrt(coverage*(1-coverage)/len(valid))) if valid else None,
                    'bias':float(np.mean([r['estimate']-r['truth'] for r in valid])) if valid else None})
                save(root/'monte-carlo-progress.json',results)
    return {'state':'complete','synthetic':True,'cells':results,'boundary':'Small designed benchmark, not proof of correct coverage for Brazil. Three variables, no municipal data. Report failures separately. This benchmark does not implement the full municipal parallel-trends sensitivity study.'}
def backup(root):
    root=Path(root)
    members={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file() and p.suffix!='.zip' and p.name!='backup-verification.json'}
    manifest={n:hashlib.sha256(v).hexdigest() for n,v in members.items()}
    archive=root/'robustness-backup.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in members.items():z.writestr(n,v)
        z.writestr('file-manifest.json',json.dumps(manifest,sort_keys=True))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(manifest)|{'file-manifest.json'}
        for n,d in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==d
    save(root/'backup-verification.json',{'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(members),'crc':'passed','readback':'all member hashes passed'})
    return archive
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--stage',choices=['inspect','residuals','lp','saved-draws','simulation'],default='inspect')
    ap.add_argument('--replications',type=int,default=1000);a=ap.parse_args()
    root=plan(a.run,a.output,a.replications);before={s:sha(a.run/s) for s in ['prepared/quarterly.csv','models/national.json']}
    print('Separate robustness identity:',root.name,'stage:',a.stage,flush=True)
    if a.stage!='inspect':
        target=root/(a.stage+'.json')
        if target.exists():
            status=json.loads((root/(a.stage+'-status.json')).read_bytes())
            assert status['sha256']==sha(target),'Cached stage checksum mismatch'
            assert json.loads(target.read_bytes())['state']=='complete'
            print('Verified completed cached stage:',target.name)
        else:
            result={'residuals':lambda:residual_checks(a.run),'lp':lambda:lp_sensitivity(a.run),'saved-draws':lambda:saved_draw_summaries(a.run),'simulation':lambda:monte_carlo(root,a.replications)}[a.stage]()
            save(target,result)
            save(root/(a.stage+'-status.json'),{'sha256':sha(target),'state':'complete'})
    assert before=={s:sha(a.run/s) for s in before},'Baseline mutated'
    print('Read-back verified backup:',backup(root),flush=True)
if __name__=='__main__':main()

