"""Separately identified price/FX extension; never estimates or reruns a model.

acquire: preserve official responses locally. build: deterministic preparation,
validation and a read-back verified archive (also executed in the CPU Colab).
"""
from pathlib import Path
import argparse, csv, hashlib, io, json, math, statistics, zipfile
from datetime import datetime, timezone

PARENT = '4b63a4eef4770644f07f41375529d7123116a72ce633799510dccac397fbc0c4'
CONFIG = {'version': 1, 'parent': PARENT, 'start': 1996, 'end': 2025, 'base': 2025,
          'usd_deflator': 'A191RD3A086NBEA', 'brl_deflator': 'IPCA 1737/2266',
          'brl_method': 'sum(monthly USD * monthly mean BRL/USD * mean(base-year IPCA) / monthly IPCA)'}

def sha(data): return hashlib.sha256(data).hexdigest()
def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False), encoding='utf8')
def read(path): return json.loads(path.read_text(encoding='utf8'))
def valid(v): return isinstance(v, (int, float)) and math.isfinite(v)

def acquire(folder, run):
    import requests
    raw = folder/'raw'; raw.mkdir(parents=True, exist_ok=True)
    manifest = read(raw/'sources.json') if (raw/'sources.json').exists() else {}
    urls = {
        'us_gdp_deflator': ('https://fred.stlouisfed.org/graph/fredgraph.csv?id=A191RD3A086NBEA', 'BEA via FRED', 'Annual US GDP implicit price deflator, 2017=100'),
        'ipca_metadata': ('https://servicodados.ibge.gov.br/api/v3/agregados/1737/metadados', 'IBGE', 'IPCA table and variable definitions'),
        'ipca': ('https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/'+ '|'.join(f'{y}{m:02}' for y in range(1995,2026) for m in range(1,13))+'/variaveis/2266?localidades=N1[all]', 'IBGE SIDRA', 'Monthly IPCA index, December 1993=100'),
        'population': ('https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&date=1996:2025&per_page=20000', 'World Bank WDI', 'Observed annual total population; missing years retained')}
    for key, (url, provider, definition) in urls.items():
        old = manifest.get(key); target = raw/(key+('.csv' if key=='us_gdp_deflator' else '.json'))
        if old and target.exists() and sha(target.read_bytes())==old['sha256'] and old['url']==url: continue
        response = requests.get(url, timeout=(20,120)); response.raise_for_status()
        if key!='us_gdp_deflator': response.json()
        target.write_bytes(response.content)
        manifest[key] = {'file': target.name, 'url': url, 'provider': provider, 'definition': definition,
                         'sha256': sha(response.content), 'bytes': len(response.content), 'retrieved_at': datetime.now(timezone.utc).isoformat()}
        dump(raw/'sources.json', manifest)
        print('Preserved',key,len(response.content),flush=True)
    parent_manifest = read(run/'raw/sources.json')
    for key in ['sgs_22885','sgs_3698']:
        r = parent_manifest[key]; data=(run/'raw'/r['file']).read_bytes(); assert sha(data)==r['sha256']
        (raw/r['file']).write_bytes(data);manifest[key]=r
    # Freeze the exact already-reviewed annual export, not a refreshed nominal series.
    data=(run/'exports/public/observatory.json').read_bytes()
    (raw/'observatory.json').write_bytes(data)
    manifest['observatory']={'file':'observatory.json','sha256':sha(data),'bytes':len(data),'provider':'Reviewed national export','parent':PARENT}
    dump(raw/'sources.json',manifest)

def monthly(records):
    result={}
    for r in records:
        d,m,y=r['data'].split('/'); key=f'{y}-{m}'
        if key in result: raise ValueError('Duplicate monthly observation '+key)
        try: result[key]=float(r['valor'])
        except (TypeError,ValueError): result[key]=None
    return result

def annual_brl(year, flows, fx, prices, base):
    keys=[f'{year}-{m:02}' for m in range(1,13)]
    if not all(valid(flows.get(k)) and valid(fx.get(k)) and fx[k]>0 and valid(prices.get(k)) and prices[k]>0 for k in keys): return None
    return sum(flows[k]*1e6*fx[k]*base/prices[k] for k in keys)

def rolling(values, i, width, stdev=False):
    window=values[max(0,i-width+1):i+1]
    if len(window)!=width or not all(valid(v) for v in window):return None
    return statistics.stdev(window) if stdev else statistics.mean(window)

