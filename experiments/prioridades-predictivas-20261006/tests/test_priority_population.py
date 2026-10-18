from pathlib import Path
import pandas as pd
import pytest
from agrocebada.common import ROOT, ID, TARGET
from agrocebada.priority_population import validate_population_and_schemes


@pytest.fixture
def inputs():
    return (pd.read_parquet(ROOT / 'data/processed/parcels.parquet'),
            pd.read_csv(ROOT / 'registry/schemes.csv'))


def test_original_assignments(inputs):
    master, assignments = inputs
    assert validate_population_and_schemes(master, assignments)['labeled'] == 138


@pytest.mark.parametrize('alteration', ['duplicate', 'hidden_label', 'fold', 'missing_id', 'cutoff'])
def test_incompatible_inputs_rejected(inputs, alteration):
    master, assignments = inputs
    cutoff = '2025-10-31'
    if alteration == 'duplicate':
        assignments = pd.concat([assignments, assignments.iloc[[0]]])
    elif alteration == 'hidden_label':
        master.loc[master[TARGET].isna().idxmax(), TARGET] = 3.
    elif alteration == 'fold':
        assignments.loc[0, 'fold'] = 9
    elif alteration == 'missing_id':
        assignments.loc[0, ID] = 'NO_OFICIAL'
    else:
        cutoff = '2025-09-30'
    with pytest.raises(ValueError):
        validate_population_and_schemes(master, assignments, cutoff)
