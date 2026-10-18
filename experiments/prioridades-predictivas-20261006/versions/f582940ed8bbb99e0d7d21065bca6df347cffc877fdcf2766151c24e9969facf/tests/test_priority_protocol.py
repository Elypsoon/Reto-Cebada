from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from agrocebada.priority_catalog import candidates, MAXIMUMS, ENSEMBLES, PriorityCandidate
from agrocebada.priority_adapter import FittedCandidate
from agrocebada.priority_selection import select, fit_selection, calibrate
from agrocebada.priority_functional import FunctionalProjection
from agrocebada.priority_curves import BRANCHES, QUALITY
from agrocebada.priority_selectors import ENVIRONMENT


def inputs(n=120):
    rng = np.random.default_rng(2026)
    ids = [f'ID{i}' for i in range(n)]
    frame = pd.DataFrame({**{f'coef_{b}_{j}': rng.normal(size=n) for b in BRANCHES for j in range(6)},
         **{c: rng.normal(size=n) for c in list(ENVIRONMENT)+list(QUALITY)},
         's2_evi_middle': rng.normal(size=n), 'region__A': 1., 'region__B': 0.}, index=ids)
    target = pd.Series(3+.2*frame.s2_evi_middle, index=ids)
    groups = pd.Series(np.arange(n)%4, index=ids)
    states = pd.Series('A', index=ids)
    return frame, target, groups, states


def test_corrected_catalog_counts_and_frozen_recipe():
    for block, maximum in MAXIMUMS.items():
        grid = candidates(block)
        assert len(grid)+len(ENSEMBLES) == maximum <= 160
        assert len({c.id for c in grid}) == len(grid)
    p06 = candidates('P06')
    assert {c.representation for c in p06} == {'compact', 'functional'}
    assert {c.family for c in p06} == {'hierarchical_gpr', 'hierarchical_gam', 'global_mean', 'regional_mean'}


def test_outer_labels_and_curves_cannot_change_internal_learning():
    frame, target, groups, states = inputs()
    grid = [PriorityCandidate('functional', 'hierarchical_gpr', components=2, state_setting=.25),
            PriorityCandidate('functional', 'global_mean'), PriorityCandidate('functional', 'regional_mean')]
    train, query = frame.index[:90], frame.index[90:]
    first = select('P06', train, target, groups, states, {'functional': frame}, grid=grid)
    model = fit_selection(first, target, {'functional': frame})
    before = model.contract()
    expected = model.predict({'functional': frame}, [query[0]])
    altered_frame = frame.copy()
    altered_frame.loc[query[1:]] = frame.loc[query[1:]]*1e5
    altered_target = target.copy()
    altered_target.loc[query] = -1e8
    second = select('P06', train, altered_target, groups, states, {'functional': altered_frame}, grid=grid)
    fitted = fit_selection(second, altered_target, {'functional': altered_frame})
    assert before == fitted.contract()
    np.testing.assert_allclose(expected, fitted.predict({'functional': altered_frame}, [query[0]]), atol=1e-10, rtol=0)
    # El lote adicional no transforma ni actualiza el contexto de train.
    altered_frame.loc[query[1:], 'region__A'] = 1.
    altered_frame.loc[query[1:], 'region__B'] = 0.
    np.testing.assert_allclose(expected, fitted.predict({'functional': altered_frame}, query)[:1], atol=1e-10, rtol=0)
    assert before == fitted.contract()


def test_invalid_candidate_not_averaged_over_surviving_folds():
    frame, target, groups, states = inputs(60)
    # Nunca alcanza las 20 parcelas/50% de una rama en cada inner-train.
    frame.loc[frame.index[15:], frame.columns.str.startswith('coef_')] = np.nan
    grid = [PriorityCandidate('functional', 'gpr', components=2), PriorityCandidate('functional', 'global_mean'),
            PriorityCandidate('functional', 'regional_mean')]
    result = select('P05', frame.index, target, groups, states, {'functional': frame}, grid=grid)
    assert len(result['failures']) == 1 and len(result['scores']) == 2
    assert not result['failures'][0]['averaged_partial_folds']
    assert len(fit_selection(result, target, {'functional': frame}).predict({'functional': frame}, frame.index)) == 60


def test_calibration_is_excluded_from_bases_and_center():
    frame, target, groups, states = inputs()
    grid = [PriorityCandidate('functional', 'hierarchical_gpr', components=2, state_setting=0.),
            PriorityCandidate('functional', 'global_mean'), PriorityCandidate('functional', 'regional_mean')]
    calibration = calibrate('P06', frame.index, target, groups, states, {'functional': frame}, grid=grid)
    assert len(calibration['calibration_ids']) >= 25
    assert not set(calibration['fit_ids']) & set(calibration['calibration_ids'])
    assert all(not set(component.training_ids_) & set(calibration['calibration_ids']) for component in calibration['model'].models)
    assert calibration['nominal'] == .9


@pytest.mark.parametrize('family,kwargs', [('hierarchical_ridge', {'state_setting': 10}),
              ('hierarchical_gpr', {'state_setting': .25}), ('hierarchical_gam', {'state_setting': 10}),
              ('gam', {}), ('ridge', {}), ('gpr', {})])
def test_composition_and_incompatible_transform_rejected(family, kwargs):
    frame, target, _, _ = inputs(60)
    candidate = PriorityCandidate('x', family, selector='all', **kwargs)
    model = FittedCandidate(candidate).fit(frame, target)
    parts = model.decompose(frame.iloc[[0]])
    np.testing.assert_allclose(model.predict(frame.iloc[[0]]), parts['reference']+parts['state_effect']+parts['parcel_effect'], atol=1e-10, rtol=0)
    with pytest.raises(ValueError):
        model.predict(frame.drop(columns='region__B'))
