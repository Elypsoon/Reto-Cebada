import numpy as np
import pandas as pd
import pytest
from agrocebada.priority_selectors import PrioritySelector, AGRONOMIC


def test_no_ranking_keeps_low_marginal_nonlinear_signal_without_k_limit():
    x = np.linspace(-2, 2, 101)
    frame = pd.DataFrame({'curve': x, **{f'z{i}': np.sin((i+1)*x) for i in range(25)},
                          'constant': 1., 'RENDIMIENTO_T_HA': x*x, 'location_x': x})
    y = x*x
    assert abs(np.corrcoef(x, y)[0, 1]) < 1e-10
    selector = PrioritySelector('all', k=1).fit(frame, y)
    assert 'curve' in selector.columns_ and selector.effective_dimension_ == 26
    assert 'constant' not in selector.columns_ and 'RENDIMIENTO_T_HA' not in selector.columns_
    assert 'location_x' not in selector.columns_


def test_imputation_and_dimension_use_train_only():
    train = pd.DataFrame({'x': [1., np.nan, 3., 5.], 'low_availability': [np.nan, np.nan, np.nan, 9.]})
    selector = PrioritySelector('all').fit(train, [0., 1., 2., 3.])
    query = pd.DataFrame({'x': [np.nan, 1e6], 'low_availability': [100., 100.]})
    assert selector.transform(query).iloc[0, 0] == 3.
    assert selector.contract()['effective_dimension'] == 1
    assert selector.transform(query.iloc[[0]]).equals(selector.transform(query).iloc[[0]])
    with pytest.raises(ValueError):
        selector.transform(query.drop(columns='x'))


def test_agronomic_is_exactly_16_prespecified_names():
    assert len(AGRONOMIC) == 16 and len(set(AGRONOMIC)) == 16
    frame = pd.DataFrame({c: np.arange(12.) for c in AGRONOMIC} | {'extra': np.arange(12.)})
    selector = PrioritySelector('agronomic').fit(frame, np.arange(12.)**2)
    assert selector.columns_ == list(AGRONOMIC)
    ranked = PrioritySelector('rank', 10).fit(frame, np.arange(12.)**2)
    assert len(ranked.columns_) == 1  # redundancia histórica, no aplicada a modo fijo


def test_unsupervised_modes_invariant_to_labels():
    frame = pd.DataFrame({'s2_evi_middle': [1., 2., 3., np.nan], 'x': [2., 1., 4., 7.]})
    for mode in ['all', 'agronomic']:
        first = PrioritySelector(mode).fit(frame, [1, 2, 3, 4])
        second = PrioritySelector(mode).fit(frame, [900, -500, 100, 0])
        assert first.contract() == second.contract()
