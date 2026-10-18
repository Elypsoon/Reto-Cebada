import numpy as np
import pandas as pd
import pytest
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel
from agrocebada.priority_models import HierarchicalAdditive, HierarchicalGPR, DirectGAM


def inputs():
    rng = np.random.default_rng(2026)
    states = np.array(['A']*24 + ['B']*5 + ['C'])
    x = rng.normal(size=30)
    frame = pd.DataFrame({'s2_evi_middle': x, 'climate_PREC_middle': x*x,
                          **{f'region__{s}': (states == s).astype(float) for s in ['A', 'B', 'C', 'D']}})
    y = 3 + .2*x + np.where(states == 'A', 0., 1.)
    return frame, y


@pytest.mark.parametrize('spline', [False, True])
def test_joint_fit_zero_weighted_effects_and_zero_support(spline):
    frame, y = inputs()
    model = HierarchicalAdditive(spline=spline).fit(frame, y)
    assert abs(sum(model.state_counts_[s]*model.state_effects_[s] for s in model.states_)) < 1e-10
    assert model.state_counts_['region__C'] == 1
    query = frame.iloc[[0]].copy()
    query.loc[:, query.columns.str.startswith('region__')] = 0.
    query['region__D'] = 1.
    assert model.predict(query)[0] == y.mean()
    parts = model.decompose(frame)
    np.testing.assert_allclose(model.predict(frame), parts['reference']+parts['state_effect']+parts['parcel_effect'])
    no_effect = HierarchicalAdditive(spline=spline, state_penalty=np.inf).fit(frame, y)
    assert set(no_effect.state_effects_.values()) == {0.}


def test_zero_state_variance_equivalent_to_original_gpr_and_unseen_fallback():
    frame, y = inputs()
    model = HierarchicalGPR(state_variance=0).fit(frame, y)
    numeric = model.scale_.transform(model.select_.transform(frame))
    control = GaussianProcessRegressor(kernel=Matern(length_scale=1., nu=2.5)+WhiteKernel(.15),
                                       optimizer=None, normalize_y=True).fit(numeric, y)
    np.testing.assert_allclose(model.predict(frame), control.predict(numeric), atol=1e-10, rtol=0)
    query = frame.iloc[[0]].copy()
    query.loc[:, query.columns.str.startswith('region__')] = 0.
    assert model.predict(query)[0] == y.mean()


@pytest.mark.parametrize('model', [HierarchicalAdditive(), HierarchicalAdditive(spline=True),
                                   HierarchicalGPR(), DirectGAM()])
def test_batch_invariance_contract_and_decomposition(model):
    frame, y = inputs()
    model.fit(frame, y)
    before = model.contract()
    first = model.predict(frame.iloc[[0]])
    query = frame.copy()
    query.loc[1:, 's2_evi_middle'] = 1000000.
    np.testing.assert_allclose(first, model.predict(query)[:1], atol=1e-10, rtol=0)
    assert before == model.contract()
    parts = model.decompose(query)
    np.testing.assert_allclose(model.predict(query), parts['reference']+parts['state_effect']+parts['parcel_effect'], atol=1e-10, rtol=0)
    with pytest.raises(ValueError):
        model.predict(query.drop(columns='s2_evi_middle'))
