"""Entrenamiento/recuperación con población y protocolo íntegros."""
import sys
from dataclasses import asdict
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
from .common import ROOT,ID,TARGET,SCHEMES,read,save,digest,now
from .registry import protocol
from .modeling import Recipe,table,fit,select,metric,Reference

def load():
    master=pd.read_parquet(ROOT/'data/processed/parcels.parquet')
    base={name:pd.read_parquet(ROOT/f'data/processed/control-{name}.parquet') for name in ['official','enriched']}
    for X in base.values(): X['Estado']=master.set_index(ID).loc[X.index,'Estado']
    blocks={'R':pd.read_parquet(ROOT/'data/processed/block-radiation.parquet')}
    soil=ROOT/'data/processed/block-soil.parquet'
    if soil.exists(): blocks['G']=pd.read_parquet(soil)
    weekly=pd.read_parquet(ROOT/'data/processed/weekly-inputs.parquet')
    schemes=pd.read_csv(ROOT/'registry/schemes.csv')
    return master,base,blocks,weekly,schemes

def grouped_metrics(frame):
    summary={k:metric(frame[TARGET],frame[k]) for k in ['prediction','regional_mean','global_mean']}
    summary['by_state']={str(s):{'n':len(g),'prediction':metric(g[TARGET],g.prediction),'regional':metric(g[TARGET],g.regional_mean)} for s,g in frame.groupby('Estado')}
    summary['by_fold']={str(s):{'n':len(g),'metrics':metric(g[TARGET],g.prediction)} for s,g in frame.groupby('spatial_group')}
    # Area bins are descriptive only and never feed selection.
    q=pd.qcut(frame.AREA_HA.rank(method='first'),3,labels=['small','middle','large'])
    summary['by_area']={str(s):{'n':len(g),'metrics':metric(g[TARGET],g.prediction)} for s,g in frame.groupby(q,observed=True)}
    return summary

def train(run):
    p=protocol();master,base,blocks,weekly,schemes=load()
    recipes=[Recipe(r['family'],r['setting'],tuple(r['blocks']),r['source']) for r in p['catalog']['variants'][run]]
    semantic='S' in p['catalog']['available_blocks']
    y=master[TARGET].to_numpy();states=master.Estado.to_numpy()
    labeled=np.flatnonzero(np.isfinite(y));hidden=np.flatnonzero(~np.isfinite(y));folder=ROOT/f'runs/{run}'
    reports={}
    with threadpool_limits(limits=2):
        for scheme in SCHEMES:
            mapping=schemes[schemes.scheme.eq(scheme)].set_index(ID).fold
            groups=master[ID].map(mapping).fillna(-1).to_numpy(dtype=int)
            frame=master.iloc[labeled][[ID,'Estado','Municipio','AREA_HA',TARGET]].copy()
            frame['spatial_group']=groups[labeled]
            for c in ['prediction','regional_mean','global_mean']:frame[c]=np.nan
            selections=[]
            for f in sorted(set(groups[labeled])):
                tr=labeled[groups[labeled]!=f];va=labeled[groups[labeled]==f]
                if len(tr)<80 or len(va)<15:raise ValueError('Tamaño externo insuficiente')
                recipe,decision=select(run,recipes,tr,y,groups,states,base,blocks,weekly,semantic)
                model=fit(recipe,tr,y,base,blocks,weekly,semantic)
                predictions=model.predict(table(recipe,base,blocks).iloc[va])
                if not np.isfinite(predictions).all():raise ValueError('OOF no finita')
                frame.loc[va,'prediction']=predictions
                for c,regional in [('regional_mean',True),('global_mean',False)]:
                    frame.loc[va,c]=Reference(regional).fit(base['official'].iloc[tr],y[tr]).predict(base['official'].iloc[va])
                selections.append({'fold':int(f),'train_n':len(tr),'validation_n':len(va),'train_state_counts':pd.Series(states[tr]).value_counts().to_dict(),'decision':decision})
                print(run,scheme,'fold',f,'winner',recipe.id,flush=True)
            assert len(frame)==138 and frame[ID].is_unique and np.isfinite(frame[['prediction','regional_mean','global_mean']]).all().all()
            frame.to_csv(folder/f'oof-{scheme}.csv',index=False,float_format='%.17g')
            reports[scheme]=grouped_metrics(frame)
            save(folder/f'metrics-{scheme}.json',reports[scheme]);save(folder/f'selections-{scheme}.json',selections)
        main=schemes[schemes.scheme.eq(SCHEMES[0])].set_index(ID).fold
        groups=master[ID].map(main).fillna(-1).to_numpy(dtype=int)
        recipe,decision=select(run,recipes,labeled,y,groups,states,base,blocks,weekly,semantic)
        model=fit(recipe,labeled,y,base,blocks,weekly,semantic)
        X=table(recipe,base,blocks)
        prediction=model.predict(X.iloc[hidden])
        if len(prediction)!=59 or not np.isfinite(prediction).all() or (prediction<0).any():raise ValueError('Exportación inválida')
        pd.DataFrame({ID:master.iloc[hidden][ID].to_numpy(),TARGET:prediction}).to_csv(folder/'predictions_59.csv',index=False,float_format='%.17g')
        joblib.dump({'model':model,'recipe':recipe,'decision':decision},folder/'model.joblib')
        used=model.named_steps['numeric'].columns_ if hasattr(model,'named_steps') else []
        save(folder/'contract.json',{'run':run,'recipe':asdict(recipe),'columns':list(X.columns),'used_numeric_columns':used,
         'model_hash':digest(folder/'model.joblib'),'protocol_hash':digest(ROOT/'registry/frozen-protocol.json'),
         'data_hashes':p['hashes'],'new_block_admitted':decision['new_block_admitted'],'interval_available':False,
         'training_ids':master.iloc[labeled][ID].tolist(),'hidden_ids':master.iloc[hidden][ID].tolist()})
        save(folder/'final-selection.json',decision)
        save(folder/'metrics.json',reports)

