"""Strictly import the new Colab follow-up; never fit a model here."""
from pathlib import Path
import argparse,hashlib,json,math,statistics
from build_fdi_robustness_export import read_archive,PARENT,PACKAGES
from fdi_inference_followup import CONFIG,BASELINE,OLD_SHA,COMPACT_SHA,canon
REPO=Path(__file__).resolve().parents[1]
def digest(b):return hashlib.sha256(b).hexdigest()
def finite(x):assert isinstance(x,(int,float)) and math.isfinite(x)
def close(a,b):assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-11),(a,b)
def validate(raw):
 members=read_archive(raw);plan=json.loads(members['plan.json']);spec=plan['specification']
 assert plan['identity']==digest(canon(spec))
 assert spec['config']==CONFIG and spec['baseline']==BASELINE and spec['previous_archive']==OLD_SHA
 assert spec['paired_input_sha256'] in [OLD_SHA,COMPACT_SHA]
 assert spec['versions']==PACKAGES
 assert spec['source']==digest(members['source.py'])==digest((REPO/'scripts/fdi_inference_followup.py').read_bytes())
 assert spec['models_source']==digest((REPO/'scripts/fdi/models.py').read_bytes())
 stages={}
 for s in ['empirical','calibration']:
  status=json.loads(members[s+'-status.json']);assert status['state']=='complete' and status['sha256']==digest(members[s+'.json'])
  stages[s]=json.loads(members[s+'.json']);assert stages[s]['state']=='complete'
 empirical=stages['empirical'];assert empirical['normalization_equivalence_max_abs_difference']<1e-9
 rows=empirical['rows'];assert len(rows)==52 and {(r['p'],r['h']) for r in rows}=={(p,h) for p in range(1,5) for h in range(13)}
 for r in rows:
  assert r['n']==115-r['h'] and r['k']==11+5*r['p'] and r['df']==r['n']-r['k']
  assert r['first_predictor_quarter']=='1997Q2' and r['impact_zero_imposed']==(r['h']==0)
  finite(r['max_leverage']);assert 0<r['max_leverage']<1
  for key,v in r['intervals'].items():
   assert key in CONFIG['methods'][:4]
   for value in v.values():finite(value)
   assert v['lower']<=v['estimate']<=v['upper'] and v['se']>=0
  assert len({v['estimate'] for v in r['intervals'].values()})==1
 allnames={n for n in members if n.startswith('mc/')};expected=set();cal=stages['calibration'];assert cal['checkpoints']==12000 and len(cal['cells'])==12
 for cell in cal['cells']:
  sample,n,ma,p=cell['sample'],cell['n'],cell['ma'],cell['p'];assert sample in ['paired','holdout'] and n in ([119,240] if sample=='paired' else [119]) and ma in [0.,.5] and p in [1,2]
  records=[]
  for rep in range(0 if sample=='paired' else 1000,1000 if sample=='paired' else 2000):
   name=f'mc/{sample}/n{n}-ma{ma}-p{p}/{rep:05}.json';expected.add(name)
   cp=json.loads(members[name]);r=cp['result'];assert cp['sha256']==digest(canon(r))
   if 'failure' not in r:
    finite(r['truth']);assert r['legacy_paired']==(sample=='paired')
    assert set(r['methods'])==set(CONFIG['methods'])
    for v in r['methods'].values():
     for k in ['estimate','se','lower','upper']:finite(v[k])
     assert v['se']>0 and v['lower']<=v['estimate']<=v['upper']
     assert v['covered']==(v['lower']<=r['truth']<=v['upper'])
    records.append(r)
  for method,report in cell['methods'].items():
   assert method in CONFIG['methods'] and report['valid']==len(records) and report['failures']==1000-len(records)
   assert records,'No valid replications'
   flags=[int(r['methods'][method]['covered']) for r in records];deltas=[a-int(r['methods']['legacy_hac_normal']['covered']) for a,r in zip(flags,records)]
   c=sum(flags)/len(flags);close(report['coverage'],c);close(report['mcse'],math.sqrt(c*(1-c)/len(flags)))
   close(report['coverage_difference'],statistics.mean(deltas));close(report['paired_difference_mcse'],statistics.stdev(deltas)/math.sqrt(len(flags)))
   close(report['mean_width'],statistics.mean(r['methods'][method]['upper']-r['methods'][method]['lower'] for r in records))
   close(report['bias'],statistics.mean(r['methods'][method]['estimate']-r['truth'] for r in records))
 assert allnames==expected and len(expected)==12000
 result={'state':'complete','parent':PARENT,'run_identity':plan['identity'],'archive_sha256':digest(raw),
   'configuration':CONFIG,'empirical':empirical,'calibration':cal,
   'validation':{'checkpoints_reconciled':12000,'archive_members':len(members),'CRC_and_all_members':'passed'},
   'preservation':{'original_baseline':BASELINE,'previous_robustness_archive':OLD_SHA,'baseline_rerun':False,'original_bootstrap_rerun':False}}
 result['identity']=digest(canon(result));return result
def main():
 ap=argparse.ArgumentParser();ap.add_argument('archive',type=Path);ap.add_argument('--output',type=Path,default=REPO/'web/public/data/fdi/inference-followup.json');a=ap.parse_args()
 result=validate(a.archive.read_bytes());a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(canon(result));print(json.dumps({'identity':result['identity'],'checkpoint_count':12000}))
if __name__=='__main__':main()
