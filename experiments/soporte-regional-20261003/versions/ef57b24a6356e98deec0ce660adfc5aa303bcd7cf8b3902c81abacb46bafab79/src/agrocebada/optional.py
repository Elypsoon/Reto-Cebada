"""TabPFN-2.5 local: contexto entrenado recuperable y entorno independiente."""
from pathlib import Path
import os,sys,subprocess,json,time
import numpy as np
import pandas as pd
from .common import ROOT,PROCESSED,ARTIFACTS,ID,TARGET,sha256,code_hash,SEED
from .tracking import Registry,read,atomic_json,compare_frames,LIMITATION

OPTIONAL=ROOT/'optional/tabpfn-2.5'

def worker_env():
    return dict(os.environ,PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1',TABPFN_DISABLE_TELEMETRY='1',HF_HUB_OFFLINE='1',TABPFN_MODEL_CACHE_DIR=str(OPTIONAL))

def estimator():
    import torch
    from tabpfn import TabPFNRegressor
    torch.set_num_threads(2)
    info=read(OPTIONAL/'manifest.json')
    if sha256(OPTIONAL/info['checkpoint'])!=info['sha256']:raise ValueError('Checkpoint alterado')
    if sha256(OPTIONAL/'LICENSE')!=info['license_sha256']:raise ValueError('Licencia alterada')
    return TabPFNRegressor(model_path=OPTIONAL/info['checkpoint'],**info['parameters'])

def inspect_optional():
    from importlib.metadata import version
    import psutil,torch
    started=time.perf_counter()
    # Smoke check uses synthetic labels only; no parcel outcome is inspected.
    rng=np.random.default_rng(SEED);x=rng.normal(size=(80,12));y=x[:,0]*.3+x[:,1]+3
    model=estimator().fit(x[:60],y[:60]);p=model.predict(x[60:]);assert np.isfinite(p).all()
    config=read(OPTIONAL/'manifest.json')
    result={'available':True,'reason':None,'versions':{name:version(name) for name in ['tabpfn','torch','numpy','pandas','scikit-learn','scipy']},'checkpoint':config,'device':'cpu','threads':2,'smoke_seconds':time.perf_counter()-started,'smoke_rss_mb':psutil.Process().memory_info().rss/1024**2,'available_memory_mb':psutil.virtual_memory().available/1024**2,'no_active_dependencies_changed':True}
    result.update(requirements_lock_hash=sha256(OPTIONAL/'requirements.lock'),effective_parameters={key:repr(value) for key,value in model.get_params().items()})
    atomic_json(OPTIONAL/'preflight.json',result);print(result,flush=True)

def worker(key,destination,verify=False):
    import psutil
    from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
    def metric(y,p):return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'bias':float(np.mean(p-y))}
    started=time.perf_counter();destination=Path(destination)
    master=pd.read_parquet(PROCESSED/'parcels.parquet');table=pd.read_parquet(PROCESSED/f'features_{key}.parquet').reindex(master[ID]);x=table.to_numpy(dtype=float);y=master[TARGET].to_numpy();train=np.flatnonzero(np.isfinite(y));hidden=np.flatnonzero(~np.isfinite(y))
    if verify:
        context=np.load(destination/'training-context.npz')
        config=read(destination/'context-contract.json')
        if list(table.columns)!=config['columns'] or sha256(PROCESSED/f'features_{key}.parquet')!=config['table_hash'] or code_hash()!=config['code_hash']:raise ValueError('Contexto incompatible')
        model=estimator().fit(context['X'],context['y']);pred=model.predict(x[hidden]);saved=pd.read_csv(destination/'predictions_official_only_59.csv').set_index(ID).reindex(master.iloc[hidden][ID])
        assert np.allclose(pred,saved[TARGET],rtol=0,atol=1e-10)
        atomic_json(destination/'fresh-process-check.json',{'passed':True,'predictions':59,'checkpoint_hash':read(OPTIONAL/'manifest.json')['sha256'],'context_hash':sha256(destination/'training-context.npz'),'tolerance':1e-10});return
    groups=pd.read_csv(ROOT/'registry/schemes.csv');metrics={}
    for scheme in ['principal-5','balanceado-4','rotado-45-5']:
        assignments=groups[groups.scheme.eq(scheme)].set_index(ID).reindex(master.iloc[train][ID]).fold.to_numpy();pred=np.zeros(len(train));records=[]
        for fold in sorted(np.unique(assignments)):
            tr=train[assignments!=fold];va=train[assignments==fold]
            print(key,scheme,fold,'train',len(tr),'validation',len(va),flush=True)
            fit=estimator().fit(x[tr],y[tr]);p=fit.predict(x[va]);pred[assignments==fold]=p
            records.append({'fold':int(fold),'train_ids':master.iloc[tr][ID].tolist(),'validation_ids':master.iloc[va][ID].tolist(),'state_counts':master.iloc[tr].Estado.value_counts().to_dict(),'metrics':metric(y[va],p)})
            del fit
        frame=master.iloc[train][[ID,'Estado','Municipio','AREA_HA',TARGET]].copy();frame['spatial_group']=assignments;frame['official']=pred;frame.to_csv(destination/f'oof-{scheme}.csv',index=False)
        metrics[scheme]=metric(y[train],pred)
        atomic_json(destination/f'validation-{scheme}.json',{'metrics':metrics[scheme],'by_state':{s:metric(z[TARGET],z.official) for s,z in frame.groupby('Estado')},'folds':records,'parameters':read(OPTIONAL/'manifest.json')['parameters']})
    fit=estimator().fit(x[train],y[train]);pred=fit.predict(x[hidden])
    if not np.isfinite(pred).all() or (pred<0).any():raise ValueError('Predicciones no válidas')
    np.savez(destination/'training-context.npz',X=x[train],y=y[train],ids=master.iloc[train][ID].to_numpy(dtype=str))
    atomic_json(destination/'context-contract.json',{'columns':list(table.columns),'table_hash':sha256(PROCESSED/f'features_{key}.parquet'),'code_hash':code_hash(),'checkpoint':read(OPTIONAL/'manifest.json'),'versions':read(OPTIONAL/'preflight.json')['versions'],'transformations':'preprocesadores TabPFN aprendidos en fit; contexto de train conservado; fit_preprocessors; faltantes nativos'})
    pd.DataFrame({ID:master.iloc[hidden][ID].to_numpy(),TARGET:pred}).sort_values(ID).to_csv(destination/'predictions_official_only_59.csv',index=False)
    atomic_json(destination/'worker-metrics.json',metrics)
    atomic_json(destination/'resources.json',{'seconds':time.perf_counter()-started,'rss_at_end_mb':psutil.Process().memory_info().rss/1024**2,'device':'cpu','threads':2})

