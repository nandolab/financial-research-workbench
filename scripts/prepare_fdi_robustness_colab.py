"""Package only the Python robustness extension in a new, nonexecuted Colab notebook."""
from pathlib import Path
import base64,hashlib,io,json,textwrap,zipfile
ROOT=Path(__file__).resolve().parents[1]
def build():
    members=['scripts/fdi_robustness.py','scripts/fdi/models.py','scripts/fdi/storage.py','scripts/fdi/__init__.py','research/fdi/requirements.txt']
    blob=io.BytesIO()
    with zipfile.ZipFile(blob,'w',zipfile.ZIP_DEFLATED) as z:
        for name in members:
            info=zipfile.ZipInfo(name,date_time=(2000,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,(ROOT/name).read_bytes())
    raw=blob.getvalue();digest=hashlib.sha256(raw).hexdigest()
    config=json.loads((ROOT/'web/public/data/fdi/transparency.json').read_text(encoding='utf8'))
    cells=[]
    def cell(kind,s):
        s=textwrap.dedent(s).strip()
        c={'cell_type':kind,'metadata':{},'source':s.splitlines(True),'id':hashlib.sha256((str(len(cells))+s).encode()).hexdigest()[:8]}
        if kind=='code':c.update(execution_count=None,outputs=[])
        cells.append(c)
    cell('markdown',"""# Brazil FDI Observatory — Python robustness laboratory
**Prepared extension; not a completed empirical sensitivity study. Fernando Barbosa.**
Use a standard free CPU. Do not connect a GPU or purchase compute. This is a new notebook;
it does not run the Financial Intelligence models, LangSmith experiments or the baseline 2,000-draw bootstrap.
The baseline study and all prior archives remain read-only.
Read Research & Methods before interpreting responses as effects.
""")
    cell('markdown',"""## Questions and assumptions, before computation
1. Are remaining residual patterns seasonal or serially dependent? Test squared-residual quarter indicators (seasonal volatility) and auxiliary residual-vector lag dependence; report the entire equation family with Holm adjustment. Quarter-mean tests would be tautological after fitting quarter indicators.
2. Do LP responses depend on additional lags? Compare 0, 1 and 2 additional lags with HAC bands. These reuse generated baseline shocks, omit some uncertainty and do not implement a new identification design.
3. How do units and growth accumulation change interpretation? Normalize each saved draw to a +1 percentage-point FDI/GDP impact; accumulate GDP growth and convert log differences to level percentages draw by draw.
4. How does a finite-order model behave when the true system contains moving-average dynamics? Repeated synthetic DGPs, 119/240 observations, VARMA coefficients 0/0.5, fitted lags 1/2, 1,000 deterministic replications per cell. Report bias, coverage, Monte Carlo standard error and failures.
These are prespecified for this new extension, after the original baseline was observed. They are not retroactive preregistration.
No municipal treatment registry currently supports an empirical ATT. HonestDiD-style sensitivity, a municipal Monte Carlo battery, alternative inflation deflators and new omitted-variable specifications remain separate unfinished work—not claimed implemented here.
""")
    cell('markdown',"""## Books and papers actually informing the checks
Pearl & Mackenzie (2018), *The Book of Why*, Chapters 1 and 4: association versus intervention; common causes, mediators and colliders.
Freedman (2009), *Statistical Models: Theory and Practice*, Chapters 1, 6 and 8: stability under interventions, economic units and bootstrap assumptions.
Verbeek (2017), *A Guide to Modern Econometrics*, Sections 2.5.7, 5.2.4 and 9.2: power/p-values, reverse causality and Granger prediction.
Matheus Facure's Python handbook: graphical causal models, doubly robust estimation and staggered DiD.
LP interpretation/inference: Plagborg-Møller & Wolf (2021), Montiel Olea & Plagborg-Møller (2021), Li et al. (2024).
Municipal design: Callaway & Sant'Anna (2021), Sant'Anna & Zhao (2020), Sun & Abraham (2021), Roth (2022), Rambachan & Roth (2023).
The workbench bibliography includes DOI links and the two multinational-investment applications. Private books are not embedded or redistributed.
""")
    cell('code',f"""from pathlib import Path
import base64,hashlib,io,json,sys,subprocess,zipfile,shutil
PROJECT=Path('/content/brazil-fdi-robustness-source')
raw=base64.b64decode({base64.b64encode(raw).decode()!r})
assert hashlib.sha256(raw).hexdigest()=={digest!r}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    assert z.testzip() is None
    for name in z.namelist():
        assert (PROJECT/name).resolve().is_relative_to(PROJECT.resolve())
    z.extractall(PROJECT)
print('Source SHA256 verified:',{digest!r})
""")
    cell('markdown',"""## Environment (CPU only)
Install the tested pinned baseline dependencies. This notebook uses Python only. Installation does not run any estimator.
""")
    cell('code',"""subprocess.run([sys.executable,'-m','pip','install','--quiet','-r',str(PROJECT/'research/fdi/requirements.txt')],check=True)
import importlib.metadata
VERSIONS={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','statsmodels']}
print(VERSIONS)
""")
    cell('markdown',"""## Resume inspection and input authentication
Use the existing study folder. Mounting Drive uses the previously authorized project scope.
Find the exact saved quarterly panel and native national output by their known hashes.
Stop if absent or ambiguous; restore a verified archive rather than reacquiring data or re-estimating.
""")
    q=ROOT/'artifacts/local/fdi/runs/4b63a4eef4770644/prepared/quarterly.csv'
    n=q.parents[1]/'models/national.json'
    cell('code',f"""from google.colab import drive
drive.mount('/content/drive')
STUDY=Path('/content/drive/MyDrive/Brazil FDI Observatory')
EXPECTED={{'prepared/quarterly.csv':{hashlib.sha256(q.read_bytes()).hexdigest()!r},'models/national.json':{hashlib.sha256(n.read_bytes()).hexdigest()!r}}}
candidates=[]
for panel in STUDY.rglob('quarterly.csv'):
    run=panel.parent.parent
    if all((run/name).is_file() and hashlib.sha256((run/name).read_bytes()).hexdigest()==v for name,v in EXPECTED.items()):candidates.append(run)
assert candidates,'Matching baseline absent: restore a verified archive. Never rerun it here.'
# Identical verified copies are interchangeable; choose the shortest canonical path and disclose it.
RUN=sorted(candidates,key=lambda p:(len(str(p)),str(p)))[0]
OUTPUT=STUDY/'robustness-extension'
sys.path.insert(0,str(PROJECT/'scripts'))
from fdi_robustness import plan,backup
ROOT=plan(RUN,OUTPUT)
(ROOT/'environment.json').write_text(json.dumps(VERSIONS,indent=2))
print('Verified baseline:',RUN,'Matching copies:',len(candidates),'New identity:',ROOT.name)
for p in sorted(ROOT.glob('*-status.json')):print(p.name,p.read_text())
print('Prepared only; baseline untouched.')
""")
    cell('markdown',"""## Execution switches
Keep False for preparation/review. Change to True only when deliberately running this new extension.
Each completed stage is content-hash verified before reuse. Changed code/configuration/input creates a new identity.
The simulation stage is intentionally separate and may take longer; do not use Run All blindly.
""")
    cell('code',"""RUN_NEW_CHECKS=False
RUN_SIMULATIONS=False
""")
    for stage in ['residuals','lp','saved-draws','simulation']:
        cell('markdown',f"""## Stage: {stage}
Outputs are saved in the separate identity. Backups are ZIP-CRC and per-member SHA256 read-back verified.
After this stage, download its backup and independently verify the local copy before proceeding.
No result from this cell is present until the switch is deliberately enabled and execution completes.
""")
        flag='RUN_SIMULATIONS' if stage=='simulation' else 'RUN_NEW_CHECKS'
        cell('code',f"""if {flag}:
    subprocess.run([sys.executable,str(PROJECT/'scripts/fdi_robustness.py'),'--run',str(RUN),'--output',str(OUTPUT),'--stage',{stage!r}],check=True)
else:
    print('Prepared, not executed:',{stage!r})
""")
        cell('code',"""# Separate download action: never combine cell execution with a blocking browser download wait.
from google.colab import files
if ROOT.exists() and (ROOT/'robustness-backup.zip').exists():
    CHECK=json.loads((ROOT/'backup-verification.json').read_text())
    assert hashlib.sha256((ROOT/'robustness-backup.zip').read_bytes()).hexdigest()==CHECK['sha256']
    print(CHECK)
    # Deliberately uncomment only after a completed stage:
    # files.download(str(ROOT/'robustness-backup.zip'))
""")
    cell('markdown',"""## Release gate
No automatic publication exists. A completed output is not automatically scientifically validated.
Inspect all failures, estimates, interval definitions, assumptions, source hashes and simulated coverage uncertainty.
A new national check cannot cure missing municipal exposure histories. Retain null/inconclusive results.
Upload only validated aggregate exports to the website; keep books, private microdata and research archives private.
""")
    notebook={'nbformat':4,'nbformat_minor':5,'metadata':{'colab':{'name':'brazil_fdi_robustness.ipynb'},'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'},'research_status':'prepared_not_executed','source_sha256':digest},'cells':cells}
    out=ROOT/'notebooks/brazil_fdi_robustness.ipynb';out.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    public=ROOT/'web/public/data/brazil_fdi_robustness.ipynb';public.write_bytes(out.read_bytes())
    assert json.loads(out.read_text(encoding='utf8'))==notebook
    # Syntax-compile all code cells after IPython-free construction; execute none.
    for i,c in enumerate(cells):
        if c['cell_type']=='code':compile(''.join(c['source']),f'cell-{i}','exec')
    print('Notebook prepared:',len(cells),'cells, SHA256',hashlib.sha256(out.read_bytes()).hexdigest())
if __name__=='__main__':build()

