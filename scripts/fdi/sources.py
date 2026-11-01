"""Official-source acquisition. Original bytes and request identities are retained."""
from __future__ import annotations
import json, re, time, shutil
from pathlib import Path
from urllib.parse import urlencode
import requests
from .storage import save_json, read_json, file_hash, now

BCB_POSITIONS='https://www.bcb.gov.br/content/estatisticas/Documents/Tabelas_especiais/TabelasCompletasPosicaoIDP.xlsx'
IBGE='https://servicodados.ibge.gov.br/api'
FRED='https://fred.stlouisfed.org/graph/fredgraph.csv?id='
WB='https://api.worldbank.org/v2/'
WORLD='https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson'

class Acquisition:
    def __init__(self, study):
        self.study=study;self.raw=study.run/'raw';self.manifest=self.raw/'sources.json'
        self.records=read_json(self.manifest) if self.manifest.exists() else {}
        self.previous=[]
        for p in sorted(study.root.glob('runs/*/raw/sources.json')):
            if p!=self.manifest:
                self.previous.append((p.parent,read_json(p)))
    def get(self,key,url,provider,definition,required=True):
        previous=self.records.get(key)
        if previous and previous.get('status')=='observed' and previous.get('url')==url:
            path=self.raw/previous['file']
            if path.exists() and file_hash(path)==previous['sha256']:return path
        for folder,records in self.previous:
            record=records.get(key)
            if record and record.get('status')=='observed' and record.get('url')==url:
                cached=folder/record['file']
                if cached.exists() and file_hash(cached)==record['sha256']:
                    target=self.raw/record['file'];shutil.copyfile(cached,target)
                    self.records[key]=record;save_json(self.manifest,self.records)
                    return target
        try:
            for attempt in range(3):
                response=requests.get(url,timeout=(20,120),headers={'User-Agent':'FernandoBarbosa-FDIResearch/1.0'})
                if response.status_code not in (429,500,502,503,504):break
                time.sleep(min(10,2**attempt))
            response.raise_for_status()
            data=response.content
            ctype=response.headers.get('content-type','')
            if 'json' in ctype or url==WORLD:
                json.loads(data)
            path=self.raw/(key+('.xlsx' if 'xlsx' in url else '.xls' if '.xls' in url else '.csv' if 'fredgraph' in url else '.json'))
            path.write_bytes(data)
            self.records[key]={'status':'observed','file':path.name,'sha256':file_hash(path),'bytes':len(data),'url':url,'provider':provider,'definition':definition,'retrieved_at':now(),'content_type':ctype}
            save_json(self.manifest,self.records)
            print(f'SOURCE {key}: {len(data):,} bytes, SHA256 {file_hash(path)}',flush=True)
            return path
        except Exception as exc:
            self.records[key]={'status':'unavailable','url':url,'provider':provider,'definition':definition,'reason':str(exc),'checked_at':now()}
            save_json(self.manifest,self.records)
            if required:raise
            return None
    def json(self,key,url,provider,definition,required=True):
        p=self.get(key,url,provider,definition,required)
        return read_json(p) if p else None

