"""Append a versioned counterfactual workflow without changing national model code."""
from pathlib import Path
import base64,hashlib,io,json,textwrap,zipfile
import nbformat as nbf

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'artifacts/local/fdi/backups/executed-notebook-20261031.ipynb'
n=nbf.read(base,as_version=4)
files=[ROOT/'scripts/fdi_causal.py',ROOT/'scripts/fdi_review.py',ROOT/'scripts/fdi_publication_figures.py',*sorted((ROOT/'scripts/causal').glob('*.py')),ROOT/'research/fdi/causal-design.json',ROOT/'research/fdi/requirements-causal.txt',ROOT/'research/fdi/official-source-audit.md']
b=io.BytesIO()
with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:
        info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),date_time=(2000,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
payload=b.getvalue();sha=hashlib.sha256(payload).hexdigest()
def add(kind,source):
    source=textwrap.dedent(source).strip();ident=hashlib.sha256((kind+source).encode()).hexdigest()[:8]
    n.cells.append(nbf.v4.new_markdown_cell(source,id=ident) if kind=='md' else nbf.v4.new_code_cell(source,id=ident))
# Remove superseded installer experiments from the active notebook. The original
# executed notebook is retained privately as dated provenance, never overwritten.
n.cells=[c for c in n.cells if not (c.cell_type=='code' and ('did_process' in c.source or 'r_code' in c.source or 'causal_setup' in c.source))]
# Replace unexecuted legacy municipal/final-export launchers with pointers to the
# stronger audit. Completed national cells, outputs and private history remain.
for c in n.cells:
    if c.cell_type=='markdown':
        c.source=c.source.replace("R's pinned `did 2.5.1` is needed only when the verified municipal inputs exist.","The municipal causal model uses the isolated Python-only environment in section 12.")
    if c.cell_type=='code' and c.source.strip() in ["start('municipal')","inspect('municipal')","start('export')","inspect('export')","download_backup('full')"]:
        c.source="print('Use the audited Model C and strict reviewed-export cells in section 12 below. No legacy stage launched.')";c.outputs=[];c.execution_count=None
add('md','''## 12. Counterfactual impact model — Facure-informed extension
The primary municipal causal model is **Callaway–Sant’Anna doubly robust staggered DiD**, not a renamed VAR. It estimates ATT(g,t) for verified operational openings, with eligible comparison histories, overlap, pretreatment diagnostics and explicit identifying assumptions.

Matheus Facure’s [causal graphs](https://matheusfacure.github.io/python-causality-handbook/04-Graphical-Causal-Models.html), [doubly robust estimation](https://matheusfacure.github.io/python-causality-handbook/12-Doubly-Robust-Estimation.html) and [staggered DiD](https://matheusfacure.github.io/python-causality-handbook/24-The-Diff-in-Diff-Saga.html) guide the implementation. Doubly robust estimation does not cure unobserved confounding; pretrend non-rejection does not prove parallel trends.

The already completed national bootstrap is retained unchanged. This separately hashed extension validates its saved results and audits the municipal design. It never reruns Financial Intelligence.''')
add('code',f'''from pathlib import Path
import base64,hashlib,io,json,zipfile,subprocess,sys
PROJECT=Path('/content/brazil-fdi-src')
ROOT=Path('/content/drive/MyDrive/Brazil FDI Observatory')
assert ROOT.is_dir(), 'Inspect and mount the approved persistent Drive folder first'
EXTENSION_SHA256={sha!r}
extension=base64.b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(extension).hexdigest()==EXTENSION_SHA256
with zipfile.ZipFile(io.BytesIO(extension)) as z:
    assert z.testzip() is None
    for name in z.namelist():
        target=(PROJECT/name).resolve();assert target.is_relative_to(PROJECT.resolve())
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
sys.path.insert(0,str(PROJECT/'scripts'))
from fdi.storage import Study,read_json,save_json,verify_archive,file_hash
current=Study(ROOT,PROJECT)
assert current.identity=='4b63a4eef4770644f07f41375529d7123116a72ce633799510dccac397fbc0c4', 'Inspect a changed national study before reuse'
(current.run/'extensions').mkdir(exist_ok=True)
(current.run/'extensions/causal-source.zip').write_bytes(extension)
save_json(current.run/'extensions/causal-source.json',{{'sha256':EXTENSION_SHA256,'language':'Python','separate_from_national_identity':True}})
national_archive=ROOT/'backups/fdi-4b63a4eef4770644-national.zip'
assert file_hash(national_archive)=='98bf3b3bac8d3265416a07a764f2e46ab494f0a978cbb8750f0751f27ad6e4c0'
verify_archive(national_archive)
print('Completed national archive and causal extension verified:',EXTENSION_SHA256)
print(read_json(PROJECT/'research/fdi/causal-design.json')['primary_effect_model'])
import shutil
frozen=list((PROJECT/'scripts/fdi').glob('*.py'))+list((PROJECT/'scripts/fdi').glob('*.R'))+[PROJECT/'scripts/fdi_pipeline.py',PROJECT/'research/fdi/study.json',PROJECT/'research/fdi/requirements.txt']
for source in frozen:
    target=current.run/'reproducibility/national-source'/source.relative_to(PROJECT)
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
print('Original national code/specification copied for audit; no archived legacy municipal code executed.')''')
add('md','''### Python-only environment and estimator validation
Use pinned **ModernDiD 0.4.0**, NumPy CPU, and the author's **pySidraData** at the declared commit. A separate Python >=3.12 environment avoids changing the completed national environment. Save the resolved versions. The generated known-effect test below validates the estimator; it is **not** an empirical result for Brazil. No R code is executed.''')
add('code','''import importlib.metadata as metadata
causal_venv=Path('/content/fdi-causal-env')
causal_python=causal_venv/'bin/python'
if not causal_python.exists():
    subprocess.run([sys.executable,'-m','pip','install','virtualenv==20.35.4'],check=True)
    subprocess.run([sys.executable,'-m','virtualenv','--system-site-packages',str(causal_venv)],check=True)
check=subprocess.run([str(causal_python),'-c',"from importlib.metadata import version;assert version('moderndid')=='0.4.0';assert version('pySidraData')=='0.1.0';assert version('sidrapy')=='0.1.4'"],capture_output=True)
if check.returncode:
    log=ROOT/'jobs/python-causal-environment.log'
    with log.open('a') as handle:
        causal_environment=subprocess.Popen([str(causal_python),'-m','pip','install','-r',str(PROJECT/'research/fdi/requirements-causal.txt')],stdout=handle,stderr=subprocess.STDOUT)
    print('Python environment PID:',causal_environment.pid)
else:
    causal_environment=None
    print('Pinned Python packages already available; installation skipped')''')
add('code',"print('Environment exit:',causal_environment.poll() if causal_environment is not None else 0)\nprint((ROOT/'jobs/python-causal-environment.log').read_text(errors='replace')[-2000:] if (ROOT/'jobs/python-causal-environment.log').exists() else '')")
add('code',"""assert causal_environment is None or causal_environment.poll()==0, 'Pinned environment is not ready; inspect its log'
environment=subprocess.run([str(causal_python),'-m','pip','list','--format=json'],capture_output=True,text=True,check=True)
save_json(current.run/'extensions/python-environment.json',json.loads(environment.stdout))
report=current.run/'models/did-estimator-simulation.json'
result=subprocess.run([str(causal_python),'-m','causal.validate_estimator','--output',str(report)],cwd=PROJECT/'scripts',capture_output=True,text=True)
print(result.stdout[-1500:]);print(result.stderr[-1500:]);result.check_returncode()
print(read_json(report))
print(current.backup('causal-estimator-validation'))""")
add('md','''### Real IBGE observations through pySidraData
The author's pinned Client supplied SIDRA metadata and the São Paulo 2025 observation, checked against preserved official responses. The 111-response source cache covers 116,908 observed municipal population estimates. Population is economic context, not municipal FDI or working-age population. Unpublished years remain gaps.

The verified seed is persistent in the private project backups. Read and verify it first. Colab reprocesses that actual data; it does not substitute generated data when the IBGE endpoint times out.''')
add('code',"""seed=ROOT/'backups/ibge-population-20261031.zip'
assert seed.is_file(), 'Restore the verified official-data seed before continuing'
assert file_hash(seed)=='5eb55f5f124489d73b16fd6a25ac3e2369049f3767729ca10cbffe6f813b84b1'
verify_archive(seed)
if not (current.run/'extensions/ibge/report.json').exists():
    with zipfile.ZipFile(seed) as z:
        for name in z.namelist():
            if name=='ARCHIVE-MANIFEST.json':continue
            target=(current.run/name).resolve();assert target.is_relative_to(current.run.resolve())
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
result=subprocess.run([str(causal_python),str(PROJECT/'scripts/causal/ibge.py'),'--output',str(current.run/'extensions/ibge')],capture_output=True,text=True)
print(result.stdout[-2500:]);print(result.stderr[-1500:]);result.check_returncode()
print(current.backup('population-prepared'))""")
add('md','''### Primary municipal estimator and identification audit
Input CSVs belong in the prepared run directory. Both treated and comparison municipalities need verified earlier exposure histories. A short list of projects does not establish never-treated status. The wrapper blocks unsupported comparisons before Python estimation and prevents a causal label until the prespecified sensitivity evidence is complete.

If no credible registry/panel is available, the honest output is an unavailable causal chapter. The national and descriptive chapters remain usable. Do not change the treatment definition after examining effect estimates.''')
add('code',"""result=subprocess.run([str(causal_python),str(PROJECT/'scripts/fdi_causal.py'),'--root',str(ROOT)],capture_output=True,text=True)
print(result.stdout[-3000:]);print(result.stderr[-2000:]);result.check_returncode()""")
add('md','''### Strict saved-result review and final public-safe export
Recompute deterministic national quantities and confidence intervals from saved draws; never rerun the 2,000 bootstrap replications. Derive forecast-error shares for the correct 1–12-quarter horizons and separate historical deterministic/initial-condition terms. Native model records remain unchanged, with derivations explicitly disclosed.

Verify and download the resulting archive through Drive before handing off presentation assets. No website or article is published by these cells.''')
add('code',"""result=subprocess.run([sys.executable,str(PROJECT/'scripts/fdi_review.py'),'--root',str(ROOT),'--archive',str(national_archive),'--destination','/content/fdi-public'],capture_output=True,text=True)
print(result.stdout[-3000:]);print(result.stderr[-2000:]);result.check_returncode()
subprocess.run([sys.executable,str(PROJECT/'scripts/fdi_publication_figures.py'),'--data','/content/fdi-public'],check=True)
for p in Path('/content/fdi-public').iterdir():
    if p.suffix in ['.png','.svg'] or p.name=='publication-figures.json':
        shutil.copyfile(p,current.run/'exports/public'/p.name)
        shutil.copyfile(p,current.run/'figures'/p.name)
print(current.backup('reviewed-full'))""")
add('code',"""archive=ROOT/'backups'/f'fdi-{current.identity[:16]}-reviewed-full.zip'
verification=read_json(archive.with_suffix('.verified.json'))
assert file_hash(archive)==verification['sha256'];verify_archive(archive)
print('Verified final archive:',verification)
print('Download from the private Drive backups folder, then verify SHA256, CRC and every manifest member locally.')""")
n.metadata['fdi']['causal_extension_sha256']=sha
nbf.validate(n)
for c in n.cells:
    if c.cell_type=='code':compile(c.source,'<colab-cell>','exec')
private=ROOT/'artifacts/local/fdi/backups/notebook-with-causal-extension.ipynb';nbf.write(n,private)
for c in n.cells:
    if c.cell_type=='code':c.outputs=[];c.execution_count=None
nbf.write(n,ROOT/'notebooks/brazil_fdi_observatory.ipynb')
(ROOT/'web/public/data/brazil_fdi_observatory.ipynb').write_bytes((ROOT/'notebooks/brazil_fdi_observatory.ipynb').read_bytes())
print(json.dumps({'extension_sha256':sha,'cells':len(n.cells),'private_notebook':str(private),'template_sha256':hashlib.sha256((ROOT/'notebooks/brazil_fdi_observatory.ipynb').read_bytes()).hexdigest()}))
