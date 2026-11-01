import numpy as np
from fdi_review import forecast_fevd

def test_forecast_horizon_one_contains_impact_only():
    irf=np.array([[[1.,0.],[1.,2.]],[[.9,.8],[.7,.6]],[[.2,.1],[.3,.4]]])
    value=forecast_fevd(irf)
    assert value.shape==(2,2,2)
    assert np.allclose(value[0],[[1.,0.],[.2,.8]])
    assert np.allclose(value.sum(axis=2),1)
