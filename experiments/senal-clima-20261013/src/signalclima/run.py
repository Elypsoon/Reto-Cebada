import sys
from dataclasses import asdict
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
from .common import ROOT,ID,TARGET,SCHEMES,read,save,digest,now
from .registry import protocol
from .modeling import Recipe,fit,select,table,original


def load():
    master=pd.read_parquet(ROOT/'data/processed/parcels.parquet').reset_index(drop=True)
    keys=['monthly_40_10','whittaker_40_10']
    tables={k:pd.read_parquet(ROOT/f'data/processed/features_{k}.parquet').reindex(master[ID]) for k in keys}
    nasa=pd.read_parquet(ROOT/'data/processed/external_nasa.parquet').reindex(master[ID])
    quality=pd.read_parquet(ROOT/'data/processed/quality-common.parquet').reindex(master[ID])
    blocks={}
    for name in ['D','H','M']:
        p=ROOT/f'data/processed/block-{name}.parquet'
        if p.exists():blocks[name]=pd.read_parquet(p).reindex(master[ID])
    regions=pd.get_dummies(master.Estado,prefix='region',prefix_sep='__',dtype=float);regions.index=pd.Index(master[ID],name=ID)
    context_path=ROOT/'data/processed/paired-intervals.parquet'
    context=pd.read_parquet(context_path) if context_path.exists() else pd.DataFrame()
    inputs={'tables':tables,'nasa':nasa,'quality':quality,'blocks':blocks,'regions':regions,'context':context,
            'semantic':read(ROOT/'registry/viability.json').get('H',{}).get('admitted',False)}
    assert all(X.index.equals(pd.Index(master[ID],name=ID)) for X in [*tables.values(),nasa,quality,regions,*blocks.values()])
    return master,inputs,pd.read_csv(ROOT/'registry/schemes.csv')


def metric(y,p):
    return {**original.metric(y,p),'bias':float(np.mean(np.asarray(p)-np.asarray(y)))}


def grouped_metrics(frame):
    out={name:metric(frame[TARGET],frame[name]) for name in ['prediction','regional_mean','global_mean']}
    out['by_state']={str(s):{'n':len(g),'prediction':metric(g[TARGET],g.prediction),'regional':metric(g[TARGET],g.regional_mean)} for s,g in frame.groupby('Estado')}
    out['by_fold']={str(s):{'n':len(g),'metrics':metric(g[TARGET],g.prediction)} for s,g in frame.groupby('spatial_group')}
    bins=pd.qcut(frame.AREA_HA.rank(method='first'),3,labels=['small','middle','large'])
    out['by_area']={str(s):{'n':len(g),'metrics':metric(g[TARGET],g.prediction)} for s,g in frame.groupby(bins,observed=True)}
    return out


def train(run):
    p=protocol();master,inputs,schemes=load()
    if run not in p['variants']:raise ValueError('Ejecución no viable/no registrada')
    folder=ROOT/'runs'/run
    if read(folder/'run.json')['status']!='running':raise ValueError('Estado incompatible con entrenamiento')
    recipes=[Recipe(**r) for r in p['variants'][run]]
    y=master[TARGET].to_numpy();states=master.Estado.to_numpy();labeled=np.flatnonzero(np.isfinite(y));hidden=np.flatnonzero(~np.isfinite(y));reports={}
    with threadpool_limits(limits=2):
        for scheme in SCHEMES:
            mapping=schemes[schemes.scheme.eq(scheme)].set_index(ID).fold
            groups=master[ID].map(mapping).fillna(-1).to_numpy(dtype=int)
            frame=master.iloc[labeled][[ID,'Estado','Municipio','AREA_HA',TARGET]].copy();frame['spatial_group']=groups[labeled]
            for name in ['prediction','regional_mean','global_mean']:frame[name]=np.nan
            selections=[]
            for f in sorted(set(groups[labeled])):
                tr=labeled[groups[labeled]!=f];va=labeled[groups[labeled]==f]
                if len(tr)<80 or len(va)<15:raise ValueError('Tamaño externo insuficiente')
                recipe,decision=select(run,recipes,tr,y,groups,states,inputs)
                model=fit(recipe,tr,y,**inputs);X=table(recipe,**{k:inputs[k] for k in ['tables','nasa','blocks','quality','regions']})
                frame.loc[va,'prediction']=model.predict(X.iloc[va])
                references=original.baseline_predictions(y[tr],states[tr],states[va])
                for name in ['regional_mean','global_mean']:frame.loc[va,name]=references[name]
                selections.append({'fold':int(f),'train_n':len(tr),'validation_n':len(va),'train_state_counts':pd.Series(states[tr]).value_counts().to_dict(),'decision':decision})
                print(run,scheme,'fold',f,decision['winner'],flush=True)
            assert len(frame)==138 and frame[ID].is_unique and np.isfinite(frame[['prediction','regional_mean','global_mean']]).all().all()
            frame.to_csv(folder/f'oof-{scheme}.csv',index=False,float_format='%.17g')
            reports[scheme]=grouped_metrics(frame);save(folder/f'metrics-{scheme}.json',reports[scheme]);save(folder/f'selections-{scheme}.json',selections)
        main=schemes[schemes.scheme.eq(SCHEMES[0])].set_index(ID).fold
        groups=master[ID].map(main).fillna(-1).to_numpy(dtype=int)
        recipe,decision=select(run,recipes,labeled,y,groups,states,inputs);model=fit(recipe,labeled,y,**inputs)
        X=table(recipe,**{k:inputs[k] for k in ['tables','nasa','blocks','quality','regions']});predictions=model.predict(X.iloc[hidden])
        if len(predictions)!=59 or not np.isfinite(predictions).all():raise ValueError('Exportación incompleta/no finita')
        pd.DataFrame({ID:master.iloc[hidden][ID].to_numpy(),TARGET:predictions}).to_csv(folder/'predictions_59.csv',index=False,float_format='%.17g')
        joblib.dump({'model':model,'recipe':recipe,'decision':decision},folder/'model.joblib')
        used=model.named_steps['select'].columns_
        save(folder/'contract.json',{'run':run,'recipe':asdict(recipe),'columns':list(X.columns),'used_columns':list(used),'model_hash':digest(folder/'model.joblib'),
             'protocol_hash':digest(ROOT/'registry/frozen-protocol.json'),'data_hashes':p['hashes'],'new_information_used':bool(recipe.profile),'hidden_ids':master.iloc[hidden][ID].tolist(),'interval_available':False})
        save(folder/'final-selection.json',decision);save(folder/'metrics.json',reports)