def build(folder):
    raw=folder/'raw'; manifest=read(raw/'sources.json')
    for record in manifest.values(): assert sha((raw/record['file']).read_bytes())==record['sha256'],record['file']
    b=read(raw/'observatory.json'); assert b['identity']==PARENT
    deflator={int(r['observation_date'][:4]):float(r['A191RD3A086NBEA']) for r in csv.DictReader(io.StringIO((raw/'us_gdp_deflator.csv').read_text(encoding='utf-8-sig'))) if r['A191RD3A086NBEA'] not in ('','.','NaN')}
    assert all(deflator.get(y,0)>0 for y in range(1996,2026))
    metadata=read(raw/'ipca_metadata.json'); assert any(v['id']==2266 and '1993' in v['nome'] for v in metadata['variaveis'])
    ipca={}
    for variable in read(raw/'ipca.json'):
        assert str(variable['id'])=='2266'
        for result in variable['resultados']:
            for series in result['series']:
                assert str(series['localidade']['id'])=='1'
                for period,value in series['serie'].items():
                    try: ipca[period[:4]+'-'+period[4:]]=float(value)
                    except ValueError: ipca[period[:4]+'-'+period[4:]]=None
    assert all(valid(ipca.get(f'2025-{m:02}')) for m in range(1,13))
    base=statistics.mean(ipca[f'2025-{m:02}'] for m in range(1,13))
    pop_data=read(raw/'population.json'); assert pop_data[0]['pages']==1
    population={(r['countryiso3code'],int(r['date'])):r['value'] for r in pop_data[1]}
    flows=monthly(read(raw/'sgs_22885.json'));fx=monthly(read(raw/'sgs_3698.json'))
    ids={c['id'] for c in b['countries']}; rows=[]
    fields=['current_usd','constant_usd','constant_usd_per_person','flow_gdp','constant_brl']
    for r in b['annual']:
        if r['country'] not in ids: continue
        year=r['year'];flow=r['flow_usd'];p=population.get((r['country'],year))
        real=flow*deflator[2025]/deflator[year] if valid(flow) else None
        row={'country':r['country'],'year':year,'current_usd':flow,'constant_usd':real,'population':p,
             'constant_usd_per_person':real/p if valid(real) and valid(p) and p>0 else None,
             'flow_gdp':r['flow_gdp'],'constant_brl':annual_brl(year,flows,fx,ipca,base) if r['country']=='BRA' else None}
        rows.append(row)
    for country in ids:
        group=sorted([r for r in rows if r['country']==country],key=lambda r:r['year'])
        assert [r['year'] for r in group]==list(range(1996,2026))
        for key in fields:
            values=[r[key] for r in group]
            for i,r in enumerate(group):
                r[key+'_ma3']=rolling(values,i,3)
                r[key+'_sd5']=rolling(values,i,5,True)
                previous=values[i-1] if i else None
                r[key+'_change']=values[i]-previous if valid(values[i]) and valid(previous) else None
    context=[]
    for year in range(1996,2026):
        keys=[f'{year}-{m:02}' for m in range(1,13)]
        mean_fx=statistics.mean(fx[k] for k in keys) if all(valid(fx.get(k)) for k in keys) else None
        this=ipca.get(f'{year}-12');previous=ipca.get(f'{year-1}-12')
        context.append({'year':year,'brl_per_usd':mean_fx,'ipca_pct':100*(this/previous-1) if valid(this) and valid(previous) and previous>0 else None,'us_gdp_deflator':deflator[year]})
    identity=sha(json.dumps({'config':CONFIG,'code':sha(Path(__file__).read_bytes()),'sources':{k:v['sha256'] for k,v in manifest.items()}},sort_keys=True).encode())
    output={'schema_version':1,'identity':identity,'parent':PARENT,'base_year':2025,'built_at':datetime.now(timezone.utc).isoformat(),'config':CONFIG,'sources':manifest,'rows':rows,'context':context,'ipca_base_mean':base}
    # Acceptance checks on actual data: 2025 identity, complete Brazilian months,
    # frozen nominal values, preserved signs/missingness and independent totals.
    for r in rows:
        if r['year']==2025 and valid(r['current_usd']):assert math.isclose(r['constant_usd'],r['current_usd'],rel_tol=1e-12)
        if valid(r['constant_usd']) and valid(r['current_usd']):assert (r['constant_usd']>=0)==(r['current_usd']>=0)
        if not valid(r['current_usd']):assert r['constant_usd'] is None
    assert sum(valid(r['constant_brl']) for r in rows)==30
    for component in b['components']:
        y=component['year']; observed=[flows.get(f'{y}-{m:02}') for m in range(1,13)]
        if all(valid(v) for v in observed) and valid(component['total']):assert math.isclose(sum(observed)*1e6,component['total'],abs_tol=.1)
    report={'state':'complete','identity':identity,'parent':PARENT,'rows':len(rows),'brazil_real_brl_years':30,'checks':['all source SHA256','annual base-year identity','signed flows and missingness','monthly BCB annual reconciliation','complete-month FX/IPCA conversion'],'models_rerun':False}
    export=folder/'exports';dump(export/'temporal.json',output);dump(folder/'validation.json',report)
    with (export/'temporal.csv').open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    package(folder,identity)
    print(json.dumps(report),flush=True)
    return output

def package(folder,identity):
    files={p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*') if p.is_file() and p.suffix!='.zip' and p.name!='backup.json'}
    files['reproducibility/fdi_temporal.py']=Path(__file__).read_bytes()
    manifest={k:{'sha256':sha(v),'bytes':len(v)} for k,v in files.items()}
    files['MANIFEST.json']=json.dumps(manifest,sort_keys=True,indent=2).encode()
    archive=folder/('fdi-temporal-'+identity[:16]+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,record in manifest.items():assert sha(z.read(name))==record['sha256']
    dump(folder/'backup.json',{'file':archive.name,'sha256':sha(archive.read_bytes()),'bytes':archive.stat().st_size,'members':len(files),'read_back_verified':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['acquire','build']);p.add_argument('--folder',type=Path,required=True);p.add_argument('--run',type=Path)
    a=p.parse_args()
    if a.stage=='acquire':acquire(a.folder,a.run)
    else:build(a.folder)