def run_optional(protocol):
    registry=Registry(ROOT);registry.transition('E07','running');main=ROOT/'runs/E07'
    try:
        results={}
        for key in protocol['keys']:
            rid='E07-'+key;folder=ROOT/'runs'/rid;registry.validate_protocol(rid);registry.transition(rid,'running')
            try:
                arguments=[str(OPTIONAL/'env/Scripts/python.exe'),'-m','agrocebada.optional','run',key,str(folder/'artifacts')]
                subprocess.run(arguments,env=worker_env(),cwd=ROOT,check=True)
                subprocess.run([*arguments[:3],'verify',key,str(folder/'artifacts')],env=worker_env(),cwd=ROOT,check=True)
                metrics=read(folder/'artifacts/worker-metrics.json')
                for scheme in metrics:
                    frame=pd.read_csv(folder/f'artifacts/oof-{scheme}.csv');control=pd.read_csv(ROOT/f'runs/E00/artifacts/oof-{scheme}.csv')
                    paired=compare_frames(frame,control,'official');paired.to_csv(folder/f'artifacts/comparison-{scheme}-official.csv',index=False)
                    metrics[scheme]['control_delta_rmse']=metrics[scheme]['rmse']-float(np.sqrt(np.mean((control.official-control[TARGET])**2)))
                changes={'model_absent':False,'family':'TabPFN-2.5','table':key,'checkpoint':read(OPTIONAL/'manifest.json'),'context_hash':sha256(folder/'artifacts/training-context.npz'),'control':'E00','model_format':'checkpoint y contexto; no joblib convencional'}
                registry.finish(rid,{'official':metrics},read(folder/'artifacts/fresh-process-check.json'),changes,{'eligible':False,'activated':False,'promotion_scope':'exploratorio','reason':'Configuración fija; no selección externa ni incorporación en E08'})
                results[key]=metrics
            except BaseException as error:
                registry.transition(rid,'failed',repr(error));raise
        registry.finish('E07',results,{'passed':True,'configurations':list(results)},{'model_absent':False,'children':['E07-'+k for k in protocol['keys']]},{'eligible':False,'activated':False,'reason':'Dos configuraciones fijas registradas individualmente'})
    except BaseException as error:
        registry.transition('E07','failed',repr(error));raise

def main():
    if sys.argv[1]=='inspect':inspect_optional()
    else:worker(sys.argv[2],sys.argv[3],sys.argv[1]=='verify')

if __name__=='__main__':main()