def verify(run):
    p=protocol();master,base,blocks,weekly,schemes=load();folder=ROOT/f'runs/{run}'
    contract=read(folder/'contract.json')
    assert digest(folder/'model.joblib')==contract['model_hash']
    assert digest(ROOT/'registry/frozen-protocol.json')==contract['protocol_hash']
    bundle=joblib.load(folder/'model.joblib');recipe=bundle['recipe'];model=bundle['model']
    X=table(recipe,base,blocks)
    assert list(X.columns)==contract['columns']
    hidden=np.flatnonzero(master[TARGET].isna());expected=pd.read_csv(folder/'predictions_59.csv',float_precision='round_trip')
    assert expected[ID].tolist()==master.iloc[hidden][ID].tolist() and len(expected)==59
    with threadpool_limits(limits=2):
        np.testing.assert_allclose(model.predict(X.iloc[hidden]),expected[TARGET],atol=1e-10,rtol=0)
        single=np.array([model.predict(X.iloc[[i]])[0] for i in hidden])
        np.testing.assert_allclose(single,expected[TARGET],atol=1e-10,rtol=0)
    for scheme in SCHEMES:
        frame=pd.read_csv(folder/f'oof-{scheme}.csv',float_precision='round_trip')
        assert len(frame)==138 and frame[ID].is_unique
        assignment=schemes[schemes.scheme.eq(scheme)].set_index(ID).fold
        assert np.array_equal(frame.spatial_group,frame[ID].map(assignment))
        current=grouped_metrics(frame);record=read(folder/f'metrics-{scheme}.json')
        def check(a,b):
            if isinstance(a,dict):
                assert a.keys()==b.keys()
                for k in a:check(a[k],b[k])
            elif a is None:assert b is None
            else:np.testing.assert_allclose(a,b,atol=1e-10,rtol=0)
        check(current,record)
    files={f.name:digest(f) for f in folder.iterdir() if f.is_file() and f.suffix in ['.json','.csv','.joblib'] and f.name not in ['fresh-process-check.json','recovery-package.json','run.json']}
    save(folder/'recovery-package.json',{'phase_root':str(ROOT),'protocol':str(ROOT/'registry/frozen-protocol.json'),
      'shared_inputs':p['hashes'],'artifacts':files,'model_or_context':True,'offline_verified':True,'atol':1e-10,'rtol':0})
    save(folder/'fresh-process-check.json',{'passed':True,'offline':True,'n_hidden':59,'metrics_recalculated':True,'batch_single_invariant':True,'atol':1e-10,'rtol':0,'at':now()})
    print(run,'recuperación y métricas verificadas',flush=True)

if __name__=='__main__':
    mode,run=sys.argv[1:]
    if mode=='train':train(run)
    elif mode=='verify':verify(run)
    else:raise ValueError('Modo de ejecución no registrado')
