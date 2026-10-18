"""Comparaciones A01/A02, curva A03 y recuperación de modelos sin entrenarlos."""
import argparse
from dataclasses import asdict
import joblib
import numpy as np
import pandas as pd
import geopandas as gpd
from threadpoolctl import threadpool_limits
from .common import ROOT, ID, TARGET, SCHEMES, read, save
from .spatial import SpatialGuard, support
from .selection import SelectionEngine, Configuration, NonViable, group_fraction, metric, public
from .weighted import sample_weights
from .registry import Registry


def load_inputs():
    master=gpd.read_parquet(ROOT/'data/processed/parcels.parquet').set_index(ID)
    x=pd.read_parquet(ROOT/'data/processed/common-official.parquet')
    ax=pd.read_parquet(ROOT/'data/processed/common-auxiliary.parquet')
    aux=pd.read_parquet(ROOT/'data/processed/cimmyt-admitted.parquet')
    candidates=pd.read_parquet(ROOT/'data/processed/cimmyt-label-candidates.parquet')
    assert master.index.equals(x.index) and ax.index.equals(aux.index)
    assert len(master)==197 and master[TARGET].notna().sum()==138
    guard=SpatialGuard(candidates,master)
    engine=SelectionEngine(x,ax,aux,guard)
    schemes=pd.read_csv(ROOT/'registry/schemes.csv')
    return master,engine,{s:part.set_index(ID).fold for s,part in schemes.groupby('scheme') if s in SCHEMES}


def references(target,states,train_ids):
    y=target.loc[train_ids];state=states.loc[train_ids]
    return {'global':float(y.mean()),'regional':{str(s):float(y[state.eq(s)].mean()) for s in state.unique()}}


def reference_prediction(reference,states,kind):
    return np.full(len(states),reference['global']) if kind=='global' else np.array([
        reference['regional'].get(str(s),reference['global']) for s in states])


def diagnostics(frame, column):
    def stats(part): return metric(part[TARGET],part[column])
    area=pd.qcut(frame.AREA_HA,3,labels=['small','medium','large'])
    return {'overall':stats(frame),'state':{str(k):stats(v) for k,v in frame.groupby('Estado')},
        'fold':{str(k):stats(v) for k,v in frame.groupby('fold')},
        'area':{str(k):stats(frame.loc[area.eq(k)]) for k in area.unique()}}


def execute_comparison(run_id):
    Registry().protocol();master,engine,schemes=load_inputs()
    destination=ROOT/f'runs/{run_id}/artifacts';destination.mkdir(exist_ok=True)
    ids=master.index[master[TARGET].notna()];hidden=master.index[master[TARGET].isna()]
    target=master[TARGET];states=master.Estado;all_models={};reports={}
    with threadpool_limits(limits=2):
        for scheme in SCHEMES:
            folds=schemes[scheme]
            frame=master.loc[ids,['Estado','AREA_HA',TARGET]].copy();frame['fold']=folds.loc[ids]
            for col in ['prediction','global_mean','regional_mean']:frame[col]=np.nan
            records=[]
            for fold in sorted(folds.unique()):
                tr=ids[folds.loc[ids].ne(fold)];va=ids[folds.loc[ids].eq(fold)]
                selection=engine.select(tr,target,folds,states,va.tolist(),augmented=run_id=='A02')
                model,contract=engine.fit(selection['chosen'],tr,target,va.tolist())
                reference=references(target,states,tr)
                prediction=model.predict(engine.X.loc[va])
                frame.loc[va,'prediction']=prediction
                for kind in ['global','regional']:
                    frame.loc[va,kind+'_mean']=reference_prediction(reference,states.loc[va],kind)
                record={'fold':int(fold),'train_ids':tr.tolist(),'validation_ids':va.tolist(),
                    'selection':selection,'contract':contract,'reference':reference,'_model':model}
                records.append(record)
                print(run_id,scheme,'fold',int(fold),'recipe',selection['chosen_id'],
                    'donors',contract['donor_count'],flush=True)
            if not np.isfinite(frame[['prediction','global_mean','regional_mean']].to_numpy()).all():
                raise ValueError('OOF incompleta; no promediar folds parciales')
            if run_id=='A02':
                a01=pd.read_csv(ROOT/f'runs/A01/artifacts/oof-{scheme}.csv',float_precision='round_trip').set_index(ID)
                for record in records:
                    if not record['selection']['used_donors']:
                        va=record['validation_ids']
                        np.testing.assert_allclose(frame.loc[va,'prediction'],a01.loc[va,'prediction'],atol=1e-10,rtol=0)
            frame.to_csv(destination/f'oof-{scheme}.csv',float_format='%.17g')
            save(destination/f'folds-{scheme}.json',public(records))
            all_models[scheme]=records
            reports[scheme]={col:diagnostics(frame,col) for col in ['prediction','global_mean','regional_mean']}
        folds=schemes[SCHEMES[0]]
        final=engine.select(ids,target,folds,states,augmented=run_id=='A02')
        model,contract=engine.fit(final['chosen'],ids,target)
        prediction=model.predict(engine.X.loc[hidden])
        if not np.isfinite(prediction).all(): raise ValueError('Consultas ocultas no finitas')
        pd.DataFrame({ID:hidden,TARGET:prediction}).to_csv(destination/'predictions_59.csv',index=False,float_format='%.17g')
        all_models['final']={'selection':final,'contract':contract,'_model':model,'hidden_ids':hidden.tolist()}
        save(destination/'final-fit.json',public(all_models['final']))
        joblib.dump(all_models,destination/'models.joblib')
        save(destination/'metrics.json',reports)