def acquire(study,municipal=True):
    a=Acquisition(study)
    countries=a.json('wb_countries',WB+'country?format=json&per_page=400','World Bank','Country metadata; exclude regional/income aggregates')
    if not isinstance(countries,list) or len(countries)!=2:raise ValueError('Unexpected World Bank metadata')
    for code in ['BX.KLT.DINV.CD.WD','BX.KLT.DINV.WD.GD.ZS','NY.GDP.MKTP.CD']:
        a.get('wb_'+code,WB+'country/all/indicator/'+code+'?'+urlencode({'format':'json','date':'1996:2025','per_page':20000}),'World Bank',code+'; annual observations, gaps retained')
    a.get('world_boundaries',WORLD,'Natural Earth','Admin-0, 1:110m; contemporary boundaries, historical charts do not imply constant historical borders')
    a.get('bcb_positions',BCB_POSITIONS,'BCB','IDP positions, investor definitions, joint sectors and census geographic allocations; table-specific coverage')
    a.get('bcb_flow_matrix','https://www.bcb.gov.br/ftp/notaecon/IDP_matriz_pais_vs_setor_p.xlsx','BCB','Published country-sector equity flow matrix',False)
    a.get('bcb_bilateral_flows','https://www.bcb.gov.br/ftp/notaecon/InvEstrp.xls','BCB','Equity flows by immediate country and sector, not total FDI',False)
    # Monthly flows; do not substitute the net assets-minus-liabilities series 22864.
    for code,definition in [(22885,'Inward IDP, net inflows, USD millions'),(22891,'Inward equity excluding reinvested earnings, USD millions'),(22892,'Reinvested earnings in Brazil, USD millions'),(22893,'Intercompany debt liabilities, USD millions'),(3698,'Period-average BRL/USD selling exchange rate')]:
        a.get('sgs_'+str(code),f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados?'+urlencode({'formato':'json','dataInicial':'01/01/1995','dataFinal':'31/12/2025'}),'BCB SGS',definition)
    for code,definition in [('NFCI','US financial conditions, weekly'),('GDPC1','US real GDP, seasonally adjusted annual-rate level; quarterly'),('FEDFUNDS','Effective federal funds rate, monthly'),('RBBRBIS','BIS broad real effective exchange rate for Brazil, monthly; increase means appreciation')]:
        a.get('fred_'+code,FRED+code,'Federal Reserve / BIS',definition)
    periods='|'.join(f'{y}{q:02}' for y in range(1996,2026) for q in range(1,5))
    a.get('ibge_quarterly',f'{IBGE}/v3/agregados/1621/periodos/{periods}/variaveis/584?localidades=N1[all]&classificacao=11255[90707,93406]','IBGE SIDRA 1621','Seasonally adjusted chained volume indices: GDP and gross fixed capital formation')
    a.get('ibge_quarterly_nominal',f'{IBGE}/v3/agregados/1846/periodos/{periods}/variaveis/585?localidades=N1[all]&classificacao=11255[90707]','IBGE SIDRA 1846','Quarterly nominal GDP, BRL millions')
    states=a.json('ibge_states',IBGE+'/v1/localidades/estados','IBGE','Official state IDs and names')
    a.get('brazil_states_geometry',IBGE+'/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson&qualidade=minima&intrarregiao=UF','IBGE','State boundaries; actual vintage retained from response')
    all_cities=a.json('ibge_municipalities',IBGE+'/v1/localidades/municipios','IBGE','Official municipality identifiers including check digits; nested current administrative regions')
    # Total/GVA values are BRL thousands. Sector gaps in 2022–23 are retained.
    years='|'.join(map(str,range(2002,2024)))
    a.get('ibge_state_accounts',f'{IBGE}/v3/agregados/5938/periodos/{years}/variaveis/37|498|513|517|6575|525?localidades=N3[all]','IBGE SIDRA 5938','State GDP and economic structure, reference-2010 series')
    if municipal:
        for state in states:
            state_id=str(state['id'])
            a.get('municipal_geometry_'+state_id,f'{IBGE}/v3/malhas/estados/{state_id}?formato=application/vnd.geo%2Bjson&qualidade=minima&intrarregiao=municipio','IBGE','Municipal boundaries, contemporary vintage')
            for first in range(2002,2024,6):
                window='|'.join(map(str,range(first,min(first+6,2024))))
                a.get(f'municipal_accounts_{state_id}_{first}',f'{IBGE}/v3/agregados/5938/periodos/{window}/variaveis/37|498|513|517|6575|525?localidades=N6[N3[{state_id}]]','IBGE SIDRA 5938','Municipal GDP/GVA, BRL thousands; bounded cell budget; null/suppressed values retained',False)
        # GDP-per-capita is from the official research API, revised series 47001.
        # Its locality keys omit the check digit, so joins explicitly restore official 7-digit IDs.
        ids=[str(c['id']) for c in all_cities]
        for start in range(0,len(ids),150):
            batch='|'.join(ids[start:start+150])
            a.get(f'municipal_percap_{start:05}',f'{IBGE}/v1/pesquisas/38/indicadores/47001/resultados/{batch}','IBGE GDP municipalities','Revised municipal GDP per capita, BRL/person, original year coverage',False)
    expected=[k for k,v in a.records.items() if v['status']=='observed']
    outputs=[a.raw/a.records[k]['file'] for k in expected]+[a.manifest]
    study.finish('acquisition',outputs,details={'sources':len(expected),'municipal':municipal,'missing':[k for k,v in a.records.items() if v['status']!='observed']})
    return a.records
