"""Public-safe, source-audited additions without altering frozen native models."""
from pathlib import Path
import json
import pandas as pd
from fdi.storage import read_json,save_json,file_hash


def enrich(study,bundle,destination):
    folder=study.run/'extensions/ibge';report_path=folder/'report.json'
    if not report_path.exists():return
    report=read_json(report_path);manifest=read_json(folder/'sources.json')
    if file_hash(folder/'sources.json')!=report['source_manifest_sha256']:raise ValueError('Population source manifest mismatch')
    if file_hash(folder/'municipal-population.csv')!=report['csv_sha256']:raise ValueError('Population table hash mismatch')
    for record in manifest.values():
        if file_hash(folder/record['file'])!=record['sha256']:raise ValueError('Population raw response changed')
    pop=pd.read_csv(folder/'municipal-population.csv',dtype={'id':str,'state':str})
    if pop[['id','year']].duplicated().any():raise ValueError('Population duplicate')
    bundle['population_extension']={k:v for k,v in report.items() if k!='definition'}
    bundle['source_manifest']['ibge_population_pysidradata']={'status':'observed','provider':'IBGE / pySidraData',
        'url':'https://sidra.ibge.gov.br/tabela/6579','definition':'Resident population estimates, persons. Actual published years only; no census-year interpolation.',
        'sha256':report['source_manifest_sha256'],'retrieved_at':max(x['retrieved_at'] for x in manifest.values())}
    for state,rows in pop.groupby('state'):
        source=study.run/'prepared'/f'municipal-{state}.json'
        data=read_json(source);lookup={(r['id'],r['year']):r for r in data['observations']}
        for row in rows.to_dict('records'):
            key=(row['id'],int(row['year']))
            if key not in lookup:
                lookup[key]={'id':row['id'],'name':row['name'],'year':int(row['year'])}
            lookup[key]['population']=None if pd.isna(row['population']) else int(row['population'])
        data['observations']=sorted(lookup.values(),key=lambda r:(r['id'],r['year']))
        data['population_coverage']=bundle['population_extension']
        for target in [study.run/'exports/public'/source.name,Path(destination)/source.name]:save_json(target,data)
