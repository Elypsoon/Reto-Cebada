import numpy as np
import pandas as pd
import pytest
from agrocebada.priority_selectors import AGRONOMIC
from agrocebada.priority_models import PriorityEBM


@pytest.mark.parametrize('max_bins,interactions', [(8, 'none'), (16, 'fixed_pairs')])
def test_ebm_effective_parameters_and_recovery(max_bins, interactions, tmp_path):
    import joblib
    rng = np.random.default_rng(2026)
    frame = pd.DataFrame({c: rng.normal(size=45) for c in AGRONOMIC})
    target = 3 + .2*frame.s2_evi_middle + .1*frame.climate_PREC_middle*frame.s2_evi_middle
    model = PriorityEBM(max_bins, interactions).fit(frame, target)
    contract = model.contract()
    assert contract['parameters']['outer_bags'] == 8
    assert contract['parameters']['max_rounds'] == 1000
    assert contract['parameters']['early_stopping_rounds'] == 0
    assert len(contract['effective_interactions']) == (0 if interactions == 'none' else 2)
    before = model.predict(frame.iloc[[0]])
    query = frame.copy()
    query.iloc[1:] = 9000.
    np.testing.assert_allclose(before, model.predict(query)[:1], atol=1e-10, rtol=0)
    parts = model.decompose(query)
    np.testing.assert_allclose(model.predict(query), parts['reference']+parts['parcel_effect'], atol=1e-10, rtol=0)
    joblib.dump(model, tmp_path/'model.joblib')
    restored = joblib.load(tmp_path/'model.joblib')
    np.testing.assert_allclose(model.predict(query), restored.predict(query), atol=1e-10, rtol=0)
