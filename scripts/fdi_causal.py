"""Primary municipal causal workflow with independent, explicit provenance.

Keeps the completed national study and its bootstrap unchanged. No empirical
estimate is manufactured when verified exposure histories or outcomes are absent.
"""
from pathlib import Path
import argparse,json
import pandas as pd
from causal.audit import audit_panel
from fdi.storage import Study,read_json,save_json,canonical,digest,file_hash


def execute(study):
    design_path=study.project/'research/fdi/causal-design.json';design=read_json(design_path)
    events=study.run/'prepared/verified-events.csv';panel=study.run/'prepared/municipal-panel.csv';target=study.run/'models/municipal.json'
    sources=[Path(__file__),study.project/'scripts/causal/audit.py',study.project/'scripts/causal/estimate.py',study.project/'scripts/causal/validate_estimator.py',study.project/'research/fdi/requirements-causal.txt',design_path]
    simulation=study.run/'models/did-estimator-simulation.json'
    identity=digest(canonical({'parent':study.identity,'code':{p.relative_to(study.project).as_posix():file_hash(p) for p in sources},'inputs':{p.relative_to(study.run).as_posix():file_hash(p) if p.exists() else None for p in [events,panel,simulation,study.run/'extensions/python-environment.json']}}))
    previous=read_json(target) if target.exists() else {}
    if previous.get('causal_identity')==identity and previous.get('state')=='complete':return previous
    result={'schema_version':1,'state':'unavailable','causal_release_eligible':False,'causal_identity':identity,'parent_national_study':study.identity,'events':[],'design':design,'required_event_fields':['event_id','municipality_id','operational_year','opening_source_url','foreign_investment_source_url','verified','sector','investor_country'],'required_panel_fields':['municipality_id','year','opening_year','history_verified','history_source_url','baseline_year']+study.config['models']['municipal_did']['covariates']+study.config['models']['municipal_did']['outcomes']}
    if not events.exists() or not panel.exists():
        result['reason']='Verified operational-opening and prior-exposure histories, defensible comparison municipalities and the harmonized IBGE/RAIS outcome panel are not yet available. No local causal effect is estimated.'
        result['identification_audit']={'state':'blocked_missing_inputs','treatment_registry':events.exists(),'outcome_panel':panel.exists(),'bcb_boundary':'Individual foreign-capital census records are confidential; published aggregates cannot classify untreated municipalities.'}
    else:
        if not simulation.exists() or read_json(simulation).get('state')!='passed':raise ValueError('Pinned Python estimator validation must pass first')
        e=pd.read_csv(events,dtype={'municipality_id':str});d=pd.read_csv(panel,dtype={'municipality_id':str})
        if not set(result['required_event_fields']).issubset(e.columns):raise ValueError('Incomplete operational/ownership evidence')
        if not e.verified.astype(str).str.lower().eq('true').all():raise ValueError('Unverified opening records')
        for key in ['opening_source_url','foreign_investment_source_url']:
            if not e[key].fillna('').str.startswith('https://').all():raise ValueError('Primary-source URLs required')
        result['identification_audit']=audit_panel(e,d,design)
        from causal.estimate import estimate_panel
        result.update(estimate_panel(d,study.config));result['events']=e.to_dict('records')
        supported=all(v.get('state')=='estimated_conditional_on_assumptions' for v in result['outcomes'].values())
        pretrends=all(v.get('pretest_pvalue') is not None and v['pretest_pvalue']>=.05 for v in result['outcomes'].values())
        # Substantive design review and prespecified sensitivity evidence are separate
        # from a non-rejected statistical pretest. They cannot be silently assumed.
        evidence=study.run/'prepared/identification-review.json'
        audit=read_json(evidence) if evidence.exists() else {}
        required=['conditional_parallel_trends_defensible','first_exposure_histories_verified','spillover_review_passed','placebo_checks_completed','anticipation_sensitivity_completed','never_treated_sensitivity_completed','neighbor_exclusion_completed','estimator_simulation_passed']
        result['remaining_release_checks']=[k for k in required if audit.get(k) is not True]
        result['causal_release_eligible']=bool(supported and pretrends and not result['remaining_release_checks'])
        result['state']='complete' if result['causal_release_eligible'] else 'partial'
        result['reason']='Effects estimated with supported comparisons and completed identification review.' if result['causal_release_eligible'] else 'Statistical estimates remain conditional; incomplete sensitivity or identification evidence blocks causal interpretation.'
    save_json(target,result);save_json(study.run/'models/municipal-design.json',design)
    study.finish('municipal_causal_audit',[target,study.run/'models/municipal-design.json'],[p for p in [events,panel] if p.exists()],{'causal_identity':identity,'state':result['state']})
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('artifacts/local/fdi'));a=ap.parse_args();s=Study(a.root,Path(__file__).resolve().parents[1]);r=execute(s)
    print(json.dumps({'state':r['state'],'causal_identity':r['causal_identity'],'reason':r['reason']}));print(s.backup('municipal-audit'))
