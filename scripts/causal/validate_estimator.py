"""Known-effect estimator validation; never a Brazil empirical result."""
from pathlib import Path
import argparse,json,sys
import numpy as np
import pandas as pd
from .estimate import estimate_panel


def validate():
    seed=20261031;rng=np.random.default_rng(seed);n=800
    x=rng.uniform(-1,1,(n,4));g=rng.choice([0,2010,2012],n,p=[.5,.25,.25]);unit=rng.normal(size=n)
    rows=[]
    for i in range(n):
        for year in range(2003,2018):
            effect=1.8 if g[i] and year>=g[i] else 0.
            y=unit[i]+.1*(year-2003)+.15*(year-2003)*x[i,0]+effect+rng.normal(0,.15)
            rows.append([i+1,year,g[i],*x[i],y])
    cov=['baseline_population','baseline_gdp_per_capita','baseline_industry_share','baseline_employment_intensity']
    panel=pd.DataFrame(rows,columns=['municipality_id','year','opening_year',*cov,'generated_outcome'])
    config={'seed':seed,'bootstrap_replications':199,'models':{'municipal_did':{'covariates':cov,'outcomes':['generated_outcome']}}}
    output=estimate_panel(panel,config)['outcomes']['generated_outcome']
    expected=1.8;estimate=output['overall'];se=output['overall_se']
    if abs(estimate-expected)>.12 or not estimate-1.96*se<expected<estimate+1.96*se:
        raise AssertionError('Known generated effect not recovered with interval coverage')
    repeated=estimate_panel(panel,config)['outcomes']['generated_outcome']
    if output!=repeated:raise AssertionError('Fixed-seed estimator did not reproduce exactly')
    return {'state':'passed','kind':'generated estimator test — not Brazil findings','expected_effect':expected,
        'estimated_effect':estimate,'clustered_se':se,'municipalities':n,'replications':199,
        'seed':seed,'deterministic_replay':'passed','reference_event_year':-3,'implementation':'Python ModernDiD 0.4.0'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    result=validate();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8');print(json.dumps(result))
