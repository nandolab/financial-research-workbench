"""Validated website bundle and source-backed publication figures."""
from pathlib import Path
import json, shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .storage import read_json, save_json, now, file_hash

def validate(study):
    d=read_json(study.run/'prepared/descriptive.json');checks=[]
    for r in d['reconciliation']:
        if abs(r['difference'])>max(1e3,r['expected']*1e-6):raise ValueError(f"BCB country total does not reconcile: {r['table']} {r['year']}")
    for r in d['components']:
        if r.get('reconciliation_difference') is not None and abs(r['reconciliation_difference'])>1e6:raise ValueError('FDI components do not reconcile')
    seen=set()
    for r in d['annual']:
        key=(r['country'],r['year'])
        if key in seen:raise ValueError('Duplicate country-year')
        seen.add(key)
        if r.get('flow_usd') is not None and r.get('flow_gdp') is not None and r.get('gdp_usd'):
            computed=100*r['flow_usd']/r['gdp_usd']
            if abs(computed-r['flow_gdp'])>.02:checks.append({'check':'World Bank denominator consistency','country':r['country'],'year':r['year'],'difference_pp':computed-r['flow_gdp']})
    sources=read_json(study.run/'raw/sources.json')
    for name,r in sources.items():
        if r['status']=='observed' and file_hash(study.run/'raw'/r['file'])!=r['sha256']:raise ValueError('Raw source hash mismatch: '+name)
    result={'state':'passed_with_source_notes' if checks else 'passed','checked_at':now(),'annual_records':len(seen),'source_records':len(sources),'notes':checks,'boundary':'Validation checks numeric/source integrity, not economic causal identification.'}
    save_json(study.run/'exports/validation.json',result);return result

def export(study,destination=None):
    d=read_json(study.run/'prepared/descriptive.json');validation=validate(study)
    national=read_json(study.run/'models/national.json') if (study.run/'models/national.json').exists() else {'state':'not_run','causal_release_eligible':False,'reason':'National analysis has not completed'}
    municipal=read_json(study.run/'models/municipal.json') if (study.run/'models/municipal.json').exists() else {'state':'not_run','events':[],'reason':'Municipal treatment registry not yet verified'}
    # Show precise source status; never turn unavailable model outputs into zero estimates.
    source_meta={k:{a:v for a,v in r.items() if a not in ['file']} for k,r in d.pop('sources').items()}
    bundle={**d,'identity':study.identity,'built_at':now(),'source_manifest':source_meta,'validation':validation,'national':national,'municipal':municipal,'study':study.config,'research_status':{'descriptive':'observed','national':national['state'],'national_diagnostics':national.get('diagnostics',{}).get('passed',False),'municipal':municipal['state'],'complete_causal_study':bool(national.get('causal_release_eligible') and municipal.get('state')=='complete')}}
    out=study.run/'exports/public';out.mkdir(parents=True,exist_ok=True)
    save_json(out/'observatory.json',bundle)
    for p in (study.run/'prepared').glob('*.geo.json'):shutil.copyfile(p,out/p.name)
    for p in (study.run/'prepared').glob('municipal-*.json'):shutil.copyfile(p,out/p.name)
    import pandas as pd
    pd.DataFrame(d['annual']).to_csv(out/'annual-observations.csv',index=False)
    figures(study,bundle)
    if destination:
        dest=Path(destination);dest.mkdir(parents=True,exist_ok=True)
        for p in out.iterdir():shutil.copyfile(p,dest/p.name)
        for p in (study.run/'figures').glob('*'):shutil.copyfile(p,dest/p.name)
    study.finish('export',list(out.iterdir())+[study.run/'exports/validation.json'],[study.run/'prepared/descriptive.json']+list((study.run/'models').glob('*.json')))
    return bundle

def figures(study,bundle):
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#586374','text.color':'#081b41','svg.fonttype':'none'})
    br=sorted([r for r in bundle['annual'] if r['country']=='BRA'],key=lambda x:x['year'])
    fig,axs=plt.subplots(2,1,figsize=(11,7),sharex=True,layout='constrained')
    for ax,field,label in [(axs[0],'flow_usd','Annual inward FDI · US$ billion'),(axs[1],'flow_gdp','Annual inward FDI · % of GDP')]:
        ax.plot([r['year'] for r in br],[r.get(field,np.nan)/(1e9 if field=='flow_usd' else 1) if r.get(field) is not None else np.nan for r in br],color='#167c80',linewidth=2)
        ax.set_ylabel(label);ax.axhline(0,color='#d9dfe8',linewidth=.7);ax.grid(axis='y',alpha=.15)
    fig.suptitle('Foreign direct investment into Brazil, 1996–2025',fontsize=17)
    fig.supxlabel('Source: World Bank WDI · source snapshot '+bundle['built_at'][:10]+' · Fernando Barbosa')
    for ext in ['svg','png']:fig.savefig(study.run/'figures'/f'01-investment-trajectory.{ext}',dpi=180)
    plt.close(fig)
    for basis in ['immediate','ultimate']:
        records=bundle['origins'];year=max(r['year'] for r in records)
        rows=sorted([r for r in records if r['year']==year and r['basis']==basis],key=lambda x:x['value_usd'],reverse=True)[:10][::-1]
        fig,ax=plt.subplots(figsize=(10,6),layout='constrained');ax.barh([r['name'] for r in rows],[r['value_usd']/1e9 for r in rows],color='#167c80');ax.set_xlabel('Inward equity position · US$ billion');ax.set_title(f'Investor countries, {year} · {basis} attribution');fig.supxlabel('Source: BCB IDP positions workbook · Fernando Barbosa')
        for ext in ['svg','png']:fig.savefig(study.run/'figures'/f'02-investor-origins-{basis}.{ext}',dpi=180)
        plt.close(fig)
