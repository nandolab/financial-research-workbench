"""Facure-informed identification checks and panel doubly robust ATT diagnostics.

The empirical primary estimator is Python ModernDiD att_gt(est_method='dr'). This module
audits its comparison sets and supplies an independently testable two-period
DR-DiD score. It never treats a project catalogue as proof of untreated status.
"""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm


def dr_att(delta,treated,x,*,bounds=(.05,.95),min_treated=5,min_controls=20,min_ess=15):
    """Normalized panel DR ATT using pretreatment covariates (not cross-sectional ATE).

    With overlap and conditional parallel trends, consistency requires either
    the comparison propensity model or the untreated change regression correct.
    Those statistical protections do not remove unobserved confounding.
    """
    delta=np.asarray(delta,float);treated=np.asarray(treated,int);x=np.asarray(x,float)
    if x.ndim==1:x=x[:,None]
    if not(len(delta)==len(treated)==len(x)) or not np.isfinite(delta).all() or not np.isfinite(x).all():raise ValueError('Nonfinite or mismatched comparison input')
    if not np.isin(treated,[0,1]).all():raise ValueError('Treatment must be binary')
    n1=int(treated.sum());n0=len(treated)-n1
    if n1<min_treated or n0<min_controls:raise ValueError('Insufficient treated or comparison municipalities')
    design=sm.add_constant(x,has_constant='add')
    if np.linalg.matrix_rank(design)<design.shape[1]:raise ValueError('Rank-deficient pretreatment covariates')
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        try:ps=sm.Logit(treated,design).fit(disp=False,maxiter=150).predict(design)
        except Exception as e:raise ValueError('Propensity model failed or separated') from e
    control=treated==0;exposed=~control
    if np.any((ps<bounds[0])|(ps>bounds[1])):raise ValueError('Positivity gate failed; no silent score clipping')
    if ps[exposed].min()<ps[control].min() or ps[exposed].max()>ps[control].max():raise ValueError('Treated municipalities outside comparison common support')
    odds=ps[control]/(1-ps[control]);ess=float(odds.sum()**2/np.square(odds).sum())
    if ess<min_ess:raise ValueError('Comparison effective sample size below threshold')
    fit=sm.OLS(delta[control],design[control]).fit();mu0=fit.predict(design)
    wt=treated/treated.mean();wc=np.zeros(len(treated));wc[control]=odds;wc/=wc.mean()
    score=(wt-wc)*(delta-mu0)
    return {'att':float(score.mean()),'n_treated':n1,'n_controls':n0,'control_ess':ess,'propensity_range':[float(ps.min()),float(ps.max())],'overlap_bounds':list(bounds),'control_weight_max':float((odds/odds.sum()).max()),'outcome_model':'OLS untreated outcome change','propensity_model':'logistic comparison-cohort membership','boundary':'Diagnostic panel DR-DiD score; primary uncertainty and aggregation use Python ModernDiD, not this diagnostic.'}


def audit_panel(events:pd.DataFrame,panel:pd.DataFrame,config:dict):
    """Block empirical estimation when treatment history or overlap is unsupported."""
    rules=config['audit'];cov=['baseline_population','baseline_gdp_per_capita','baseline_industry_share','baseline_employment_intensity']
    required=['municipality_id','year','opening_year','history_verified','history_source_url','baseline_year']+cov
    missing=[v for v in required if v not in panel]
    if missing:raise ValueError('Missing identification fields: '+', '.join(missing))
    if panel[['municipality_id','year']].duplicated().any():raise ValueError('Duplicate municipality-year')
    if not panel.history_verified.astype(str).str.lower().eq('true').all():raise ValueError('Untreated and treated histories must both be verified')
    if not panel.history_source_url.fillna('').str.startswith('https://').all():raise ValueError('Each comparison history needs a source')
    for ident,rows in panel.groupby('municipality_id'):
        if any(rows[c].nunique(dropna=False)!=1 for c in cov+['baseline_year','opening_year']):raise ValueError('Pretreatment covariates, baseline year or first opening change within municipality')
        if not np.isfinite(rows[cov].to_numpy(float)).all():raise ValueError('Missing baseline covariates')
        cohort=int(rows.opening_year.iloc[0]);declared=events[events.municipality_id.astype(str)==str(ident)]
        actual=int(declared.operational_year.min()) if len(declared) else 0
        if cohort!=actual:raise ValueError('Treatment history differs from opening registry')
        if cohort and int(rows.baseline_year.iloc[0])>cohort-3:raise ValueError('Baseline measured during anticipation or after opening')
        if cohort and not set(range(cohort-7,cohort+6)).issubset(set(rows.year)):raise ValueError('Five clean pre-periods plus anticipation and post-window unavailable')
    cohorts=sorted(int(g) for g in panel.opening_year.unique() if g>0);checks=[]
    if not cohorts:raise ValueError('No eligible treated cohort')
    if panel.baseline_year.nunique()!=1 or int(panel.baseline_year.iloc[0])>min(cohorts)-3:
        raise ValueError('All municipalities require one common, clean pretreatment covariate vintage')
    outcomes=['log_gdp_per_capita_deflated','formal_jobs_per_working_age_resident','log_real_formal_earnings']
    for g in cohorts:
        baseline=g-3
        for t in range(g,g+6):
            eligible=panel[(panel.opening_year==g)|(panel.opening_year==0)|(panel.opening_year>t+rules['anticipation_years'])]
            a=eligible[eligible.year==baseline].set_index('municipality_id');b=eligible[eligible.year==t].set_index('municipality_id')
            ids=a.index.intersection(b.index);a=a.loc[ids];b=b.loc[ids]
            if not len(ids):raise ValueError('Empty cohort comparison')
            if a.baseline_year.max()>baseline:raise ValueError('Comparison baseline is not pretreatment')
            for outcome in outcomes:
                if outcome not in a or outcome not in b:raise ValueError('Missing prespecified outcome: '+outcome)
                result=dr_att(b[outcome].to_numpy()-a[outcome].to_numpy(),(a.opening_year==g).astype(int),a[cov].to_numpy(),bounds=rules['overlap_probability_bounds'],min_treated=rules['minimum_treated_per_cohort'],min_controls=rules['minimum_controls_per_comparison'],min_ess=rules['minimum_control_effective_sample_size'])
                checks.append({'cohort':g,'year':t,'outcome':outcome,**result})
    return {'state':'passed_input_and_overlap_checks','comparisons':checks,'causal_proof':False,'remaining_assumptions':config['assumptions'],'boundary':'Empirical pretrend/placebo and spillover checks remain required; passing overlap is not causal identification.'}
