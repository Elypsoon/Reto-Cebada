"""Recupera control y métricas originales sin ajustar modelos."""
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
from signalclima.common import ROOT,ID,TARGET,SCHEMES,read,save,digest,now

assert code_hash()==read(ROOT/'controls/C-activa/provenance/procedure.json')['code_hash']
assert PROCESSED==ROOT/'controls/C-activa/data/processed'
master=gpd.read_parquet(PROCESSED/'parcels.parquet')
tables,external,location=historic.load_tables(master)
hidden=np.flatnonzero(master[TARGET].isna())
source=ROOT/'controls/W00-artifacts';folder=ROOT/'runs/F00-ACT'
if (folder/'fresh-process-check.json').exists():raise ValueError('Control ya recuperado; verificar paquete existente')
folder.mkdir(parents=True,exist_ok=True)
with threadpool_limits(limits=2):
    for route,name in [('official','predictions_official_only_59.csv'),('selected','predictions_59.csv')]:
        bundle=joblib.load(source/f'model_{route}.joblib')
        predicted=historic.predict_selection(bundle['model'],bundle['selection'],hidden,tables,external,location)
        expected=pd.read_csv(source/name,float_precision='round_trip').set_index(ID).loc[master.iloc[hidden][ID],TARGET]
        np.testing.assert_allclose(predicted,expected,atol=1e-10,rtol=0)
        individual=np.array([historic.predict_selection(bundle['model'],bundle['selection'],np.array([i]),tables,external,location)[0] for i in hidden])
        np.testing.assert_allclose(individual,expected,atol=1e-10,rtol=0)
        pd.DataFrame({ID:master.iloc[hidden][ID].to_numpy(),TARGET:predicted}).to_csv(folder/name,index=False,float_format='%.17g')
    reports={};schemes=pd.read_csv(ROOT/'registry/schemes.csv')
    for scheme in SCHEMES:
        frame=pd.read_csv(source/f'oof-{scheme}.csv',float_precision='round_trip')
        assert len(frame)==138 and frame[ID].is_unique
        mapping=schemes[schemes.scheme.eq(scheme)].set_index(ID).fold
        assert np.array_equal(frame.spatial_group,frame[ID].map(mapping))
        prior=read(source/f'metrics-{scheme}.json');report={}
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
files={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'controls/C-activa').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
files.update({str(p.relative_to(ROOT)):digest(p) for p in source.iterdir() if p.is_file()})
save(folder/'recovery-package.json',{'artifacts':files,'offline_verified':True,'new_training':False,'atol':1e-10,'rtol':0})
save(folder/'run.json',{'status':'completed','verified':True,'new_training':False,'metrics':reports,'at':now()})
print('F00-ACT recuperado: dos rutas, 59 consultas y tres esquemas',flush=True)
