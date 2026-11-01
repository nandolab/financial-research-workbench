"""Restricted structural VAR and identified-shock local projections.

The recursive impact matrix identifies shocks only under the declared restrictions.
Passing diagnostics does not establish the truth of those economic restrictions.
"""
from __future__ import annotations
import json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import chi2
from statsmodels.tsa.stattools import adfuller, kpss
import statsmodels.api as sm
from .storage import read_json, save_json, digest, canonical

def plain(x):
    if isinstance(x,np.ndarray):return plain(x.tolist())
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
    if isinstance(x,np.generic):return plain(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    return x

def design(y,z,p,start=None):
    start=p if start is None else start
    return np.column_stack([np.ones(len(y)-start),z[start:],*[y[start-len_lag:len(y)-len_lag] for len_lag in range(1,p+1)]])

def fit_system(y,z,p,start=None):
    n,k=y.shape;start=p if start is None else start
    x=design(y,z,p,start);target=y[start:];d=1+z.shape[1]
    beta=np.zeros((x.shape[1],k));counts=[]
    for j in range(k):
        use=list(range(d)) + ([d+lag*k for lag in range(p)] if j==0 else list(range(d,d+p*k)))
        b,_,rank,_=np.linalg.lstsq(x[:,use],target[:,j],rcond=None)
        if rank!=len(use):raise ValueError('Rank-deficient model design')
        beta[use,j]=b;counts.append(len(use))
    resid=target-x@beta;cov=resid.T@resid/len(resid)
    sign,logdet=np.linalg.slogdet(cov)
    if sign<=0:raise ValueError('Non-positive residual covariance')
    A=np.stack([beta[d+l*k:d+(l+1)*k,:].T for l in range(p)])
    companion=np.zeros((p*k,p*k));companion[:k,:]=np.hstack(A)
    if p>1:companion[k:,:-k]=np.eye((p-1)*k)
    radius=float(np.max(np.abs(np.linalg.eigvals(companion))))
    return {'beta':beta,'A':A,'cov':cov,'residuals':resid,'start':start,'p':p,'d':d,'radius':radius,'bic':float(logdet+sum(counts)*np.log(len(resid))/len(resid)),'parameters':sum(counts),'rows':len(resid)}

def responses(model,horizon=12,order=None):
    k=len(model['cov']);order=list(range(k)) if order is None else order
    perm=np.eye(k)[order];B=perm.T@np.linalg.cholesky(perm@model['cov']@perm.T)@perm
    phi=np.zeros((horizon+1,k,k));phi[0]=np.eye(k)
    for h in range(1,horizon+1):
        for lag,A in enumerate(model['A'],1):
            if h>=lag:phi[h]+=A@phi[h-lag]
    return phi@B,B

def local_projections(y,z,model,horizon=12,hac=False):
    start=model['start'];_,B=responses(model,0)
    shocks=np.linalg.solve(B,model['residuals'].T).T
    x=design(y,z,model['p'],start)
    xx=np.column_stack([x,shocks]);k=y.shape[1];est=np.zeros((horizon+1,k,k));se=np.zeros_like(est)
    for h in range(horizon+1):
        n=len(shocks)-h;target=y[start+h:start+h+n];reg=xx[:n]
        coefficients=np.linalg.lstsq(reg,target,rcond=None)[0]
        est[h]=coefficients[-k:].T
        if hac:
            for j in range(k):
                fitted=sm.OLS(target[:,j],reg).fit(cov_type='HAC',cov_kwds={'maxlags':h+model['p']})
                se[h,j]=fitted.bse[-k:]
    return est,se

def historical(y,z,model):
    p=model['p'];start=model['start'];k=y.shape[1];A=model['A'];beta=model['beta'];d=model['d'];_,B=responses(model,0)
    eps=np.linalg.solve(B,model['residuals'].T).T
    pieces=np.zeros((len(y),k,k));baseline=np.zeros_like(y);baseline[:start]=y[:start]
    for t in range(start,len(y)):
        baseline[t]=np.r_[1,z[t]]@beta[:d]
        for lag in range(1,p+1):
            baseline[t]+=A[lag-1]@baseline[t-lag]
            pieces[t]+=A[lag-1]@pieces[t-lag]
        pieces[t]+=B*eps[t-start][None,:]
    difference=float(np.max(np.abs(y[start:]-baseline[start:]-pieces[start:].sum(axis=2))))
    if difference>1e-7:raise ValueError('Historical decomposition failed to reconcile')
    return {'contributions':pieces[start:],'baseline':baseline[start:],'max_reconciliation_error':difference}

def whiteness(model,m=8):
    u=model['residuals'];u=u-u.mean(axis=0);n,k=u.shape;inv=np.linalg.inv(u.T@u/n);Q=0.
    for h in range(1,m+1):
        c=u[h:].T@u[:-h]/n;Q+=np.trace(c.T@inv@c@inv)/(n-h)
    Q*=n*n
    df=k*k*(m-model['p'])+(k-1)*model['p']
    return {'lag':m,'statistic':float(Q),'df':df,'pvalue':float(chi2.sf(Q,df)),'method':'adjusted multivariate portmanteau; restriction-adjusted asymptotic degrees of freedom'}

def diagnostics(frame,model,variables):
    stationarity=[]
    for name in variables:
        s=frame[name].to_numpy()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');a=adfuller(s,maxlag=4,autolag='BIC');k=kpss(s,regression='c',nlags='auto')
        stationarity.append({'variable':name,'adf_pvalue':float(a[1]),'kpss_pvalue':float(k[1]),'blocked':bool(a[1]>.10 and k[1]<.05)})
    white=whiteness(model)
    return {'stationarity':stationarity,'whiteness':white,'spectral_radius':model['radius'],'stable':model['radius']<1,'passed':model['radius']<1 and white['pvalue']>=.05 and not any(x['blocked'] for x in stationarity),'boundary':'Economic identification assumptions remain untestable; diagnostics are necessary checks, not proof of causality.'}

def national_models(study,replications=None):
    source=study.run/'prepared/quarterly.csv';inputs=[source]
    if study.cached('national_models',inputs):return read_json(study.run/'models/national.json')
    frame=pd.read_csv(source,index_col=0)
    names=study.config['variables'];y=frame[names].to_numpy(float)
    z=np.column_stack([frame[['us_gdp_growth','fedfunds_change']].to_numpy(float),pd.get_dummies(frame['quarter'],drop_first=True).to_numpy(float)])
    if len(y)<80:raise ValueError('Fewer than 80 comparable quarters; national estimation held')
    start=max(study.config['lags'])
    candidates=[fit_system(y,z,p,start) for p in study.config['lags']]
    selected=min(candidates,key=lambda m:m['bic']);p=selected['p']
    # Refit on all available observations for chosen p; BIC comparison used common sample.
    model=fit_system(y,z,p);H=study.config['horizons'];irf,B=responses(model,H)
    lp,hac=local_projections(y,z,model,H,True);diag=diagnostics(frame,model,names)
    hist=historical(y,z,model)
    squares=np.cumsum(irf**2,axis=0);fevd=squares[1:]/squares[1:].sum(axis=2,keepdims=True)
    requested=replications if replications is not None else study.config['bootstrap_replications']
    cache=study.run/'checkpoints/national-bootstrap';cache.mkdir(exist_ok=True)
    fingerprint=digest(canonical({'input':study.fingerprint(inputs),'p':p,'config':study.config,'code':study.code_hash}))
    meta=cache/'identity.json'
    if meta.exists() and read_json(meta)['fingerprint']!=fingerprint:raise ValueError('Bootstrap cache identity mismatch')
    save_json(meta,{'fingerprint':fingerprint,'requested':requested,'seed':study.config['seed']})
    valid=[];failures=[];resid=model['residuals']-model['residuals'].mean(axis=0)
    for i in range(requested):
        cp=cache/f'{i:05}.npz';failure=cache/f'{i:05}.failed.json'
        if cp.exists():
            with np.load(cp) as c:valid.append((c['irf'],c['lp']))
            continue
        if failure.exists():failures.append(read_json(failure));continue
        rng=np.random.default_rng(np.random.SeedSequence([study.config['seed'],i]))
        errors=resid[rng.integers(0,len(resid),len(resid))]
        simulated=y.copy()
        for t in range(p,len(y)):
            simulated[t]=np.r_[1,z[t]]@model['beta'][:model['d']]
            for lag in range(1,p+1):simulated[t]+=model['A'][lag-1]@simulated[t-lag]
            simulated[t]+=errors[t-p]
        try:
            fitted=fit_system(simulated,z,p)
            if fitted['radius']>=1:raise ValueError('unstable bootstrap system')
            b_irf,_=responses(fitted,H);b_lp,_=local_projections(simulated,z,fitted,H)
            if not np.isfinite(b_irf).all() or not np.isfinite(b_lp).all():raise ValueError('nonfinite bootstrap')
            temp=cp.with_suffix('.tmp.npz');np.savez_compressed(temp,irf=b_irf,lp=b_lp);temp.replace(cp);valid.append((b_irf,b_lp))
        except (ValueError,np.linalg.LinAlgError) as e:
            f={'replication':i,'reason':str(e)};save_json(failure,f);failures.append(f)
        if (i+1)%study.config['bootstrap_batch']==0:
            save_json(cache/'progress.json',{'requested':requested,'completed':i+1,'valid':len(valid),'failed':len(failures),'fingerprint':fingerprint})
            print(f'BOOTSTRAP {i+1}/{requested}: {len(valid)} valid, {len(failures)} rejected',flush=True)
    if valid:
        distribution=np.stack([v[0] for v in valid]);lp_distribution=np.stack([v[1] for v in valid])
        intervals={str(q):np.quantile(distribution,q,axis=0) for q in [.025,.16,.84,.975]}
        lp_intervals={str(q):np.quantile(lp_distribution,q,axis=0) for q in [.025,.16,.84,.975]}
    else:intervals={};lp_intervals={}
    sensitivity=[]
    for order in study.config['alternative_orders']:
        response,_=responses(model,H,[names.index(x) for x in order]);sensitivity.append({'name':'Order: '+', '.join(order),'kind':'identification','irf':response})
    for lag in study.config['lags']:
        f=fit_system(y,z,lag);response,_=responses(f,H);sensitivity.append({'name':f'{lag} quarterly lags','kind':'lag','stable':f['radius']<1,'irf':response})
    # Contiguous pre-pandemic sample; never delete interior quarters and join nonadjacent dates.
    pre=frame.index<'2020Q1'
    if pre.sum()>60:
        f=fit_system(y[pre],z[pre],p);response,_=responses(f,H);sensitivity.append({'name':'Pre-pandemic, through 2019Q4','kind':'sample','stable':f['radius']<1,'irf':response})
    complete=requested==study.config['bootstrap_replications'] and len(valid)>=.95*requested
    output={'schema_version':1,'state':'complete' if complete else 'validation_run','causal_release_eligible':bool(complete and diag['passed']),'variables':names,'units':['NFCI index points','GDP log growth, % q/q','GFCF log growth, % q/q','REER log change, % q/q; rise=appreciation','Inward FDI / quarterly GDP, %'],'sample':{'start':frame.index[0],'end':frame.index[-1],'observations':len(frame),'estimation_rows':model['rows']},'lag':p,'lag_selection':[{'p':m['p'],'bic':m['bic'],'rows':m['rows']} for m in candidates],'controls':['US real GDP log growth','Change in effective federal funds rate','Quarter seasonal indicators'],'impact_matrix':B,'coefficients':model['beta'],'residual_covariance':model['cov'],'irf':irf,'irf_intervals':intervals,'local_projections':{'irf':lp,'hac_standard_errors':hac,'bootstrap_intervals':lp_intervals,'boundary':'Same identified shocks, not independent causal evidence'},'fevd':fevd,'historical':{**hist,'periods':frame.index[model['start']:].tolist(),'observed':y[model['start']:]},'diagnostics':diag,'bootstrap':{'requested':requested,'completed':requested,'valid':len(valid),'rejected':failures,'conditional_on_selected_lag':True},'sensitivity':sensitivity,'identification':study.config['identification'],'boundary':'Estimated structural responses conditional on the declared restrictions. Failed diagnostics prevent a causal-results release.'}
    output=plain(output);save_json(study.run/'models/national.json',output)
    if complete:study.finish('national_models',[study.run/'models/national.json'],inputs,{'diagnostics_passed':diag['passed'],'valid_replications':len(valid)})
    else:study.unavailable('national_models','Full configured bootstrap not completed',{'requested':requested,'valid':len(valid)})
    return output
