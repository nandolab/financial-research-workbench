"""Strict read-only validation of saved national results, then derived public exports.

No bootstrap is rerun. Native model files and verified archives remain unchanged.
Forecast-horizon FEVD and separated historical baseline terms are derived from
the verified saved system and explicitly attributed in the public bundle.
"""
from pathlib import Path
import argparse,json,sys
import numpy as np
import pandas as pd
from fdi.storage import Study,read_json,save_json,file_hash,digest,canonical,verify_archive
from fdi.models import fit_system,responses,local_projections,historical,plain
from fdi.export import export


def forecast_fevd(irf):
    # h-step forecast error uses innovations Psi_0 through Psi_(h-1).
    sums=np.cumsum(np.asarray(irf,float)**2,axis=0)[:-1]
    return sums/sums.sum(axis=2,keepdims=True)


def review(study,archive,destination):
    manifest=verify_archive(archive);native_path=study.run/'models/national.json';native_sha=file_hash(native_path)
    if manifest.get('models/national.json')!=native_sha:raise ValueError('Imported model does not match verified Colab archive')
    ident=read_json(study.run/'identity.json')
    if ident['identity']!=study.identity or ident['code_sha256']!=study.code_hash:raise ValueError('Frozen study/code identity mismatch')
    native=read_json(native_path)
    if native['state']!='complete' or native['bootstrap']['valid']<1900 or native['bootstrap']['requested']!=2000:raise ValueError('Full prespecified bootstrap not completed')
    frame=pd.read_csv(study.run/'prepared/quarterly.csv',index_col=0);names=study.config['variables'];y=frame[names].to_numpy(float)
    z=np.column_stack([frame[['us_gdp_growth','fedfunds_change']].to_numpy(float),pd.get_dummies(frame['quarter'],drop_first=True).to_numpy(float)])
    fitted=fit_system(y,z,native['lag']);irf,B=responses(fitted,12);lp,hac=local_projections(y,z,fitted,12,True);hist=historical(y,z,fitted)
    for expected,actual,label in [(fitted['beta'],native['coefficients'],'coefficients'),(B,native['impact_matrix'],'structural impact'),(irf,native['irf'],'IRF'),(lp,native['local_projections']['irf'],'LP'),(hac,native['local_projections']['hac_standard_errors'],'HAC'),(hist['baseline'],native['historical']['baseline'],'historical baseline')]:
        if not np.allclose(expected,actual,atol=1e-10,rtol=1e-9):raise ValueError('Reproduction mismatch: '+label)
    draws=[];lp_draws=[]
    for i in range(2000):
        rel=f'checkpoints/national-bootstrap/{i:05}.npz';p=study.run/rel
        if not p.exists():
            failed=f'checkpoints/national-bootstrap/{i:05}.failed.json'
            if failed not in manifest:raise ValueError('Missing deterministic replication')
            continue
        if file_hash(p)!=manifest.get(rel):raise ValueError('Saved bootstrap draw differs from archive')
        with np.load(p,allow_pickle=False) as c:draws.append(c['irf']);lp_draws.append(c['lp'])
    for field,draw in [(native['irf_intervals'],draws),(native['local_projections']['bootstrap_intervals'],lp_draws)]:
        distribution=np.stack(draw)
        for q in [.025,.16,.84,.975]:
            if not np.allclose(np.quantile(distribution,q,axis=0),field[str(q)],atol=1e-12,rtol=1e-10):raise ValueError('Saved uncertainty does not reproduce')
    p=fitted['p'];initial=np.zeros_like(y);initial[:p]=y[:p]
    for t in range(p,len(y)):
        for lag in range(1,p+1):initial[t]+=fitted['A'][lag-1]@initial[t-lag]
    initial=initial[p:];deterministic=hist['baseline']-initial
    if not np.allclose(y[p:],hist['contributions'].sum(axis=2)+initial+deterministic,atol=1e-9):raise ValueError('Historical components do not reconcile')
    bundle=export(study,destination)
    bundle['national']['fevd']=plain(forecast_fevd(irf))
    bundle['national']['historical']['initial_conditions']=plain(initial)
    bundle['national']['historical']['deterministic_terms']=plain(deterministic)
    bundle['national']['review']={'state':'passed','native_model_sha256':native_sha,'archive_sha256':file_hash(archive),'review_code_sha256':file_hash(Path(__file__)),'verified_saved_draws':len(draws),'recomputed_fields':['coefficients','structural impacts','IRFs','LPs','HAC standard errors','bootstrap quantiles','historical decomposition'],'derived_fields':['FEVD: h-step forecast horizon uses Psi_0 through Psi_(h-1); native archive summary retained unchanged','Historical initial-condition and deterministic components separated without refitting'], 'no_bootstrap_reexecution':True}
    design=read_json(study.project/'research/fdi/causal-design.json')
    bundle['causal_design']=design
    bundle['study']['models']['municipal_did']['estimator']='Python ModernDiD 0.4.0 / Callaway–Sant’Anna doubly robust ATT(g,t)'
    bundle['study']['municipal_language']='Python only; separately versioned causal extension'
    from causal.enrich import enrich
    enrich(study,bundle,destination)
    bundle['export_identity']=digest(canonical({'study':study.identity,'national':native_sha,'review':bundle['national']['review'],'causal_design':design,'municipal':bundle['municipal'],'population_extension':bundle.get('population_extension'),'enrich_code':file_hash(study.project/'scripts/causal/enrich.py')}))
    save_json(study.run/'exports/review.json',bundle['national']['review'])
    for target in [study.run/'exports/public/observatory.json',Path(destination)/'observatory.json']:save_json(target,bundle)
    study.finish('export',list((study.run/'exports/public').iterdir())+[study.run/'exports/validation.json',study.run/'exports/review.json'],[study.run/'prepared/descriptive.json']+list((study.run/'models').glob('*.json')),{'derived_export_identity':bundle['export_identity'],'review_code_sha256':file_hash(Path(__file__))})
    if file_hash(native_path)!=native_sha:raise ValueError('Native model mutated during review')
    print(json.dumps({'review':'passed','saved_draws':len(draws),'export_identity':bundle['export_identity'],'national':native['state'],'municipal':bundle['municipal']['state']}))
    return bundle


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('artifacts/local/fdi'));ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--destination',type=Path,default=Path('web/public/data/fdi'));a=ap.parse_args()
    review(Study(a.root,Path(__file__).resolve().parents[1]),a.archive,a.destination)
