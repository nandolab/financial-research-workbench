"""Use the author's pinned pySidraData client with preserved official responses.

Adds a separately versioned population extension. Never reseals or reruns the
completed national study, and never labels population as municipal FDI.
"""
from pathlib import Path
from datetime import datetime,timezone
from importlib.metadata import version
import argparse,hashlib,json,sys
import pandas as pd
from pySidraData import Client


def run(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);manifest_path=root/'sources.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf8')) if manifest_path.exists() else {}
    client=Client()
    def persist(response,*args,**kwargs):
        response.raise_for_status();key=hashlib.sha256(response.url.encode()).hexdigest()
        path=root/(key+'.json');path.write_bytes(response.content)
        manifest[response.url]={'file':path.name,'sha256':hashlib.sha256(response.content).hexdigest(),
            'bytes':len(response.content),'retrieved_at':datetime.now(timezone.utc).isoformat()}
        manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf8')
    client.session.hooks['response'].append(persist)
    original_get=client.session.get
    def cached_get(url,**kwargs):
        import requests
        url=requests.Request('GET',url).prepare().url
        record=manifest.get(url)
        if record:
            content=(root/record['file']).read_bytes()
            if hashlib.sha256(content).hexdigest()!=record['sha256']:raise ValueError('Cached IBGE response changed')
            response=requests.Response();response.status_code=200;response.url=url;response._content=content
            response.encoding='utf8';return response
        kwargs.setdefault('timeout',90);return original_get(url,**kwargs)
    client.session.get=cached_get
    meta=client.get_metadata('6579')
    if not any(str(v['id'])=='9324' for v in meta['variaveis']):raise ValueError('Population definition changed')
    base=client.BASE_URL+'/6579'
    periods=client.session.get(base+'/periodos').json()
    years=[int(v['id']) for v in periods if str(v['id']).isdigit() and 1996<=int(v['id'])<=2025]
    states=['11','12','13','14','15','16','17','21','22','23','24','25','26','27','28','29','31','32','33','35','41','42','43','50','51','52','53']
    output=[]
    for state in states:
        for start in range(0,len(years),6):
            selected=years[start:start+6]
            url=base+'/periodos/'+ '|'.join(map(str,selected))+'/variaveis/9324?localidades=N6[N3['+state+']]'
            data=client.session.get(url).json()
            for item in data:
                for result in item['resultados']:
                    for row in result['series']:
                        locality=row['localidade']
                        for year,value in row['serie'].items():
                            # SIDRA symbols retain missing status, never zero-fill.
                            numeric=float(value) if str(value).replace('.','',1).isdigit() else None
                            output.append({'id':locality['id'],'name':locality['nome'],'state':state,
                                'year':int(year),'population':numeric,'raw_value':value,'source_url':url})
        print('Population state complete:',state,flush=True)
    frame=pd.DataFrame(output)
    if frame[['id','year']].duplicated().any():raise ValueError('Duplicate municipality population')
    observed=frame[frame.population.notna()]
    if (observed.population<=0).any():raise ValueError('Invalid observed population')
    # Verify one real observation through the package's public data API too.
    preview_path=root/'pysidradata-sao-paulo-2025.csv'
    preview=pd.read_csv(preview_path) if preview_path.exists() else client.get_data(table_code='6579',territorial_level='6',ibge_territorial_code='3550308',period='2025',variable='9324')
    values=pd.to_numeric(preview['V'],errors='coerce').dropna()
    expected=observed[(observed.id=='3550308')&(observed.year==2025)].population
    if len(expected)!=1 or not values.eq(expected.iloc[0]).any():raise ValueError('pySidraData/direct official API discrepancy')
    preview.to_csv(preview_path,index=False)
    frame.to_csv(root/'municipal-population.csv',index=False)
    report={'state':'complete','kind':'official observed population, not FDI or a causal estimate',
        'package':'pySidraData','package_version':version('pySidraData'),
        'commit':'85a2b39c0cc5eec56d0a3605bbfa1d497899cc8e','sidrapy':version('sidrapy'),
        'table':'6579','variable':'9324','definition':meta,'years':sorted(years),
        'observations':len(frame),'observed':len(observed),'sources':len(manifest),
        'cross_client_check':'São Paulo 2025 matched','source_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'csv_sha256':hashlib.sha256((root/'municipal-population.csv').read_bytes()).hexdigest(),
        'gaps':'Unpublished census/estimate years remain missing. No interpolation or foreign-capital allocation.'}
    (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='definition'},ensure_ascii=False))
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();run(a.output)
