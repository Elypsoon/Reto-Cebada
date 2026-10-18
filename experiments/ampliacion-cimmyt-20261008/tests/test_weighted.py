import numpy as np
import pandas as pd
import pytest
from cimmyt.weighted import COLUMNS, CONTINUOUS, STATES, sample_weights, fit_weighted


def frame(n, seed=2026):
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.normal(size=(n, len(CONTINUOUS))), columns=CONTINUOUS)
    for j, name in enumerate(STATES):
        X[name] = (np.arange(n) % 4 == j).astype(float)
    return X[COLUMNS]


def test_mass_and_equal_group_influence():
    weights = sample_weights(100, ['a', 'a', 'a', 'b'], .5)
    assert weights[:100].sum() == 100
    assert weights[100:].sum() == 50
    assert weights[100:103].sum() == weights[103]


def test_ridge_matches_documented_weighted_objective():
    official, donor = frame(24), frame(12, 8)
    y = np.linspace(1., 4., 24)
    yd = np.linspace(2., 5., 12)
    groups = ['a']*8 + ['b']*4
    model, contract = fit_weighted(official, y, donor, yd, groups, .5, 10.)
    X = pd.concat([official, donor], ignore_index=True)
    z = model['scale'].transform(X)
    design = np.column_stack([np.ones(len(z)), z])
    weights = np.asarray(contract['weights'])
    penalty = np.diag(np.r_[0, np.full(z.shape[1], 10.)])
    solution = np.linalg.solve(design.T @ (weights[:, None]*design) + penalty,
                               design.T @ (weights * np.r_[y, yd]))
    np.testing.assert_allclose(model.predict(X), design @ solution, atol=1e-12, rtol=0)
    np.testing.assert_allclose(contract['scale_mean'], np.average(X[CONTINUOUS], axis=0, weights=weights))
    np.testing.assert_array_equal(model['scale'].transform(X)[:, len(CONTINUOUS):], X[STATES])


def test_queries_do_not_change_fit():
    X, y = frame(30), np.linspace(1., 5., 30)
    model, contract = fit_weighted(X.iloc[:20], y[:20])
    first = model.predict(X.iloc[20:])
    query = X.iloc[20:].copy()
    query[CONTINUOUS] *= 1000
    model.predict(query)
    np.testing.assert_array_equal(first, model.predict(X.iloc[20:]))
    assert model['scale'].scaler_.mean_.tolist() == contract['scale_mean']


def test_source_or_missing_columns_rejected():
    X = frame(10)
    with pytest.raises(ValueError, match='Contrato'):
        fit_weighted(X.assign(source=1), np.arange(10))
    X.iloc[0, 0] = np.nan
    with pytest.raises(ValueError, match='Contrato'):
        fit_weighted(X, np.arange(10))


def test_auxiliary_rows_cannot_enter_zero_influence_control():
    X = frame(10)
    with pytest.raises(ValueError, match='exclusivamente'):
        fit_weighted(X, np.arange(10), X, np.arange(10), ['a']*10, 0.)
