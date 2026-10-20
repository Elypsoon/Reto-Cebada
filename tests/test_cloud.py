import json
from pathlib import PurePosixPath
import pandas as pd
import pytest
from agrocebada.common import ROOT, PROCESSED, dependencies
from agrocebada.inference import compatible_dependencies


def test_python_patch_changes_are_allowed_but_libraries_and_minor_are_exact():
    expected = dependencies()
    actual = dict(expected, python='3.12.99')
    assert compatible_dependencies(expected, actual)
    assert not compatible_dependencies(expected, dict(actual, python='3.13.0'))
    assert not compatible_dependencies(expected, dict(actual, **{'scikit-learn': '0.0.0'}))
    actual.pop('numpy')
    assert not compatible_dependencies(expected, actual)


def test_every_feature_table_has_a_portable_existing_relative_path():
    configs = json.loads((PROCESSED / 'feature-configs.json').read_text())
    assert len(configs) == 9
    for value in configs.values():
        path = PurePosixPath(value)
        assert '\\' not in value and not path.is_absolute() and '..' not in path.parts
        assert (ROOT / path).is_file()


def test_selective_satellite_read_matches_original_observations():
    # The cloud optimization must retain every observation, cloud value and index value.
    from agrocebada.features import SENSORS
    original = pd.read_parquet(PROCESSED / 'satellite.parquet')
    parcels = original.ID_POLIGONO.drop_duplicates().iloc[[0, -1]]
    for pid in parcels:
        for sensor, (_, indices) in SENSORS.items():
            col = indices[0] + '_promedio'
            columns = ['ID_POLIGONO', 'sensor', 'date', 'porcentaje_nubosidad', col]
            expected = original.loc[
                original.ID_POLIGONO.eq(pid) & original.sensor.eq(sensor)
                & original.date.between('2025-04-01', '2025-10-31'), columns
            ].sort_values('date').reset_index(drop=True)
            actual = pd.read_parquet(PROCESSED / 'satellite.parquet', columns=columns,
                filters=[('ID_POLIGONO', '==', pid), ('sensor', '==', sensor),
                         ('date', '>=', pd.Timestamp('2025-04-01')), ('date', '<=', pd.Timestamp('2025-10-31'))]
            ).sort_values('date').reset_index(drop=True)
            pd.testing.assert_frame_equal(actual, expected)


def test_e12_export_and_intervals_match_incoming_research():
    import numpy as np
    from agrocebada.common import ARTIFACTS, ID, TARGET
    from agrocebada.inference import Predictor, official_export
    p = Predictor('selected')
    expected = pd.read_csv(ROOT / 'experiments/fisiologia-siniestros-20261018/runs/E12/predictions_59.csv').set_index(ID)
    exported = official_export(p)
    np.testing.assert_allclose(exported[TARGET], expected.loc[exported[ID], TARGET], rtol=0, atol=1e-10)
    saved = pd.read_csv(ARTIFACTS / 'predictions_59_intervals.csv').set_index(ID)
    actual = p.predict(exported[ID])
    for column in [TARGET, 'INTERVAL_LOW', 'INTERVAL_HIGH']:
        np.testing.assert_allclose(actual[column], saved.loc[actual[ID], column], rtol=0, atol=1e-10)
    assert actual.INTERVAL_LOW.ge(0).all()


def test_precomputed_ensemble_does_not_claim_base_model_explanations():
    from agrocebada.inference import Predictor
    p = Predictor('selected')
    effects, info = p.explain(p.master.ID_POLIGONO.iloc[0])
    assert effects.empty and info['available'] is False and info['exact_additive'] is False
    official = Predictor('official')
    effects, info = official.explain(official.master.ID_POLIGONO.iloc[0])
    assert not effects.empty and info.get('available', True)
