"""Reintento versionado de E07; exportación float64 sin cambiar el modelo."""
from pathlib import Path
import sys,os,shutil,subprocess,time
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from agrocebada.tracking import Registry,read,atomic_json,manifest,check_manifest,compare_frames
from agrocebada.common import sha256,TARGET
import numpy as np,pandas as pd
registry=Registry(root)
reason='CSV de float32 redondeó hasta 2.2082519546273716e-7; predicciones reconstruidas idénticas al convertir el CSV a float32. Se exporta float64 con 17 dígitos, sin modificar modelo, parámetros, tablas ni particiones. Nuevos IDs y código separado.'
adapter=root/'optional/adapter-v3'
assert not adapter.exists()
shutil.copytree(root/'src',adapter/'src',ignore=shutil.ignore_patterns('__pycache__'))
for name in ['workspace.json','requirements.lock','pyproject.toml']:shutil.copy2(root/name,adapter/name)
shutil.copytree(root/'data/processed',adapter/'data/processed')
(adapter/'registry').mkdir();shutil.copy2(root/'registry/schemes.csv',adapter/'registry/schemes.csv')
optional=adapter/'optional/tabpfn-2.5';optional.mkdir(parents=True)
for name in ['manifest.json','preflight.json','requirements.lock','LICENSE','tabpfn-v2.5-regressor-v2.5_default.ckpt']:shutil.copy2(root/'optional/tabpfn-2.5'/name,optional/name)
source=adapter/'src/agrocebada/optional.py';original=source.read_text(encoding='utf-8')
old="TARGET:pred}).sort_values(ID).to_csv(destination/'predictions_official_only_59.csv',index=False)"
new="TARGET:pred.astype(np.float64)}).sort_values(ID).to_csv(destination/'predictions_official_only_59.csv',index=False,float_format='%.17g')"
assert original.count(old)==1;source.write_text(original.replace(old,new).replace("pd.read_csv(destination/'predictions_official_only_59.csv')","pd.read_csv(destination/'predictions_official_only_59.csv',float_precision='round_trip')"),encoding='utf-8')
atomic_json(adapter/'manifest.json',manifest(adapter))
env=dict(os.environ,PYTHONPATH=str(adapter/'src'),PYTHONDONTWRITEBYTECODE='1',AGROCEBADA_ARTIFACTS=str(adapter/'artifacts'),TABPFN_DISABLE_TELEMETRY='1',HF_HUB_OFFLINE='1',PYTHONIOENCODING='utf-8')
python=root/'optional/tabpfn-2.5/env/Scripts/python.exe'
digest=subprocess.check_output([str(python),'-c','from agrocebada.common import code_hash; print(code_hash())'],env=env,cwd=adapter,text=True).strip()
oldprotocol=read(root/'runs/E07-v2/protocol.json');protocol={**oldprotocol,'adapter_code_hash':digest,'adapter_manifest_hash':sha256(adapter/'manifest.json'),'revision_reason':reason,'worker_root':str(adapter),'revision':3}
rid='E07-v3'
pending='E07-v2-whittaker_20_10'
if read(root/'runs'/pending/'run.json')['status']=='frozen':registry.transition(pending,'failed','No llegó a entrenar: falló la comprobación de exportación de su configuración hermana. Sustituida por E07-v3-whittaker_20_10.')
registry.create('E07',protocol,control='E00-v2',run_id=rid,retry_of='E07-v2')
for key in protocol['keys']:registry.create('E07',{**protocol,'keys':[key],'optional_config':key},control='E00-v2',parent=rid,run_id=rid+'-'+key,retry_of='E07-v2-'+key)
atomic_json(root/'registry/optional-retry-catalog.json',{'revision':3,'reason':reason,'no_model_selection_change':True,'adapter_code_hash':digest,'adapter_manifest_hash':sha256(adapter/'manifest.json'),'base_catalog_hash':sha256(root/'registry/catalog.json'),'runs':{run:sha256(root/'runs'/run/'protocol.json') for run in [rid]+[rid+'-'+k for k in protocol['keys']]}})
receipt=sha256(root/'registry/optional-retry-catalog.json');atomic_json(root/'registry/optional-retry-receipt.json',{'sha256':receipt})
registry.transition(rid,'running');results={}
try:
    for key in protocol['keys']:
        child=rid+'-'+key;folder=root/'runs'/child;registry.transition(child,'running')
        try:
            assert check_manifest(adapter,read(adapter/'manifest.json'))
            with (folder/'execution.log').open('a',encoding='utf-8') as log:
                for action in ['run','verify']:subprocess.run([str(python),'-m','agrocebada.optional',action,key,str(folder/'artifacts')],env=env,cwd=adapter,stdout=log,stderr=subprocess.STDOUT,check=True)
            metrics=read(folder/'artifacts/worker-metrics.json')
            for scheme in metrics:
                frame=pd.read_csv(folder/f'artifacts/oof-{scheme}.csv');control=pd.read_csv(root/f'runs/E00-v2/artifacts/oof-{scheme}.csv')
                compare_frames(frame,control,'official').to_csv(folder/f'artifacts/comparison-{scheme}-official.csv',index=False)
                metrics[scheme]['control_delta_rmse']=metrics[scheme]['rmse']-float(np.sqrt(np.mean((control.official-control[TARGET])**2)))
            assert check_manifest(adapter,read(adapter/'manifest.json')) and sha256(root/'registry/optional-retry-catalog.json')==receipt
            changes={'model_absent':False,'family':'TabPFN-2.5','table':key,'checkpoint':read(optional/'manifest.json'),'context_hash':sha256(folder/'artifacts/training-context.npz'),'model_format':'checkpoint y contexto; no joblib convencional','adapter_code_hash':digest,'adapter_manifest_hash':sha256(adapter/'manifest.json'),'adapter_root':str(adapter),'previous_run': 'E07-v2-'+key,'procedure_change':reason,'model_parameters_changed':False}
            registry.finish(child,{'official':metrics},read(folder/'artifacts/fresh-process-check.json'),changes,{'eligible':False,'activated':False,'promotion_scope':'exploratorio','reason':'Configuración fija separada; sin incorporación en E08'})
            results[key]=metrics;print(child,'cerrado',metrics,flush=True)
        except BaseException as error:registry.transition(child,'failed',repr(error));raise
    registry.finish(rid,{}, {'passed':True,'configurations':list(results)},{'model_absent':False,'children':[rid+'-'+k for k in protocol['keys']],'adapter_code_hash':digest},{'eligible':False,'activated':False,'reason':'Reintento de exportación; dos configuraciones fijas verificadas'})
except BaseException as error:registry.transition(rid,'failed',repr(error));raise
