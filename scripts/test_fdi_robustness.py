from pathlib import Path
import json,sys,zipfile,hashlib
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from fdi_robustness import plan,backup,inputs,lp_sensitivity,simulation_replication,residual_checks
from fdi.models import fit_system,responses
@pytest.fixture
def run(tmp_path):
    rng=np.random.default_rng(20261031);n=119;k=5
    periods=pd.period_range('1996Q2','2025Q4',freq='Q')
    y=np.zeros((n,k))
    for i in range(1,n):y[i]=.4*y[i-1]+rng.normal(size=k)
    f=pd.DataFrame(y,index=periods.astype(str),columns=['nfci','gdp_growth','gfcf_growth','reer_change','fdi_gdp'])
    f['us_gdp_growth']=rng.normal(size=n);f['fedfunds_change']=rng.normal(size=n);f['quarter']=periods.quarter
    z=np.column_stack([f[['us_gdp_growth','fedfunds_change']],pd.get_dummies(f.quarter,drop_first=True).astype(float)])
    m=fit_system(y,z,1);_,B=responses(m,0)
    root=tmp_path/'baseline';(root/'prepared').mkdir(parents=True);(root/'models').mkdir()
    f.to_csv(root/'prepared/quarterly.csv')
    (root/'models/national.json').write_text(json.dumps({'state':'complete','bootstrap':{'valid':2000},'lag':1,'coefficients':m['beta'].tolist(),'impact_matrix':B.tolist()}))
    return root
def test_missing_quarter_is_a_hard_failure(run):
    p=run/'prepared/quarterly.csv';f=pd.read_csv(p,index_col=0);f.drop(f.index[30]).to_csv(p)
    with pytest.raises(AssertionError):inputs(run)
def test_changed_inputs_and_replication_budget_create_separate_identities(run,tmp_path):
    output=tmp_path/'checks'
    first=plan(run,output);assert plan(run,output)==first
    assert plan(run,output,8)!=first
    p=run/'prepared/quarterly.csv';f=pd.read_csv(p,index_col=0);f.iloc[0,0]+=.01;f.to_csv(p)
    assert plan(run,output)!=first
def test_baseline_is_never_a_write_destination(run):
    with pytest.raises(AssertionError):plan(run,run/'checks')
def test_archive_crc_and_all_members_survive_readback(run,tmp_path):
    root=plan(run,tmp_path/'checks');p=backup(root)
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        d=json.loads(z.read('file-manifest.json'))
        assert set(z.namelist())==set(d)|{'file-manifest.json'}
        assert all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in d.items())
def test_additional_lp_lags_preserve_baseline_bytes_and_have_full_horizon(run):
    files=[run/'prepared/quarterly.csv',run/'models/national.json'];before=[p.read_bytes() for p in files]
    result=lp_sensitivity(run)
    assert [x['extra_lags'] for x in result['specifications']]==[0,1,2]
    for spec in result['specifications']:
        assert np.asarray(spec['irf']).shape==(13,5,5)
        ci=np.asarray(spec['pointwise_95_hac']);assert ci.shape==(13,5,5,2)
        assert np.isfinite(ci).all() and (ci[...,0]<=ci[...,1]).all()
    assert before==[p.read_bytes() for p in files]
def test_synthetic_replications_are_deterministic_and_not_brazilian_evidence():
    r=simulation_replication(119,.5,1,7);assert r==simulation_replication(119,.5,1,7)
    assert np.isclose(r['truth'],.0154155)


def test_residual_checks_use_volatility_and_estimable_joint_lag_families(run):
    result=residual_checks(run)
    assert len(result["seasonal"])==5 and len(result["serial"])==10
    assert {r["df"] for r in result["serial"]}=={20,40}
    assert all(0<=r["p"]<=r["holm_p"]<=1 for r in result["seasonal"]+result["serial"])

def test_quarter_labels_must_match_dates(run):
    p=run/"prepared/quarterly.csv";f=pd.read_csv(p,index_col=0);f.iloc[0,f.columns.get_loc("quarter")]=4;f.to_csv(p)
    with pytest.raises(AssertionError):inputs(run)

def test_replication_resume_verifies_content_before_reuse(tmp_path,monkeypatch):
    import fdi_robustness as module
    calls=[]
    def fake(*args):
        calls.append(args);return {"truth":1.,"estimate":1.,"se":.1,"covered":True}
    monkeypatch.setattr(module,"simulation_replication",fake)
    module.monte_carlo(tmp_path,1);assert len(calls)==8
    module.monte_carlo(tmp_path,1);assert len(calls)==8
    p=next((tmp_path/"mc").rglob("*.json"));d=json.loads(p.read_bytes());d["result"]["truth"]=99;p.write_text(json.dumps(d))
    with pytest.raises(AssertionError,match="checksum"):module.monte_carlo(tmp_path,1)
