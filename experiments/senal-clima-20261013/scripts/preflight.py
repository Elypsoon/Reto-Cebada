"""Entrena/recupera con datos inventados en una réplica temporal aislada y sin red."""
from pathlib import Path
import sys
import shutil
from dataclasses import asdict
import subprocess
import os
import json
PHASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PHASE/'src'))
from signalclima.common import ROOT,ID,TARGET,SCHEMES,WINDOWS,save,read,digest,now,safe
from signalclima.modeling import Recipe,catalog
import numpy as np
import pandas as pd

if (ROOT/'registry/frozen-protocol.json').exists():raise ValueError('Preflight previo a congelación solamente')
clone=safe(ROOT/'tmp'/('preflight-'+now().replace(':','').replace('+','')));clone.mkdir(parents=True,exist_ok=False)
for folder in ['src','scripts','controls/C-activa/src']:
    shutil.copytree(ROOT/folder,clone/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copyfile(ROOT/'requirements.lock',clone/'requirements.lock')
rng=np.random.default_rng(2026);ids=pd.Index([f'synthetic-{i:03}' for i in range(197)],name=ID)
base=pd.DataFrame(rng.normal(size=(197,6)),index=ids,columns=[f'x{i}' for i in range(6)])
signal=pd.DataFrame({f'H_signal_{w}':rng.normal(size=197) for w in WINDOWS},index=ids)
daily=pd.DataFrame({f'D_precip_{w}':rng.uniform(10,200,size=197) for w in WINDOWS},index=ids)
main=pd.DataFrame({f'M_{n}_{w}':rng.normal(size=197) for w in WINDOWS for n in ['vpd','tmean']},index=ids)
y=3+base.x0*.8+signal.H_signal_early*.2+rng.normal(0,.1,197);y.iloc[138:]=np.nan
master=pd.DataFrame({ID:ids,'Estado':np.where(np.arange(197)%2,'A','B'),'Municipio':'synthetic','AREA_HA':np.arange(197)+1.,TARGET:y.to_numpy()})
processed=clone/'data/processed';processed.mkdir(parents=True)
master.to_parquet(processed/'parcels.parquet',index=False)
for key in ['monthly_40_10','whittaker_40_10']:base.to_parquet(processed/f'features_{key}.parquet')
pd.DataFrame({'nasa_synthetic':rng.normal(size=197)},index=ids).to_parquet(processed/'external_nasa.parquet')
pd.DataFrame(index=ids).to_parquet(processed/'quality-common.parquet')
for block,frame in [('D',daily),('H',signal),('M',pd.concat([daily,signal,main],axis=1))]:frame.to_parquet(processed/f'block-{block}.parquet')
context=pd.DataFrame([{ID:pid,'window':w,'interval':j,'days':14,'cell':f'cell-{i%4}',
                       'signal':signal.loc[pid,f'H_signal_{w}'],'vpd':float(j+i%4),'tmean':float(j+i%4)+10} for i,pid in enumerate(ids) for w in WINDOWS for j in range(4)])
context.to_parquet(processed/'paired-intervals.parquet',index=False)
(clone/'registry').mkdir()
pd.concat([pd.DataFrame({ID:ids[:138],'scheme':s,'fold':np.arange(138)%n}) for s,n in zip(SCHEMES,[5,4,5])]).to_csv(clone/'registry/schemes.csv',index=False)
for name,value in [('viability',{'available':['D','H','M','I'],'H':{'admitted':True},'synthetic':True}),('nasa-audit',{'synthetic':True}),
                   ('spectral-audit',{'synthetic':True}),('preflight',{'synthetic':True,'passed':False})]:
    (clone/f'registry/{name}.json').write_text(json.dumps(value))
env={**os.environ,'PYTHONPATH':str(clone/'src'),'PYTHONDONTWRITEBYTECODE':'1','PROJ_NETWORK':'OFF','MKL_CBWR':'COMPATIBLE',
     **{name:'2' for name in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']}}
variants={'F00':[Recipe('monthly_40_10','gpr',1),Recipe('monthly_40_10','elastic',.05)]+[Recipe('monthly_40_10',f) for f in ['global_mean','regional_mean']],
          'F04':[Recipe('monthly_40_10','elastic',.05,False,p) for p in ['M','I']]+[Recipe('monthly_40_10',f) for f in ['global_mean','regional_mean']]}
# The fixture protocol belongs exclusively to this synthetic replica, never the actual phase.
bootstrap="from signalclima.common import ROOT,save,runtime;from signalclima.registry import input_hashes;import json;save(ROOT/'registry/frozen-protocol.json',{'hashes':input_hashes(),'dependencies':runtime(),'variants':json.loads("+repr(json.dumps({k:[asdict(r) for r in v] for k,v in variants.items()}))+"),'synthetic':True})"
subprocess.run([sys.executable,'-c',bootstrap],cwd=clone,env=env,check=True)
records={}
for run in variants:
    subprocess.run([sys.executable,str(clone/'scripts/execute.py'),run],cwd=clone,env=env,check=True)
    record=read(clone/f'runs/{run}/fresh-process-check.json')
    if not record['passed'] or record['n_hidden']!=59:raise ValueError('Preflight de recuperación incompleto')
    records[run]={'proof':record,'train_resources':read(clone/f'runs/{run}/resources-run.json'),'verify_resources':read(clone/f'runs/{run}/resources-verify.json')}
full,_=catalog(['D','H','M','I'])
fits={k:57*len(v)+15 for k,v in full.items()}
save(ROOT/'registry/preflight.json',{'at':now(),'passed':True,'synthetic':True,'real_labels_used':False,'root':str(clone),'runs':records,
 'unique_candidates_max':82,'expected_fit_upper_bound_all_viable':fits,'all_viable_total':sum(fits.values()),
 'method':'sum outer k*(k-1)*c plus outer k; final 5*c+1; k=5,4,5, before failures',
 'limits':{'run_seconds':21600,'tree_memory_bytes':6*1024**3,'threads':2},
 'production_frozen':False,'code_hashes':{str(p.relative_to(ROOT)):digest(p) for folder in ['src','scripts'] for p in (ROOT/folder).rglob('*.py')}})
print('Preflight sintético recuperado; ninguna etiqueta real utilizada.',flush=True)
