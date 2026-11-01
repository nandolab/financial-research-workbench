from fdi_temporal import annual_brl, rolling
import math

def test_monthly_conversion_and_missing_inputs():
    keys=[f"2020-{m:02}" for m in range(1,13)]
    flows={k:1 for k in keys};fx={k:2 for k in keys};prices={k:100 for k in keys}
    fx[keys[0]]=4;prices[keys[0]]=200
    assert annual_brl(2020,flows,fx,prices,200)==48e6
    flows[keys[0]]=-1
    assert annual_brl(2020,flows,fx,prices,200)==40e6
    del prices[keys[-1]]
    assert annual_brl(2020,flows,fx,prices,200) is None

def test_rolling_requires_complete_window_and_sample_dispersion():
    assert rolling([1,None,3],2,3) is None
    assert rolling([1,2,3],1,3) is None
    assert rolling([1,2,3],2,3)==2
    assert math.isclose(rolling([1,2,3],2,3,True),1)
