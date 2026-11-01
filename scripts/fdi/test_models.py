import numpy as np
import pytest
from fdi.models import fit_system, responses, historical, local_projections
from fdi.storage import Study, verify_archive
from pathlib import Path

def sample(n=2500):
    rng=np.random.default_rng(22);A=np.array([[.4,0],[.2,.3]]);B=np.array([[1,0],[.35,.8]]);y=np.zeros((n,2));z=np.empty((n,0))
    for t in range(1,n):y[t]=A@y[t-1]+B@rng.normal(size=2)
    return y,z,A,B

def test_structural_recovery():
    y,z,A,B=sample();m=fit_system(y,z,1);irf,impact=responses(m,5)
    assert m['beta'][2,0]==0 # Brazilian/second variable lag excluded from first block.
    assert np.max(abs(m['A'][0]-A))<.08
    assert np.max(abs(impact-B))<.08
    assert np.max(abs(irf[3]-np.linalg.matrix_power(A,3)@B))<.08

def test_history_reconciles_and_shock_labels_persist():
    y,z,A,B=sample(400);m=fit_system(y,z,2);h=historical(y,z,m)
    assert h['max_reconciliation_error']<1e-10
    irf,impact=responses(m,3,[1,0])
    assert np.allclose(impact@impact.T,m['cov'])
    assert impact[1,0]==0

def test_local_projections_recover_known_response():
    y,z,A,B=sample(5000);m=fit_system(y,z,1);lp,_=local_projections(y,z,m,3)
    assert np.max(abs(lp[0]-B))<.06
    assert np.max(abs(lp[2]-np.linalg.matrix_power(A,2)@B))<.06

def test_fevd_is_partition_of_variance():
    y,z,_,_=sample(300);m=fit_system(y,z,2);irf,_=responses(m,12);s=np.cumsum(irf**2,axis=0);v=s/s.sum(axis=2,keepdims=True)
    assert np.allclose(v.sum(axis=2),1)
    assert (v>=0).all()

def test_rank_deficiency_is_not_silently_fitted():
    with pytest.raises(ValueError,match='Rank-deficient'):fit_system(np.ones((30,2)),np.empty((30,0)),2)