def execute_curve():
    Registry().protocol();master,engine,schemes=load_inputs()
    source=joblib.load(ROOT/'runs/A02/artifacts/models.joblib')
    destination=ROOT/'runs/A03/artifacts';destination.mkdir(exist_ok=True)
    bundle={};reports={};records=[];applicable=0
    with threadpool_limits(limits=2):
        for scheme in SCHEMES:
            frame=pd.read_csv(ROOT/f'runs/A02/artifacts/oof-{scheme}.csv',float_precision='round_trip').set_index(ID)
            for fraction in [.25,.5,1.]:frame[f'curve_{fraction:g}']=np.nan
            models=[]
            for record in source[scheme]:
                config=record['selection']['chosen'];tr=record['train_ids'];va=record['validation_ids']
                if not config.influence:
                    for fraction in [.25,.5,1.]:
                        records.append({'scheme':scheme,'fold':record['fold'],'fraction':fraction,'status':'not_applicable',
                            'reason':'A02 eligió control sin auxiliares','configuration':asdict(config)})
                    continue
                applicable+=1;donor,admission=engine.donors(config,va)
                for fraction in [.25,.5,1.]:
                    sampled=group_fraction(donor,fraction)
                    result={'scheme':scheme,'fold':record['fold'],'fraction':fraction,'configuration':asdict(config),
                        'validation_ids':va,'sampled_keys':sampled.index.tolist(),'support':support(sampled)}
                    if not support(sampled)['viable']:
                        records.append(dict(result,status='non_viable',reason='Soporte insuficiente; no sustituir por 100%'))
                        continue
                    if fraction==1.:
                        frame.loc[va,'curve_1']=frame.loc[va,'prediction']
                        models.append({**result,'_model':record['_model'],'contract':record['contract'],'reused_A02':True})
                    else:
                        model,contract=engine.fit(config,tr,master[TARGET],va,donor_override=sampled)
                        frame.loc[va,f'curve_{fraction:g}']=model.predict(engine.X.loc[va])
                        models.append({**result,'_model':model,'contract':contract,'reused_A02':False})
                    records.append(dict(result,status='completed',reused_A02=fraction==1.))
            frame.to_csv(destination/f'curve-{scheme}.csv',float_format='%.17g')
            bundle[scheme]=models
            reports[scheme]={f'{fraction:g}':{'complete_official_oof':bool(frame[f'curve_{fraction:g}'].notna().all()),
                'available_predictions':int(frame[f'curve_{fraction:g}'].notna().sum()),
                'metrics':metric(frame[TARGET],frame[f'curve_{fraction:g}']) if frame[f'curve_{fraction:g}'].notna().all() else None}
                for fraction in [.25,.5,1.]}
    save(destination/'curve-status.json',{'records':records,'applicable_outer_fits':applicable,
        'selects_configuration':False,'100_percent_reuses_A02':True})
    save(destination/'metrics.json',reports);joblib.dump(bundle,destination/'models.joblib')
    print('A03 ajustes con receta auxiliar:',applicable,flush=True)


def assert_prediction(actual,expected):
    np.testing.assert_allclose(actual,expected,atol=1e-10,rtol=0,equal_nan=False)


