"""Pinned Python Callaway--Sant'Anna estimator. No R or TWFE fallback.

This consumes an already audited, real municipal panel. Simulated data belong
only to estimator validation and never enter empirical release bundles.
"""
from importlib.metadata import version
import warnings
import numpy as np


def estimate_panel(panel, config, *, outcomes=None, replications=None):
    if version('moderndid') != '0.4.0':
        raise RuntimeError('Use the isolated pinned ModernDiD 0.4.0 Python environment')
    from moderndid import att_gt, aggte
    names=outcomes or config['models']['municipal_did']['outcomes']
    cov=config['models']['municipal_did']['covariates']
    draws=replications or config['bootstrap_replications'];seed=config['seed']
    data=panel.copy();data['municipality_id']=data.municipality_id.astype(int)
    if data[['municipality_id','year']].duplicated().any():raise ValueError('Duplicate municipality-year')
    years=set(data.year)
    if any(set(rows.year)!=years for _,rows in data.groupby('municipality_id')):
        raise ValueError('Principal sample must be balanced; no silent unit deletion by the estimator')
    results={}
    for name in names:
        required=['municipality_id','year','opening_year',*cov,name]
        if data[required].isna().any().any():raise ValueError('Incomplete outcome/covariate panel; no silent case deletion')
        with warnings.catch_warnings(record=True) as emitted:
            fit=att_gt(data=data,yname=name,tname='year',idname='municipality_id',gname='opening_year',
                xformla='~ '+' + '.join(cov),panel=True,allow_unbalanced_panel=False,
                control_group='notyettreated',anticipation=2,est_method='dr',base_period='universal',
                boot=True,cband=True,alpha=.05,biters=draws,clustervars=['municipality_id'],
                random_state=seed,n_jobs=1,backend='numpy')
            if fit.n_units!=data.municipality_id.nunique():raise ValueError('Estimator changed the audited municipality sample')
            kw=dict(type='dynamic',balance_e=5,na_rm=False,boot=True,cband=True,biters=draws,random_state=seed)
            dynamic=aggte(fit,min_e=-7,max_e=5,**kw)
            post=aggte(fit,min_e=1,max_e=5,**kw)
        critical=np.asarray(dynamic.critical_values,float)
        if critical.size==1:critical=np.full(len(dynamic.event_times),critical.item())
        standard_errors=np.asarray(dynamic.se_by_event,float).copy()
        reference=np.asarray(dynamic.event_times)==-3
        if reference.sum()!=1 or not np.array_equal(np.asarray(dynamic.att_by_event)[reference],[0.]):
            raise ValueError('Universal base must be the exact zero-normalized event year -3')
        # The pinned package returns NaN SE for the zero-variance normalized base.
        # This is a definition, not an estimated observation or repaired failure.
        standard_errors[reference]=0.;critical=critical.copy();critical[reference]=0.
        for label,values in [('effects',dynamic.att_by_event),('SE',standard_errors),('critical values',critical),('summary',[post.overall_att,post.overall_se])]:
            if not np.isfinite(values).all():raise ValueError('Unsupported/nonfinite '+label+': '+repr(np.asarray(values))+' at '+repr(np.asarray(dynamic.event_times)))
        if not np.array_equal(np.asarray(post.event_times),np.arange(1,6)):
            raise ValueError('Principal average requires all five post-opening years')
        results[name]={'state':'estimated_conditional_on_assumptions',
            'periods':np.asarray(dynamic.event_times).tolist(),'att':np.asarray(dynamic.att_by_event).tolist(),
            'se':standard_errors.tolist(),'simultaneous_critical_values':critical.tolist(),
            'normalization':'Event year -3 is identically zero by the universal-base definition; its confidence band is [0,0]. Package NaN at this zero-variance reference is retained in native package behavior, not interpreted as an estimated effect.',
            'overall':float(post.overall_att),'overall_se':float(post.overall_se),
            'pretest_pvalue':None if fit.wald_pvalue is None else float(fit.wald_pvalue),
            'municipalities':int(data.municipality_id.nunique()),
            'treated':int(data.loc[data.opening_year>0,'municipality_id'].nunique()),
            'comparison':'verified never-treated and not-yet-treated', 'anticipation':2,'reference_event_year':-3,
            'bootstrap':{'replications':draws,'seed':seed,'clustering':'municipality','simultaneous_bands':True},
            'warnings':[str(w.message) for w in emitted]}
    return {'estimator':'Python ModernDiD 0.4.0 / Callaway–Sant’Anna doubly robust ATT(g,t)',
        'outcomes':results,'language':'Python','inference':'municipality multiplier bootstrap'}