def check_nested(a,b):
    if isinstance(a,dict):
        assert a.keys()==b.keys()
        for key in a:check_nested(a[key],b[key])
    elif a is None:assert b is None
    else:np.testing.assert_allclose(a,b,atol=1e-10,rtol=0)


def verify(run):
    p=protocol();master,inputs,schemes=load();folder=ROOT/'runs'/run;contract=read(folder/'contract.json')
    if digest(folder/'model.joblib')!=contract['model_hash'] or digest(ROOT/'registry/frozen-protocol.json')!=contract['protocol_hash']:raise ValueError('Contrato/modelo incompatible')
    bundle=joblib.load(folder/'model.joblib');recipe=bundle['recipe'];model=bundle['model']
    if contract['data_hashes']!=p['hashes'] or contract['recipe']!=asdict(recipe) or contract['run']!=run:
        raise ValueError('Contrato de datos/receta incompatible')
    if asdict(recipe) not in p['variants'][run] or contract['used_columns']!=list(model.named_steps['select'].columns_):
        raise ValueError('Receta/selector fuera del contrato')
    X=table(recipe,**{k:inputs[k] for k in ['tables','nasa','blocks','quality','regions']})
    if list(X.columns)!=contract['columns']:raise ValueError('Columnas incompatibles')
    hidden=np.flatnonzero(master[TARGET].isna());expected=pd.read_csv(folder/'predictions_59.csv',float_precision='round_trip')
    if contract['hidden_ids']!=master.iloc[hidden][ID].tolist():raise ValueError('IDs ocultos incompatibles')
    assert len(expected)==59 and expected[ID].tolist()==master.iloc[hidden][ID].tolist()
    with threadpool_limits(limits=2):
        np.testing.assert_allclose(model.predict(X.iloc[hidden]),expected[TARGET],atol=1e-10,rtol=0)
        individual=[model.predict(X.iloc[[i]])[0] for i in hidden]
        np.testing.assert_allclose(individual,expected[TARGET],atol=1e-10,rtol=0)
    for scheme in SCHEMES:
        frame=pd.read_csv(folder/f'oof-{scheme}.csv',float_precision='round_trip');assert len(frame)==138 and frame[ID].is_unique
        mapping=schemes[schemes.scheme.eq(scheme)].set_index(ID).fold
        assert np.array_equal(frame.spatial_group,frame[ID].map(mapping))
        labels=master.set_index(ID).loc[frame[ID],TARGET].to_numpy()
        np.testing.assert_array_equal(labels,frame[TARGET])
        check_nested(grouped_metrics(frame),read(folder/f'metrics-{scheme}.json'))
    artifacts={f.name:digest(f) for f in folder.iterdir() if f.is_file() and f.suffix in ['.csv','.json','.joblib'] and f.name not in ['run.json','fresh-process-check.json','recovery-package.json']}
    save(folder/'recovery-package.json',{'shared_inputs':p['hashes'],'artifacts':artifacts,'offline_verified':True,'atol':1e-10,'rtol':0})
    save(folder/'fresh-process-check.json',{'at':now(),'passed':True,'offline':True,'n_hidden':59,'metrics_recalculated':True,'batch_single_invariant':True})
    print(run,'recuperado y verificado sin red',flush=True)


if __name__=='__main__':
    mode,run=sys.argv[1:]
    if mode=='train':train(run)
    elif mode=='verify':verify(run)
    else:raise ValueError('Modo no registrado')
