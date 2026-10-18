import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from agrocebada.priority_functional import individual_projection, FunctionalProjection
from agrocebada.priority_curves import BRANCHES, QUALITY
from agrocebada.priority_selectors import ENVIRONMENT, PrioritySelector
from agrocebada.segments import reconstruct_segments


def test_individual_support_and_no_gap_weight():
    dates = pd.to_datetime(['2025-04-01', '2025-04-08', '2025-04-15', '2025-04-22',
                            '2025-08-01', '2025-08-08', '2025-08-15', '2025-08-22'])
    observations = pd.DataFrame({'date': dates, 'v': np.arange(8.)/8, 'porcentaje_nubosidad': 0.})
    pieces, _, _ = reconstruct_segments(observations, 'v')
    coef, meta = individual_projection({'pieces': pieces, 'column': 'v'})
    assert len(coef) == 6 and np.isfinite(coef).all()
    assert meta['weighted_dates'] == dates.strftime('%Y-%m-%d').tolist()
    assert meta['unobserved_weight'] == 0 and not meta['reconstructed_values']
    coef, meta = individual_projection({'pieces': pieces[:1], 'column': 'v'})
    assert np.isnan(coef).all() and not meta['available']
    # Ocho observaciones limitadas a un tercio siguen siendo insuficientes.
    observations.date = pd.date_range('2025-04-01', periods=8, freq='7D')
    pieces, _, _ = reconstruct_segments(observations, 'v')
    coef, _ = individual_projection({'pieces': pieces, 'column': 'v'})
    assert np.isnan(coef).all()


def inputs(n=50):
    rng = np.random.default_rng(2026)
    return pd.DataFrame({**{f'coef_{b}_{j}': rng.normal(size=n) for b in BRANCHES for j in range(6)},
                         **{c: rng.normal(size=n) for c in list(ENVIRONMENT)+list(QUALITY)}})


@pytest.mark.parametrize('components', [2, 3])
def test_train_only_basis_batch_invariance_missing_rows(components):
    train = inputs()
    projection = FunctionalProjection(components).fit(train)
    before = projection.contract()
    query = inputs(7)
    single = projection.transform(query.iloc[[0]])
    query.loc[1:, [c for c in query if c.startswith('coef_')]] = 100000.
    pd.testing.assert_frame_equal(single, projection.transform(query).iloc[[0]])
    query.loc[0, [c for c in query if c.startswith('coef_')]] = np.nan
    transformed = projection.transform(query)
    assert len(transformed) == 7 and transformed.filter(like='fpca_').iloc[0].isna().all()
    assert before == projection.contract()
    assert before == FunctionalProjection(components).fit(train, np.arange(50.)**2).contract()


def test_minimum_training_support_and_no_external_basis():
    train = inputs(50)
    train.loc[20:, train.columns.str.startswith('coef_')] = np.nan
    with pytest.raises(ValueError):
        FunctionalProjection().fit(train)
    train = inputs(30)
    train.loc[19:, train.columns.str.startswith('coef_')] = np.nan
    with pytest.raises(ValueError):
        FunctionalProjection().fit(train)


def test_fitted_prediction_unaffected_by_queries_or_external_labels():
    train = inputs()
    pipe = Pipeline([('functional', FunctionalProjection()), ('select', PrioritySelector('all')),
                     ('scale', StandardScaler()), ('model', Ridge(alpha=1.))])
    pipe.fit(train, np.arange(50.)/20)
    before = pipe.named_steps['functional'].contract()
    query = inputs(7)
    expected = pipe.predict(query.iloc[[0]])
    query.loc[1:, :] = -9000.
    np.testing.assert_allclose(expected, pipe.predict(query)[:1], atol=1e-10, rtol=0)
    assert before == pipe.named_steps['functional'].contract()
    # Las etiquetas externas no son argumento de transformación ni de inferencia.
    external_labels = np.arange(7.)*1e6
    assert np.isfinite(external_labels).all()
    np.testing.assert_allclose(expected, pipe.predict(query.iloc[[0]]), atol=1e-10, rtol=0)
