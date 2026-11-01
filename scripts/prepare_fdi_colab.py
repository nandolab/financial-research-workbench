"""Build a self-contained, private-study Colab notebook from the exact local source."""
from pathlib import Path
import argparse,base64,hashlib,io,json,textwrap,zipfile,inspect
import nbformat as nbf

ROOT=Path(__file__).resolve().parents[1]

def build(seed_name='',seed_sha=''):
    files=[ROOT/'scripts/fdi_pipeline.py',*sorted((ROOT/'scripts/fdi').glob('*.py')),*sorted((ROOT/'scripts/fdi').glob('*.R')),*sorted((ROOT/'research/fdi').glob('*'))]
    blob=io.BytesIO()
    with zipfile.ZipFile(blob,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:
            if p.is_file():
                info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),date_time=(2000,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(info,p.read_bytes())
    source=blob.getvalue();sha=hashlib.sha256(source).hexdigest();encoded=base64.b64encode(source).decode('ascii')
    notebook=nbf.v4.new_notebook();cells=[]
    def md(s):
        source=inspect.cleandoc(s);cells.append(nbf.v4.new_markdown_cell(source,id=hashlib.sha256(('md'+str(len(cells))+source).encode()).hexdigest()[:8]))
    def code(s):
        source=textwrap.dedent(s).strip();cells.append(nbf.v4.new_code_cell(source,id=hashlib.sha256(('code'+str(len(cells))+source).encode()).hexdigest()[:8]))
    md('''# Brazil FDI Observatory
    **Fernando Barbosa · Independent economics research · 1996–2025**

    A dedicated CPU study of investment patterns, structural drivers and economic effects.
    This notebook contains its exact research scripts. It never imports or reruns the Financial Intelligence models or LangSmith experiments.

    **Use a standard free CPU runtime.** No GPU, paid upgrade or credentials are required for public economic sources.
    Every stage is resumable and saves a verified archive before subsequent analysis. Keep this notebook and research archives private.
    ''')
    md('''## 1. Frozen specification and source package
    The study uses a block-exogenous recursive structural VAR, identified-shock local projections and a separately gated municipal Callaway–Sant’Anna study.
    Causal interpretations depend on explicit restrictions. Unavailable treatment evidence never becomes a zero estimate.
    The embedded source archive is SHA256-verified before extraction. Inspect `research/fdi/study.json` and the scripts before running the empirical stages.''')
    code(f'''from pathlib import Path
import base64, hashlib, io, json, os, sys, zipfile, subprocess, time
PROJECT=Path('/content/brazil-fdi-src')
SOURCE_SHA256={sha!r}
SOURCE_B64={encoded!r}
payload=base64.b64decode(SOURCE_B64)
assert hashlib.sha256(payload).hexdigest()==SOURCE_SHA256
PROJECT.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(io.BytesIO(payload)) as archive:
    assert archive.testzip() is None
    for name in archive.namelist():
        target=(PROJECT/name).resolve()
        assert target.is_relative_to(PROJECT.resolve())
    archive.extractall(PROJECT)
# A changed source package must not reuse old in-memory study modules after reconnect.
for name in list(sys.modules):
    if name=='fdi' or name.startswith('fdi.'):
        del sys.modules[name]
print('Source package verified:',SOURCE_SHA256)
print((PROJECT/'research/fdi/study.json').read_text())''')
    md('''## 2. Pinned CPU environment
    Install only the study's pinned public Python packages. The municipal model uses the separate Python-only ModernDiD environment in the causal extension.
    No GPU initialization, model-weight download or financial-inference command exists in this notebook.''')
    code('''subprocess.run([sys.executable,'-m','pip','install','--quiet','-r',str(PROJECT/'research/fdi/requirements.txt')],check=True)
sys.path.insert(0,str(PROJECT/'scripts'))
from fdi.storage import Study, read_json, save_json, verify_archive, file_hash
import importlib.metadata
versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','statsmodels','openpyxl','matplotlib','requests']}
print(versions)''')
    md('''## 3. Persistent study folder and resume inspection
    Mount your existing Google Drive. The study writes only inside **MyDrive/Brazil FDI Observatory**.
    Do not disconnect another notebook to obtain resources. The underlying filesystem is temporary; Drive and independently verified local downloads are the durable copies.''')
    code('''from google.colab import drive
drive.mount('/content/drive')
ROOT=Path('/content/drive/MyDrive/Brazil FDI Observatory')
ROOT.mkdir(parents=True,exist_ok=True)
save_json(ROOT/'python-environment.json',versions)
study=Study(ROOT,PROJECT)
print('Current run:',study.identity)
for status in sorted((study.run/'status').glob('*.json')):
    record=read_json(status);print(status.stem,record.get('state'),record.get('at'))''')
    md('''## 4. Restore the verified source snapshot, if supplied
    Restoring saved public-source bytes avoids new source vintages and unnecessary downloads. ZIP CRC, full member list, content hashes and safe extraction paths must all pass.''')
    code(f'''SEED_NAME={seed_name!r}
SEED_SHA256={seed_sha!r}
if SEED_NAME:
    seed=ROOT/SEED_NAME
    assert seed.is_file(), f'Missing verified source snapshot: {{seed.name}}'
    assert file_hash(seed)==SEED_SHA256, 'Source archive SHA256 mismatch'
    manifest=verify_archive(seed)
    destination=ROOT/'runs'/('seed-'+SEED_SHA256[:16])
    with zipfile.ZipFile(seed) as archive:
        for name in manifest:
            target=(destination/name).resolve()
            assert target.is_relative_to(destination.resolve())
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():target.write_bytes(archive.read(name))
            assert file_hash(target)==manifest[name]
    print('Verified saved sources restored:',len(manifest))
else:
    print('No seed archive supplied. Acquisition will preserve official-source bytes and request identities.')''')
    md('''## 5. Safe stage launcher and bounded monitor
    Launch one stage at a time. The launcher checks for a surviving process before starting another. A runtime reconnect must inspect files and process state first.
    Each command writes its stage status and checksum-verified backup to Drive. The monitor never prints credentials or private files.''')
    code('''def running(record):
    proc=Path('/proc')/str(record.get('pid',0))/'cmdline'
    if not proc.exists():return False
    command=proc.read_bytes().replace(b'\\x00',b' ').decode(errors='replace')
    return 'fdi_pipeline.py' in command and str(ROOT) in command

def start(stage):
    directory=ROOT/'jobs';directory.mkdir(exist_ok=True)
    for p in directory.glob('*.json'):
        previous=read_json(p)
        if running(previous):raise RuntimeError('A study process is already active: '+previous['stage'])
    log=directory/(stage+'.log')
    handle=log.open('a')
    process=subprocess.Popen([sys.executable,'-u',str(PROJECT/'scripts/fdi_pipeline.py'),stage,'--project',str(PROJECT),'--root',str(ROOT)],stdout=handle,stderr=subprocess.STDOUT)
    handle.close()
    save_json(directory/(stage+'.json'),{'stage':stage,'pid':process.pid,'source_sha256':SOURCE_SHA256,'log':str(log)})
    print('Started',stage,'PID',process.pid,'log',log.name)

def inspect(stage):
    record=read_json(ROOT/'jobs'/(stage+'.json'))
    print('Active:',running(record),'PID:',record['pid'])
    print(Path(record['log']).read_text(errors='replace')[-6000:])
    current=Study(ROOT,PROJECT)
    print('Study identity:',current.identity)
    for p in sorted((current.run/'status').glob('*.json')):
        r=read_json(p);print(p.stem,r.get('state'),r.get('reason',''))

def download_backup(label):
    current=Study(ROOT,PROJECT)
    archive=ROOT/'backups'/f'fdi-{current.identity[:16]}-{label}.zip'
    assert archive.exists(), 'Stage backup is not yet present'
    verification=read_json(archive.with_suffix('.verified.json'))
    assert file_hash(archive)==verification['sha256']
    verify_archive(archive)
    print('Verified backup:',archive.name,verification['bytes'],'bytes',verification['sha256'])
    from google.colab import files
    files.download(str(archive))''')
    for title,stage,desc in [
      ('6. Official-source acquisition','acquire','Fetch or reuse World Bank, BCB, IBGE, Natural Earth, Federal Reserve and BIS sources. Original bytes are checksummed immediately. Inspect unavailable batches before claiming coverage.'),
      ('7. Normalization and descriptive analysis','prepare','Reconcile country/sector definitions, currencies, quarterly growth, denominators and municipal identifiers. Missing observations remain missing. Immediately download and verify the prepared-data backup before national estimation.'),
      ('8. National causal models and uncertainty','national','Run the restricted SVAR and local projections; 2,000 deterministic bootstrap replications resume from saved checkpoints. Diagnostics and alternative restrictions are recorded. Download the national-model backup before proceeding.'),
      ('9. Municipal causal design','municipal','Run only with a verified event registry and harmonized outcome panel. Without those inputs, record unavailable explicitly and do not fit substitute or fabricated treatment effects.'),
      ('10. Validation','validate','Validate raw hashes, official totals, component reconciliation and observation keys. Statistical/source validation is distinct from economic identification.'),
      ('11. Release exports','export','Generate public-safe JSON, geographic bundles, CSV tables and SVG/PNG figures. The export reports whether each empirical chapter actually completed. A partial causal study must not be called complete.')]:
        md('## '+title+'\n'+desc)
        code(f"start({stage!r})")
        code(f"inspect({stage!r})")
        if stage in ['prepare','national','export']:
            md('Execute the download cell only after the stage is idle and its backup has passed verification. Verify the downloaded local file before starting the next analysis stage.')
            label={'prepare':'prepared','national':'national','export':'full'}[stage]
            code(f"download_backup({label!r})")
    md('''## Publication boundary
    This notebook does not deploy a website, publish a LinkedIn article or write to LangSmith.
    Review the research diagnostics, raw-source coverage, local backup verification, desktop/mobile interface and article claims before release.
    Original PUC-SP manuscripts remain unrecovered; new results are not described as reproduced historical estimates.''')
    notebook.cells=cells;notebook.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'},'colab':{'name':'Brazil FDI Observatory · CPU economic research','provenance':[]},'fdi':{'source_sha256':sha,'seed_archive':seed_name,'seed_sha256':seed_sha,'no_financial_inference':True,'accelerator':'none'}}
    out=ROOT/'notebooks/brazil_fdi_observatory.ipynb';nbf.write(notebook,out)
    nbf.validate(notebook)
    for cell in cells:
        if cell.cell_type=='code':compile(cell.source,'<colab-cell>','exec')
    copy=ROOT/'web/public/data/brazil_fdi_observatory.ipynb';copy.write_bytes(out.read_bytes())
    print(json.dumps({'notebook':str(out),'cells':len(cells),'source_sha256':sha,'notebook_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seed-name',default='');parser.add_argument('--seed-sha',default='');a=parser.parse_args();build(a.seed_name,a.seed_sha)
