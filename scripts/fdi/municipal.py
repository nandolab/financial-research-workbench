"""Eligibility gates for externally verified treatment events and municipal panels."""
from pathlib import Path
import shutil, subprocess
import pandas as pd
from .storage import save_json, read_json

def municipal_models(study):
    events=study.run/'prepared/verified-events.csv';panel=study.run/'prepared/municipal-panel.csv'
    target=study.run/'models/municipal.json'
    if not events.exists() or not panel.exists():
        result={'schema_version':1,'state':'unavailable','events':[], 'reason':'A source-verified operational-opening registry and harmonized IBGE/RAIS outcome panel are required; no treatment effects have been estimated.', 'required_event_fields':['event_id','municipality_id','operational_year','opening_source_url','foreign_investment_source_url','verified','sector','investor_country'],'required_panel_fields':['municipality_id','year','opening_year']+study.config['models']['municipal_did']['covariates']+study.config['models']['municipal_did']['outcomes'],'inference_boundary':'Municipal economic context is not investment treatment and cannot substitute for an identified intervention.'}
        save_json(target,result);study.unavailable('municipal_models',result['reason']);return result
    inputs=[events,panel]
    if study.cached('municipal_models',inputs):return read_json(target)
    e=pd.read_csv(events,dtype={'municipality_id':str});d=pd.read_csv(panel,dtype={'municipality_id':str})
    required=['event_id','municipality_id','operational_year','opening_source_url','foreign_investment_source_url','verified','sector','investor_country']
    if any(c not in e for c in required):raise ValueError('Incomplete investment-event provenance')
    if not e['verified'].astype(str).str.lower().eq('true').all():raise ValueError('Unverified events cannot enter a causal study')
    if not e[['opening_source_url','foreign_investment_source_url']].apply(lambda s:s.str.startswith('https://')).all().all():raise ValueError('Primary evidence URLs required')
    if e['event_id'].duplicated().any() or d[['municipality_id','year']].duplicated().any():raise ValueError('Duplicate event or panel row')
    for ident,rows in d.groupby('municipality_id'):
        treatment=e[e.municipality_id==ident]
        declared=rows.opening_year.fillna(0).unique()
        actual=int(treatment.operational_year.min()) if len(treatment) else 0
        if len(declared)!=1 or declared[0]!=actual:raise ValueError('Treatment assignment differs from verified event registry')
        if actual:
            needed=set(range(actual-7,actual+6))
            if not needed.issubset(set(rows.year)):raise ValueError('Insufficient clean pre/post coverage')
    rscript=shutil.which('Rscript')
    if not rscript:raise RuntimeError('Rscript is required for the prespecified did estimator; no substitute estimator is permitted')
    subprocess.run([rscript,str(study.project/'scripts/fdi/municipal_did.R'),str(panel),str(study.project/'research/fdi/study.json'),str(target)],check=True)
    result=read_json(target);result['events']=e.to_dict('records')
    states=[v['state'] for v in result['outcomes'].values()]
    result['state']='complete' if states and all(s=='estimated_conditional_on_assumptions' for s in states) else 'partial' if any(s=='estimated_conditional_on_assumptions' for s in states) else 'unavailable'
    result['reason']='All prespecified outcomes estimated, conditional on identification assumptions.' if result['state']=='complete' else 'At least one prespecified outcome failed eligibility or estimation; inspect per-outcome diagnostics.'
    save_json(target,result)
    study.finish('municipal_models',[target],inputs);return result
