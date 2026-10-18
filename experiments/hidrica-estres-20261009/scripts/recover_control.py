"""Recupera las dos rutas históricas originales sin reentrenar."""
import sys
from pathlib import Path
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'controls/C-activa/src'))
sys.path.insert(0,str(PHASE/'src'))
import numpy as np
import pandas as pd
import geopandas as gpd
import joblib
from threadpoolctl import threadpool_limits
from agrocebada import modeling as historic
from agrocebada.common import code_hash,PROCESSED
from hydric.common import ROOT,ID,TARGET,SCHEMES,read,save,digest,now
from hydric.registry import protocol

protocol()
assert code_hash()==read(ROOT/'controls/C-activa/provenance/procedure.json')['code_hash']
assert PROCESSED==ROOT/'controls/C-activa/data/processed'
master=gpd.read_parquet(PROCESSED/'parcels.parquet')
tables,external,location=historic.load_tables(master)
hidden=np.flatnonzero(master[TARGET].isna())
source=ROOT/'controls/W00-artifacts';folder=ROOT/'runs/W00';folder.mkdir(parents=True,exist_ok=True)
with threadpool_limits(limits=2):
    for route,name in [('official','predictions_official_only_59.csv'),('selected','predictions_59.csv')]:
        bundle=joblib.load(source/f'model_{route}.joblib')
        predicted=historic.predict_selection(bundle['model'],bundle['selection'],hidden,tables,external,location)
        expected=pd.read_csv(source/name,float_precision='round_trip').set_index(ID).loc[master.iloc[hidden][ID],TARGET]
        np.testing.assert_allclose(predicted,expected,atol=1e-10,rtol=0)
        individual=np.array([historic.predict_selection(bundle['model'],bundle['selection'],np.array([i]),tables,external,location)[0] for i in hidden])
        np.testing.assert_allclose(individual,expected,atol=1e-10,rtol=0)
        pd.DataFrame({ID:master.iloc[hidden][ID].to_numpy(),TARGET:predicted}).to_csv(folder/name,index=False,float_format='%.17g')
    reports={}
    schemes=pd.read_csv(ROOT/'registry/schemes.csv')
    for scheme in SCHEMES:
        frame=pd.read_csv(source/f'oof-{scheme}.csv',float_precision='round_trip')
        assert len(frame)==138 and frame[ID].is_unique
        mapping=schemes[schemes.scheme.eq(scheme)].set_index(ID).fold
        assert np.array_equal(frame.spatial_group,frame[ID].map(mapping))
        prior=read(source/f'metrics-{scheme}.json')
        report={}
        for route in ['official','selected','regional_mean','global_mean']:
            current=historic.metric(frame[TARGET],frame[route]);report[route]=current
            if route in prior:
                for key,value in current.items():np.testing.assert_allclose(value,prior[route][key],atol=1e-10,rtol=0)
        reports[scheme]=report
        frame.to_csv(folder/f'oof-{scheme}.csv',index=False,float_format='%.17g')
        save(folder/f'metrics-{scheme}.json',report)
save(folder/'metrics.json',reports)
save(folder/'fresh-process-check.json',{'passed':True,'offline':True,'n_hidden':59,'routes':['official','selected'],
  'historical_code_hash':code_hash(),'metrics_recalculated':True,'new_training':False,'atol':1e-10,'rtol':0,'at':now()})
save(folder/'recovery-package.json',{'historical_code':str(ROOT/'controls/C-activa/src'),
  'models_and_context':str(source),'protocol_hash':digest(ROOT/'registry/frozen-protocol.json'),
  'original_contracts':str(ROOT/'controls/C-activa/artifacts'),'offline_verified':True})
print('W00 recuperado: dos rutas, 59 consultas y tres esquemas',flush=True)