def check_contract(model,contract,engine):
    config=Configuration(**contract['configuration']);tr=contract['official_train_ids']
    assert set(tr).isdisjoint(contract['admission']['retained_ids'])
    donor,admission=engine.donors(config,contract['admission']['retained_ids'])
    assert admission['keys']==contract['admission']['keys']
    keys=contract['donor_keys'];assert set(keys).issubset(donor.index)
    assert len(keys)==contract['donor_count']
    groups=engine.aux.loc[keys,'dependence_group'].tolist()
    assert groups==contract['donor_group_keys']
    expected=sample_weights(len(tr),groups,config.influence)
    assert_prediction(expected,contract['weights'])
    assert_prediction(model['scale'].scaler_.mean_,contract['scale_mean'])
    assert_prediction(model['scale'].scaler_.scale_,contract['scale_std'])
    assert_prediction(model['ridge'].coef_,contract['coef'])
    assert_prediction(model['ridge'].intercept_,contract['intercept'])


def recover(run_id):
    Registry().protocol();master,engine,schemes=load_inputs()
    destination=ROOT/f'runs/{run_id}/artifacts';bundle=joblib.load(destination/'models.joblib')
    computed={};checks=0
    with threadpool_limits(limits=2):
        for scheme in SCHEMES:
            if run_id=='A03':
                frame=pd.read_csv(destination/f'curve-{scheme}.csv',float_precision='round_trip').set_index(ID)
                computed[scheme]={}
                for record in bundle[scheme]:
                    check_contract(record['_model'],record['contract'],engine)
                    va=record['validation_ids'];column=f"curve_{record['fraction']:g}"
                    assert_prediction(record['_model'].predict(engine.X.loc[va]),frame.loc[va,column]);checks+=1
                for fraction in [.25,.5,1.]:
                    column=f'curve_{fraction:g}'
                    computed[scheme][f'{fraction:g}']={'complete_official_oof':bool(frame[column].notna().all()),
                        'available_predictions':int(frame[column].notna().sum()),
                        'metrics':metric(frame[TARGET],frame[column]) if frame[column].notna().all() else None}
                continue
            frame=pd.read_csv(destination/f'oof-{scheme}.csv',float_precision='round_trip').set_index(ID)
            assert len(frame)==138 and frame.index.is_unique and set(frame.index)==set(schemes[scheme].index)
            for record in bundle[scheme]:
                check_contract(record['_model'],record['contract'],engine)
                va=record['validation_ids']
                assert_prediction(record['_model'].predict(engine.X.loc[va]),frame.loc[va,'prediction']);checks+=1
                for kind in ['global','regional']:
                    assert_prediction(reference_prediction(record['reference'],master.loc[va,'Estado'],kind),frame.loc[va,kind+'_mean'])
                for score in record['selection']['scores']:
                    ids=record['selection']['train_ids'];inner=pd.Series(np.nan,index=ids)
                    for model,fit in zip(score['_models'],score['fits']):
                        check_contract(model,fit['contract'],engine)
                        vi=fit['validation_ids'];inner.loc[vi]=model.predict(engine.X.loc[vi]);checks+=1
                    assert_prediction(inner.to_numpy(),score['prediction'])
            computed[scheme]={col:diagnostics(frame,col) for col in ['prediction','global_mean','regional_mean']}
        if run_id!='A03':
            final=bundle['final'];check_contract(final['_model'],final['contract'],engine)
            saved=pd.read_csv(destination/'predictions_59.csv',float_precision='round_trip').set_index(ID)
            assert len(saved)==59 and set(saved.index)==set(master.index[master[TARGET].isna()])
            assert_prediction(final['_model'].predict(engine.X.loc[saved.index]),saved[TARGET]);checks+=1
            selection=final['selection']
            for score in selection['scores']:
                inner=pd.Series(np.nan,index=selection['train_ids'])
                for model,fit in zip(score['_models'],score['fits']):
                    check_contract(model,fit['contract'],engine)
                    vi=fit['validation_ids'];inner.loc[vi]=model.predict(engine.X.loc[vi]);checks+=1
                assert_prediction(inner.to_numpy(),score['prediction'])
    expected=read(destination/'metrics.json')
    def compare(a,b):
        if isinstance(a,dict):
            assert set(a)==set(b)
            for key in a:compare(a[key],b[key])
        elif isinstance(a,(float,int)) and not isinstance(a,bool):assert_prediction(a,b)
        else:assert a==b
    compare(computed,expected)
    save(destination/'fresh-process-check.json',{'passed':True,'offline':True,'atol':1e-10,'rtol':0,
        'model_predictions_checked':checks,'metrics_recalculated':True,'cohorts_weights_contracts_checked':True,
        'hidden_queries_checked':run_id!='A03','run':run_id})
    print('Recuperación verificada',run_id,'comprobaciones de modelos:',checks,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['run','verify']);parser.add_argument('run',choices=['A01','A02','A03'])
    args=parser.parse_args()
    if args.mode=='verify':recover(args.run)
    elif args.run=='A03':execute_curve()
    else:execute_comparison(args.run)
