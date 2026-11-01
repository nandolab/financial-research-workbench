import numpy as np
import pytest
from causal.audit import dr_att

def test_dr_panel_att_recovers_known_effect_under_confounding():
    rng=np.random.default_rng(20261031);n=25000;x=rng.uniform(-1,1,(n,2));ps=1/(1+np.exp(-(.4*x[:,0]-.3*x[:,1])))
    d=rng.binomial(1,ps);change=1+2*x[:,0]-.7*x[:,1]+1.8*d+rng.normal(0,.25,n)
    # Include broad-support controls so the finite-sample common-support check is explicit.
    d[:4]=0;x[:4]=[[-1,-1],[-1,1],[1,-1],[1,1]];change[:4]=1+2*x[:4,0]-.7*x[:4,1]
    result=dr_att(change,d,x);assert abs(result['att']-1.8)<.025;assert result['control_ess']>1000

def test_no_clipped_propensities_under_separation():
    x=np.r_[np.linspace(-3,-1,100),np.linspace(1,3,100)];d=(x>0).astype(int)
    with pytest.raises(ValueError,match='separated|Positivity'):dr_att(d,d,x)

def test_too_few_comparisons_block_effect_estimation():
    with pytest.raises(ValueError,match='Insufficient'):dr_att(np.arange(10),[0]*5+[1]*5,np.arange(10))
