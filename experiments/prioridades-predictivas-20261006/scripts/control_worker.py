"""Llama procedimientos históricos exactos desde su propia copia aislada."""
import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path
import joblib
import geopandas as gpd
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from agrocebada import modeling as m
from agrocebada.common import ROOT, PROCESSED, ARTIFACTS, ID, TARGET, code_hash, sha256, write_json

PHASE=Path(__file__).resolve().parents[1]
PROJECT=PHASE.parents[1]
CONTROL=ROOT.name
SCHEMES=['principal-5','balanceado-4','rotado-45-5','intraestado-3']


def setup():
    if ROOT!=PHASE/'controls'/CONTROL or CONTROL not in ['C-activa','C-soporte']:
        raise ValueError('Importación del control incorrecta')
    master=gpd.read_parquet(PROCESSED/'parcels.parquet')
    tables,external,location=m.load_tables(master)
    if CONTROL=='C-soporte':
        from agrocebada import variants as v
        v.configure('E00')
        tables={k:tables[k] for k in ['monthly_20_10','whittaker_20_10']}
    return master,tables,external,location


def inspect():
    master,tables,external,location=setup()
    write_json(ROOT/'provenance/procedure.json',{'control':CONTROL,'code_hash':code_hash(),
        'keys':list(tables),'candidate_grid':[asdict(c) for c in m.candidate_grid(tables)],
        'sources':list(external),'routes':['official','selected'],'schemes':SCHEMES,
        'data_hashes':{p.name:sha256(p) for p in PROCESSED.glob('*') if p.is_file()},
        'selection':'Procedimiento histórico original sin cambiar parámetros, grilla, admisión o ensambles.',
        'atol':1e-10,'rtol':0,'new_metrics':None})
    print(CONTROL,'protocolo histórico inspeccionado',flush=True)


def run():
    master,tables,external,location=setup()
    indices=np.flatnonzero(master[TARGET].notna());hidden=np.flatnonzero(master[TARGET].isna())
    y=master[TARGET].to_numpy();states=master.Estado.to_numpy()
    assignments=pd.read_csv(PHASE/'registry/schemes.csv');sets={}
    for scheme in SCHEMES:
        groups=np.full(len(master),-1)
        groups[indices]=assignments[assignments.scheme.eq(scheme)].set_index(ID).loc[master.iloc[indices][ID]].fold.to_numpy()
        sets[scheme]=groups
    with threadpool_limits(limits=2):
        for scheme,groups in sets.items():
            if CONTROL=='C-soporte':
                from agrocebada import robust as r
                r.evaluate(scheme,master,tables,external,location,groups,indices)
                frame=pd.read_csv(ARTIFACTS/f'oof-{scheme}.csv',float_precision='round_trip').set_index(ID)
                source=PROJECT/'experiments/soporte-regional-20261003/runs/E00-v2/artifacts'/f'oof-{scheme}.csv'
                if source.exists():
                    expected=pd.read_csv(source,float_precision='round_trip').set_index(ID).loc[frame.index]
                    for field in ['official','selected','regional_mean','global_mean','gpr','catboost']:
                        np.testing.assert_allclose(frame[field],expected[field],atol=1e-10,rtol=0)
            else:
                frame=master.iloc[indices][[ID,'Estado','Municipio','AREA_HA',TARGET]].copy().set_index(ID)
                frame['spatial_group']=groups[indices]
                records=[]
                for fold in sorted(np.unique(groups[indices])):
                    tr=indices[groups[indices]!=fold];va=indices[groups[indices]==fold]
                    print(CONTROL,scheme,'fold',fold,flush=True)
                    official=m.select(tr,y,groups,states,tables,external,location,allow_external=False)
                    selected=m.select(tr,y,groups,states,tables,external,location,base_scores=official['_raw_scores']) if external else official
                    for route,selection in [('official',official),('selected',selected)]:
                        model=m.fit_selection(selection,tr,y,tables,external,location)
                        frame.loc[master.iloc[va][ID],route]=m.predict_selection(model,selection,va,tables,external,location)
                    for key,values in m.baseline_predictions(y[tr],states[tr],states[va]).items():
                        frame.loc[master.iloc[va][ID],key]=values
                    records.append({'fold':int(fold),'official':m._serial_selection(official),'selected':m._serial_selection(selected)})
                    write_json(ARTIFACTS/f'folds-{scheme}.json',records)
                frame.reset_index().to_csv(ARTIFACTS/f'oof-{scheme}.csv',index=False,float_format='%.17g')
                if scheme=='principal-5':
                    expected=pd.read_csv(PROJECT/'artifacts/oof.csv',float_precision='round_trip').set_index(ID).loc[frame.index]
                    for field in ['official','selected','regional_mean','global_mean']:
                        np.testing.assert_allclose(frame[field],expected[field],atol=1e-10,rtol=0)
            write_json(ARTIFACTS/f'metrics-{scheme}.json',{route:m.metric(frame[TARGET],frame[route]) for route in ['official','selected','regional_mean']})
        groups=sets['principal-5']
        official=m.select(indices,y,groups,states,tables,external,location,False)
        selected=m.select(indices,y,groups,states,tables,external,location,True,base_scores=official['_raw_scores']) if external else official
        for route,selection in [('official',official),('selected',selected)]:
            model=m.fit_selection(selection,indices,y,tables,external,location)
            prediction=m.predict_selection(model,selection,hidden,tables,external,location)
            filename='predictions_59.csv' if route=='selected' else 'predictions_official_only_59.csv'
            output=pd.DataFrame({ID:master.iloc[hidden][ID].to_numpy(),TARGET:prediction}).sort_values(ID)
            source=(PROJECT/'artifacts' if CONTROL=='C-activa' else PROJECT/'experiments/soporte-regional-20261003/runs/E00-v2/artifacts')/filename
            expected=pd.read_csv(source,float_precision='round_trip').sort_values(ID)
            if not output[ID].reset_index(drop=True).equals(expected[ID].reset_index(drop=True)):
                raise ValueError('IDs de consultas históricos incompatibles')
            np.testing.assert_allclose(output[TARGET],expected[TARGET],atol=1e-10,rtol=0)
            output.to_csv(ARTIFACTS/filename,index=False,float_format='%.17g')
            joblib.dump({'model':model,'selection':selection},ARTIFACTS/f'model_{route}.joblib')
        write_json(ARTIFACTS/'reproduction.json',{'control':CONTROL,'passed':True,'code_hash':code_hash(),
                   'principal_and_hidden_atol':1e-10,'rtol':0,'routes':['official','selected'],'schemes':SCHEMES})


