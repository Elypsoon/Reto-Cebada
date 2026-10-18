"""Evaluación pareada congelada, diagnósticos y recuperación de objetos ajustados."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from .common import ROOT, ID, TARGET, sha256
from .tracking import atomic_json
from .modeling import metric
from .priority_adapter import FittedCandidate
from .priority_catalog import candidates
from .priority_data import load
from .priority_selection import select, fit_selection, calibrate
from .priority_validation import SCHEMES, interval_summary


def serial(selection):
    return {**selection,'candidates':[asdict(c) for c in selection['candidates']]}


def diagnostics(frame, column='official'):
    def stats(part):
        return {**metric(part[TARGET],part[column]),'bias':float((part[column]-part[TARGET]).mean()),'n':len(part)}
    bins = pd.qcut(frame.AREA_HA,3,labels=['pequeña','mediana','grande'])
    return {'metrics':stats(frame),'by_state':{str(k):stats(v) for k,v in frame.groupby('Estado')},
            'by_fold':{str(k):stats(v) for k,v in frame.groupby('spatial_group')},
            'by_area':{str(k):stats(frame.loc[bins.eq(k)]) for k in bins.unique()}}


def evaluate(block,scheme,master,tables,groups,destination):
    ids = master.index[master[TARGET].notna()]
    y, states = master[TARGET], master.Estado
    frame = master.loc[ids,['Estado','Municipio','AREA_HA',TARGET]].copy()
    frame['spatial_group'] = groups.loc[ids]
    for field in ['official','regional_mean','global_mean','interval_low','interval_high']:
        frame[field] = np.nan
    grid = candidates(block)
    individual = pd.DataFrame(np.nan,index=ids,columns=[c.id for c in grid])
    failed, records = [], []
    for fold in sorted(groups.loc[ids].unique()):
        tr = ids[groups.loc[ids].ne(fold)]; va = ids[groups.loc[ids].eq(fold)]
        if len(tr)<80 or len(va)<15:
            raise ValueError('Partición externa fuera de mínimos')
        print(block,scheme,'fold',fold,'train',len(tr),'validación',len(va),flush=True)
        selection = select(block,tr,y,groups,states,tables)
        fitted = fit_selection(selection,y,tables)
        frame.loc[va,'official'] = fitted.predict(tables,va)
        parts = fitted.decompose(tables,va)
        for field,value in parts.items():
            frame.loc[va,field] = value
        for c in grid:
            try:
                m = FittedCandidate(c).fit(tables[c.representation].loc[tr],y.loc[tr])
                values = m.predict(tables[c.representation].loc[va])
                individual.loc[va,c.id] = values
                if c.family.endswith('_mean'):
                    frame.loc[va,c.family] = values
            except (ValueError,np.linalg.LinAlgError) as error:
                failed.append({'scheme':scheme,'fold':int(fold),'candidate':c.id,'reason':str(error)})
        cal = calibrate(block,tr,y,groups,states,tables) if block=='P06' else None
        if cal:
            center = cal['model'].predict(tables,va)
            frame.loc[va,'interval_low'] = center-cal['radius']
            frame.loc[va,'interval_high'] = center+cal['radius']
        records.append({'fold':int(fold),'train_ids':tr.tolist(),'validation_ids':va.tolist(),
                        'selection':serial(selection),'contract':fitted.contract(),
                        'calibration':{k:v for k,v in cal.items() if k not in ['model','selection']} if cal else None})
        atomic_json(destination/f'folds-{scheme}.json',records)
        frame.reset_index().to_csv(destination/f'partial-oof-{scheme}.csv',index=False,float_format='%.17g')
    if not np.isfinite(frame[['official','regional_mean','global_mean']]).all().all():
        raise ValueError('OOF incompleta; no se promedian folds parciales')
    frame.reset_index().to_csv(destination/f'oof-{scheme}.csv',index=False,float_format='%.17g')
    individual.to_csv(destination/f'individual-oof-{scheme}.csv',float_format='%.17g')
    reports = {c.id:{'configuration':asdict(c),'complete':bool(individual[c.id].notna().all()),
                    'metrics':metric(y.loc[ids],individual[c.id]) if individual[c.id].notna().all() else None}
               for c in grid}
    atomic_json(destination/f'individual-{scheme}.json',{'candidates':reports,'failures':failed,
                'outer_selects_configuration':False,'interpretation':'Diagnósticos de configuraciones fijas; no redefinen P06.'})
    frame['squared_error_delta_regional']=(frame.official-frame[TARGET])**2-(frame.regional_mean-frame[TARGET])**2
    frame.reset_index().to_csv(destination/f'paired-{scheme}.csv',index=False,float_format='%.17g')
    atomic_json(destination/f'validation-{scheme}.json',diagnostics(frame))
    return frame


def stress(master,tables,groups,destination):
    import geopandas as gpd
    ids=master.index[master[TARGET].notna()]
    projected=master.to_crs(32614)
    scenarios=[]
    for state in sorted(master.loc[ids].Estado.unique()):
        tr=ids[master.loc[ids].Estado.ne(state)];va=ids[master.loc[ids].Estado.eq(state)]
        scenarios.append(('exclusión estatal',state,tr,va,None))
    for fold in sorted(groups.loc[ids].unique()):
        tr=ids[groups.loc[ids].ne(fold)];va=ids[groups.loc[ids].eq(fold)]
        distance=projected.loc[tr].geometry.distance(projected.loc[va].geometry.union_all())
        kept=tr[distance.ge(1000)]
        scenarios.append(('buffer 1000 m',int(fold),kept,va,float(distance.loc[kept].min()) if len(kept) else None))
    records=[]
    for kind,key,tr,va,distance in scenarios:
        record={'kind':kind,'held_out':key,'train_ids':tr.tolist(),'validation_ids':va.tolist(),
                'minimum_polygon_distance_m':distance}
        if len(tr)<80 or groups.loc[tr].nunique()<2:
            record.update(status='non_viable',reason='Train menor que 80 o menos de dos grupos internos')
        else:
            print('P06 sensibilidad',kind,key,flush=True)
            selection=select('P06',tr,master[TARGET],groups,master.Estado,tables)
            model=fit_selection(selection,master[TARGET],tables)
            prediction=model.predict(tables,va)
            parts=model.decompose(tables,va)
            if kind=='exclusión estatal':
                np.testing.assert_allclose(prediction,master.loc[tr,TARGET].mean(),atol=1e-10,rtol=0)
            output=master.loc[va,['Estado',TARGET]].copy()
            output['official']=prediction
            for field,value in parts.items():output[field]=value
            filename=f'stress-{len(records)}.csv'
            output.to_csv(destination/filename,float_format='%.17g')
            record.update(status='completed',metrics=metric(master.loc[va,TARGET],prediction),selection=serial(selection),file=filename)
        records.append(record)
        atomic_json(destination/'stress.json',records)


def run(block,destination):
    destination=Path(destination);destination.mkdir(exist_ok=True)
    master,tables,group_sets=load()
    ids=master.index[master[TARGET].notna()];hidden=master.index[master[TARGET].isna()]
    schemes=SCHEMES+(['intraestado-3'] if block=='P06' else [])
    frames={}
    with threadpool_limits(limits=2):
        for scheme in schemes:
            frames[scheme]=evaluate(block,scheme,master,tables,group_sets[scheme],destination)
        groups=group_sets[SCHEMES[0]]
        selection=select(block,ids,master[TARGET],groups,master.Estado,tables)
        model=fit_selection(selection,master[TARGET],tables)
        prediction=model.predict(tables,hidden)
        if not np.isfinite(prediction).all() or (prediction<0).any():
            raise ValueError('Exportación inválida; sin recortar predicciones')
        pd.DataFrame({ID:hidden,TARGET:prediction}).to_csv(destination/'predictions_59.csv',index=False,float_format='%.17g')
        cal=calibrate(block,ids,master[TARGET],groups,master.Estado,tables) if block=='P06' else None
        if block=='P06':
            atomic_json(destination/'intervals.json',interval_summary(frames[SCHEMES[0]],cal))
            stress(master,tables,groups,destination)
        joblib.dump({'model':model,'selection':selection,'interval':cal},destination/'model.joblib')
        atomic_json(destination/'contract.json',{'block':block,'model_hash':sha256(destination/'model.joblib'),
                    'selection':serial(selection),'fitted':model.contract(),'hidden_ids':hidden.tolist(),
                    'protocol_hash':sha256(destination.parent/'protocol.json'),
                    'data_hashes':{p.name:sha256(p) for p in (ROOT/'data/processed').glob('*') if p.is_file()}})
        atomic_json(destination/'metrics.json',{scheme:diagnostics(frame)['metrics'] for scheme,frame in frames.items()})


def verify(destination):
    destination=Path(destination)
    contract=json.loads((destination/'contract.json').read_text(encoding='utf-8'))
    if sha256(destination/'model.joblib')!=contract['model_hash'] or sha256(destination.parent/'protocol.json')!=contract['protocol_hash']:
        raise ValueError('Objeto/protocolo alterados')
    if any(sha256(ROOT/'data/processed'/name)!=digest for name,digest in contract['data_hashes'].items()):
        raise ValueError('Datos alterados')
    master,tables,_=load();hidden=master.index[master[TARGET].isna()]
    if hidden.tolist()!=contract['hidden_ids']:raise ValueError('Consultas incompatibles')
    bundle=joblib.load(destination/'model.joblib')
    pred=bundle['model'].predict(tables,hidden)
    saved=pd.read_csv(destination/'predictions_59.csv',float_precision='round_trip').set_index(ID).loc[hidden,TARGET]
    np.testing.assert_allclose(pred,saved,atol=1e-10,rtol=0)
    metrics=json.loads((destination/'metrics.json').read_text(encoding='utf-8'))
    for scheme,expected in metrics.items():
        frame=pd.read_csv(destination/f'oof-{scheme}.csv',float_precision='round_trip').set_index(ID)
        got=diagnostics(frame)['metrics']
        for key,value in expected.items():np.testing.assert_allclose(got[key],value,atol=1e-10,rtol=0)
    parts=bundle['model'].decompose(tables,hidden)
    np.testing.assert_allclose(sum(parts.values()),pred,atol=1e-10,rtol=0)
    atomic_json(destination/'fresh-process-check.json',{'passed':True,'n':59,'atol':1e-10,'rtol':0,'offline':True,
                                                      'metrics_recalculated':True,'no_transform_refit':True})
    print('Recuperación verificada',contract['block'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['run','verify']);parser.add_argument('key');parser.add_argument('destination',nargs='?')
    args=parser.parse_args()
    if args.action=='run':run(args.key,args.destination)
    else:verify(args.destination or args.key)
