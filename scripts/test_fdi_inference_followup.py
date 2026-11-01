import sys,json
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).parent))
from fdi_inference_followup import ols_intervals,replication,summarize,checked_zip
from fdi_robustness import simulation_replication

def test_paired_reconstruction_matches_the_saved_procedure():
 old=simulation_replication(119,.5,2,7)
 result=replication(119,.5,2,7,old)
 assert result['legacy_paired'] and len(result['methods'])==5
 assert result==replication(119,.5,2,7,old)
 assert result['methods']['hac_corrected_t']['se']>old['se']

def test_critical_value_changes_do_not_change_estimates():
 rng=np.random.default_rng(99);x=np.column_stack([np.ones(100),rng.normal(size=(100,4))]);y=x@np.arange(5)+rng.normal(size=100)
 vals,d=ols_intervals(y,x,-1,4,2)
 assert len({v['estimate'] for v in vals.values()})==1
 assert d['df']==95
 assert vals['hac_corrected_t']['upper']-vals['hac_corrected_t']['lower']>vals['hac_corrected_normal']['upper']-vals['hac_corrected_normal']['lower']

def test_summary_reports_failure_and_paired_uncertainty():
 row=replication(119,0.,1,2);res=summarize([row,row,{'failure':'example'}])
 assert all(v['valid']==2 and v['failures']==1 for v in res.values())
 assert res['legacy_hac_normal']['coverage_difference']==0
 assert res['legacy_hac_normal']['paired_difference_mcse']==0

def test_rank_deficiency_stops_inference():
 with pytest.raises(AssertionError,match='Rank-deficient'):
  ols_intervals(np.arange(20),np.ones((20,2)),-1,4,1)
