"""Recuperación en proceso nuevo del control oficial copiado, sin reentrenar."""
import sys
import os
from pathlib import Path
PHASE = Path(__file__).resolve().parents[1]
CONTROL = PHASE / 'controls/C-activa'
sys.path.insert(0, str(CONTROL / 'src'))
os.environ['AGROCEBADA_ARTIFACTS'] = str(CONTROL / 'artifacts')
import geopandas as gpd
import pandas as pd
import numpy as np
import joblib
from threadpoolctl import threadpool_limits
from agrocebada import modeling as m
from agrocebada.common import ROOT as CONTROL_ROOT, PROCESSED, code_hash
from cimmyt.common import ROOT, ID, TARGET, SCHEMES, read, save, digest, now

assert CONTROL_ROOT == CONTROL
assert code_hash() == read(CONTROL / 'provenance/procedure.json')['code_hash']
master = gpd.read_parquet(PROCESSED / 'parcels.parquet')
tables, external, location = m.load_tables(master)
hidden = np.flatnonzero(master[TARGET].isna())
folder = ROOT / 'runs/A00/artifacts'
bundle = joblib.load(folder / 'model_official.joblib')
with threadpool_limits(limits=2):
    prediction = m.predict_selection(bundle['model'], bundle['selection'], hidden, tables, external, location)
expected = pd.read_csv(folder / 'predictions_official_only_59.csv', float_precision='round_trip').set_index(ID).loc[master.iloc[hidden][ID], TARGET]
np.testing.assert_allclose(prediction, expected, atol=1e-10, rtol=0)
metrics = {}
for scheme in SCHEMES:
    frame = pd.read_csv(folder / f'oof-{scheme}.csv', float_precision='round_trip')
    assert len(frame) == 138 and frame[ID].is_unique
    reference = read(folder / f'metrics-{scheme}.json')['official']
    metrics[scheme] = m.metric(frame[TARGET], frame.official)
    for key, value in reference.items():
        np.testing.assert_allclose(metrics[scheme][key], value, atol=1e-10, rtol=0)
save(folder / 'fresh-process-check.json', {'passed': True, 'offline': True, 'n_hidden': 59,
     'metrics_recalculated': True, 'atol': 1e-10, 'rtol': 0, 'source_code_hash': code_hash(), 'at': now()})
save(ROOT / 'runs/A00/run.json', {'status': 'completed', 'verified': True, 'historical_control': True,
     'new_training': False, 'metrics': metrics, 'activated': False, 'deployed': False, 'sent': False})
print('A00 recuperado: 59 consultas y métricas de 138 OOF por esquema verificadas')