def verify():
    master,tables,external,location=setup();hidden=np.flatnonzero(master[TARGET].isna())
    procedure=json.loads((ROOT/'provenance/procedure.json').read_text(encoding='utf-8'))
    if code_hash()!=procedure['code_hash'] or any(sha256(PROCESSED/name)!=h for name,h in procedure['data_hashes'].items()):
        raise ValueError('Procedimiento/datos históricos alterados')
    for route in ['official','selected']:
        bundle=joblib.load(ARTIFACTS/f'model_{route}.joblib')
        p=m.predict_selection(bundle['model'],bundle['selection'],hidden,tables,external,location)
        filename='predictions_59.csv' if route=='selected' else 'predictions_official_only_59.csv'
        expected=pd.read_csv(ARTIFACTS/filename,float_precision='round_trip').set_index(ID).loc[master.iloc[hidden][ID],TARGET]
        np.testing.assert_allclose(p,expected,atol=1e-10,rtol=0)
    for scheme in SCHEMES:
        expected=json.loads((ARTIFACTS/f'metrics-{scheme}.json').read_text(encoding='utf-8'))
        frame=pd.read_csv(ARTIFACTS/f'oof-{scheme}.csv',float_precision='round_trip')
        for route,values in expected.items():
            got=m.metric(frame[TARGET],frame[route])
            for key,value in values.items():np.testing.assert_allclose(got[key],value,atol=1e-10,rtol=0)
    write_json(ARTIFACTS/'fresh-process-check.json',{'passed':True,'n_per_route':59,'offline':True,
                'metrics_recalculated':True,'atol':1e-10,'rtol':0,'no_refit':True})
    print(CONTROL,'recuperación verificada',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['inspect','run','verify']);args=parser.parse_args()
    ARTIFACTS.mkdir(exist_ok=True)
    {'inspect':inspect,'run':run,'verify':verify}[args.action]()
